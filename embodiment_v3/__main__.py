"""Run a local embodied session or a paired memory ablation."""
import argparse
import json
import os
import random
from pathlib import Path
from tempfile import TemporaryDirectory

from .agent import ChatAgent
from .session import Session


def memory_probe(classify, *, trials: int, seed: int) -> dict:
    rng = random.Random(seed)
    cases = ["self", "external"] * trials
    rng.shuffle(cases)
    results = []
    with TemporaryDirectory() as directory:

        for index, expected in enumerate(cases):
            checkpoint = Path(directory) / f"body-{index}.json"
            session = Session()
            action = "reach" if expected == "self" else rng.choice(("hold", "reach"))
            experience = session.turn(lambda _, selected=action: selected, external="hold" if expected == "self" else "push")
            if (experience["palm_contact"]["seconds"] <= 0
                    or session.audit[-1]["contact_added_by_action"] != (expected == "self")):
                raise RuntimeError("physics no longer matches the probe design")
            session.save(checkpoint)
            resumed = Session.load(checkpoint)
            conditions = ["with_history", "without_history"]
            rng.shuffle(conditions)
            row = {"expected": expected}
            for condition in conditions:
                # A retrospective query after restart: match the cue across cases
                # and withhold current geometry so it cannot identify the condition.
                observation = {"cue": "Recall the last left-palm contact."}
                if condition == "with_history":
                    observation["recent_experience"] = resumed.observation()["recent_experience"]
                row[condition] = classify(observation)
            results.append(row)
    return {
        "trials": results,
        "accuracy": {condition: sum(row[condition] == row["expected"] for row in results) / len(results)
                     for condition in ("with_history", "without_history")},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--steps", type=int, default=3)
    parser.add_argument("--model", help="enable calls to an OpenAI-compatible endpoint")
    parser.add_argument("--base-url", default="http://127.0.0.1:11434/v1")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--probe", action="store_true")
    mode.add_argument("--inspect-as", metavar="RELATIVE_PATH", help="print Kai checkpoint reference metadata")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if not 1 <= args.steps <= 100:
        parser.error("--steps must be between 1 and 100")
    if args.inspect_as:
        if not args.checkpoint:
            parser.error("--inspect-as requires --checkpoint")
        print(json.dumps(Session.inspect(args.checkpoint, reference_path=args.inspect_as), indent=2))
        return
    agent = ChatAgent(args.base_url, args.model, os.getenv("VBK_API_KEY")) if args.model else None
    if args.probe:
        if agent is None:
            parser.error("--probe requires --model")
        print(json.dumps(memory_probe(agent.attribute, trials=args.steps, seed=args.seed), indent=2))
        return

    session = Session.load(args.checkpoint) if args.checkpoint and args.checkpoint.exists() else Session()
    demo = (("reach", "hold"), ("withdraw", "reset"), ("hold", "push"))
    for offset in range(args.steps):
        if agent is not None:
            result = session.turn(agent)
        else:
            action, external = demo[offset % len(demo)]
            result = session.turn(lambda _, selected=action: selected, external=external)
        if args.checkpoint:
            session.save(args.checkpoint)
        print(json.dumps({"experience": result, "audit": session.audit[-1]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

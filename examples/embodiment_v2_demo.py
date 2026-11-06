"""Run from repository root: python -m examples.embodiment_v2_demo"""
from __future__ import annotations
import json
from embodiment_v2 import (EmbodimentEngine, HardwareBoundary, MotionIntent,
                           SensoryEvent, to_agent_context, to_kai_tags)


def main() -> None:
    body = EmbodimentEngine()
    body.step(0.1, [SensoryEvent("touch", "palm_left", .6, origin="simulated")])
    body.step(0.1, [SensoryEvent("vision", "face", .4, origin="sensor")],
              [MotionIntent("neck_yaw", 15.0, requested_speed_deg_s=15.0,
                            reason="turn head in a virtual environment")])
    print(json.dumps(to_agent_context(body), ensure_ascii=False, indent=2))
    print(to_kai_tags(body))
    print(json.dumps(HardwareBoundary.inspect(body), indent=2))


if __name__ == "__main__":
    main()

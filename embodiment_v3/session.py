"""Closed-loop simulated embodiment with resumable, source-labelled experience."""
from __future__ import annotations

import json
import os
from collections import deque
from collections.abc import Callable
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from embodiment_v2 import EmbodimentEngine, SensoryEvent, to_agent_context

from .physics import ACTIONS, STEPS, Physics

SCHEMA = "vbk.causal-session/1"
WINDOW = 64
Agent = Callable[[dict], str]


class Session:
    def __init__(self) -> None:
        self.lineage_id = uuid4().hex
        self._last_saved_digest = None
        self.physics = Physics()
        self.body = EmbodimentEngine()
        self.experience = deque(maxlen=WINDOW)
        self.audit = deque(maxlen=WINDOW)

    def observation(self, *, recall: bool = True) -> dict:
        # Serialize to detach data so a provider cannot mutate the running session.
        return _detached({
            "world": self.physics.observe(),
            "body": to_agent_context(self.body),
            "left_palm": asdict(self.body.region_state["palm_left"]),
            "latest_contact": self.experience[-1]["palm_contact"] if self.experience else None,
            "recent_experience": list(self.experience)[-8:] if recall else [],
        })

    def turn(self, agent: Agent, *, external: str = "hold", recall: bool = True) -> dict:
        if external not in ("hold", "push", "reset"):
            raise ValueError("unknown external condition")
        before = self.physics.observe()
        action = agent(self.observation(recall=recall))
        if not isinstance(action, str) or action not in ACTIONS:
            raise ValueError("agent must choose reach, withdraw or hold")

        # Both branches use the same initial state and environmental intervention.
        previous = self.physics.state()
        try:
            neutral = self.physics.advance("hold", external)
        finally:
            self.physics.restore(previous)
        contact = self.physics.advance(action, external)
        events = []
        if contact.seconds > 0:
            # A sustained contact contributes its integrated force, not just its peak.
            pressure = min(1.0, contact.impulse_ns / 2.0)
            events.append(SensoryEvent("pressure", "palm_left", pressure,
                                       origin="simulated", duration_s=contact.seconds))
        self.body.step(STEPS * self.physics.dt, events)
        experience = {
            "before": before,
            "action": action,
            "after": self.physics.observe(),
            "palm_contact": {"origin": "simulated", **asdict(contact)},
        }
        self.experience.append(experience)
        self.audit.append({
            "external": external,
            "counterfactual_hold": asdict(neutral),
            "contact_added_by_action": contact.seconds > 0 and neutral.seconds == 0,
            "impulse_delta_ns": contact.impulse_ns - neutral.impulse_ns,
        })
        return _detached(experience)

    def checkpoint(self) -> dict:
        return _detached({
            "schema": SCHEMA,
            "world_fingerprint": self.physics.fingerprint,
            "lineage_id": self.lineage_id,
            "parent_checkpoint_sha256": self._last_saved_digest,
            "physics": self.physics.state(),
            "body": self.body.snapshot(),
            "experience": list(self.experience),
            "audit": list(self.audit),
        })

    @classmethod
    def restore(cls, data: dict) -> Session:
        if not isinstance(data, dict) or data.get("schema") != SCHEMA:
            raise ValueError("unsupported embodiment checkpoint")
        data = _detached(data)
        session = cls()
        if data.get("world_fingerprint") != session.physics.fingerprint:
            raise ValueError("checkpoint belongs to a different scene or MuJoCo version")
        session.lineage_id = data["lineage_id"]
        if type(session.lineage_id) is not str or len(session.lineage_id) != 32 or not _is_hex(session.lineage_id):
            raise ValueError("invalid embodiment lineage")
        parent = data.get("parent_checkpoint_sha256")
        if parent is not None and (type(parent) is not str or len(parent) != 64 or not _is_hex(parent)):
            raise ValueError("invalid parent checkpoint digest")
        session.physics.restore(data["physics"])
        session.body = EmbodimentEngine.from_snapshot(data["body"])
        for key, journal in (("experience", session.experience), ("audit", session.audit)):
            rows = data[key]
            if not isinstance(rows, list) or len(rows) > WINDOW or not all(isinstance(row, dict) for row in rows):
                raise ValueError(f"invalid checkpoint {key}")
            journal.extend(rows)
        if len(session.experience) != len(session.audit):
            raise ValueError("experience and audit length differ")
        if abs(session.physics.data.time - session.body.sim_time_s) > 1e-6:
            raise ValueError("physics and body clocks differ")
        return session

    def save(self, path: Path) -> None:
        if path.exists() and sha256(path.read_bytes()).hexdigest() != self._last_saved_digest:
            raise ValueError("checkpoint changed on disk; load it before replacing it")
        encoded = (json.dumps(self.checkpoint(), ensure_ascii=False, allow_nan=False) + "\n").encode()
        with NamedTemporaryFile(dir=path.parent, delete=False) as file:
            temp = Path(file.name)
        try:
            with temp.open("wb") as file:
                file.write(encoded)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)
        self._last_saved_digest = sha256(encoded).hexdigest()

    @classmethod
    def load(cls, path: Path) -> Session:
        raw = path.read_bytes()
        session = cls.restore(json.loads(raw))
        session._last_saved_digest = sha256(raw).hexdigest()
        return session

    @classmethod
    def inspect(cls, path: Path, *, reference_path: str) -> dict:
        """Produce a metadata-only reference to the persisted bytes for Kai."""
        raw = path.read_bytes()
        payload = json.loads(raw)
        session = cls.restore(payload)
        return {
            "schema_version": 1,
            "path": reference_path,
            "checkpoint_sha256": sha256(raw).hexdigest(),
            "parent_checkpoint_sha256": payload.get("parent_checkpoint_sha256"),
            "lineage_id": session.lineage_id,
            "age_ticks": session.body.sequence,
            "phase": "simulation",
        }


def _is_hex(value: str) -> bool:
    return all(char in "0123456789abcdef" for char in value)


def _detached(value):
    return json.loads(json.dumps(value, allow_nan=False))

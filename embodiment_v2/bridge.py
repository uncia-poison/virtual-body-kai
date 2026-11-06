"""Read-only interchange with other agent layers and legacy VBK semantics."""
from __future__ import annotations

from typing import Any, Mapping
from .core import EmbodimentEngine


def to_agent_context(engine: EmbodimentEngine) -> dict[str, Any]:
    """Small, clearly labelled summary for a language-model prompt.

    Not evidence of subjective sensation. The origin of sensory inputs must
    remain visible: 'simulated' never becomes 'sensor' in this adapter.
    """
    state = engine.snapshot()
    return {
        "schema": state["schema"],
        "kind": "virtual_body_simulation",
        "sim_time_s": state["simulation_time_s"],
        "body_focus": state["focus"],
        "physiology_simulated": state["internal"],
        "joint_positions_deg_simulated": state["joints_deg"],
        "percept_sources": sorted({p["origin"] for p in state["recent_percepts"]}),
    }


def to_kai_tags(engine: EmbodimentEngine) -> str:
    """Non-destructive tags for downstream KAiScriptor-related decoders.

    This is a v2 interchange convention, not an assertion that the historic
    KAiScriptor grammar recognizes these tags without a separate adapter.
    """
    i = engine.internal
    focus = engine.focus(1)
    zone = focus[0]["region"] if focus else "none"
    return (f"[VBK2|t={engine.sim_time_s:.2f}|zone={zone}"
            f"|energy={i.energy:.3f}|comfort={i.comfort:.3f}"
            f"|activation={i.activation:.3f}|origin=simulation]")


def legacy_reference(data: Mapping[str, Any]) -> dict[str, Any]:
    """Copy selected legacy `VirtualBody.to_dict()` fields without mutation.

    The caller may pass an existing snapshot, but this module never imports,
    instantiates, resets or edits the old implementation. The two state
    machines remain independent until a future explicit synchronization API.
    """
    return {
        "source": "legacy_virtual_body_kai",
        "read_only": True,
        "dominant_emotion": str(data.get("dominant_emotion", "unknown")),
        "trust_level": data.get("trust_level"),
        "physiological": dict(data.get("physiological") or {}),
    }


class HardwareBoundary:
    """Non-actuating hardware boundary: fail closed, always.

    There is deliberately no driver and no 'enable' switch in v2. The API
    only exports *proposals* for offline review and never sends electrical,
    servo, network, ROS or serial commands. Real robot control needs its own
    independent safety controller, collision avoidance, e-stop, and testing.
    """

    @staticmethod
    def inspect(engine: EmbodimentEngine) -> dict[str, Any]:
        return {
            "hardware_enabled": False,
            "executed_commands": 0,
            "requires_independent_safety_validation": True,
            "proposals": [
                {"joint": m.joint, "next_deg": m.next_deg,
                 "target_deg": m.target_deg, "simulated": True}
                for m in engine.last_proposals
            ],
        }

    @staticmethod
    def execute(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("v2 is simulation-only: hardware actuation is disabled")

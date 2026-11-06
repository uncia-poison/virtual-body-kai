"""Virtual Body Kai v2: additive, independent embodiment simulation.

Legacy files are intentionally not imported or modified by this package.
"""
from .core import (SCHEMA_VERSION, EmbodimentEngine, InternalState, JointLimit,
                   MotionIntent, MotionProposal, Percept, Region, RegionState,
                   SensoryEvent, Vector3, default_joint_limits, default_regions)
from .bridge import HardwareBoundary, legacy_reference, to_agent_context, to_kai_tags

__all__ = [
    "SCHEMA_VERSION", "EmbodimentEngine", "InternalState", "JointLimit",
    "MotionIntent", "MotionProposal", "Percept", "Region", "RegionState",
    "SensoryEvent", "Vector3", "default_joint_limits", "default_regions",
    "HardwareBoundary", "legacy_reference", "to_agent_context", "to_kai_tags",
]

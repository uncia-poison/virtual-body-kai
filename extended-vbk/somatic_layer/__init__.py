"""Somatic layer package for virtual-body-kai.

This module exposes convenient imports for constructing and
using the somatic layer. It aggregates types and functions from
submodules: state, dynamics, grammar, stars, resolve, policy,
tracer, and fsm.
"""

from .state import BetaState, BetaGlobal, BetaZone
from .dynamics import step_update
from .grammar import parse_events
from .stars import parse_stars
from .resolve import merge_events
from .policy import derive_policy, post_edit
from .tracer import json_trace, glyphbar
from .fsm import Mode, infer_mode

__all__ = [
    "BetaState",
    "BetaGlobal",
    "BetaZone",
    "step_update",
    "parse_events",
    "parse_stars",
    "merge_events",
    "derive_policy",
    "post_edit",
    "json_trace",
    "glyphbar",
    "Mode",
    "infer_mode",
]

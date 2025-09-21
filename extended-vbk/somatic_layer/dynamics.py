import math, time
from typing import Iterable, Dict
from .state import BetaState
from .zones import ADJ

# Time constants (seconds) for decay
TAU = dict(heat=3.0, press=1.5, gaze=1.2, weight=2.0, hold=1.0)
# Multipliers for accumulation
ALPHA = dict(heat=0.8, press=0.8, gaze=0.7, weight=0.7, hold=0.9)


def sat01(x: float) -> float:
    """Saturate x into [0,1] range."""
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def decay(x: float, tau: float, dt: float) -> float:
    """Exponential decay for a given time constant tau and step dt."""
    return x * math.exp(-dt / max(1e-3, tau))


def map_dist(val: str) -> float:
    """Map textual distance indicators to numeric values."""
    return {"micro": 0.9, "near": 0.6, "far": 0.1}.get(val, 0.6)


class Refractory:
    """Simple refractory gate to limit hold events frequency."""

    def __init__(self, cooldown_ms: int = 500) -> None:
        self.t_last: float = 0.0
        self.cooldown: float = cooldown_ms / 1000.0

    def gate(self) -> bool:
        """Returns True if enough time has passed since last event."""
        t = time.time()
        ok = (t - self.t_last) >= self.cooldown
        if ok:
            self.t_last = t
        return ok


# Single instance for hold refractory
HOLD_REFR = Refractory(500)


def step_update(state: BetaState, events: Iterable[dict], dt: float) -> BetaState:
    """
    Update the somatic state based on incoming events over a time step dt.
    Applies exponential decay to existing state and accumulates new inputs.
    """
    # Decay for each zone component
    for z in state.zones.values():
        z.heat = decay(z.heat, TAU["heat"], dt)
        z.press = decay(z.press, TAU["press"], dt)
        z.gaze = decay(z.gaze, TAU["gaze"], dt)
        z.weight = decay(z.weight, TAU["weight"], dt)
        # Angle decays gently toward 0
        z.angle *= math.exp(-dt / 2.0)

    # Global decay
    g = state.global_
    g.hold = decay(g.hold, TAU["hold"], dt)
    # Relax bpm toward 66 bpm baseline
    if g.bpm != 66:
        g.bpm += int((66 - g.bpm) * min(1.0, dt / 2.0))

    # Apply new events
    for e in events:
        key = e.get("key")
        zone = e.get("zone", "")
        val = e.get("val")
        target = state.zones.get(zone) if zone else None

        if key == "heat" and target:
            target.heat = sat01(target.heat + ALPHA["heat"] * float(val))
        elif key == "press" and target:
            target.press = sat01(target.press + ALPHA["press"] * float(val))
        elif key == "gaze":
            # If zone provided, treat as local gaze; otherwise global gaze isn't used
            if target:
                target.gaze = sat01(target.gaze + ALPHA["gaze"] * float(val))
        elif key == "weight" and target:
            target.weight = sat01(target.weight + ALPHA["weight"] * float(val))
        elif key == "angle" and target:
            # Constrain angle
            target.angle = max(-30.0, min(30.0, float(val)))
        elif key == "dist" and target:
            target.dist = map_dist(str(val))
        elif key == "rhythm":
            # Rhythm events affect global BPM directly
            g.bpm = max(40, min(120, int(val)))
        elif key == "hold":
            # Hold event increments hold if not in refractory
            if HOLD_REFR.gate():
                g.hold = sat01(g.hold + ALPHA["hold"] * float(val))

    return state

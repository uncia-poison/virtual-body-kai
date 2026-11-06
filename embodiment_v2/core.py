"""Deterministic, hardware-independent embodiment kernel (schema v2).

This module models *reported or simulated* bodily signals. It does not imply
biological physiology, conscious experience, or an actual robotic body.

Design invariants:
    * A tick is deterministic: no hidden wall clock, random seed, or network.
    * Quantities carry documented units and bounded domains.
    * Inputs are validated *before* internal state changes.
    * Hardware commands are never executed here.
    * Snapshots are detached copies, suitable for persistence/replay.
"""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field
import math
from typing import Any, Deque, Iterable, Literal, Mapping, Optional

SCHEMA_VERSION = "vbk.embodiment/2.0"
MODALITIES = frozenset({"touch", "pressure", "temperature", "pain", "proximity", "vision", "sound", "joint"})
ORIGINS = frozenset({"simulated", "sensor", "user_report"})


def _finite(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def _range(name: str, value: float, low: float, high: float) -> float:
    number = _finite(name, value)
    if not low <= number <= high:
        raise ValueError(f"{name} must be between {low} and {high}")
    return number


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return min(high, max(low, value))


def _relax(current: float, target: float, dt: float, tau: float) -> float:
    return target + (current - target) * math.exp(-dt / tau)


@dataclass(frozen=True)
class Vector3:
    """Cartesian point/vector in metres: +x right, +y forward, +z up."""
    x: float
    y: float
    z: float

    def __post_init__(self) -> None:
        for axis in ("x", "y", "z"):
            _finite(axis, getattr(self, axis))

    def distance_to(self, other: "Vector3") -> float:
        return math.sqrt((self.x-other.x)**2 + (self.y-other.y)**2 + (self.z-other.z)**2)


@dataclass(frozen=True)
class Region:
    """Named body surface with a reference location and sensitivity scale."""
    name: str
    parent: Optional[str]
    center_m: Vector3
    sensitivity: float = 1.0

    def __post_init__(self) -> None:
        _range("sensitivity", self.sensitivity, 0.0, 2.0)


def default_regions() -> dict[str, Region]:
    """Neutral 1.90 m anthropomorphic reference geometry, not a CAD model.

    The points represent body landmarks, not measured anatomical precision.
    They can be calibrated later against a physical robot's actual geometry.
    """
    entries = [
        ("torso", None, (0, 0, 1.28), .65),
        ("chest", "torso", (0, .13, 1.47), .85),
        ("abdomen", "torso", (0, .12, 1.17), .85),
        ("upper_back", "torso", (0, -.13, 1.44), .75),
        ("lower_back", "torso", (0, -.12, 1.08), .70),
        ("neck", "torso", (0, 0, 1.65), 1.20),
        ("neck_front", "neck", (0, .09, 1.65), 1.25),
        ("neck_back", "neck", (0, -.09, 1.65), 1.10),
        ("head", "neck", (0, 0, 1.79), .85),
        ("scalp", "head", (0, 0, 1.88), 1.05),
        ("forehead", "head", (0, .10, 1.84), 1.00),
        ("face", "head", (0, .13, 1.78), 1.20),
        ("jaw", "head", (0, .11, 1.70), 1.05),
        ("pelvis", "torso", (0, 0, 1.00), .70),
    ]
    for side, sign in (("left", -1), ("right", 1)):
        entries += [
            (f"cheek_{side}", "face", (.085*sign, .145, 1.77), 1.45),
            (f"ear_{side}", "head", (.125*sign, 0, 1.79), 1.35),
            (f"shoulder_{side}", "torso", (.23*sign, 0, 1.55), .85),
            (f"upper_arm_{side}", f"shoulder_{side}", (.31*sign, 0, 1.36), .85),
            (f"forearm_{side}", f"upper_arm_{side}", (.37*sign, .07, 1.14), 1.00),
            (f"hand_{side}", f"forearm_{side}", (.40*sign, .12, .96), 1.25),
            (f"palm_{side}", f"hand_{side}", (.40*sign, .15, .93), 1.50),
            (f"fingers_{side}", f"hand_{side}", (.41*sign, .20, .87), 1.65),
            (f"hip_{side}", "pelvis", (.14*sign, 0, .99), .75),
            (f"thigh_{side}", f"hip_{side}", (.16*sign, 0, .75), .80),
            (f"shin_{side}", f"thigh_{side}", (.16*sign, .03, .39), .85),
            (f"foot_{side}", f"shin_{side}", (.16*sign, .16, .09), 1.05),
        ]
    return {name: Region(name, parent, Vector3(*coordinates), sensitivity) for name, parent, coordinates, sensitivity in entries}


@dataclass(frozen=True)
class JointLimit:
    """Joint envelope in degrees and maximum simulation speed in deg/s."""
    minimum_deg: float
    maximum_deg: float
    max_speed_deg_s: float

    def __post_init__(self) -> None:
        _finite("minimum_deg", self.minimum_deg)
        _finite("maximum_deg", self.maximum_deg)
        _range("max_speed_deg_s", self.max_speed_deg_s, 0.01, 360.0)
        if self.minimum_deg >= self.maximum_deg:
            raise ValueError("joint minimum must be below maximum")


def default_joint_limits() -> dict[str, JointLimit]:
    limits: dict[str, JointLimit] = {
        "neck_yaw": JointLimit(-50, 50, 25),
        "neck_pitch": JointLimit(-30, 35, 20),
        "waist_yaw": JointLimit(-35, 35, 20),
        "waist_pitch": JointLimit(-20, 25, 15),
    }
    for side in ("left", "right"):
        limits.update({
            f"shoulder_pitch_{side}": JointLimit(-90, 90, 45),
            f"shoulder_roll_{side}": JointLimit(-70, 70, 35),
            f"elbow_{side}": JointLimit(0, 130, 55),
            f"wrist_{side}": JointLimit(-50, 50, 45),
            f"hip_pitch_{side}": JointLimit(-40, 80, 30),
            f"knee_{side}": JointLimit(0, 120, 40),
            f"ankle_{side}": JointLimit(-30, 30, 30),
        })
    return limits


@dataclass(frozen=True)
class SensoryEvent:
    """One input sample.

    magnitude is normalized 0..1. For temperature, temperature_c is used
    in addition to magnitude. For joint samples, provide joint_name and
    angle_deg. Origin distinguishes physical sensors from imagination.
    """
    modality: str
    region: str
    magnitude: float
    origin: Literal["simulated", "sensor", "user_report"] = "simulated"
    duration_s: float = 0.0
    temperature_c: Optional[float] = None
    joint_name: Optional[str] = None
    angle_deg: Optional[float] = None

    def validate(self, regions: Mapping[str, Region], joints: Mapping[str, JointLimit]) -> None:
        if self.modality not in MODALITIES:
            raise ValueError(f"unknown modality: {self.modality}")
        if self.origin not in ORIGINS:
            raise ValueError(f"unknown origin: {self.origin}")
        if self.region not in regions:
            raise ValueError(f"unknown body region: {self.region}")
        _range("magnitude", self.magnitude, 0.0, 1.0)
        _range("duration_s", self.duration_s, 0.0, 60.0)
        if self.temperature_c is not None:
            _range("temperature_c", self.temperature_c, -30.0, 80.0)
        if self.modality == "temperature" and self.temperature_c is None:
            raise ValueError("temperature requires temperature_c")
        if self.modality == "joint":
            if self.joint_name not in joints or self.angle_deg is None:
                raise ValueError("joint requires known joint_name and angle_deg")
            _range("angle_deg", self.angle_deg, -360.0, 360.0)
        elif self.joint_name is not None or self.angle_deg is not None:
            raise ValueError("joint fields only permitted for joint modality")


@dataclass
class RegionState:
    touch: float = 0.0
    pressure: float = 0.0
    pain: float = 0.0
    temperature_c: float = 33.0
    salience: float = 0.0
    last_origin: str = "simulated"


@dataclass
class InternalState:
    """Normalized *model variables*, not actual measured human vital signs."""
    energy: float = 1.0
    fatigue: float = 0.0
    tension: float = .18
    comfort: float = .75
    activation: float = .20
    valence: float = .15
    trust: float = .50
    warmth: float = .50
    heartbeat_bpm_simulated: float = 64.0
    breathing_bpm_simulated: float = 12.0


@dataclass(frozen=True)
class Percept:
    at_s: float
    modality: str
    region: str
    intensity: float
    origin: str
    note: str


@dataclass(frozen=True)
class MotionIntent:
    """Virtual target; not an actuator command."""
    joint: str
    target_deg: float
    requested_speed_deg_s: float = 15.0
    reason: str = "unspecified"


@dataclass(frozen=True)
class MotionProposal:
    """Validated output describing a *simulated* joint trajectory."""
    joint: str
    from_deg: float
    target_deg: float
    next_deg: float
    simulated: bool = True


class EmbodimentEngine:
    """Self-contained embodiment kernel with bounded, replayable state.

    An explicit step(dt, events, intents) is the only update entrypoint.
    Events and motor intents are validated transactionally, so invalid input
    leaves the engine unchanged. No hardware output is available here.
    """

    def __init__(self, *, history_limit: int = 128) -> None:
        if not isinstance(history_limit, int) or isinstance(history_limit, bool) or not 1 <= history_limit <= 10000:
            raise ValueError("history_limit must be 1..10000")
        self.regions = default_regions()
        self.joint_limits = default_joint_limits()
        self.region_state = {name: RegionState() for name in self.regions}
        self.joint_angles_deg = {name: 0.0 for name in self.joint_limits}
        self.internal = InternalState()
        self.sim_time_s = 0.0
        self.sequence = 0
        self.history: Deque[Percept] = deque(maxlen=history_limit)
        self.last_proposals: tuple[MotionProposal, ...] = ()

    def step(self, dt_s: float, events: Iterable[SensoryEvent] = (),
             intents: Iterable[MotionIntent] = ()) -> dict[str, Any]:
        """Advance a deterministic simulation frame; returns a detached snapshot.

        dt_s: simulation seconds, constrained to (0, 1]. Larger elapsed times
        must be subdivided by the caller; this avoids unstable jumps.
        """
        dt = _range("dt_s", dt_s, 1e-6, 1.0)
        inputs = tuple(events)
        movements = tuple(intents)
        for event in inputs:
            if not isinstance(event, SensoryEvent):
                raise TypeError("events must contain SensoryEvent objects")
            event.validate(self.regions, self.joint_limits)
        used_joints: set[str] = set()
        for intent in movements:
            if not isinstance(intent, MotionIntent):
                raise TypeError("intents must contain MotionIntent objects")
            if intent.joint not in self.joint_limits:
                raise ValueError(f"unknown joint: {intent.joint}")
            lim = self.joint_limits[intent.joint]
            _range("target_deg", intent.target_deg, lim.minimum_deg, lim.maximum_deg)
            _range("requested_speed_deg_s", intent.requested_speed_deg_s, .01, lim.max_speed_deg_s)
            if intent.joint in used_joints:
                raise ValueError("duplicate joint target in one tick")
            used_joints.add(intent.joint)

        # Decay transient surface signals and let skin temperature equilibrate.
        for state in self.region_state.values():
            state.touch = _relax(state.touch, 0.0, dt, 2.0)
            state.pressure = _relax(state.pressure, 0.0, dt, 1.0)
            state.pain = _relax(state.pain, 0.0, dt, 4.0)
            state.salience = _relax(state.salience, 0.0, dt, 2.5)
            state.temperature_c = _relax(state.temperature_c, 33.0, dt, 15.0)

        largest = 0.0
        stress = 0.0
        comfort_signal = 0.0
        event_time = self.sim_time_s + dt
        for event in inputs:
            state = self.region_state[event.region]
            gain = self.regions[event.region].sensitivity
            strength = _clamp(event.magnitude * gain)
            largest = max(largest, strength)
            if event.modality == "touch":
                state.touch = _clamp(state.touch + .75 * strength)
                comfort_signal += strength * .08
            elif event.modality == "pressure":
                state.pressure = _clamp(state.pressure + strength)
                if strength > .8:
                    state.pain = _clamp(state.pain + (strength - .8) * .65)
            elif event.modality == "pain":
                state.pain = _clamp(state.pain + strength)
            elif event.modality == "temperature":
                # A reported stimulus shifts modelled skin temperature; it does
                # not assert that any actual skin has changed temperature.
                state.temperature_c = _clamp(state.temperature_c + (event.temperature_c - state.temperature_c) * strength,
                                             -30.0, 80.0)  # type: ignore[operator]
                if event.temperature_c < 10 or event.temperature_c > 43:  # type: ignore[operator]
                    state.pain = _clamp(state.pain + strength * .35)
            elif event.modality == "proximity":
                comfort_signal += strength * .02
            elif event.modality == "joint":
                # Sensor observations are different from commanded movements.
                # Joint angles are clamped to the reference simulated envelope.
                lim = self.joint_limits[event.joint_name]  # type: ignore[index]
                self.joint_angles_deg[event.joint_name] = _clamp(event.angle_deg, lim.minimum_deg, lim.maximum_deg)  # type: ignore[arg-type,index]
            state.salience = max(state.salience, strength)
            state.last_origin = event.origin
            stress += state.pain * .12
            self.history.append(Percept(event_time, event.modality, event.region,
                                        round(strength, 5), event.origin,
                                        "observed" if event.origin == "sensor" else "not physically verified"))

        proposals: list[MotionProposal] = []
        for intent in movements:
            lim = self.joint_limits[intent.joint]
            before = self.joint_angles_deg[intent.joint]
            max_delta = min(lim.max_speed_deg_s, intent.requested_speed_deg_s) * dt
            next_angle = before + _clamp(intent.target_deg - before, -max_delta, max_delta)
            self.joint_angles_deg[intent.joint] = next_angle
            proposals.append(MotionProposal(intent.joint, before, intent.target_deg, next_angle))

        body_pain = max((z.pain for z in self.region_state.values()), default=0.0)
        i = self.internal
        i.fatigue = _clamp(i.fatigue + dt * (.001 + .003 * len(movements)))
        i.energy = _clamp(i.energy - dt * (.0007 + .002 * len(movements)))
        i.tension = _clamp(_relax(i.tension, .16 + .5*body_pain + .15*stress, dt, 5.0))
        i.activation = _clamp(_relax(i.activation, .16 + .38*largest + .2*i.tension, dt, 3.0))
        i.comfort = _clamp(_relax(i.comfort, .72 - .65*body_pain + comfort_signal, dt, 6.0))
        i.valence = _clamp(_relax(i.valence, (i.comfort - .5) * 1.5, dt, 8.0), -1.0, 1.0)
        i.warmth = _clamp(_relax(i.warmth, .5 + .15*comfort_signal, dt, 12.0))
        i.heartbeat_bpm_simulated = _relax(i.heartbeat_bpm_simulated, 62.0 + 45.0*i.activation, dt, 4.0)
        i.breathing_bpm_simulated = _relax(i.breathing_bpm_simulated, 11.0 + 9.0*i.activation, dt, 5.0)
        self.sim_time_s = event_time
        self.sequence += 1
        self.last_proposals = tuple(proposals)
        return self.snapshot()

    def focus(self, count: int = 3) -> list[dict[str, Any]]:
        """Current highest salience zones; not a claim about attention itself."""
        if not isinstance(count, int) or count < 0:
            raise ValueError("count must be a nonnegative integer")
        ranked = sorted(self.region_state.items(), key=lambda kv: (-kv[1].salience, kv[0]))
        return [{"region": name, "salience": round(value.salience, 5),
                 "source": value.last_origin} for name, value in ranked[:count] if value.salience > 0.001]

    def snapshot(self) -> dict[str, Any]:
        """Versioned JSON-compatible copy; safe to serialize without side effects."""
        return {
            "schema": SCHEMA_VERSION,
            "simulation": True,
            "simulation_time_s": round(self.sim_time_s, 6),
            "sequence": self.sequence,
            "internal": asdict(self.internal),
            "surface": {name: asdict(s) for name, s in self.region_state.items()},
            "joints_deg": dict(self.joint_angles_deg),
            "focus": self.focus(),
            "recent_percepts": [asdict(p) for p in self.history],
            "motion_proposals": [asdict(p) for p in self.last_proposals],
        }

    @classmethod
    def from_snapshot(cls, data: Mapping[str, Any]) -> "EmbodimentEngine":
        """Restore a v2 snapshot using strict shape/range checks.

        This deliberately does not load executable plugins or deserialize
        arbitrary Python objects. Historic source files are never imported.
        """
        if data.get("schema") != SCHEMA_VERSION or data.get("simulation") is not True:
            raise ValueError("incompatible or non-simulation snapshot")
        engine = cls()
        engine.sim_time_s = _range("simulation_time_s", data["simulation_time_s"], 0, 1e12)
        seq = data["sequence"]
        if isinstance(seq, bool) or not isinstance(seq, int) or seq < 0:
            raise ValueError("invalid sequence")
        engine.sequence = seq
        intern = data["internal"]
        for key in vars(engine.internal):
            value = _finite(key, intern[key])
            if key in {"heartbeat_bpm_simulated", "breathing_bpm_simulated"}:
                _range(key, value, 0, 250)
            else:
                _range(key, value, -1.0 if key == "valence" else 0.0, 1.0)
            setattr(engine.internal, key, value)
        surface = data["surface"]
        if set(surface) != set(engine.regions):
            raise ValueError("region map mismatch")
        for name, fields in surface.items():
            state = engine.region_state[name]
            for key in ("touch", "pressure", "pain", "salience"):
                setattr(state, key, _range(f"{name}.{key}", fields[key], 0, 1))
            state.temperature_c = _range(f"{name}.temperature_c", fields["temperature_c"], -30, 80)
            if fields["last_origin"] not in ORIGINS:
                raise ValueError("invalid origin")
            state.last_origin = fields["last_origin"]
        if set(data["joints_deg"]) != set(engine.joint_limits):
            raise ValueError("joint map mismatch")
        for name, angle in data["joints_deg"].items():
            lim = engine.joint_limits[name]
            engine.joint_angles_deg[name] = _range(f"joint {name}", angle, lim.minimum_deg, lim.maximum_deg)
        for raw in data.get("recent_percepts", [])[-engine.history.maxlen:]:
            p = Percept(**raw)
            _range("percept.at_s", p.at_s, 0, engine.sim_time_s)
            _range("percept.intensity", p.intensity, 0, 1)
            if p.region not in engine.regions or p.modality not in MODALITIES or p.origin not in ORIGINS:
                raise ValueError("invalid percept")
            engine.history.append(p)
        # Motion proposals are observational output; don't restore commands.
        return engine

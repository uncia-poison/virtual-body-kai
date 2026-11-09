"""Small headless MuJoCo world. Every contact comes from the physics solver."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import mujoco as mj
import numpy as np

_SCENE = Path(__file__).with_name("reach.xml").read_bytes()
STATE_SPEC = mj.mjtState.mjSTATE_INTEGRATION
STEPS = 250
REST = (-0.7, 1.3)
ACTIONS = ("reach", "withdraw", "hold")


@dataclass(frozen=True)
class Contact:
    seconds: float
    impulse_ns: float
    peak_n: float


class Physics:
    def __init__(self) -> None:
        self.model = mj.MjModel.from_xml_string(_SCENE.decode())
        self.data = mj.MjData(self.model)
        self.dt = float(self.model.opt.timestep)
        self.palm = self.model.geom("palm").id
        self.target = self.model.geom("target").id
        self.data.qpos[:2] = REST
        self.data.ctrl[:2] = REST
        mj.mj_forward(self.model, self.data)

    @property
    def fingerprint(self) -> str:
        return sha256(mj.__version__.encode() + b":" + _SCENE).hexdigest()

    def state(self) -> list[float]:
        values = np.empty(mj.mj_stateSize(self.model, STATE_SPEC))
        mj.mj_getState(self.model, self.data, values, STATE_SPEC)
        return values.tolist()

    def restore(self, values: list[float]) -> None:
        if not isinstance(values, list) or len(values) != mj.mj_stateSize(self.model, STATE_SPEC):
            raise ValueError("incorrect MuJoCo state size")
        if any(type(value) not in (float, int) for value in values):
            raise ValueError("MuJoCo state must contain numbers")
        vector = np.asarray(values, dtype=np.float64)
        if not np.isfinite(vector).all():
            raise ValueError("nonfinite MuJoCo state")
        mj.mj_setState(self.model, self.data, vector, STATE_SPEC)
        mj.mj_forward(self.model, self.data)
        # Forward refreshes cached observations; retain exact integration state.
        mj.mj_setState(self.model, self.data, vector, STATE_SPEC)

    def observe(self) -> dict:
        return {
            "time_s": float(self.data.time),
            "palm_xyz_m": self.data.geom_xpos[self.palm].tolist(),
            "object_xyz_m": self.data.geom_xpos[self.target].tolist(),
            "arm_angles_rad": self.data.qpos[:2].tolist(),
            "arm_velocity_rad_s": self.data.qvel[:2].tolist(),
        }

    def advance(self, action: str, external: str) -> Contact:
        if action not in ACTIONS or external not in ("hold", "push", "reset"):
            raise ValueError("unknown action or external condition")
        self.data.ctrl[:2] = {
            "reach": (0.0, 0.0),
            "withdraw": REST,
            "hold": self.data.qpos[:2].copy(),
        }[action]
        if external != "hold":
            self.data.ctrl[2] = -.115 if external == "push" else 0.0
        wrench = np.zeros(6)
        duration, impulse, peak = 0.0, 0.0, 0.0
        for _ in range(STEPS):
            mj.mj_step(self.model, self.data)
            force = 0.0
            for index in range(self.data.ncon):
                pair = self.data.contact[index]
                if {pair.geom1, pair.geom2} == {self.palm, self.target}:
                    mj.mj_contactForce(self.model, self.data, index, wrench)
                    force += max(0.0, float(wrench[0]))
            if force > 1e-6:
                duration += self.dt
                impulse += force * self.dt
                peak = max(peak, force)
        state = self.state()
        self.restore(state)
        return Contact(duration, impulse, peak)

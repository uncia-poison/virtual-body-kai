from dataclasses import dataclass, asdict
from typing import Dict
from .zones import ZONES

@dataclass
class BetaZone:
    heat: float = 0.0     # [0..1]
    press: float = 0.0    # [0..1]
    angle: float = 0.0    # degrees (-30..+30)
    # [0..1] (map: micro≈0.9, near≈0.6, far≈0.1)
    gaze: float = 0.0     # [0..1]
    weight: float = 0.0   # [0..1]

@dataclass
class BetaGlobal:
    bpm: int = 66         # [40..120]
    hold: float = 0.0     # [0..1]

@dataclass
class BetaState:
    zones: Dict[str, BetaZone]
    global_: BetaGlobal

    @classmethod
    def default(cls) -> "BetaState":
        return cls(zones={z: BetaZone() for z in ZONES}, global_=BetaGlobal())

    def to_json(self) -> Dict:
        return {
            "bpm": self.global_.bpm,
            "hold": round(self.global_.hold, 2),
            "zones": {
                k: {kk: round(vv, 2) for kk, vv in asdict(zone).items() if kk in ("heat","press","gaze","weight") and vv > 0.0}
                for k, zone in self.zones.items()
            }
        }

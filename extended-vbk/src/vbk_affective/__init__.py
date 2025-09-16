from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Stimulus:
    kind: str = "stroke"
    pressure_kpa: float = 0.0
    velocity_cm_s: float = 0.0
    temperature_c: float = 32.0
    duration_s: float = 1.0
    contact_route: str = "manual"
    material: str = "skin"
    wetness: float = 0.0
    airflow_cm_s: float = 0.0
    humidity_rel: float = 0.0

@dataclass
class BodyProfile:
    sex: str = "male"
    height_cm: int = 190
    weight_kg: int = 85
    build: str = "athletic"

class AffectiveEngine:
    """Simple affective engine with phases and tokens.

    This engine simulates a physiological arousal cycle and outputs a first-person
    description of sensations in the specified body zone. It keeps track of trust,
    memory of zones, and an arousal cycle (rest, arousal, plateau, orgasm,
    orgasm_cooldown). It produces machine-readable tokens appended to the text for
    further parsing by agents.
    """

    def __init__(self, profile: Optional[BodyProfile] = None) -> None:
        self.profile = profile or BodyProfile()
        self.phase: str = "rest"
        self.trust: float = 0.0
        self.refractory_counter: int = 0
        self.zone_memory: Dict[str, float] = {}
        self.config: Dict[str, Any] = {
            "arousal_threshold": 0.3,
            "plateau_threshold": 0.6,
            "orgasm_threshold": 1.0,
            "refractory_steps": 20,
        }

    def step(self, zone: str, stimulus: Stimulus) -> str:
        """Process a stimulus and return an affective text with tokens."""
        # Compute a simple drive value based on stimulus parameters
        drive = 0.0
        drive += max(0.0, min(1.0, 0.5 * stimulus.velocity_cm_s / 5.0 + 0.5 * stimulus.pressure_kpa / 5.0))
        drive += stimulus.wetness * 0.3
        drive -= max(0.0, (stimulus.pressure_kpa - 5.0) / 10.0)
        # Update trust and zone memory
        self.trust = min(1.0, self.trust + drive * 0.05)
        self.zone_memory[zone] = self.zone_memory.get(zone, 0.0) + drive
        # Update cycle phase
        event: Optional[str] = None
        if self.phase == "rest":
            if drive > self.config["arousal_threshold"]:
                self.phase = "arousal"
        elif self.phase == "arousal":
            if drive > self.config["plateau_threshold"]:
                self.phase = "plateau"
        elif self.phase == "plateau":
            if drive > self.config["orgasm_threshold"]:
                self.phase = "orgasm"
                event = "orgasm"
                self.refractory_counter = self.config["refractory_steps"]
        elif self.phase == "orgasm":
            self.phase = "orgasm_cooldown"
        elif self.phase == "orgasm_cooldown":
            self.refractory_counter -= 1
            if self.refractory_counter <= 0:
                self.phase = "rest"
        # Build text description
        zone_desc = zone.replace("_", " ")
        if self.phase == "rest":
            tone = "calm"
        elif self.phase == "arousal":
            tone = "rising"
        elif self.phase == "plateau":
            tone = "steady"
        elif self.phase == "orgasm":
            tone = "peak"
        else:
            tone = "afterglow"
        text = f"In my {zone_desc}, a {stimulus.kind} creates a {tone} sensation."
        # Build tokens
        tokens = [f"<<phase:{self.phase}>>", f"<<mode:{stimulus.kind}>>", f"<<material:{stimulus.material}>>"]
        if event:
            tokens.append(f"<<event:{event}>>")
        if stimulus.wetness > 0.0:
            tokens.append(f"<<wet:{stimulus.wetness:.2f}>>")
        # Append tokens to text
        return text + " " + " ".join(tokens)

    def step_labeled(self, zone: str, stimulus: Stimulus) -> Dict[str, Any]:
        """Return structured output for the stimulus."""
        text = self.step(zone, stimulus)
        event = "orgasm" if "<<event:orgasm>>" in text else None
        labels = {
            "text": text,
            "phase": self.phase,
            "event": event,
            "orgasm": event is not None,
            "tags": {
                "zone": zone,
                "trust": self.trust,
                "mode": stimulus.kind,
                "material": stimulus.material,
                "wetness": stimulus.wetness,
            },
        }
        return labels

__all__ = ["Stimulus", "BodyProfile", "AffectiveEngine"]

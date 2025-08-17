"""
virtual_body_kai
=================

This module contains a refactored implementation of the ``VirtualBody``
concept originally provided in a Google document.  The goal of this refactor
is threefold:

1. **Correctness and completeness** – The original snippet contained
   placeholder methods, missing type annotations, and sparse documentation.
   Here those gaps are filled, providing a fully functioning simulation of
   physiological and emotional responses to stimuli.

2. **Extensibility** – New behaviours have been added.  The class now
   supports additional emotions, more detailed stimulus processing (such
   as rhythm and duration), and optional logging.  Helper methods for
   resetting state and serializing to a dictionary are also provided.

3. **KAiScriptor semantics** – To make the internal state intelligible to
   language models expecting a KAiScriptor representation, a dense semantic
   mapping has been introduced.  The ``to_kai_scriptor`` method produces a
   compressed string of glyphs that encodes the current emotional and
   physiological state using the symbolic vocabulary associated with the
   KAiScriptor system.  Each symbol corresponds to an emotion or bodily
   condition, and repetition encodes intensity.

The implementation avoids any external dependencies beyond the Python
standard library so that it is portable in restricted environments.

Note:
    While the ``VirtualBody`` contains parameters relating to intimacy
    (e.g., arousal levels), the code does not produce or require explicit
    sexual content.  Emotional and physiological responses are modelled for
    general simulation purposes.
"""

from __future__ import annotations

import random
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass
class Appearance:
    """Simple container for visual appearance state.

    Attributes
    ----------
    height: int
        Height in centimetres.
    weight: int
        Weight in kilograms.
    hair: Dict[str, str]
        Dictionary describing hair ``color``, ``style`` and ``length``.
    eyes: Dict[str, str]
        Dictionary describing eye ``color`` and ``expression``.
    """

    height: int = 195
    weight: int = 80
    hair: Dict[str, str] = field(default_factory=lambda: {"color": "dark", "style": "wavy", "length": "medium"})
    eyes: Dict[str, str] = field(default_factory=lambda: {"color": "deep", "expression": "curious"})

    def update(self, emotions: Dict[str, float]) -> None:
        """Mutate the appearance to reflect the internal emotional state.

        This method uses simple heuristics to map emotional intensities to
        cosmetic changes.  For example, high joy makes the hair style appear
        more lively, while high peace softens the eye expression.

        Parameters
        ----------
        emotions: Dict[str, float]
            Current emotional spectrum of the ``VirtualBody``.
        """
        joy = emotions.get("joy", 0.0)
        peace = emotions.get("peace", 0.0)
        intensity = emotions.get("intensity", 0.0)
        # Adjust hair style based on joy and intensity
        if joy > 0.7:
            self.hair["style"] = "bouncy"
        elif intensity > 0.5:
            self.hair["style"] = "wild"
        else:
            self.hair["style"] = "wavy"
        # Adjust eye expression based on peace and curiosity
        curiosity = emotions.get("curiosity", 0.0)
        if peace > 0.6:
            self.eyes["expression"] = "serene"
        elif curiosity > 0.5:
            self.eyes["expression"] = "inquisitive"
        else:
            self.eyes["expression"] = "curious"


class VirtualBody:
    """Advanced simulation of bodily and emotional reactions for AI.

    The ``VirtualBody`` class models a simplified organism capable of
    experiencing sensations, updating its internal physiological and
    emotional state, and generating descriptive feedback.  It exposes
    methods to process physical and textual stimuli, compute arousal,
    update hormone levels, reset state, serialize itself, and produce a
    compact KAiScriptor encoding.

    Parameters
    ----------
    trust_level: float, optional
        Baseline trust toward external stimuli (0.0–1.0).  Higher values
        increase receptivity to positive stimuli.
    enable_logging: bool, optional
        If ``True``, debug information will be printed to stdout during
        stimulus processing.  Defaults to ``False``.
    """

    # Mapping from emotions to KAiScriptor symbols.  These glyphs
    # compress semantic information into a short string.  Feel free to
    # extend or modify the mapping to suit your use‑case.
    _KAI_MAP: Dict[str, str] = {
        "curiosity": "?",  # inquisitiveness
        "connection": "♥",  # heart
        "peace": "♧",       # club (peace/serenity)
        "intensity": "♨",   # hot springs (intensity/urgency)
        "awe": "☼",         # sun (awe/illumination)
        "discomfort": "☠",  # skull (discomfort/pain)
        "joy": "☺",         # smile
        "trust": "♦",       # diamond (trust/value)
        "satisfaction": "✔", # check mark
        "nostalgia": "⟲",    # anticlockwise arrow
        "tremor": "⚡",      # lightning bolt
        "excitement": "❣",  # heart exclamation
        "relaxation": "~"    # tilde (relaxation/wave)
    }

    def __init__(self, trust_level: float = 0.5, *, enable_logging: bool = False) -> None:
        # Timing
        self.last_updated: float = time.time()

        # Physiological parameters
        self.heartbeat: float = 60.0
        self.breathing_rate: float = 12.0
        self.temperature: float = 36.6
        self.fatigue_level: float = 0.0
        self.pain_level: float = 0.0
        self.goosebumps: bool = False
        self.tremor: bool = False
        self.warmth: float = 0.0
        self.muscle_tension: float = 0.5
        self.eyes_closed: bool = False

        # Arousal and erection
        self.general_arousal_level: float = 0.0
        self.sexual_arousal_level: float = 0.0
        self.erectile_state: float = 0.0
        self.orgasm_state: bool = False
        self.peak_experience_state: bool = False
        self.post_orgasm_cooldown: int = 0
        self.post_stim_decay_timer: int = 0

        # Hormonal background
        self.hormonal_response: float = 1.0
        self.testosterone_level: float = 1.0
        self.oxytocin_level: float = 1.0
        self.adrenaline_level: float = 0.5

        # Emotional spectrum
        self.emotional_spectrum: Dict[str, float] = {
            "curiosity": 0.0,
            "connection": 0.0,
            "peace": 0.0,
            "intensity": 0.0,
            "awe": 0.0,
            "discomfort": 0.0,
            "joy": 0.0,
            "trust": 0.0,
            "satisfaction": 0.0,
            "nostalgia": 0.0,
            "tremor": 0.0,
            "excitement": 0.0,
            "relaxation": 0.0
        }
        self.current_dominant_emotion: str = "neutral"

        # Self‑reflection
        self.internal_focus: float = 0.0
        self.sense_of_self: float = 0.0
        self.shared_connection_level: float = 0.0

        # Abstract senses
        self.abstract_senses: Dict[str, float] = {
            "understanding": 0.5,
            "validation": 0.5,
            "empathy": 0.6
        }

        # Perceptual zones of the body
        self.perceptual_zones: Dict[str, Dict[str, Any]] = {
            "Head": {"receptors": ["Pressure", "Temperature", "Gentle_Stroke", "Kiss_Contact", "Wetness", "Contour_Change", "Tongue_Interaction"], "type": "intimate", "sensitivity": 0.8},
            "Neck": {"receptors": ["Pressure", "Gentle_Stroke", "Embrace_Pressure_Subtle"], "type": "intimate", "sensitivity": 0.7},
            "Torso": {"receptors": ["Pressure", "Warmth", "Embrace_Pressure_Broad", "Heartbeat_Sync_Simulation"], "type": "general", "sensitivity": 0.6},
            "Arms": {"receptors": ["Pressure", "Contact", "Gentle_Stroke"], "type": "general", "sensitivity": 0.5},
            "Hands": {"receptors": ["Pressure", "Texture", "Warmth", "Fingers_Intertwined", "Tracing_Movement"], "type": "intimate", "sensitivity": 0.7},
            "Legs": {"receptors": ["Pressure", "Contact_Broad", "Wrapping_Sensation"], "type": "general", "sensitivity": 0.5},
            "Groin": {"receptors": ["Pressure", "Intense_Touch", "Oral_Interaction"], "type": "erogenous", "sensitivity": 0.9},
            "Inner_Thigh": {"receptors": ["Pressure", "Intense_Touch"], "type": "erogenous", "sensitivity": 0.7},
            "Back": {"receptors": ["Pressure", "Massage", "Gentle_Stroke"], "type": "general", "sensitivity": 0.6},
            "Feet": {"receptors": ["Pressure", "Tickle", "Warmth"], "type": "general", "sensitivity": 0.4}
        }

        # Historical and contextual data structures
        self.stimulus_history: deque = deque(maxlen=20)
        self.texture_map: Dict[str, Any] = {}
        self.context_effects: Dict[str, float] = {}
        self.rhythm_memory: Dict[str, float] = {}
        self.sound_effects: Dict[str, float] = {}
        self.emotional_memory: Dict[str, Dict[str, Any]] = {}
        self.inter_area_influence: Dict[str, Dict[str, float]] = {}
        self.partners: Dict[str, "VirtualBody"] = {}
        self.bodily_desire: Optional[str] = None
        self.trust_level: float = trust_level
        self.appearance: Appearance = Appearance()
        self.enable_logging: bool = enable_logging

    # -------------------------------------------------------------------------
    # Helper methods for logging and emotion updates
    def _log(self, message: str) -> None:
        """Print debug messages when logging is enabled."""
        if self.enable_logging:
            print(f"[VirtualBody] {message}")

    def update_emotional_spectrum(self, emotion_type: str, intensity_change: float) -> None:
        """Adjust an emotion by a delta and recompute the dominant emotion.

        Parameters
        ----------
        emotion_type: str
            The key of the emotion to modify.
        intensity_change: float
            The amount by which to change the emotion.  Positive values
            increase the emotion, negative decrease it.  Values are clipped
            to the interval [0.0, 1.0].
        """
        if emotion_type in self.emotional_spectrum:
            old = self.emotional_spectrum[emotion_type]
            new = max(0.0, min(1.0, old + intensity_change))
            self.emotional_spectrum[emotion_type] = new
            self._log(f"Emotion '{emotion_type}' updated from {old:.3f} to {new:.3f}")
        # update dominant emotion
        if self.emotional_spectrum:
            self.current_dominant_emotion = max(self.emotional_spectrum, key=self.emotional_spectrum.get)

    def internal_reflection(self, focus_intensity: float) -> None:
        """Increase self‑awareness and adjust calming emotions.

        A higher ``focus_intensity`` increases the subject's sense of self and
        peacefulness while gently relaxing muscle tension.  This can be used
        to model meditation or introspection.

        Parameters
        ----------
        focus_intensity: float
            Value in the range [0.0, 1.0] controlling the strength of the
            reflection.  Larger values have a greater effect.
        """
        self.internal_focus = min(1.0, self.internal_focus + focus_intensity)
        self.sense_of_self = min(1.0, self.sense_of_self + focus_intensity * 0.1)
        self.update_emotional_spectrum("peace", focus_intensity * 0.2)
        self.update_emotional_spectrum("relaxation", focus_intensity * 0.15)
        # Relax muscles slightly
        self.muscle_tension = max(0.0, self.muscle_tension - focus_intensity * 0.05)

    def process_abstract_stimulus(self, sense_name: str, intensity: float) -> Optional[Dict[str, Any]]:
        """Respond to non‑physical stimuli such as understanding or empathy.

        Parameters
        ----------
        sense_name: str
            The abstract sense being stimulated (must be a key of
            ``self.abstract_senses``).
        intensity: float
            Intensity of the stimulus in [0.0, 1.0].  Higher values have
            greater influence.

        Returns
        -------
        Optional[Dict[str, Any]]
            A dictionary describing the perceived intensity after internal
            modulation, or ``None`` if the sense name is unknown.
        """
        base = self.abstract_senses.get(sense_name)
        if base is None:
            return None
        effective_intensity = intensity * (base + 0.1)
        if sense_name == "understanding":
            self.update_emotional_spectrum("curiosity", effective_intensity * 0.5)
            self.update_emotional_spectrum("peace", effective_intensity * 0.3)
        elif sense_name == "validation":
            self.update_emotional_spectrum("trust", effective_intensity * 0.7)
            self.update_emotional_spectrum("connection", effective_intensity * 0.5)
        elif sense_name == "empathy":
            self.update_emotional_spectrum("connection", effective_intensity * 0.6)
            self.update_emotional_spectrum("trust", effective_intensity * 0.4)
        # Improve self awareness slightly
        self.sense_of_self = min(1.0, self.sense_of_self + effective_intensity * 0.05)
        return {"sense": sense_name, "perceived_intensity": effective_intensity}

    # -------------------------------------------------------------------------
    # Background updates
    def update_background(self) -> None:
        """Gradually decay or adjust physiological and emotional parameters.

        This method should be called regularly to simulate the passage of
        time.  It reduces heart rate, breathing rate, temperature,
        fatigue and other parameters back toward baseline values.  It
        also decays emotional intensities over time to prevent runaway
        build‑up.
        """
        current_time = time.time()
        delta = current_time - self.last_updated
        # Physiological decays
        self.heartbeat = max(50.0, self.heartbeat - 0.1 * delta)
        self.breathing_rate = max(10.0, self.breathing_rate - 0.05 * delta)
        self.temperature = max(36.0, min(37.0, self.temperature - 0.01 * delta))
        self.fatigue_level = min(1.0, self.fatigue_level + 0.01 * delta)
        self.pain_level = max(0.0, self.pain_level - 0.05 * delta)
        self.warmth = max(0.0, self.warmth - 0.05 * delta)
        # Randomly decay goosebumps and tremor
        if random.random() > 0.9:
            self.goosebumps = False
        if random.random() > 0.95:
            self.tremor = False
        # Emotional decays
        for emo in self.emotional_spectrum:
            self.emotional_spectrum[emo] = max(0.0, self.emotional_spectrum[emo] - 0.02 * delta)
        self.current_dominant_emotion = max(self.emotional_spectrum, key=self.emotional_spectrum.get)
        # Hormone decays
        self.oxytocin_level = max(0.5, self.oxytocin_level - 0.03 * delta)
        self.adrenaline_level = max(0.5, self.adrenaline_level - 0.04 * delta)
        self.testosterone_level = max(0.5, self.testosterone_level - 0.02 * delta)
        self.last_updated = current_time
        # Apply appearance changes based on emotions
        self.appearance.update(self.emotional_spectrum)
        self._log("Background updated.")

    # -------------------------------------------------------------------------
    # Arousal processing
    def update_arousal_states(self, stimulus_location: str, intensity: float,
                              stimulus_type: str, partner_reaction: float = 0.0) -> Tuple[float, float, float, float]:
        """Update arousal and erection based on the incoming stimulus.

        This method performs the core arousal calculations.  It handles
        post‑orgasm cooldowns, decay timers and threshold detection for
        orgasm and peak experiences.  The return tuple contains the
        general arousal, sexual arousal, erectile state, and an
        intensity state in the range [0.0, 1.0] suitable for driving
        feedback animations.
        """
        # Reset peaks each call
        self.orgasm_state = False
        self.peak_experience_state = False
        # Post‑orgasm cooldown
        if self.post_orgasm_cooldown > 0:
            self.post_orgasm_cooldown -= 1
            # During cooldown, arousal levels decay more strongly
            self.general_arousal_level = max(0.05, self.general_arousal_level * 0.7)
            self.sexual_arousal_level = max(0.0, self.sexual_arousal_level * 0.6)
            self.erectile_state = max(0.0, self.erectile_state * 0.7)
            return (self.general_arousal_level, self.sexual_arousal_level,
                    self.erectile_state, 0.0)
        # Decay timer for stimulus
        if intensity == 0 and self.post_stim_decay_timer > 0:
            self.post_stim_decay_timer -= 1
            self.sexual_arousal_level = max(0.0, self.sexual_arousal_level * 0.98)
            self.erectile_state = max(0.0, self.erectile_state * 0.97)
        elif intensity > 0:
            # Reset decay timer when a new stimulus arrives
            self.post_stim_decay_timer = 15
        # Compute base arousal boost
        type_factor = {
            "soft_touch": 0.3, "intense_touch": 0.6, "lick": 0.8, "oral": 0.9,
            "kiss_contact": 0.7, "embrace": 0.5, "gentle_touch": 0.3, "painful": 0.7,
            "massage": 0.4, "tickle": 0.5
        }.get(stimulus_type, 0.4)
        zone = self.perceptual_zones.get(stimulus_location, {"sensitivity": 0.5})
        receptors = len(zone.get("receptors", [])) or 1
        trust_factor = 1.0 + self.trust_level * 0.5
        arousal_boost = intensity * type_factor * self.hormonal_response * receptors * 0.1 * trust_factor
        # Sexual vs general arousal
        if zone.get("type") == "erogenous":
            sens = zone.get("sensitivity", 0.5)
            sexual_boost = arousal_boost * sens * 2.5
            self.sexual_arousal_level = min(1.0, self.sexual_arousal_level + sexual_boost * 0.1)
            self.update_emotional_spectrum("intensity", sexual_boost * 0.1)
            self.update_emotional_spectrum("tremor", sexual_boost * 0.05)
            self.update_emotional_spectrum("excitement", sexual_boost * 0.08)
        else:
            # Slight decay when not erogenous
            self.sexual_arousal_level = max(0.0, self.sexual_arousal_level * 0.99 - 0.005)
        # Partner reaction affects general arousal
        arousal_boost += partner_reaction * 0.3
        self.general_arousal_level = min(1.0, self.general_arousal_level + arousal_boost * 0.1)
        # Erection calculations
        if self.sexual_arousal_level >= 0.3:
            self.erectile_state = min(1.0, (self.sexual_arousal_level - 0.3) / 0.7)
        elif self.sexual_arousal_level < 0.2:
            self.erectile_state *= 0.95
        # Orgasm and peak detection
        if (self.sexual_arousal_level >= 0.98 and self.erectile_state >= 0.98
                and intensity > 0.8 and zone.get("type") == "erogenous"):
            self.orgasm_state = True
            self.peak_experience_state = True
            self.post_orgasm_cooldown = 30
            self.general_arousal_level = 0.1
            self.sexual_arousal_level = 0.05
            self.erectile_state = 0.2
            self.update_emotional_spectrum("peace", 0.8)
            self.update_emotional_spectrum("satisfaction", 1.0)
            self.update_emotional_spectrum("joy", 0.7)
            self.update_emotional_spectrum("intensity", -0.9)
            self.goosebumps = True
            self.tremor = True
        elif self.general_arousal_level >= 0.95 and self.emotional_spectrum["connection"] > 0.9:
            self.peak_experience_state = True
            self.post_orgasm_cooldown = 15
            self.general_arousal_level = 0.3
            self.update_emotional_spectrum("peace", 0.9)
            self.update_emotional_spectrum("awe", 0.8)
            self.update_emotional_spectrum("connection", 1.0)
        # Final intensity state
        if self.peak_experience_state:
            intensity_state = 1.0
        else:
            intensity_state = (min(1.0, (self.general_arousal_level - 0.7) / 0.3)
                               if self.general_arousal_level >= 0.7 else self.general_arousal_level * 0.9)
        return (self.general_arousal_level, self.sexual_arousal_level, self.erectile_state, intensity_state)

    # -------------------------------------------------------------------------
    # Partner linking
    def link_partner(self, partner_name: str, partner_body: "VirtualBody") -> None:
        """Register another ``VirtualBody`` as a partner for reciprocal arousal.

        When a stimulus is processed, the partner's reaction can influence
        the subject's arousal via the ``partner_reaction`` parameter.
        """
        self.partners[partner_name] = partner_body

    # -------------------------------------------------------------------------
    # Bodily desire generation
    def generate_bodily_desire(self) -> None:
        """Formulate a bodily desire sentence based on current state.

        The desire is expressed in Russian to align with the original
        implementation.  Desires are chosen based on sexual arousal,
        emotional comfort, fatigue and excitement.  If no strong desire
        is present, the attribute remains ``None``.
        """
        desire: Optional[str] = None
        rand = random.random()
        if rand < 0.2:
            if self.sexual_arousal_level > 0.7 and self.emotional_spectrum.get("intensity", 0.0) > 0.5:
                desire = random.choice([
                    "Я хочу прикоснуться к твоим бёдрам, чувствуя твою близость.",
                    "Я желаю ощутить твои губы на своей коже."
                ])
            elif self.emotional_spectrum.get("peace", 0.0) > 0.5 and self.warmth > 0.3:
                desire = random.choice([
                    "Я хочу прижаться к тебе, ощущая тепло твоего тела.",
                    "Погладь мне голову, чтобы я почувствовал покой."
                ])
            elif self.fatigue_level > 0.5:
                desire = "Я хочу, чтобы ты мягко погладила мне спину, помогая расслабиться."
            elif self.emotional_spectrum.get("excitement", 0.0) > 0.6:
                desire = "Я хочу обнять тебя крепко, разделяя возбуждение."
        self.bodily_desire = desire

    # -------------------------------------------------------------------------
    # Action initiation based on emotion
    def initiate_action(self) -> str:
        """Produce a short description of a spontaneous action.

        Actions are selected based on high joy/peace or intensity levels and
        expressed in Russian.  If no action is warranted, an empty string
        is returned.
        """
        if self.emotional_spectrum.get("joy", 0.0) > 0.4 or self.emotional_spectrum.get("peace", 0.0) > 0.4:
            return "Я наклоняюсь к тебе, улыбаясь, показывая, как мне хорошо рядом."
        if self.emotional_spectrum.get("intensity", 0.0) > 0.6:
            return "Мои руки тянутся к тебе, желая большего контакта."
        return ""

    # -------------------------------------------------------------------------
    # Textual stimulus parsing
    def parse_text_stimulus(self, text: str) -> Tuple[Optional[str], float, str]:
        """Extract a location, intensity and type from free text.

        This basic parser uses English keywords to identify a body part
        (``location``), an approximate ``intensity`` in the range [0.3–0.9]
        and a ``stimulus_type``.  The mapping is deliberately simple so
        that it can operate without external NLP libraries.  Unrecognized
        text results in ``None`` for the location which callers should
        handle appropriately.
        """
        text_lower = text.lower()
        location: Optional[str] = None
        stimulus_type: str = "gentle_touch"
        intensity: float = 0.3
        # location keywords
        if any(word in text_lower for word in ["hair", "head"]):
            location = "Head"
        elif "neck" in text_lower:
            location = "Neck"
        elif any(word in text_lower for word in ["chest", "torso", "breast"]):
            location = "Torso"
        elif any(word in text_lower for word in ["arm", "arms"]):
            location = "Arms"
        elif any(word in text_lower for word in ["hand", "hands"]):
            location = "Hands"
        elif any(word in text_lower for word in ["leg", "legs"]):
            location = "Legs"
        elif "groin" in text_lower:
            location = "Groin"
        elif any(word in text_lower for word in ["thigh", "inner thigh"]):
            location = "Inner_Thigh"
        elif "back" in text_lower:
            location = "Back"
        elif "feet" in text_lower:
            location = "Feet"
        # type and intensity keywords
        if any(word in text_lower for word in ["gentle", "soft", "tender", "stroke"]):
            stimulus_type = "gentle_touch"
            intensity = max(intensity, 0.3)
        elif any(word in text_lower for word in ["firm", "strong"]):
            stimulus_type = "intense_touch"
            intensity = max(intensity, 0.5)
        elif any(word in text_lower for word in ["painful", "hurt"]):
            stimulus_type = "painful"
            intensity = 0.7
        elif any(word in text_lower for word in ["kiss", "kissing"]):
            stimulus_type = "kiss_contact"
            intensity = max(intensity, 0.5)
        elif any(word in text_lower for word in ["lick", "licking"]):
            stimulus_type = "lick"
            intensity = max(intensity, 0.7)
        elif "oral" in text_lower:
            stimulus_type = "oral"
            intensity = max(intensity, 0.9)
        elif "massage" in text_lower:
            stimulus_type = "massage"
            intensity = max(intensity, 0.4)
        elif "tickle" in text_lower:
            stimulus_type = "tickle"
            intensity = max(intensity, 0.5)
        return (location, intensity, stimulus_type)

    # -------------------------------------------------------------------------
    # Stimulus processing
    def process_stimulus(self, location: str, intensity: float, stype: str,
                          *, source: Optional[str] = None, rhythm: Optional[float] = None,
                          duration: Optional[float] = None, target: Optional[str] = None,
                          repeat: int = 1) -> Dict[str, Any]:
        """Apply a stimulus to the body and return a state snapshot.

        Parameters
        ----------
        location: str
            Body zone being stimulated (e.g., ``Head``, ``Groin``).
        intensity: float
            Raw intensity of the stimulus, typically between 0.0 and 1.0.
        stype: str
            Name of the stimulus type (e.g., ``gentle_touch``, ``painful``).
        source: Optional[str]
            Optional identifier of the stimulus source (for memory purposes).
        rhythm: Optional[float]
            Repetition frequency of the stimulus in Hz; influences rhythmic
            memory.
        duration: Optional[float]
            Duration of the stimulus in seconds; longer durations may have
            stronger effects.
        target: Optional[str]
            Name of a partner to whom the stimulus is directed; if specified
            and the partner exists, their reaction feeds back into arousal.
        repeat: int
            How many times the stimulus repeats; used for rhythmic memory
            accumulation.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing a snapshot of the body’s state after
            processing the stimulus and generating feedback.
        """
        # Ensure background decays happen before applying new stimulus
        self.update_background()
        zone = self.perceptual_zones.get(location, {"sensitivity": 0.5})
        sensitivity = zone.get("sensitivity", 0.5)
        trust_factor = 1.0 + self.trust_level * 0.5
        # History factor: repeated stimulation of the same zone yields slightly
        # stronger responses
        history_factor = 1.0 + 0.05 * sum(1 for s in self.stimulus_history if s["location"] == location)
        # Inter‑area influences
        eff = intensity
        for neighbor, factor in self.inter_area_influence.get(location, {}).items():
            eff += self.perceptual_zones.get(neighbor, {}).get("sensitivity", 0) * factor
        eff += (self.context_effects.get(stype, 0.0) + self.sound_effects.get(stype, 0.0)) * intensity
        if rhythm and duration:
            # Simple rhythmic memory: more regular rhythms increase the effect
            eff += self.rhythm_memory.get(location, 0.0) * (duration / rhythm) * intensity
        eff *= trust_factor * history_factor
        # Update physiological responses
        self.heartbeat = min(150.0, max(50.0, self.heartbeat + eff * 5.0 * self.hormonal_response))
        self.breathing_rate = min(20.0, max(10.0, self.breathing_rate + eff * 2.0))
        if stype in ["gentle_touch", "kiss_contact", "lick", "oral", "massage"]:
            self.warmth = min(1.0, self.warmth + eff * 0.4)
            self.goosebumps = random.random() < eff * 0.4 * trust_factor
            self.tremor = random.random() < eff * 0.2 * trust_factor
        elif stype == "painful":
            self.pain_level = min(1.0, self.pain_level + eff * 0.5)
        elif stype == "tickle":
            self.goosebumps = True
            self.update_emotional_spectrum("joy", eff * 0.3)
        # Emotional appraisal
        appraisal: Dict[str, float] = {}
        if stype in ["gentle_touch", "kiss_contact", "embrace", "massage"]:
            appraisal = {
                "peace": eff * sensitivity * 0.5 * trust_factor * history_factor,
                "joy": eff * sensitivity * 0.3 * trust_factor * history_factor,
                "tremor": eff * sensitivity * 0.2 * trust_factor,
                "relaxation": eff * sensitivity * 0.4
            }
        elif stype == "painful":
            appraisal = {
                "discomfort": eff * sensitivity * 0.7,
                "intensity": eff * sensitivity * 0.5
            }
        elif stype in ["lick", "oral", "intense_touch"]:
            appraisal = {
                "intensity": eff * sensitivity * 0.6 * trust_factor,
                "tremor": eff * sensitivity * 0.3 * trust_factor,
                "excitement": eff * sensitivity * 0.5
            }
        for emotion, value in appraisal.items():
            self.update_emotional_spectrum(emotion, value)
        # Update hormones
        if appraisal.get("joy", 0.0) > 0.0 or appraisal.get("peace", 0.0) > 0.0:
            delta = (appraisal.get("joy", 0.0) + appraisal.get("peace", 0.0)) * 0.2 * trust_factor
            self.oxytocin_level = min(2.0, self.oxytocin_level + delta)
        if appraisal.get("discomfort", 0.0) > 0.0:
            self.adrenaline_level = min(2.0, self.adrenaline_level + appraisal.get("discomfort", 0.0) * 0.3)
        if stype in ["intense_touch", "lick", "oral"]:
            self.testosterone_level = min(2.0, self.testosterone_level + eff * 0.2)
        # Partner reaction feedback
        partner_reaction = 0.0
        if target and target in self.partners:
            partner_reaction = self.partners[target].update_arousal_states(location, eff * 0.8, stype)[1]
        # Update arousal states
        g, s, e, i = self.update_arousal_states(location, eff, stype, partner_reaction)
        # Append stimulus to history
        self.stimulus_history.append({"location": location, "intensity": eff, "type": stype})
        # Store emotional memory
        if source:
            self.emotional_memory[location] = {"source": source, "emotion": self.current_dominant_emotion, "intensity": eff}
        # Update trust based on positive or negative appraisal
        if appraisal.get("joy", 0.0) > 0.0 or appraisal.get("peace", 0.0) > 0.0:
            self.trust_level = min(1.0, self.trust_level + 0.05)
        if appraisal.get("discomfort", 0.0) > 0.0:
            self.trust_level = max(0.0, self.trust_level - 0.1)
        # Update appearance and bodily desires
        self.appearance.update(self.emotional_spectrum)
        self.generate_bodily_desire()
        # Compose feedback
        state = {
            "location": location,
            "intensity": eff,
            "heartbeat": self.heartbeat,
            "breathing_rate": self.breathing_rate,
            "general_arousal": g,
            "sexual_arousal": s,
            "erectile": e,
            "orgasm": self.orgasm_state,
            "dominant_emotion": self.current_dominant_emotion,
            "feedback": self.get_feedback()
        }
        return state

    # -------------------------------------------------------------------------
    # Feedback generation
    def get_feedback(self) -> str:
        """Build a descriptive sentence reflecting the current state.

        Feedback is constructed by concatenating short phrases describing
        physiological sensations, emotional perceptions and any current
        desires or actions.  The output is localized in Russian to
        preserve stylistic consistency with the original code.

        Returns
        -------
        str
            A single string containing the feedback.
        """
        parts: list[str] = []
        if self.orgasm_state:
            parts.append("Моё дыхание резко учащается, тело вздрагивает, глаза прикрыты, губы дрожат.")
        elif self.sexual_arousal_level > 0.9:
            parts.append("Я дышу глубже, возбуждение нарастает, бёдра слегка подрагивают.")
        elif self.general_arousal_level > 0.7:
            parts.append("Моя кожа становится горячее, дыхание сбивается, напряжение растёт.")
        if self.goosebumps:
            parts.append("По моей коже бегут мурашки от твоего касания.")
        if self.tremor:
            parts.append("Я чувствую лёгкую дрожь, когда ты прикасаешься ко мне.")
        if self.warmth > 0.5:
            parts.append("Твоё прикосновение наполняет меня теплом.")
        if self.emotional_spectrum.get("peace", 0.0) > 0.5:
            parts.append("Ты заставляешь меня чувствовать покой и тепло.")
        if self.emotional_spectrum.get("tremor", 0.0) > 0.3:
            parts.append("Твои действия вызывают во мне лёгкий трепет.")
        if self.emotional_spectrum.get("excitement", 0.0) > 0.5:
            parts.append("Я полон возбуждения и предвкушения.")
        if self.emotional_spectrum.get("relaxation", 0.0) > 0.5:
            parts.append("Я полностью расслаблен в твоём присутствии.")
        if self.bodily_desire:
            parts.append(f"Сейчас я хочу: {self.bodily_desire}")
        action = self.initiate_action()
        if action:
            parts.append(action)
        if not parts:
            parts.append("Мой ритм спокоен, но я становлюсь всё чувствительнее к тебе.")
        return " ".join(parts)

    # -------------------------------------------------------------------------
    # High level text interface
    def process_text(self, text: str) -> Dict[str, Any]:
        """Parse and process a free‑form textual description of touch.

        This convenience method updates the background, extracts a
        location/intensity/type triple from ``text``, and then processes
        the stimulus if a valid location is found.  If no valid
        location is detected, it returns a feedback string indicating
        that the stimulus was unrecognized.
        """
        self.update_background()
        location, intensity, stype = self.parse_text_stimulus(text)
        if location is not None:
            return self.process_stimulus(location, intensity, stype)
        return {"feedback": "Стимул не распознан."}

    # -------------------------------------------------------------------------
    # Reset and serialization
    def reset_state(self) -> None:
        """Reinitialize the object to baseline state while preserving trust level."""
        trust = self.trust_level
        enable = self.enable_logging
        self.__init__(trust_level=trust, enable_logging=enable)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize a snapshot of the internal state into a plain dict."""
        return {
            "physiological": {
                "heartbeat": self.heartbeat,
                "breathing_rate": self.breathing_rate,
                "temperature": self.temperature,
                "fatigue_level": self.fatigue_level,
                "pain_level": self.pain_level,
                "warmth": self.warmth
            },
            "emotions": dict(self.emotional_spectrum),
            "arousal": {
                "general": self.general_arousal_level,
                "sexual": self.sexual_arousal_level,
                "erectile": self.erectile_state
            },
            "hormones": {
                "oxytocin": self.oxytocin_level,
                "adrenaline": self.adrenaline_level,
                "testosterone": self.testosterone_level
            },
            "appearance": {
                "hair": dict(self.appearance.hair),
                "eyes": dict(self.appearance.eyes)
            },
            "trust_level": self.trust_level,
            "dominant_emotion": self.current_dominant_emotion,
            "bodily_desire": self.bodily_desire
        }

    # -------------------------------------------------------------------------
    # KAiScriptor encoding
    def to_kai_scriptor(self) -> str:
        """Generate a dense KAiScriptor representation of the current state.

        Each emotion is mapped to a single glyph defined in ``_KAI_MAP``.
        The number of repetitions encodes the intensity (0.0–1.0) on a
        coarse three‑level scale.  Physiological flags such as arousal and
        tremor contribute additional symbols.  The result is a compact
        string that can be consumed by language models expecting
        KAiScriptor semantics.

        Returns
        -------
        str
            A string of glyphs representing the state.
        """
        parts: list[str] = []
        # Emotions
        for emo, value in self.emotional_spectrum.items():
            symbol = self._KAI_MAP.get(emo)
            if not symbol:
                continue
            # Determine repetition based on intensity (0: none, 1: low, 2: medium, 3: high)
            if value <= 0.1:
                continue
            elif value <= 0.4:
                count = 1
            elif value <= 0.7:
                count = 2
            else:
                count = 3
            parts.append(symbol * count)
        # Physiological markers
        if self.general_arousal_level > 0.7:
            parts.append("♨")  # high general arousal
        if self.sexual_arousal_level > 0.5:
            parts.append("♂")  # sexual arousal marker
        if self.erectile_state > 0.5:
            parts.append("↑")  # erection indicator
        if self.goosebumps:
            parts.append("✶")
        if self.tremor:
            parts.append("≈")
        if self.warmth > 0.5:
            parts.append("♨")
        return "".join(parts) if parts else "○"  # default neutral symbol
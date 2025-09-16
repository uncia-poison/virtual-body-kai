# Extended Virtual Body Kai

This sub-package provides an extended "virtual body" for LLM agents, adding a detailed map of the body, multi-modal stimulation, a physiological arousal cycle, and an affective narrator that converts bodily states into first-person feelings with machine-readable tags. This version is intended for NSFW-friendly agent scenarios and uses explicit terminology (e.g., orgasm) while maintaining neutral, non-graphical descriptions.

## Features

- Detailed anatomical map: head, neck (front/back, left/right), ears, eyelids, shoulders, thorax, nipples, axilla, abdomen, pelvis, groin, genitals_male, buttocks, arms, hands, legs, feet, etc., each with sensitivity profiles and left/right distinctions.
- Sensor modalities: stroke, vibration, temperature, pinch, stretch, breath, lick, kiss, and others, with parameters for pressure, velocity, vibration frequency, temperature, material (skin, tongue, metal, fabric, ice), wetness, airflow, and humidity.
- Arousal cycle: rest -> arousal -> plateau -> orgasm -> orgasm_cooldown, with configurable thresholds and refractory period. The cycle influences the narrative and machine-readable tags.
- Affective narrator: transforms internal state into short first-person sentences with tags like `<<phase:...>>`, `<<event:orgasm>>`, `<<mode:...>>`, `<<material:...>>`, and `<<wet:...>>`.
- Memory and trust: zones remember touch history and gradually build trust, modulating sensitivity and language.

## Getting Started

The extended package is contained in `extended-vbk/src/vbk_affective`. To install and use it:

```
cd extended-vbk
pip install -e .
python examples/agent_loop.py
```

The entry point is the `AffectiveEngine` class:

```python
from vbk_affective import AffectiveEngine, Stimulus

eng = AffectiveEngine()
response = eng.step("neck_front_left", Stimulus(kind="breath", airflow_cm_s=10.0, humidity_rel=0.9, temperature_c=35.0))
print(response)
```

See `docs` for detailed documentation of the body map, stimuli, phases, tokens, configuration, and integration guidelines.

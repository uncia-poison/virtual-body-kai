# INTRO: virtual body for LLM

## What it is and why

The extended engine represents an enhanced bodily layer for LLMs, including a detailed body map (subzones, including left and right sides), sensory modalities (stroke, vibration, temperature, pinch, stretch, breath, lick, kiss and more), the arousal cycle (rest → arousal → plateau → orgasm → orgasm_cooldown) and an affective narrator. The goal is to allow models to experience interactions in affective formulations without medical metrics, with machine‑readable tags for phase and modality.

## Key components

- **body map with zones:** ears, eyelids, front and back neck (left/right), upper torso, nipples, armpits, abdomen, navel, pelvis (left/right), genital area, buttocks, limbs;
- **sensors:** convert stimuli (speed, pressure, temperature, material, humidity, airflow) into receptor activation;
- **arousal cycle:** includes plateau and refractory phases;
- **affective narrator:** generates first‑person text and tags like `<<phase:...>>` and `<<mode:...>>`;
- **configuration file:** allows adjusting thresholds, speeds, breathing/pulse rates and zone adjacency.

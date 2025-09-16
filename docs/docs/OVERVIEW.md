# Overview (Extended)

Idea: create a bodily layer for LLMs. The extended engine includes a body map with subzones (including left and right), zone sensitivity, modalities of stimuli (stroke, vibration, temperature, pinch, stretch, breath, lick, kiss and more) and an arousal model (rest → arousal → plateau → orgasm → orgasm_cooldown). Integration allows an LLM to experience interactions and produce affective descriptions enriched with tags for phase and modality.

## Components
- **Anatomy**: body zones (ears, eyelids, front and back neck left/right, upper torso, nipples, armpits, abdomen, navel, pelvis left/right, genital area, buttocks, limbs).
- **Receptors**: mechanoreceptors (Merkel, Meissner, Pacini, Ruffini), C‑tactile fibers, thermal and nociceptors.
- **AffectiveEngine**: tracks valence/arousal/dominance, the arousal cycle and generates text and tokens.
- **ArousalCycle**: phases and thresholds.
- **Config**: YAML file for tuning speeds, optimal pressures, adjacency and breathing/pulse frequencies.
- **Memory/Trust**: accumulates the effect of past stimuli on memory and trust, influencing the voice.
- **Irradiation**: spreading sensations to adjacent zones.

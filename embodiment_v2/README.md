# Virtual Body Kai — Embodiment v2 (additive preview)

This directory introduces a new, standalone body simulation while preserving every historical source file. The existing virtual_body_kai.py, extended-vbk/, docs and all earlier commits remain unchanged.

The purpose is to make embodied state **explicit, continuous, testable and portable**. This module does not assert biological sensations, subjective consciousness or a functioning physical robot. The terms warmth, comfort, pain, pulse and breath in this package describe **simulation variables** rather than observed human physiology.

## Architecture

- core.py — the deterministic body kernel, validated input types, reference anatomy, joint envelopes, virtual proprioception, sensor integration, bounded affect/interoception and JSON snapshots.
- bridge.py — read-only data exchange for agent prompts and a future KAiScriptor adapter. Provides an intentionally non-actuating hardware boundary.
- __init__.py — public API; does not import or run legacy modules.
- ../examples/embodiment_v2_demo.py — executable demonstration.
- ../tests/test_embodiment_v2.py — regression tests using the Python standard library.

### Body representation

The reference anatomy contains 36 named regions including left/right cheeks, ears, shoulders, arms, hands, palms, fingers, hips, thighs, shins, and feet. Each region has a parent, a reference Cartesian center in metres (+x right, +y forward, +z up), and a sensitivity gain. The landmarks assume a roughly 1.90 m anthropomorphic reference and are illustrative, not fitted to any actual chassis.

The joint model includes neck and waist yaw/pitch, shoulder pitch/roll, elbow, wrist, hip, knee and ankle positions on both sides. Limits and maximum simulated speeds are explicit. Motions are clamped to a bounded per-frame increment. No body collisions, loads, gravity or torque are computed.

### Sensory events

A SensoryEvent has a modality, body region, magnitude in [0,1], provenance, and optional modality-specific attributes. Supported modalities: touch, pressure, temperature, pain, proximity, vision, sound and joint position. Every input origin is one of simulated, sensor or user_report. No adapter may quietly convert simulated input into physically observed input.

Skin contact, pressure, pain and salience have different decay constants. Temperature gradually relaxes toward a baseline. The engine keeps a bounded trace of percepts and exposes a salience-based focus list. Long-term autobiographical memory and interpretation of emotions are deliberately not conflated with the transient sensory buffer.

### Internal variables

Energy, fatigue, tension, comfort, activation, valence, trust and warmth are normalized model variables. Heartbeat and breathing variables are explicitly suffixed with _simulated. These formulas are simple, transparent heuristics; they are not clinical models.

### Deterministic continuity

The caller supplies dt_s in (0,1] seconds. No external wall clock, random generator or internet is involved. All events and intents are validated before mutation, so invalid inputs leave the entire engine untouched. A versioned JSON snapshot supports persistence and validated restoration. Separate version tags prevent accidental loading of incompatible data.

### Intent vs actual actuation

MotionIntent creates only a simulated MotionProposal and changes virtual joint positions. HardwareBoundary.inspect() provides a reviewable summary; HardwareBoundary.execute() unconditionally raises a RuntimeError. The absence of physical command output is intentional. Before any real robot integration, implement an independently reviewed safety controller, limit switches, collision detection, watchdog, dead-man switch, hardware emergency stop, and calibration procedures.

## Run (Python 3.10+, no third-party packages)

From the repository root:

    python -m examples.embodiment_v2_demo
    python -m unittest discover -s tests -p 'test_embodiment_v2.py' -v

Example:

    from embodiment_v2 import EmbodimentEngine, SensoryEvent, MotionIntent
    body = EmbodimentEngine()
    snapshot = body.step(
        0.1,
        events=[SensoryEvent("touch", "palm_left", 0.6, origin="simulated")],
        intents=[MotionIntent("neck_yaw", 15, requested_speed_deg_s=10)],
    )
    assert snapshot["simulation"] is True

Agent integrations can call to_agent_context(body) and to_kai_tags(body). The new VBK2 tag grammar is an interchange proposal, **not** a claim of compatibility with existing KAiScriptor decoders. A legacy snapshot can be passed to legacy_reference(legacy.to_dict()) for read-only reference without mutating or importing the old implementation.

## Historical preservation and next engineering steps

1. Never edit past sources merely to add v2 functionality; prefer additional modules and a reviewed adapter.
2. Keep the original source and all old commits intact; contributions are additive.
3. Preserve simulated vs observed source labels in logs and derived text.
4. Next: calibrated skeleton (URDF), force sensors, orientation/vestibular estimates, robust inter-sensor timestamp handling, body collision model, tactile receptive-field maps, stance and balance, durable event logging, and optional ROS 2 bridge behind an independently tested physical safety controller.

**Status:** tested software simulation kernel; not a claim of completed physical embodiment or autonomous agency.

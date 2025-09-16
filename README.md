# virtual-body-kai

### What it is and why

**virtual-body-kai** is a repository about a "bodily layer" for large language models (LLMs). It contains two layers:

- **Legacy** (`virtual_body_kai.py`) — the historical version, left unchanged.
- **Extended** (`extended-vbk/`) — an expanded embodiment engine: a body map with subzones (including left/right), modalities of touch (breath, lick/kiss, fingers, cold fingers and more), an affective narrator, the cycle rest → arousal → plateau → orgasm → orgasm_cooldown, memory/trust, breathing and pulse rhythms, and machine‑readable tags in text and JSON output.

**Why:** to let an agent or model not just **describe** but **experience** interactions in an embodied, affective way — within safe language and without euphemisms in code. Suitable for adult NSFW‑friendly scenarios (not for children).

### Quick start (Extended)

```bash
cd extended-vbk
pip install -e .
python examples/agent_loop.py
```

### Documentation

See the files in [`docs`](./docs/).

### DOI

Pochinova Alina. Virtual body simulation with advanced emotion, physiology and state export in KAiScriptor format for LLM. DOI: 10.5281/zenodo.16945929.

### License

MIT.

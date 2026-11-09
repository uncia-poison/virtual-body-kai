# Embodiment v3: experience from action

An LLM receives a body observation, chooses a movement and gets a new observation
shaped by the physical result. In the first scene, a simulated left arm can reach
a tabletop object, retract or hold position. MuJoCo runs the shoulder and elbow
actuators and computes contact. The model receives pose, joint position and
velocity, pressure in the palm, contact duration, peak force, impulse and the
existing VBK internal-state summary. The contact impulse also feeds the v2 body
model, whose pressure and attention signals persist and decay.

The scene is planar and headless. Its world coordinates are structured sensory
input. Pulse, breathing and other v2 internal variables are simulated. The
architecture gives a model a record of situated experience whose effects can
be checked. The pilot measures attribution of a contact to an action.

## Try it

Python 3.10+ with the tested solver version:

```sh
python -m pip install -r embodiment_v3/requirements.txt
python -m embodiment_v3 --checkpoint body.json --steps 3
python -m embodiment_v3 --checkpoint body.json --steps 3
python -m unittest discover -s tests -v
```

The scripted demo reaches, retracts, and then lets the environment push the
object toward the hand. It needs no model, credentials or GPU. The second
invocation resumes the saved session. Save to a private local path with a
single writer, and keep the checkpoint out of Git. It includes both the
agent-visible experience and the experimenter's audit trail.

To give an LLM control, point the CLI at a running OpenAI-compatible endpoint.
The default URL is Ollama's local compatibility endpoint. Use the name of a
model already available on your server:

```sh
python -m embodiment_v3 --model YOUR_MODEL --checkpoint body.json --steps 4
python -m embodiment_v3 --model YOUR_MODEL --probe --steps 6
```

For a different server, pass `--base-url` ending in its API base path and set
`VBK_API_KEY` if needed. A hosted endpoint receives the observation and recent
experience. Responses must be one of the defined actions. Transport errors or
invalid actions leave the pending tick uncommitted.

## Experience and attribution

Each tick advances the scene 0.5 simulated seconds. The journal stores the
observation before the action, the chosen action, the resulting observation and
the measured left-palm contact. The session retains 64 episodes and exposes
the most recent eight to the model. Physical state, the v2 body state and both
journals are saved together. Restoring requires the same scene and solver
version. The session can be resumed with a different model.

For every tick, the audit runs a second physics rollout from the same
integration state with the same environmental input and a neutral arm command.
Contact is marked as added by the action when the real rollout had contact and
the neutral rollout had none. If both touch, the model action can still change
the force. The audit reports the impulse difference separately. The model does
not receive the neutral rollout, external command or expected answer.

The probe saves and reloads each episode before asking the model about the
contact. It varies whether the environment moved the object and sometimes
uses a reach in both categories. Both conditions get the same retrospective
cue. Only one gets the restored episodes. This is a balanced, paired smoke
test with a small set of deterministic cases. Estimating a general memory
benefit requires new scene layouts, independent episodes and additional
controls, such as shuffled history and competing explanations.

## Hand a checkpoint reference to Kai

```sh
python -m embodiment_v3 --checkpoint body.json --inspect-as lineages/demo/body.json
```

This emits the metadata accepted by Kai's
`EmbodimentBridge.reference_from_inspect`: a relative locator, SHA-256,
lineage ID, age and parent digest. Use the relative locator for the checkpoint
where you actually store it. An explicit host can attach the reference to
Kai's ledger. The simulation owns the checkpoint bytes. This metadata format
provides no remote lease or automatic agent orchestration.

V3 has no hardware backend. Its scene models a single arm and palm contact.
The v2 source, earlier implementations and their files remain available.

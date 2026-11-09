import json
import unittest
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread

try:
    import mujoco
except ImportError:
    mujoco = None

if mujoco is not None:
    from embodiment_v3 import Session
    from embodiment_v3.__main__ import memory_probe
    from embodiment_v3.agent import ChatAgent


@unittest.skipIf(mujoco is None, "optional MuJoCo dependency")
class CausalEmbodimentTests(unittest.TestCase):
    def test_touch_origin_requires_physical_counterfactual(self):
        for action, external, necessary in [
            ("reach", "hold", True), ("hold", "push", False), ("reach", "push", False),
        ]:
            with self.subTest(action=action, external=external):
                session = Session()
                event = session.turn(lambda _, selected=action: selected, external=external)
                self.assertGreater(event["palm_contact"]["seconds"], 0)
                self.assertGreater(event["palm_contact"]["impulse_ns"], 0)
                self.assertEqual(event["palm_contact"]["origin"], "simulated")
                self.assertEqual(session.audit[-1]["contact_added_by_action"], necessary)
                observed = session.observation()
                self.assertGreater(observed["left_palm"]["pressure"], 0)
                self.assertNotIn("counterfactual", json.dumps(observed))
                self.assertNotIn('"external"', json.dumps(observed))

    def test_checkpoint_preserves_next_step_and_kai_lineage(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "body.json"
            continuous = Session()
            continuous.turn(lambda _: "reach")
            continuous.save(path)
            prior = Session.inspect(path, reference_path="lineages/demo/body.json")
            self.assertEqual(prior["checkpoint_sha256"], sha256(path.read_bytes()).hexdigest())
            resumed = Session.load(path)
            expected = continuous.turn(lambda _: "withdraw", external="reset")
            actual = resumed.turn(lambda _: "withdraw", external="reset")
            self.assertEqual(actual, expected)
            self.assertEqual(continuous.checkpoint(), resumed.checkpoint())
            resumed.save(path)
            info = Session.inspect(path, reference_path="lineages/demo/body.json")
            self.assertEqual(info["age_ticks"], prior["age_ticks"] + 1)
            self.assertEqual(info["lineage_id"], prior["lineage_id"])
            self.assertEqual(info["parent_checkpoint_sha256"], prior["checkpoint_sha256"])
            self.assertNotIn("experience", info)
            with self.assertRaises(ValueError):
                continuous.save(path)

    def test_rejected_agent_action_does_not_advance_body(self):
        session = Session()
        before = session.checkpoint()
        with self.assertRaises(ValueError):
            session.turn(lambda _: "fly", external="push")
        self.assertEqual(session.checkpoint(), before)

    def test_memory_ablation_keeps_control_cue_identical(self):
        requests = []

        def classifier(obs):
            requests.append(obs)
            return "external"

        report = memory_probe(classifier, trials=2, seed=42)
        controls = [req for req in requests if "recent_experience" not in req]
        self.assertEqual(len(controls), 4)
        self.assertTrue(all(control == controls[0] for control in controls))
        self.assertEqual(report["accuracy"], {"with_history": 0.5, "without_history": 0.5})
        self.assertEqual(len(report["trials"]), 4)

    def test_chat_endpoint_gets_body_and_then_consequences(self):
        calls = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                calls.append((self.path, json.loads(request["messages"][-1]["content"])))
                payload = b'{"choices":[{"message":{"content":"reach"}}]}'
                self.send_response(200)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *args):
                pass

        with HTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = Thread(target=server.serve_forever)
            thread.start()
            try:
                agent = ChatAgent(f"http://127.0.0.1:{server.server_port}/v1", "test")
                session = Session()
                session.turn(agent)
                session.turn(agent)
            finally:
                server.shutdown()
                thread.join()

        self.assertEqual(calls[0][0], "/v1/chat/completions")
        self.assertEqual(calls[0][1]["recent_experience"], [])
        self.assertGreater(calls[1][1]["latest_contact"]["seconds"], 0)
        self.assertEqual(calls[1][1]["recent_experience"][-1]["action"], "reach")

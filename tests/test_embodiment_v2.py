"""Stdlib tests: python -m unittest discover -s tests -p 'test_embodiment_v2.py'."""
import copy
import json
import math
import unittest

from embodiment_v2 import (EmbodimentEngine, HardwareBoundary, JointLimit,
                           MotionIntent, SensoryEvent, Vector3, default_regions,
                           legacy_reference, to_agent_context, to_kai_tags)


class EmbodimentTests(unittest.TestCase):
    def test_anatomy_is_connected(self):
        regions = default_regions()
        self.assertGreaterEqual(len(regions), 30)
        for name, region in regions.items():
            if region.parent:
                self.assertIn(region.parent, regions, name)

    def test_vector_is_finite(self):
        self.assertAlmostEqual(Vector3(0, 0, 0).distance_to(Vector3(1, 2, 2)), 3.0)
        with self.assertRaises(ValueError):
            Vector3(math.nan, 0, 0)

    def test_tick_is_deterministic(self):
        e = SensoryEvent("touch", "cheek_right", .6)
        a, b = EmbodimentEngine(), EmbodimentEngine()
        for _ in range(4):
            self.assertEqual(a.step(.25, [e]), b.step(.25, [e]))

    def test_event_is_identified_as_simulation(self):
        body = EmbodimentEngine()
        state = body.step(.1, [SensoryEvent("touch", "palm_left", .5)])
        self.assertGreater(state["surface"]["palm_left"]["touch"], 0)
        self.assertEqual(state["recent_percepts"][0]["origin"], "simulated")
        self.assertTrue(state["simulation"])

    def test_sensor_origin_survives_bridge(self):
        body = EmbodimentEngine()
        body.step(.1, [SensoryEvent("vision", "face", .5, origin="sensor")])
        self.assertEqual(to_agent_context(body)["percept_sources"], ["sensor"])

    def test_decay(self):
        body = EmbodimentEngine()
        body.step(.1, [SensoryEvent("touch", "hand_left", 1)])
        before = body.region_state["hand_left"].touch
        body.step(1)
        self.assertLess(body.region_state["hand_left"].touch, before)

    def test_joint_motion_rate_limited(self):
        body = EmbodimentEngine()
        state = body.step(.1, intents=[MotionIntent("neck_yaw", 50, 20)])
        self.assertAlmostEqual(state["joints_deg"]["neck_yaw"], 2)
        self.assertTrue(state["motion_proposals"][0]["simulated"])

    def test_hardware_disabled(self):
        body = EmbodimentEngine()
        body.step(.1, intents=[MotionIntent("neck_yaw", 30)])
        self.assertFalse(HardwareBoundary.inspect(body)["hardware_enabled"])
        with self.assertRaises(RuntimeError):
            HardwareBoundary.execute(body)

    def test_invalid_event_is_transactional(self):
        body = EmbodimentEngine()
        before = body.snapshot()
        with self.assertRaises(ValueError):
            body.step(.1, [SensoryEvent("touch", "hand_left", .4),
                           SensoryEvent("touch", "missing", .5)])
        self.assertEqual(body.snapshot(), before)

    def test_invalid_intent_is_transactional(self):
        body = EmbodimentEngine()
        before = body.snapshot()
        with self.assertRaises(ValueError):
            body.step(.1, [SensoryEvent("touch", "hand_left", .4)],
                      [MotionIntent("neck_yaw", 500)])
        self.assertEqual(body.snapshot(), before)

    def test_bad_numbers_rejected(self):
        body = EmbodimentEngine()
        for bad in (float("nan"), float("inf"), -.1, 1.1):
            with self.assertRaises(ValueError):
                body.step(.1, [SensoryEvent("touch", "palm_left", bad)])
        for dt in (0, -1, 1.1, float("nan")):
            with self.assertRaises(ValueError):
                body.step(dt)

    def test_joint_report_is_bounded(self):
        body = EmbodimentEngine()
        body.step(.1, [SensoryEvent("joint", "neck", .3, joint_name="neck_yaw", angle_deg=120)])
        self.assertEqual(body.joint_angles_deg["neck_yaw"], 50)

    def test_temperature_and_discomfort(self):
        body = EmbodimentEngine()
        body.step(.1, [SensoryEvent("temperature", "palm_right", 1, temperature_c=2)])
        self.assertGreater(body.region_state["palm_right"].pain, 0)

    def test_json_snapshot_roundtrip(self):
        body = EmbodimentEngine()
        body.step(.25, [SensoryEvent("touch", "cheek_left", .7)])
        encoded = json.loads(json.dumps(body.snapshot()))
        clone = EmbodimentEngine.from_snapshot(encoded)
        self.assertEqual(clone.snapshot()["internal"], body.snapshot()["internal"])
        self.assertEqual(clone.snapshot()["recent_percepts"], body.snapshot()["recent_percepts"])
        self.assertEqual(clone.snapshot()["joints_deg"], body.snapshot()["joints_deg"])

    def test_corrupt_snapshot_rejected(self):
        body = EmbodimentEngine()
        data = body.snapshot()
        data["internal"]["energy"] = 99
        with self.assertRaises(ValueError):
            EmbodimentEngine.from_snapshot(data)

    def test_snapshot_detached(self):
        body = EmbodimentEngine()
        snapshot = body.snapshot()
        snapshot["internal"]["trust"] = 0
        snapshot["surface"]["hand_left"]["touch"] = 1
        self.assertEqual(body.internal.trust, .5)
        self.assertEqual(body.region_state["hand_left"].touch, 0)

    def test_history_is_bounded(self):
        body = EmbodimentEngine(history_limit=3)
        for _ in range(7):
            body.step(.1, [SensoryEvent("sound", "head", .4)])
        self.assertEqual(len(body.history), 3)

    def test_legacy_adapter_is_read_only(self):
        source = {"dominant_emotion": "curiosity", "physiological": {"warmth": .4}}
        frozen = copy.deepcopy(source)
        result = legacy_reference(source)
        result["physiological"]["warmth"] = 1
        self.assertEqual(source, frozen)
        self.assertIn("VBK2", to_kai_tags(EmbodimentEngine()))


if __name__ == "__main__":
    unittest.main()

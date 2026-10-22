import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "receiver" / "receiver.py"
spec = importlib.util.spec_from_file_location("ddsm_receiver", MODULE_PATH)
receiver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(receiver)


class ReplayProtectionTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        receiver.EVENTS_FILE = Path(self.temp_dir.name) / "events.jsonl"
        receiver.seen_ids.clear()

    def test_restores_event_ids_from_archive(self):
        receiver.EVENTS_FILE.write_text(
            json.dumps({"event_id": "already-accepted"}) + "\n"
            + "{broken json\n"
            + json.dumps({"event_id": "also-accepted"}) + "\n",
            encoding="utf-8",
        )
        receiver.load_seen_ids()
        self.assertIn("already-accepted", receiver.seen_ids)
        self.assertIn("also-accepted", receiver.seen_ids)

    def test_missing_archive_is_ok(self):
        receiver.load_seen_ids()
        self.assertEqual(receiver.seen_ids, set())


if __name__ == "__main__":
    unittest.main()

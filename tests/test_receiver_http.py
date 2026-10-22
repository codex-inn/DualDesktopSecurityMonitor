import importlib.util
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "receiver" / "receiver.py"
spec = importlib.util.spec_from_file_location("ddsm_receiver_http", MODULE_PATH)
receiver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(receiver)


class ReceiverHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        receiver.EVENTS_FILE = Path(self.temp_dir.name) / "events.jsonl"
        receiver.seen_ids.clear()
        self.token = "unit-test-token-that-is-long-enough-123456"
        self.server = receiver.ThreadingHTTPServer(("127.0.0.1", 0), receiver.Handler)
        self.server.auth_token = self.token
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self._stop_server)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def _stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, path, method="GET", payload=None, token=None, content_type="application/json"):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {}
        if token is not None:
            headers["Authorization"] = "Bearer " + token
        if data is not None:
            headers["Content-Type"] = content_type
        req = urllib.request.Request(self.base + path, data=data, headers=headers, method=method)
        try:
            response = urllib.request.urlopen(req, timeout=3)
            return response.status, response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8")

    def test_health_and_dashboard(self):
        status, body = self.request("/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["status"], "ok")
        status, body = self.request("/")
        self.assertEqual(status, 200)
        self.assertIn("DualDesktopSecurityMonitor", body)

    def test_accepts_authenticated_event_and_lists_it(self):
        payload = {
            "event_id": "unit-event-1",
            "source": "UnitTest",
            "event_type": "synthetic_test_alert",
            "severity": "info",
            "details": "Synthetic only.",
        }
        status, body = self.request("/api/events", "POST", payload, self.token)
        self.assertEqual(status, 201, body)
        status, body = self.request("/api/events")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["events"][0]["event_id"], "unit-event-1")

    def test_rejects_wrong_token(self):
        payload = {
            "event_id": "unit-event-2",
            "source": "UnitTest",
            "event_type": "synthetic_test_alert",
            "severity": "info",
            "details": "Synthetic only.",
        }
        status, _ = self.request("/api/events", "POST", payload, "incorrect-token")
        self.assertEqual(status, 401)

    def test_rejects_duplicate_event_id(self):
        payload = {
            "event_id": "unit-event-3",
            "source": "UnitTest",
            "event_type": "synthetic_test_alert",
            "severity": "info",
            "details": "Synthetic only.",
        }
        first, _ = self.request("/api/events", "POST", payload, self.token)
        second, _ = self.request("/api/events", "POST", payload, self.token)
        self.assertEqual(first, 201)
        self.assertEqual(second, 409)

    def test_rejects_invalid_severity(self):
        payload = {
            "event_id": "unit-event-4",
            "source": "UnitTest",
            "event_type": "synthetic_test_alert",
            "severity": "unknown",
            "details": "Synthetic only.",
        }
        status, _ = self.request("/api/events", "POST", payload, self.token)
        self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()

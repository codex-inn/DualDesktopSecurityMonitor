#!/usr/bin/env python3
"""Run a visible, loopback-only DDSM demonstration on one Windows computer."""
import argparse
import json
import secrets
import threading
import time
import urllib.request
import uuid
import webbrowser
from http.server import ThreadingHTTPServer

from receiver import receiver


def start_demo(port: int = 0, open_browser: bool = False):
    """Start a loopback-only receiver, send one synthetic alert, and return handles."""
    token = secrets.token_urlsafe(32)
    receiver.load_seen_ids()
    server = ThreadingHTTPServer(("127.0.0.1", port), receiver.Handler)
    server.auth_token = token
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    dashboard_url = f"http://127.0.0.1:{server.server_address[1]}/"
    payload = {
        "event_id": str(uuid.uuid4()),
        "source": "LocalDemo",
        "event_type": "synthetic_test_alert",
        "severity": "info",
        "details": "Harmless local demonstration. No personal data included.",
    }
    request = urllib.request.Request(
        dashboard_url.rstrip("/") + "/api/events",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            if response.status != 201:
                raise RuntimeError(f"Receiver returned unexpected HTTP status {response.status}")
            result = json.loads(response.read().decode("utf-8"))
    except Exception:
        server.shutdown()
        server.server_close()
        raise
    if open_browser:
        webbrowser.open(dashboard_url)
    return server, thread, dashboard_url, result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a local-only DDSM dashboard and send one harmless synthetic alert."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Local port; default 0 chooses an available port automatically.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open the dashboard automatically.",
    )
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("port must be between 0 and 65535")

    try:
        server, _thread, dashboard_url, result = start_demo(
            port=args.port, open_browser=not args.no_browser
        )
    except Exception as exc:
        print(f"Could not start local demo: {exc}")
        return 1

    print("DualDesktopSecurityMonitor local demo is running.")
    print("Network scope: this computer only (127.0.0.1); no Tailscale or second PC needed.")
    print(f"Dashboard: {dashboard_url}")
    print(f"Synthetic test alert accepted: {result.get('accepted')}")
    print("Leave this window open. Press Ctrl+C to stop the demo.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping local demo.")
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

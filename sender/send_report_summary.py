#!/usr/bin/env python3
"""Send a privacy-minimized summary of a locally reviewed DDSM inventory report."""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path


def summarize_report(text: str) -> dict:
    """Return counts only; never include process names or registry command data."""
    if "DualDesktopSecurityMonitor - Local Inventory Report" not in text:
        raise ValueError("This file does not look like a DDSM inventory report.")
    process_section = re.search(r"\[Running processes\](.*?)(?=\n\[|\Z)", text, re.S)
    process_count = len(re.findall(r"^PID=\d+\s+Name=", process_section.group(1), re.M)) if process_section else 0
    startup_count = 0
    for label in ("Current-user startup Run entries", "Machine startup Run entries"):
        section = re.search(r"\[" + re.escape(label) + r"\](.*?)(?=\n\[|\Z)", text, re.S)
        if section:
            startup_count += len(re.findall(r"^Name=", section.group(1), re.M))
    generated = re.search(r"^Generated:\s*(.+)$", text, re.M)
    return {
        "generated": generated.group(1).strip()[:80] if generated else "unknown",
        "process_entries": process_count,
        "startup_entries": startup_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Send counts from a local DDSM report; report contents stay on this computer."
    )
    parser.add_argument("--report", default="security_report.txt", help="Path to the local report")
    parser.add_argument("--receiver", required=True, help="Desktop B Tailscale URL, e.g. http://100.x.y.z:8787")
    parser.add_argument("--source", default="Desktop-A", help="Short source label")
    args = parser.parse_args()
    token = os.environ.get("DDSM_TOKEN", "")
    if len(token) < 32:
        raise SystemExit("Set DDSM_TOKEN to the same random secret used on Desktop B.")
    try:
        summary = summarize_report(Path(args.report).read_text(encoding="utf-8-sig", errors="replace"))
    except (OSError, ValueError) as exc:
        print(f"Cannot summarize report: {exc}", file=sys.stderr)
        return 2

    details = (
        f"Local inventory report generated: {summary['generated']}; "
        f"process entries: {summary['process_entries']}; "
        f"startup entries: {summary['startup_entries']}. "
        "Counts only; report content, process names, and startup commands were not sent."
    )
    payload = {
        "event_id": str(uuid.uuid4()),
        "source": args.source[:80] or "Desktop-A",
        "event_type": "inventory_report_summary",
        "severity": "info",
        "details": details[:2000],
    }
    request = urllib.request.Request(
        args.receiver.rstrip("/") + "/api/events",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + token},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            print("Receiver response:", response.status, response.read().decode("utf-8"))
            print("Only report counts were sent; the full report stayed local.")
            return 0 if response.status == 201 else 1
    except urllib.error.HTTPError as exc:
        print("Receiver rejected the event:", exc.code, exc.read().decode("utf-8"), file=sys.stderr)
    except (urllib.error.URLError, TimeoutError) as exc:
        print("Could not reach Desktop B. Check Tailscale, IP, port, and firewall:", exc, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

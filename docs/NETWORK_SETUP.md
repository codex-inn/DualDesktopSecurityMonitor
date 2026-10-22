# Two-desktop network setup

The receiver and synthetic sender are implemented for devices you own or are authorized to administer.

## Topology

- Desktop A: Windows 10, local sensor and test sender.
- Desktop B: Windows 11, dashboard and event receiver.
- Both devices join the same authorized Tailscale tailnet, even on different internet connections.
- The receiver binds to Desktop B's Tailscale IP. Do not configure router port forwarding or expose the listener to the public internet.

## Start Desktop B

1. Install Tailscale and Python 3.10+.
2. Find Desktop B's Tailscale IPv4 address.
3. Generate a random token locally in PowerShell; never store it in the repository:

       $bytes = New-Object byte[] 32
       [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
       $env:DDSM_TOKEN = [Convert]::ToBase64String($bytes)
       python .\receiver\receiver.py --host YOUR_TAILSCALE_IP --port 8787

4. Open the dashboard address printed by the receiver in a browser on Desktop B.
5. Keep the receiver console visible and stop it with Ctrl+C when finished.

## Send a counts-only report summary from Desktop A

After creating `security_report.txt` with the C++ sensor, run:

    python .\sender\send_report_summary.py --report .\security_report.txt --receiver http://YOUR_TAILSCALE_IP:8787

This sends the report timestamp and counts of process/startup entries only. It does not transmit process names, process IDs, or registry command values.

## Send a synthetic test from Desktop A

Set the same DDSM_TOKEN environment variable in Desktop A's PowerShell session, then run:

    python .\sender\send_test_alert.py --receiver http://YOUR_TAILSCALE_IP:8787

The receiver validates the bearer token, JSON content type, body size, required fields, severity, and event ID. Accepted events are appended to receiver/events.jsonl and displayed in the dashboard.

## Security notes

- Tailscale's encrypted WireGuard tunnel protects traffic between authorized tailnet devices. The application uses bearer-token authentication; HTTP is not independent end-to-end TLS.
- Bind only to Desktop B's Tailscale address and keep the tailnet limited to trusted devices. Add restrictive Tailscale ACLs and Windows Firewall rules where possible.
- The token is a shared secret. Do not paste it into GitHub, commit it, or send it through public channels.
- Use synthetic events first. Do not send passwords, private messages, or unnecessary personal information.
- Event IDs are restored from the JSONL event archive at startup so previously accepted IDs can be rejected after a restart. Keep the archive intact to retain this protection.
- No stealth or system-wide keyboard capture is implemented.

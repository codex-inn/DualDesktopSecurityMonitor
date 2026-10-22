# DualDesktopSecurityMonitor

**A two-computer defensive monitoring lab for Windows 10 and Windows 11.**

Desktop A creates local system inventory reports and can send a harmless test alert. Desktop B hosts a browser dashboard and authenticated event receiver. The intended connection is through your private Tailscale network, even when the computers use different internet connections.

> **Status:** Initial implementation committed. The receiver and synthetic test sender are implemented, but end-to-end operation has not yet been tested on your computers. The C++ sensor currently saves reports locally and does not automatically send findings.

## Project at a glance

| Component | Role | Status |
|---|---|---|
| C++ sensor | Lists running processes and common Windows startup Run entries; saves a local report | Implemented; Windows build still needs testing |
| Console test-input demo | Reads fictional text entered only into this program's own console; does not save the entered text | Implemented |
| Python receiver | Receives authenticated JSON events and appends them to a local JSONL archive | Implemented |
| Browser dashboard | Shows recent received events and refreshes every five seconds | Implemented |
| Python test sender | Sends one synthetic connectivity-test event | Implemented |
| Sensor-to-alert integration | Automatically sends selected sensor findings | Not implemented |
| Durable replay protection | Remembers event IDs across receiver restarts | Not implemented |

## Repository structure

```text
DualDesktopSecurityMonitor/
├── src/
│   └── sensor.cpp              # Windows local inventory sensor
├── receiver/
│   └── receiver.py             # Desktop B receiver + dashboard
├── sender/
│   └── send_test_alert.py      # Desktop A synthetic alert sender
├── docs/
│   └── NETWORK_SETUP.md        # Tailscale setup and security notes
├── CMakeLists.txt              # C++ build configuration
└── README.md
```

## Safety and privacy

- Use only computers you own or are explicitly authorized to administer.
- No stealth, persistence, system-wide keyboard capture, or hidden upload is implemented.
- Do not send real passwords, private messages, or unnecessary personal information.
- The local report may contain process names, process IDs, and startup commands. Review it before sharing.
- Never commit tokens, passwords, private certificates, or Tailscale authentication keys to GitHub.
- **Do not expose the receiver to the public internet. Do not use router port forwarding.**

## Requirements

- Windows 10 on Desktop A and Windows 11 on Desktop B (other supported Windows combinations may work).
- Tailscale installed and signed in on both computers under your authorized tailnet.
- Python 3.10+ on both computers for the receiver and sender.
- Visual Studio 2022 or Build Tools with **Desktop development with C++** and CMake, if building the C++ sensor.

## Step 1 — Start Desktop B receiver

1. Clone or download this repository on Desktop B.
2. Open PowerShell in the repository folder.
3. Find Desktop B's **Tailscale IPv4 address** in the Tailscale app.
4. Generate a random token locally in PowerShell. Keep the value secret:

   ```powershell
   $bytes = New-Object byte[] 32
   [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
   $env:DDSM_TOKEN = [Convert]::ToBase64String($bytes)
   python .\receiver\receiver.py --host YOUR_DESKTOP_B_TAILSCALE_IP --port 8787
   ```

5. Replace `YOUR_DESKTOP_B_TAILSCALE_IP` with the actual Tailscale IP before running the command.
6. Leave that PowerShell window open. Visit `http://YOUR_DESKTOP_B_TAILSCALE_IP:8787/` in a browser on Desktop B, replacing the placeholder with the same IP.

The receiver requires `DDSM_TOKEN` to contain at least 32 characters. The example generates a fresh token in that PowerShell session. Do not close the session and expect the token to remain available.

## Step 2 — Send a harmless test alert from Desktop A

1. Clone or download this repository on Desktop A.
2. Open a separate PowerShell window in the repository folder.
3. Set `DDSM_TOKEN` to the **exact same token** generated on Desktop B. For example, paste the token into this command locally (do not share it):

   ```powershell
   $env:DDSM_TOKEN = "PASTE_THE_SAME_SECRET_TOKEN_HERE"
   python .\sender\send_test_alert.py --receiver http://YOUR_DESKTOP_B_TAILSCALE_IP:8787
   ```

4. Replace the receiver IP placeholder with Desktop B's Tailscale IP.
5. A successful request should return HTTP status `201`. The synthetic alert should appear in the Desktop B dashboard within about five seconds.

If it fails, check that both devices are online in Tailscale, the IP address is correct, the receiver is still running, both sessions use the same token, and Windows Firewall permits the connection on the intended private interface. Do not open the port to the public internet.

## Step 3 — Build the C++ local sensor (optional)

Open a Visual Studio Developer Command Prompt in the repository folder:

```powershell
cmake -S . -B build
cmake --build build --config Release
.\build\Release\DualDesktopSecurityMonitor.exe
```

Choose menu option `1` to create `security_report.txt`, `2` for the console-only fictional test-input demo, or `0` to exit. The C++ sensor does **not** currently send its report to Desktop B.

## How the network security works

- Tailscale uses an encrypted WireGuard tunnel between devices in your tailnet.
- The receiver binds to the Tailscale IP supplied on its command line.
- A bearer token authenticates event submissions at the application layer.
- The receiver validates request size, required fields, severity, and event ID before saving.
- Event history is written to `receiver/events.jsonl` and is available to the dashboard.

**Important limitation:** the app uses HTTP inside the Tailscale tunnel, not separate HTTPS/TLS. Only use it on a trusted, access-controlled tailnet. The token is a shared secret; protect it and rotate it if exposed.

## Known limitations / next development tasks

- [ ] Test receiver and sender end-to-end on the two target Windows computers.
- [ ] Connect selected local sensor findings to the alert sender.
- [ ] Persist replay protection across receiver restarts.
- [ ] Add tighter receiver access controls and production-grade transport/security hardening.
- [ ] Compile and test the C++ sensor on Windows.

This is an educational prototype, not a hardened enterprise security product. Keep the receiver visible, use synthetic alerts for initial tests, and stop it with `Ctrl+C` when finished.

# DualDesktopSecurityMonitor

**A two-computer defensive monitoring lab for Windows 10 and Windows 11.**

Desktop A creates local system inventory reports and can send a harmless test alert or a counts-only report summary. Desktop B hosts a browser dashboard and authenticated event receiver. The intended connection is through your private Tailscale network, even when the computers use different internet connections.

> **Status:** Core prototype files and unit tests are committed. A separate summary sender can send only aggregate counts from the local report; it does not upload process names or startup commands. End-to-end operation and Windows compilation still need testing on your computers.



## Quick demonstration on one computer

You can demonstrate the dashboard without a second PC, Tailscale, or C++ build:

1. Install Python 3.10 or newer.
2. Download this repository ZIP from GitHub and extract it.
3. Open PowerShell in the extracted project folder.
4. Run:

   ```powershell
   python .\run_local_demo.py
   ```

5. A browser opens to a dashboard on `127.0.0.1` and one harmless synthetic alert is sent automatically. Keep the PowerShell window open during the demo; press `Ctrl+C` to stop it.

The local demo binds only to loopback (`127.0.0.1`), uses a randomly generated in-memory token, and does not require the two-computer network setup. Events are appended to `receiver/events.jsonl` in the extracted project folder. The local demo is for demonstration and testing, not a public web deployment.

To run the automated Python tests from the project folder:

```powershell
python -m unittest discover -s tests -v
```

GitHub Actions also runs these Python tests on pushes and pull requests. A green workflow confirms the Python tests passed in GitHub's test environment; it does not replace a Windows C++ build or a real two-computer network test.

## Project at a glance

| Component | Role | Status |
|---|---|---|
| C++ sensor | Lists running processes and common Windows startup Run entries; saves a local report | Implemented; Windows build still needs testing |
| Console test-input demo | Reads fictional text entered only into this program's own console; does not save the entered text | Implemented |
| Python receiver | Receives authenticated JSON events and appends them to a local JSONL archive | Implemented |
| Browser dashboard | Shows recent received events and refreshes every five seconds | Implemented |
| Python test sender | Sends one synthetic connectivity-test event | Implemented |
| Sensor-to-alert integration | Automatically sends selected sensor findings | Not implemented |
| Durable replay protection | Remembers event IDs across receiver restarts using the local archive | Implemented; tests added |

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

## Step 3 — Send a counts-only inventory summary (optional)

After choosing menu option `1` in the C++ sensor to create `security_report.txt`, run this on Desktop A. Use the same token configured on Desktop B:

```powershell
python .\sender\send_report_summary.py --report .\security_report.txt --receiver http://YOUR_DESKTOP_B_TAILSCALE_IP:8787
```

The script reads the report locally and sends only its generation timestamp and aggregate counts of process/startup entries. It does **not** send the full report, process names, process IDs, or startup command values. Check the receiver dashboard for an `inventory_report_summary` event.

## Step 4 — Build the C++ local sensor (optional)

Open a Visual Studio Developer Command Prompt in the repository folder:

```powershell
cmake -S . -B build
cmake --build build --config Release
.\build\Release\DualDesktopSecurityMonitor.exe
```

Choose menu option `1` to create `security_report.txt`, `2` for the console-only fictional test-input demo, or `0` to exit. The C++ sensor itself does not connect to the network. The separate Python summary sender can send counts only after you explicitly run it.

## How the network security works

- Tailscale uses an encrypted WireGuard tunnel between devices in your tailnet.
- The receiver binds to the Tailscale IP supplied on its command line.
- A bearer token authenticates event submissions at the application layer.
- The receiver validates request size, required fields, severity, and event ID before saving.
- Event history is written to `receiver/events.jsonl` and is available to the dashboard.

**Important limitation:** the app uses HTTP inside the Tailscale tunnel, not separate HTTPS/TLS. Only use it on a trusted, access-controlled tailnet. The token is a shared secret; protect it and rotate it if exposed.

## Known limitations / next development tasks

- [ ] Test receiver and sender end-to-end on the two target Windows computers.
- [x] Add a loopback-only local demo that sends a synthetic alert.
- [x] Add receiver HTTP tests and a GitHub Actions Python test workflow.
- [ ] Connect selected local sensor findings to the alert sender.
- [x] Persist replay protection across receiver restarts.
- [ ] Add tighter receiver access controls and production-grade transport/security hardening.
- [ ] Compile and test the C++ sensor on Windows.

Run the Python unit tests from the repository root with `python -m unittest discover -s tests -v`. This is an educational prototype, not a hardened enterprise security product. Keep the receiver visible, use synthetic alerts for initial tests, and stop it with `Ctrl+C` when finished.

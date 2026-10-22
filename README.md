# DualDesktopSecurityMonitor

A visible, consent-based defensive monitoring lab for two Windows computers you own or are authorized to administer.

- Desktop A (Windows 10): local process/startup inventory and a synthetic alert sender.
- Desktop B (Windows 11): a web dashboard and authenticated event receiver.
- Private network: run the receiver on Desktop B's Tailscale IP. Tailscale encrypts traffic between tailnet devices; the app uses a bearer token to authenticate submissions.
- Test-input demo: reads fictional text only from the program's visible console prompt. It does not capture keystrokes from other apps.

This is an educational starter, not a complete security product. The Python receiver and test sender are implemented; the C++ inventory sensor remains local-only for now.

## Safety and privacy

- Run only on devices you own or have permission to administer.
- Do not collect real passwords, private messages, or other people's activity.
- No stealth, persistence, system-wide keyboard capture, or hidden data upload.
- Review local reports before sharing; process names and startup entries can reveal personal information.
- Do not expose the receiver to the public internet. Do not use router port forwarding.

## Current status

- [x] Windows process inventory (C++ sensor)
- [x] Read-only inventory of common startup Run entries
- [x] Timestamped local text report
- [x] Console-only test-input demo; entered text is not saved
- [x] Desktop B web dashboard and authenticated JSON event receiver
- [x] Desktop A synthetic test-alert sender
- [x] Request size/schema validation and duplicate event-ID check during receiver runtime
- [ ] Connect real sensor findings to the alert sender
- [ ] Add durable replay protection across receiver restarts
- [ ] Compile and test the C++ sensor on Windows

## 1. Prepare both computers

1. Install Tailscale on Desktop A and Desktop B and sign both into your authorized tailnet.
2. On Desktop B, find its Tailscale IPv4 address in the Tailscale app.
3. Install Python 3.10+ on both computers (receiver and sender use only the standard library).
4. In Windows Firewall, allow inbound TCP port 8787 only as needed for your private Tailscale interface. Do not create a public router port forward.

## 2. Start the receiver on Desktop B

Open PowerShell in the repository folder. Generate a secret token locally (do not put it in GitHub):

    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    $env:DDSM_TOKEN = [Convert]::ToBase64String($bytes)
    python .\receiver\receiver.py --host YOUR_DESKTOP_B_TAILSCALE_IP --port 8787

Replace the placeholder with Desktop B's actual Tailscale IP. Keep the PowerShell window open. Open the dashboard on Desktop B at the same address with a trailing slash.

The receiver refuses to start unless DDSM_TOKEN is set to at least 32 characters. Keep the token secret; never paste it into issues, chat, screenshots, or commits.

## 3. Send a harmless test alert from Desktop A

Set DDSM_TOKEN in a separate PowerShell window on Desktop A to the exact same token generated on Desktop B, then run:

    python .\sender\send_test_alert.py --receiver http://YOUR_DESKTOP_B_TAILSCALE_IP:8787

The receiver should return HTTP 201 and the alert should appear on the Desktop B dashboard within five seconds. Use only your private tailnet.

## 4. Build the C++ sensor (optional)

Requirements: Windows 10/11, Visual Studio 2022 or Build Tools with Desktop development with C++ and CMake.

    cmake -S . -B build
    cmake --build build --config Release
    .\build\Release\DualDesktopSecurityMonitor.exe

The program writes security_report.txt in its current working directory. Keep the report private.

## Limitations

- The dashboard is a simple local lab interface, not a hardened production service.
- HTTP is used because the intended network is the private Tailscale tailnet, whose WireGuard tunnel encrypts traffic. Do not run the receiver on a public/untrusted interface.
- Duplicate event IDs are tracked in memory and this guard resets when the receiver restarts; durable replay protection is pending.
- The C++ sensor writes a local report and does not automatically send findings.
- No program-wide keystroke logging is implemented.

# DualDesktopSecurityMonitor

A visible, consent-based defensive monitoring lab for two Windows computers you own or are authorized to administer.

- Desktop A (Windows 10): local inventory of running processes and common startup entries.
- Desktop B (Windows 11): planned receiver/dashboard for alerts and report history.
- Network: planned private connectivity over your Tailscale tailnet; no public router port forwarding.
- Test-input demo: reads fictional text only from this program's own visible console prompt. It does not capture keystrokes from other apps.

This is an educational starter, not a complete security product. The first commit provides the local sensor/reporting foundation. Network transport and the receiver will be added as separate stages.

## Safety and privacy

- Run only on devices you own or have permission to administer.
- Do not collect real passwords, private messages, or other people's activity.
- No stealth, persistence, system-wide keyboard capture, or hidden data upload.
- Review reports before sharing; process names and startup entries can reveal personal information.

## Current status

- [x] Windows process inventory
- [x] Read-only inventory of common startup Run entries
- [x] Timestamped local text report
- [x] Explicit console-only test-input demo; entered text is not saved
- [ ] Authenticated alert transport over Tailscale
- [ ] Desktop B receiver/dashboard and report archive
- [ ] End-to-end test instructions

## Build on Windows

Requirements: Windows 10/11 and Visual Studio 2022 or Build Tools with Desktop development with C++ and CMake.

From a Developer Command Prompt in the repository:

    cmake -S . -B build
    cmake --build build --config Release
    .\build\Release\DualDesktopSecurityMonitor.exe

The program writes security_report.txt in its current working directory. Keep this report private.

## Planned two-computer setup

1. Install Tailscale on both computers and sign in to your authorized tailnet.
2. Keep the receiver bound to the Tailscale interface or use an explicit allowlist; do not expose it to the public internet.
3. Implement mutual authentication, message size limits, replay protection, and clear local logs before enabling network transport.
4. Test with harmless synthetic alert messages first.

See docs/NETWORK_SETUP.md for the network plan. Never commit passwords, API keys, private certificates, or Tailscale auth keys to GitHub.

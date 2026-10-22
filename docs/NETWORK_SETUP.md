# Two-desktop network plan

This document describes the intended setup. Network transport is not implemented in the current starter.

## Topology

- Desktop A: Windows 10 local sensor.
- Desktop B: Windows 11 intended receiver/dashboard.
- Both devices join the same authorized Tailscale tailnet, even when using different internet connections.
- Do not configure router port forwarding or expose a listener to the public internet.

## Before enabling a receiver

- Bind to the Tailscale interface where practical.
- Authenticate both ends; a private IP address alone is not authentication.
- Encrypt traffic in transit and store credentials outside the repository.
- Validate message size, type, and schema; reject unexpected input.
- Add timestamps and unique event IDs to help detect replayed messages.
- Log connection attempts and errors without recording secrets.
- Use synthetic test alerts first and verify that only Desktop B receives them.

Never commit passwords, API keys, private certificates, or Tailscale auth keys to GitHub. Do not implement stealth or system-wide keyboard capture.

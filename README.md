# Orion Monitor

**Orion Monitor** is a small read-only service for observing a production application on a Linux server and delivering operational information to an administrator through Telegram.

The project grew from a practical need: a production system consists of several independently running components, while checking their state and reading their logs traditionally required an SSH session.

Monitor brings the essential checks into one interface. It reports application and infrastructure health, shows recent `journald` entries, and automatically sends Telegram alerts when new errors appear.

The core design principle is **observer, not controller**: Monitor can read system state and report it, but it provides no functions for starting, stopping, restarting, or modifying the observed application.

This repository is a sanitized public edition of a production tool. Concrete infrastructure configuration, operational documentation, and production-environment details are intentionally not published.

## Features

- Telegram interface for operational status and logs
- systemd service health checks
- recent `journald` log viewing
- live error monitoring
- traceback aggregation
- duplicate alert suppression
- Docker / reverse-proxy status checks
- HTTP health checks
- administrator chat allowlist
- automatic startup through a dedicated systemd service

## Architecture

```text
Application services ─┐
systemd ───────────────┤
journald ──────────────┤
Docker ────────────────┼──► Orion Monitor ───► Telegram ───► Administrator
HTTP /health ──────────┘
                              │
                           READ ONLY
```

Monitor is intentionally deployed as a separate process with its own Python environment and lifecycle. Failure of the monitor must not affect the application it observes.

## Safety boundary

The public implementation follows the same central safety rule as the production version: no service control actions, database writes, migrations, arbitrary shell commands from Telegram, or application business mutations.

See [docs/SECURITY.md](docs/SECURITY.md).

## Testing

Unit tests cover health-state interpretation, read-only controls, duplicate alert suppression, journal timestamp/PID normalization, traceback aggregation, and environment configuration.

## Public edition

Production-specific service names, domains, server paths, identifiers, incident reports, backups, and infrastructure inventory are deliberately excluded or replaced with neutral examples.

## Stack

Python 3.12+ · systemd · journald · Docker CLI · Telegram Bot API · HTTP health endpoints · unittest

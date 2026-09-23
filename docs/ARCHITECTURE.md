# Architecture

Orion Monitor runs as an independent Linux service next to the application it observes.

```text
systemd service state ─┐
journald logs ─────────┤
Docker state ──────────┼──► Monitor ───► Telegram
HTTP health endpoint ──┘
```

The dependency is intentionally one-way. Monitor reads observable state and emits notifications; it does not control the observed application.

The production edition uses its own virtual environment, environment file, and systemd unit so its lifecycle remains separate from the monitored application.

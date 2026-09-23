# Security boundary

Orion Monitor is designed as an **observer and notifier**, not a remote-control plane.

Allowed operations are limited to reading systemd state and selected journald units, inspecting configured Docker container state, performing an HTTP GET health check, and sending information to one configured Telegram administrator chat.

The v1 design intentionally excludes service start/stop/restart/reload actions, database writes, migrations, Docker mutations, application business mutations, and arbitrary shell commands from Telegram.

The observed application has no lifecycle dependency on Monitor. If Monitor or Telegram fails, the application must continue operating independently.

Production-specific infrastructure details are deliberately absent from this public edition.

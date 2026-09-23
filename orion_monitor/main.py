import hashlib
import threading
import time

from .config import Config
from .monitoring.journal import JournalEvent, follow_errors, recent_errors, recent_logs
from .monitoring.services import container_running, health_endpoint, service_active, systemd_state
from .telegram.bot import TelegramBot
from .telegram.keyboards import main_keyboard

def _icon(ok: bool) -> str:
    return "OK" if ok else "PROBLEM"

def status_text(config: Config) -> str:
    app, web = systemd_state(config.app_service), systemd_state(config.web_service)
    docker = service_active(config.docker_service)
    proxy = container_running(config.proxy_container)
    health = health_endpoint(config.health_url)
    return (
        "ORION MONITOR\n\n"
        f"{_icon(app.healthy)} App: {app.active}/{app.sub} · restarts {app.restarts}\n"
        f"{_icon(web.healthy)} Web: {web.active}/{web.sub} · restarts {web.restarts}\n"
        f"{_icon(docker)} Docker: {'active' if docker else 'problem'}\n"
        f"{_icon(proxy)} Reverse proxy: {'running' if proxy else 'problem'}\n"
        f"{_icon(health)} Public /health: {'200 OK' if health else 'problem'}"
    )

def _trim(text: str, limit: int = 3500) -> str:
    return text if len(text) <= limit else "...\n" + text[-limit:]

class AlertDeduplicator:
    def __init__(self, window_seconds: int = 600):
        self.window_seconds = window_seconds
        self.seen: dict[str, float] = {}
        self.lock = threading.Lock()

    def allow(self, event: JournalEvent) -> bool:
        fingerprint = hashlib.sha256(f"{event.unit}\0{event.fingerprint_text}".encode()).hexdigest()
        now = time.monotonic()
        with self.lock:
            previous = self.seen.get(fingerprint)
            self.seen[fingerprint] = now
            for key, stamp in list(self.seen.items()):
                if now - stamp > self.window_seconds:
                    self.seen.pop(key, None)
            return previous is None or now - previous > self.window_seconds

def watch_unit(bot: TelegramBot, unit: str, label: str, dedupe: AlertDeduplicator) -> None:
    while True:
        try:
            for event in follow_errors(unit):
                if dedupe.allow(event):
                    bot.send(_trim(f"ALERT: {label}\n\n{event.text}"), main_keyboard())
        except Exception as exc:
            print(f"journal watcher failed for {unit}: {exc}", flush=True)
            time.sleep(5)

def handle(bot: TelegramBot, config: Config, text: str) -> None:
    if text in {"/start", "Status", "Refresh"}:
        bot.send(status_text(config), main_keyboard())
    elif text == "App logs":
        bot.send(_trim(f"APP — recent logs\n\n{recent_logs(config.app_service)}"), main_keyboard())
    elif text == "Web logs":
        bot.send(_trim(f"WEB — recent logs\n\n{recent_logs(config.web_service)}"), main_keyboard())
    elif text == "Errors":
        errors = recent_errors(config.app_service) + recent_errors(config.web_service)
        body = "\n".join(errors[-20:]) if errors else "No errors found in the inspected journal range."
        bot.send(_trim(f"Recent errors\n\n{body}"), main_keyboard())
    else:
        bot.send("Choose an action from the keyboard below.", main_keyboard())

def main() -> None:
    config = Config.from_env()
    bot = TelegramBot(config.token, config.admin_chat_id)
    dedupe = AlertDeduplicator()
    for unit, label in ((config.app_service, "APP"), (config.web_service, "WEB")):
        threading.Thread(target=watch_unit, args=(bot, unit, label, dedupe), daemon=True).start()
    offset = None
    bot.send("Orion Monitor started. Watching only for new errors.", main_keyboard())
    while True:
        try:
            for update in bot.updates(offset):
                offset = update["update_id"] + 1
                message = update.get("message", {})
                if str(message.get("chat", {}).get("id", "")) != config.admin_chat_id:
                    continue
                text = message.get("text")
                if text:
                    handle(bot, config, text)
        except Exception as exc:
            print(f"telegram polling failed: {exc}", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    main()

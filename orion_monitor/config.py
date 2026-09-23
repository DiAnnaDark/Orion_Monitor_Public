from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Config:
    token: str
    admin_chat_id: str
    app_service: str
    web_service: str
    health_url: str
    docker_service: str
    proxy_container: str

    @classmethod
    def from_env(cls) -> "Config":
        token = os.environ.get("MONITOR_BOT_TOKEN", "").strip()
        chat_id = os.environ.get("MONITOR_ADMIN_CHAT_ID", "").strip()
        if not token or not chat_id:
            raise RuntimeError("MONITOR_BOT_TOKEN and MONITOR_ADMIN_CHAT_ID are required")
        return cls(
            token, chat_id,
            os.environ.get("MONITOR_APP_SERVICE", "my-app.service").strip(),
            os.environ.get("MONITOR_WEB_SERVICE", "my-app-web.service").strip(),
            os.environ.get("MONITOR_HEALTH_URL", "https://example.com/health").strip(),
            os.environ.get("MONITOR_DOCKER_SERVICE", "docker.service").strip(),
            os.environ.get("MONITOR_PROXY_CONTAINER", "reverse-proxy").strip(),
        )

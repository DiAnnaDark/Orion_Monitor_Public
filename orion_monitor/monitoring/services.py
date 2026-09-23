from dataclasses import dataclass
import json
import subprocess
import urllib.request

@dataclass(frozen=True)
class ServiceState:
    name: str
    active: str
    sub: str
    result: str
    pid: int
    restarts: int

    @property
    def healthy(self) -> bool:
        return self.active == "active" and self.sub == "running" and self.result == "success"

def _run(*args: str) -> str:
    completed = subprocess.run(args, check=False, capture_output=True, text=True, timeout=10)
    return completed.stdout.strip()

def systemd_state(name: str) -> ServiceState:
    raw = _run("systemctl", "show", name, "-p", "ActiveState", "-p", "SubState",
               "-p", "Result", "-p", "MainPID", "-p", "NRestarts")
    values = dict(line.split("=", 1) for line in raw.splitlines() if "=" in line)
    return ServiceState(name, values.get("ActiveState", "unknown"), values.get("SubState", "unknown"),
                        values.get("Result", "unknown"), int(values.get("MainPID", "0") or 0),
                        int(values.get("NRestarts", "0") or 0))

def service_active(name: str) -> bool:
    return _run("systemctl", "is-active", name) == "active"

def container_running(name: str) -> bool:
    return _run("docker", "inspect", "-f", "{{.State.Running}}", name) == "true"

def health_endpoint(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=8) as response:
            if response.status != 200:
                return False
            return json.loads(response.read().decode("utf-8")).get("status") == "ok"
    except Exception:
        return False

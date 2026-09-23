import json
import urllib.parse
import urllib.request

class TelegramBot:
    def __init__(self, token: str, admin_chat_id: str):
        self.api = f"https://api.telegram.org/bot{token}"
        self.admin_chat_id = str(admin_chat_id)

    def call(self, method: str, data: dict | None = None) -> dict:
        payload = urllib.parse.urlencode(data or {}).encode()
        request = urllib.request.Request(f"{self.api}/{method}", data=payload)
        with urllib.request.urlopen(request, timeout=35) as response:
            return json.loads(response.read().decode("utf-8"))

    def send(self, text: str, reply_markup: dict | None = None) -> None:
        data = {"chat_id": self.admin_chat_id, "text": text}
        if reply_markup is not None:
            data["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)
        self.call("sendMessage", data)

    def updates(self, offset: int | None) -> list[dict]:
        data = {"timeout": 25, "allowed_updates": json.dumps(["message"])}
        if offset is not None:
            data["offset"] = offset
        return self.call("getUpdates", data).get("result", [])

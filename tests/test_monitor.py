import os
import unittest
from unittest.mock import patch

from orion_monitor.config import Config
from orion_monitor.main import AlertDeduplicator, _trim
from orion_monitor.monitoring.journal import JournalEvent
from orion_monitor.monitoring.services import ServiceState
from orion_monitor.telegram.keyboards import main_keyboard

class MonitorTests(unittest.TestCase):
    def test_service_state_healthy(self):
        self.assertTrue(ServiceState("x", "active", "running", "success", 123, 0).healthy)

    def test_service_state_not_healthy(self):
        self.assertFalse(ServiceState("x", "active", "failed", "exit-code", 0, 3).healthy)

    def test_keyboard_contains_read_only_actions(self):
        labels = [item for row in main_keyboard()["keyboard"] for item in row]
        self.assertIn("Status", labels)
        self.assertIn("Errors", labels)
        self.assertFalse(any(word in label.lower() for label in labels for word in ("restart", "stop", "start")))

    def test_trim_keeps_tail(self):
        self.assertTrue(_trim("abcdef", 4).endswith("cdef"))

    def test_deduplicator_suppresses_duplicate_across_timestamp_and_pid(self):
        dedupe = AlertDeduplicator()
        first = JournalEvent("unit", "2026-01-01T10:00:00+00:00 host python[1]: ERROR connection failed")
        second = JournalEvent("unit", "2026-01-01T10:00:03+00:00 host python[2]: ERROR connection failed")
        self.assertTrue(dedupe.allow(first))
        self.assertFalse(dedupe.allow(second))

    @patch.dict(os.environ, {"MONITOR_BOT_TOKEN": "token", "MONITOR_ADMIN_CHAT_ID": "123"}, clear=True)
    def test_config_uses_neutral_defaults(self):
        config = Config.from_env()
        self.assertEqual(config.app_service, "my-app.service")
        self.assertEqual(config.web_service, "my-app-web.service")
        self.assertEqual(config.health_url, "https://example.com/health")

if __name__ == "__main__":
    unittest.main()

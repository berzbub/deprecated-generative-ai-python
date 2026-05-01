"""Unit tests for the Alexa Plus network analyser Flask app."""

import json
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# ---------------------------------------------------------------------------
# Stub heavy optional dependencies before importing the app so tests run
# without installing bluetooth / scapy / vertexai.
# ---------------------------------------------------------------------------
_stub_bluetooth = MagicMock()
_stub_bluetooth.discover_devices.return_value = []
sys.modules.setdefault("bluetooth", _stub_bluetooth)
sys.modules.setdefault("bluetooth.ble", MagicMock())

_stub_scapy = MagicMock()
sys.modules.setdefault("scapy", _stub_scapy)
sys.modules.setdefault("scapy.all", _stub_scapy)

sys.modules.setdefault("vertexai", MagicMock())
sys.modules.setdefault("vertexai.language_models", MagicMock())
sys.modules.setdefault("google.cloud", MagicMock())
sys.modules.setdefault("google.cloud.aiplatform", MagicMock())

# Ensure the alexa_plus package directory is on the path.
import pathlib

_here = pathlib.Path(__file__).parent
sys.path.insert(0, str(_here.parent))

from app import app, NetworkScanner, BluetoothScanner, WifiScanner  # noqa: E402


class TestNetworkScanner(unittest.TestCase):
    def test_scan_returns_list(self):
        scanner = NetworkScanner()
        result = scanner.scan_network("192.168.1.0/24")
        self.assertIsInstance(result, list)

    def test_scan_returns_device_fields(self):
        scanner = NetworkScanner()
        devices = scanner.scan_network("192.168.1.0/24")
        self.assertTrue(len(devices) > 0)
        device = devices[0]
        self.assertIn("ip", device)
        self.assertIn("mac", device)

    def test_known_devices_tracking(self):
        scanner = NetworkScanner()
        first = scanner.scan_network("192.168.1.0/24")
        second = scanner.scan_network("192.168.1.0/24")
        # On second scan the device should still appear but without 'color'
        self.assertEqual(len(first), len(second))
        self.assertIn("color", first[0])
        self.assertNotIn("color", second[0])


class TestBluetoothScanner(unittest.TestCase):
    def test_scan_classic_returns_list_on_error(self):
        scanner = BluetoothScanner()
        with patch("bluetooth.discover_devices", side_effect=OSError("no device")):
            result = scanner.scan_bluetooth_classic()
        self.assertIsInstance(result, list)

    def test_scan_ble_returns_list_on_error(self):
        scanner = BluetoothScanner()
        result = scanner.scan_bluetooth_le()
        self.assertIsInstance(result, list)


class TestWifiScanner(unittest.TestCase):
    def test_scan_returns_list_on_error(self):
        scanner = WifiScanner()
        # scapy sniff is stubbed; just ensure no exception propagates
        result = scanner.scan_wifi_cameras()
        self.assertIsInstance(result, list)


class TestFlaskApp(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_index_returns_200(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Alexa Plus", response.data)

    def test_analyze_network_returns_json(self):
        mock_analyzer = MagicMock()
        mock_analyzer.analyze_network_data = AsyncMock(return_value="AI analysis text")
        mock_analyzer.generate_security_recommendations = AsyncMock(
            return_value="Security recommendations"
        )

        with patch("app.GeminiAIAnalyzer", return_value=mock_analyzer):
            response = self.client.get("/api/analyze/network")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["analysis"], "AI analysis text")
        self.assertEqual(data["security_recommendations"], "Security recommendations")

    def test_analyze_network_error_handling(self):
        with patch("app.GeminiAIAnalyzer", side_effect=Exception("connection failed")):
            response = self.client.get("/api/analyze/network")

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertIn("error", data)
        # The raw exception message must NOT be exposed to the client
        self.assertNotIn("connection failed", data["error"])


if __name__ == "__main__":
    unittest.main()

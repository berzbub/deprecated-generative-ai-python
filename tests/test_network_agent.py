# -*- coding: utf-8 -*-
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for the network agent module."""

import asyncio
import sys
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Stub out heavy optional dependencies so the module can be imported in a
# plain test environment (no Bluetooth stack, no Scapy, no Flask required).
# ---------------------------------------------------------------------------

def _stub_module(name, **attrs):
    mod = types.ModuleType(name)
    mod.__dict__.update(attrs)
    sys.modules[name] = mod
    return mod


# bluetooth
bt = _stub_module("bluetooth", discover_devices=MagicMock(return_value=[]))
_stub_module("bluetooth.ble", DiscoveryService=MagicMock)

# scapy – only the names actually used in the module are needed
scapy_all = _stub_module(
    "scapy.all",
    Dot11=object,
    Dot11Beacon=object,
    sniff=MagicMock(),
)
_stub_module("scapy", all=scapy_all)

# flask – Flask().route() must work as a decorator
class _FakeFlask:
    def __init__(self, *args, **kwargs):
        pass

    def route(self, *args, **kwargs):
        def decorator(f):
            return f
        return decorator

    def run(self, *args, **kwargs):
        pass


flask_mod = _stub_module("flask", Flask=_FakeFlask, jsonify=MagicMock())

# google.generativeai – we mock configure + GenerativeModel
genai_mock = _stub_module(
    "google.generativeai",
    configure=MagicMock(),
    GenerativeModel=MagicMock,
)
google_mod = sys.modules.get("google") or _stub_module("google")
google_mod.generativeai = genai_mock
sys.modules["google"] = google_mod
sys.modules["google.generativeai"] = genai_mock

# ---------------------------------------------------------------------------
# Now import the classes under test directly from the source file.
# ---------------------------------------------------------------------------

import importlib.machinery
import importlib.util
import pathlib

_agent_path = pathlib.Path(__file__).parent.parent / "network agent"


def _load_agent():
    """Load 'network agent' as a Python module."""
    loader = importlib.machinery.SourceFileLoader("network_agent", str(_agent_path))
    spec = importlib.util.spec_from_loader("network_agent", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


_agent = _load_agent()
NetworkScanner = _agent.NetworkScanner
GeminiAIAnalyzer = _agent.GeminiAIAnalyzer


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestNetworkScanner(unittest.TestCase):
    """Tests for NetworkScanner."""

    def setUp(self):
        self.scanner = NetworkScanner()

    def test_scan_returns_list(self):
        result = self.scanner.scan_network("192.168.1.0/24")
        self.assertIsInstance(result, list)

    def test_scan_returns_device_with_expected_keys(self):
        result = self.scanner.scan_network("192.168.1.0/24")
        self.assertTrue(len(result) > 0)
        device = result[0]
        for key in ("ip", "mac", "hostname"):
            self.assertIn(key, device)

    def test_new_device_is_marked_blue(self):
        result = self.scanner.scan_network("192.168.1.0/24")
        self.assertEqual(result[0]["color"], "blue")

    def test_known_device_not_re_marked(self):
        # First scan marks the device blue; second scan should NOT add the
        # color key again (device is already known).
        self.scanner.scan_network("192.168.1.0/24")
        result = self.scanner.scan_network("192.168.1.0/24")
        # Device is already in known set, so "color" should not appear
        self.assertNotIn("color", result[0])


class TestGeminiAIAnalyzer(unittest.TestCase):
    """Tests for GeminiAIAnalyzer using google.generativeai."""

    def _make_analyzer(self):
        """Return a GeminiAIAnalyzer with a mocked GenerativeModel."""
        with patch("google.generativeai.configure") as mock_configure, \
             patch("google.generativeai.GenerativeModel") as MockModel:
            mock_model_instance = MagicMock()
            MockModel.return_value = mock_model_instance
            analyzer = GeminiAIAnalyzer(api_key="test-key")
            analyzer.model = mock_model_instance
            return analyzer, mock_configure, MockModel, mock_model_instance

    def test_configure_called_with_api_key(self):
        with patch("google.generativeai.configure") as mock_configure, \
             patch("google.generativeai.GenerativeModel"):
            GeminiAIAnalyzer(api_key="my-key")
            mock_configure.assert_called_once_with(api_key="my-key")

    def test_model_instantiated_with_gemini_pro(self):
        with patch("google.generativeai.configure"), \
             patch("google.generativeai.GenerativeModel") as MockModel:
            GeminiAIAnalyzer(api_key="my-key")
            MockModel.assert_called_once_with("gemini-pro")

    def test_analyze_network_data_returns_text(self):
        analyzer, _, _, mock_model = self._make_analyzer()
        expected = "network analysis result"
        fake_response = MagicMock()
        fake_response.text = expected
        mock_model.generate_content_async = AsyncMock(return_value=fake_response)

        network_data = {
            "devices": [{"ip": "192.168.1.1"}],
            "signals": {},
            "traffic": {},
        }
        result = asyncio.run(analyzer.analyze_network_data(network_data))
        self.assertEqual(result, expected)

    def test_analyze_network_data_calls_generate_content_async(self):
        analyzer, _, _, mock_model = self._make_analyzer()
        fake_response = MagicMock()
        fake_response.text = "ok"
        mock_model.generate_content_async = AsyncMock(return_value=fake_response)

        network_data = {"devices": [], "signals": {}, "traffic": {}}
        asyncio.run(analyzer.analyze_network_data(network_data))
        mock_model.generate_content_async.assert_awaited_once()

    def test_generate_security_recommendations_returns_text(self):
        analyzer, _, _, mock_model = self._make_analyzer()
        expected = "use a firewall"
        fake_response = MagicMock()
        fake_response.text = expected
        mock_model.generate_content_async = AsyncMock(return_value=fake_response)

        result = asyncio.run(analyzer.generate_security_recommendations("scan data"))
        self.assertEqual(result, expected)

    def test_generate_security_recommendations_calls_generate_content_async(self):
        analyzer, _, _, mock_model = self._make_analyzer()
        fake_response = MagicMock()
        fake_response.text = "ok"
        mock_model.generate_content_async = AsyncMock(return_value=fake_response)

        asyncio.run(analyzer.generate_security_recommendations("data"))
        mock_model.generate_content_async.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()

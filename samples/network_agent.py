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
"""Network AI Analyzer — a mobile-friendly Flask app powered by Gemini.

Run locally:
    export GOOGLE_API_KEY=<your-key>
    python samples/network_agent.py

Then open http://localhost:5000 in any browser (including a phone browser on
the same Wi-Fi network) to test the app.
"""

from absl.testing import absltest

# ---------------------------------------------------------------------------
# Mobile-responsive HTML template served at '/'
# ---------------------------------------------------------------------------

_MOBILE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Network AI Analyzer</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; }
    body {
      font-family: Arial, sans-serif;
      max-width: 640px;
      margin: 0 auto;
      padding: 16px;
      background: #fff;
      color: #202124;
    }
    h1 { font-size: 1.4em; margin-bottom: 4px; }
    p  { font-size: 0.95em; color: #5f6368; margin-top: 0; }
    textarea {
      width: 100%;
      height: 130px;
      font-size: 1em;
      padding: 10px;
      border: 1px solid #dadce0;
      border-radius: 6px;
      resize: vertical;
    }
    button {
      width: 100%;
      margin-top: 10px;
      padding: 14px;
      background: #1a73e8;
      color: #fff;
      border: none;
      border-radius: 6px;
      font-size: 1em;
      cursor: pointer;
    }
    button:disabled { background: #a8c7fa; cursor: not-allowed; }
    #result {
      margin-top: 16px;
      white-space: pre-wrap;
      background: #f1f3f4;
      padding: 14px;
      border-radius: 6px;
      font-size: 0.95em;
      min-height: 48px;
    }
  </style>
</head>
<body>
  <h1>Network AI Analyzer</h1>
  <p>Describe your network environment to receive Gemini-powered security insights.</p>
  <textarea id="input"
    placeholder="e.g. I have 3 devices on my Wi-Fi: 2 Android phones and 1 laptop...">
  </textarea>
  <button id="btn" onclick="analyze()">Analyze</button>
  <div id="result"></div>
  <script>
    async function analyze() {
      const input = document.getElementById('input').value.trim();
      if (!input) return;
      const btn = document.getElementById('btn');
      const result = document.getElementById('result');
      btn.disabled = true;
      result.textContent = 'Analyzing\u2026';
      try {
        const res = await fetch('/api/analyze', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({data: input})
        });
        const json = await res.json();
        result.textContent = json.analysis || json.error || 'No response.';
      } catch (e) {
        result.textContent = 'Error: ' + e.message;
      } finally {
        btn.disabled = false;
      }
    }
  </script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Flask application factory
# ---------------------------------------------------------------------------


def create_app(api_key=None):
    """Create and return the Flask application.

    Args:
        api_key: Optional Gemini API key.  When omitted the SDK reads the key
            from the ``GOOGLE_API_KEY`` environment variable.

    Returns:
        A configured :class:`flask.Flask` application.
    """
    # [START network_agent_create_app]
    import google.generativeai as genai
    from flask import Flask, jsonify, request

    if api_key:
        genai.configure(api_key=api_key)

    app = Flask(__name__)

    @app.route("/")
    def index():
        return _MOBILE_TEMPLATE, 200, {"Content-Type": "text/html; charset=utf-8"}

    @app.route("/api/analyze", methods=["POST"])
    def analyze():
        body = request.get_json(silent=True) or {}
        data = body.get("data", "").strip()
        if not data:
            return jsonify({"error": "No network data provided."}), 400

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = (
                "You are a network security assistant. "
                "Analyze the following network description and provide clear, "
                "concise security recommendations:\n\n" + data
            )
            response = model.generate_content(prompt)
            return jsonify({"analysis": response.text})
        except Exception as e:  # pylint: disable=broad-except
            return jsonify({"error": f"Analysis failed: {e}"}), 500

    # [END network_agent_create_app]
    return app


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------


class UnitTests(absltest.TestCase):
    def setUp(self):
        super().setUp()
        self.app = create_app(api_key="test-key")
        self.client = self.app.test_client()

    def test_index_returns_mobile_html(self):
        # [START network_agent_index]
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Network AI Analyzer", response.data)
        self.assertIn(b'name="viewport"', response.data)
        # [END network_agent_index]

    def test_analyze_missing_data_returns_400(self):
        # [START network_agent_analyze_missing_data]
        response = self.client.post(
            "/api/analyze",
            json={},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        # [END network_agent_analyze_missing_data]

    def test_analyze_empty_string_returns_400(self):
        response = self.client.post(
            "/api/analyze",
            json={"data": "   "},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)


# ---------------------------------------------------------------------------
# Entry point — run as a standalone server
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    app = create_app(api_key=os.environ.get("GOOGLE_API_KEY"))
    # Bind to all interfaces so any device on the same network can reach it.
    app.run(host="0.0.0.0", port=5000)

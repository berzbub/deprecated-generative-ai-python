# -*- coding: utf-8 -*-
# Copyright 2023 Google LLC
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
"""Unit tests for the Alexa + Gemini generative AI skill handler."""

import os
import unittest
from unittest import mock

from samples import alexa_generative


def _make_launch_event() -> dict:
    return {"version": "1.0", "request": {"type": "LaunchRequest", "requestId": "req-1"}}


def _make_intent_event(intent_name: str, query: str | None = None) -> dict:
    slots = {}
    if query is not None:
        slots["query"] = {"name": "query", "value": query}
    return {
        "version": "1.0",
        "request": {
            "type": "IntentRequest",
            "requestId": "req-2",
            "intent": {"name": intent_name, "slots": slots},
        },
    }


def _make_session_ended_event() -> dict:
    return {
        "version": "1.0",
        "request": {"type": "SessionEndedRequest", "requestId": "req-3"},
    }


class TestBuildResponse(unittest.TestCase):
    def test_basic_response_structure(self):
        resp = alexa_generative._build_response("Hello world")
        self.assertEqual(resp["version"], "1.0")
        self.assertIn("response", resp)
        self.assertEqual(resp["response"]["outputSpeech"]["text"], "Hello world")
        self.assertTrue(resp["response"]["shouldEndSession"])

    def test_reprompt_included_when_provided(self):
        resp = alexa_generative._build_response(
            "Hello", reprompt_text="What next?", should_end_session=False
        )
        self.assertIn("reprompt", resp["response"])
        self.assertEqual(
            resp["response"]["reprompt"]["outputSpeech"]["text"], "What next?"
        )
        self.assertFalse(resp["response"]["shouldEndSession"])

    def test_card_uses_custom_content(self):
        resp = alexa_generative._build_response(
            "Hi", card_title="My Title", card_content="My Content"
        )
        self.assertEqual(resp["response"]["card"]["title"], "My Title")
        self.assertEqual(resp["response"]["card"]["content"], "My Content")

    def test_card_defaults_to_speech_text(self):
        resp = alexa_generative._build_response("Some text")
        self.assertEqual(resp["response"]["card"]["content"], "Some text")


class TestGetQueryFromIntent(unittest.TestCase):
    def test_returns_query_value(self):
        intent = {"name": "AskQuestionIntent", "slots": {"query": {"name": "query", "value": "hi"}}}
        self.assertEqual(alexa_generative._get_query_from_intent(intent), "hi")

    def test_returns_none_when_slot_missing(self):
        intent = {"name": "AskQuestionIntent", "slots": {}}
        self.assertIsNone(alexa_generative._get_query_from_intent(intent))

    def test_returns_none_when_slots_key_missing(self):
        intent = {"name": "AskQuestionIntent"}
        self.assertIsNone(alexa_generative._get_query_from_intent(intent))


class TestAskGemini(unittest.TestCase):
    def test_raises_without_api_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GOOGLE_API_KEY", None)
            with self.assertRaises(ValueError):
                alexa_generative._ask_gemini("hello", api_key=None)

    def test_calls_gemini_and_returns_text(self):
        fake_response = mock.Mock()
        fake_response.text = "Paris is the capital of France."
        mock_model = mock.Mock()
        mock_model.generate_content.return_value = fake_response

        with mock.patch("google.generativeai.configure") as mock_configure, \
             mock.patch("google.generativeai.GenerativeModel", return_value=mock_model):
            result = alexa_generative._ask_gemini(
                "What is the capital of France?", api_key="test-key"
            )

        mock_configure.assert_called_once_with(api_key="test-key")
        mock_model.generate_content.assert_called_once_with(
            "What is the capital of France?"
        )
        self.assertEqual(result, "Paris is the capital of France.")

    def test_uses_env_var_when_no_explicit_key(self):
        fake_response = mock.Mock()
        fake_response.text = "42"
        mock_model = mock.Mock()
        mock_model.generate_content.return_value = fake_response

        with mock.patch.dict(os.environ, {"GOOGLE_API_KEY": "env-key"}), \
             mock.patch("google.generativeai.configure") as mock_configure, \
             mock.patch("google.generativeai.GenerativeModel", return_value=mock_model):
            result = alexa_generative._ask_gemini("What is the answer?")

        mock_configure.assert_called_once_with(api_key="env-key")
        self.assertEqual(result, "42")


class TestLambdaHandler(unittest.TestCase):
    def test_launch_request_returns_welcome(self):
        resp = alexa_generative.lambda_handler(_make_launch_event(), None)
        self.assertEqual(resp["version"], "1.0")
        speech = resp["response"]["outputSpeech"]["text"]
        self.assertIn("Welcome", speech)
        self.assertFalse(resp["response"]["shouldEndSession"])

    def test_help_intent(self):
        resp = alexa_generative.lambda_handler(
            _make_intent_event("AMAZON.HelpIntent"), None
        )
        self.assertFalse(resp["response"]["shouldEndSession"])

    def test_stop_intent_ends_session(self):
        resp = alexa_generative.lambda_handler(
            _make_intent_event("AMAZON.StopIntent"), None
        )
        self.assertTrue(resp["response"]["shouldEndSession"])

    def test_cancel_intent_ends_session(self):
        resp = alexa_generative.lambda_handler(
            _make_intent_event("AMAZON.CancelIntent"), None
        )
        self.assertTrue(resp["response"]["shouldEndSession"])

    def test_fallback_intent(self):
        resp = alexa_generative.lambda_handler(
            _make_intent_event("AMAZON.FallbackIntent"), None
        )
        self.assertFalse(resp["response"]["shouldEndSession"])

    def test_session_ended_request(self):
        resp = alexa_generative.lambda_handler(_make_session_ended_event(), None)
        self.assertEqual(resp, {"version": "1.0", "response": {}})

    def test_ask_question_intent_with_gemini(self):
        fake_response = mock.Mock()
        fake_response.text = "The speed of light is 299,792,458 metres per second."
        mock_model = mock.Mock()
        mock_model.generate_content.return_value = fake_response

        with mock.patch("google.generativeai.configure"), \
             mock.patch("google.generativeai.GenerativeModel", return_value=mock_model), \
             mock.patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
            resp = alexa_generative.lambda_handler(
                _make_intent_event("AskQuestionIntent", query="What is the speed of light?"),
                None,
            )

        speech = resp["response"]["outputSpeech"]["text"]
        self.assertIn("299,792,458", speech)
        self.assertTrue(resp["response"]["shouldEndSession"])

    def test_ask_question_intent_without_query_reprompts(self):
        resp = alexa_generative.lambda_handler(
            _make_intent_event("AskQuestionIntent"), None
        )
        self.assertFalse(resp["response"]["shouldEndSession"])

    def test_ask_question_intent_gemini_error_returns_error_message(self):
        with mock.patch("google.generativeai.configure"), \
             mock.patch(
                 "google.generativeai.GenerativeModel",
                 side_effect=Exception("network error"),
             ), \
             mock.patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
            resp = alexa_generative.lambda_handler(
                _make_intent_event("AskQuestionIntent", query="Tell me something"),
                None,
            )

        speech = resp["response"]["outputSpeech"]["text"]
        self.assertIn("Sorry", speech)

    def test_unknown_request_type_returns_fallback(self):
        event = {"version": "1.0", "request": {"type": "UnknownRequest"}}
        resp = alexa_generative.lambda_handler(event, None)
        self.assertIn("response", resp)

    def test_unknown_intent_returns_fallback(self):
        resp = alexa_generative.lambda_handler(
            _make_intent_event("SomeRandomIntent"), None
        )
        self.assertFalse(resp["response"]["shouldEndSession"])


if __name__ == "__main__":
    unittest.main()

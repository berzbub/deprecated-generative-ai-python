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

"""Tests for security (safety settings, API key handling) and rate (retry/timeout) behaviors."""

import collections
import os
from unittest import mock

from absl.testing import absltest
from absl.testing import parameterized

import google.api_core.exceptions
from google.api_core import retry as api_retry

from google.generativeai import client as client_lib
from google.generativeai import generative_models
from google.generativeai import protos
from google.generativeai.types import generation_types
from google.generativeai.types import helper_types


# ---------------------------------------------------------------------------
# Shared mock client used by all tests in this module
# ---------------------------------------------------------------------------


def _simple_response(text: str) -> protos.GenerateContentResponse:
    return protos.GenerateContentResponse(
        {"candidates": [{"content": {"parts": [{"text": text}]}}]}
    )


class MockGenerativeServiceClient:
    def __init__(self, test):
        self.test = test
        self.observed_requests = []
        self.observed_kwargs = []
        self.responses = collections.defaultdict(list)

    def generate_content(
        self,
        request: protos.GenerateContentRequest,
        **kwargs,
    ) -> protos.GenerateContentResponse:
        self.test.assertIsInstance(request, protos.GenerateContentRequest)
        self.observed_requests.append(request)
        self.observed_kwargs.append(kwargs)
        response = self.responses["generate_content"].pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def stream_generate_content(self, request, **kwargs):
        self.observed_requests.append(request)
        self.observed_kwargs.append(kwargs)
        response = self.responses["stream_generate_content"].pop(0)
        return response

    def count_tokens(self, request, **kwargs):
        self.observed_requests.append(request)
        self.observed_kwargs.append(kwargs)
        return self.responses["count_tokens"].pop(0)


# ---------------------------------------------------------------------------
# Security tests
# ---------------------------------------------------------------------------


class SecuritySafetySettingsTests(parameterized.TestCase):
    """Tests that safety settings are correctly applied and enforced."""

    def setUp(self):
        self.client = MockGenerativeServiceClient(self)
        client_lib._client_manager.clients["generative"] = self.client

    @property
    def observed_requests(self):
        return self.client.observed_requests

    @property
    def responses(self):
        return self.client.responses

    def test_all_harm_categories_blocked_when_shorthand_low(self):
        """Setting safety to 'low' should apply BLOCK_LOW_AND_ABOVE to all harm categories."""
        self.responses["generate_content"].append(_simple_response("ok"))
        model = generative_models.GenerativeModel("gemini-1.5-flash", safety_settings="low")
        model.generate_content("hello")

        safety_settings = {
            s.category: s.threshold for s in self.observed_requests[0].safety_settings
        }
        harm_categories = [
            protos.HarmCategory.HARM_CATEGORY_HARASSMENT,
            protos.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            protos.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            protos.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        ]
        for category in harm_categories:
            self.assertIn(category, safety_settings)
            self.assertEqual(
                safety_settings[category],
                protos.SafetySetting.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            )

    def test_all_harm_categories_blocked_when_shorthand_none(self):
        """Setting safety to 'block_none' should disable blocking for all harm categories."""
        self.responses["generate_content"].append(_simple_response("ok"))
        model = generative_models.GenerativeModel(
            "gemini-1.5-flash", safety_settings="block_none"
        )
        model.generate_content("hello")

        safety_settings = {
            s.category: s.threshold for s in self.observed_requests[0].safety_settings
        }
        harm_categories = [
            protos.HarmCategory.HARM_CATEGORY_HARASSMENT,
            protos.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            protos.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            protos.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        ]
        for category in harm_categories:
            self.assertIn(category, safety_settings)
            self.assertEqual(
                safety_settings[category],
                protos.SafetySetting.HarmBlockThreshold.BLOCK_NONE,
            )

    def test_generate_content_raises_on_blocked_prompt(self):
        """Accessing .text on a blocked-prompt response raises ValueError with a helpful message,
        and the response's prompt_feedback indicates the block reason."""
        self.responses["generate_content"].append(
            protos.GenerateContentResponse(
                {"prompt_feedback": {"block_reason": "SAFETY"}}
            )
        )
        model = generative_models.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("unsafe content")

        # The prompt_feedback should reflect the SAFETY block reason
        self.assertEqual(
            response.prompt_feedback.block_reason,
            protos.GenerateContentResponse.PromptFeedback.BlockReason.SAFETY,
        )

        with self.assertRaisesRegex(ValueError, "blocked prompt"):
            _ = response.text

    def test_generate_content_raises_on_candidate_safety_stop(self):
        """Accessing .text when a candidate is stopped for safety raises ValueError that
        includes finish_reason information, and the finish_reason on the candidate is SAFETY."""
        self.responses["generate_content"].append(
            protos.GenerateContentResponse(
                {"candidates": [{"finish_reason": "SAFETY"}]}
            )
        )
        model = generative_models.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("hello")

        # The candidate's finish_reason should be SAFETY
        self.assertEqual(
            response.candidates[0].finish_reason,
            protos.Candidate.FinishReason.SAFETY,
        )

        with self.assertRaisesRegex(ValueError, "finish_reason"):
            _ = response.text

    def test_per_request_safety_overrides_model_default(self):
        """Safety settings supplied at call time should override model-level defaults."""
        self.responses["generate_content"].append(_simple_response("ok"))
        self.responses["generate_content"].append(_simple_response("ok"))

        # Model default: block medium and above for dangerous content
        model = generative_models.GenerativeModel(
            "gemini-1.5-flash",
            safety_settings={"danger": "medium"},
        )

        # First call uses model defaults
        model.generate_content("hello")
        danger1 = next(
            s
            for s in self.observed_requests[0].safety_settings
            if s.category == protos.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT
        )
        self.assertEqual(
            danger1.threshold,
            protos.SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        )

        # Second call overrides to block only high
        model.generate_content("hello", safety_settings={"danger": "high"})
        danger2 = next(
            s
            for s in self.observed_requests[1].safety_settings
            if s.category == protos.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT
        )
        self.assertEqual(
            danger2.threshold,
            protos.SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        )

    def test_empty_contents_raises_type_error(self):
        """Passing empty contents is a security-relevant input validation check."""
        model = generative_models.GenerativeModel("gemini-1.5-flash")
        with self.assertRaises(TypeError):
            model.generate_content("")

    def test_streaming_blocked_prompt_raises(self):
        """A blocked prompt in a streaming response should raise BlockedPromptException."""
        self.responses["stream_generate_content"].append(
            iter(
                [
                    protos.GenerateContentResponse(
                        {"prompt_feedback": {"block_reason": "SAFETY"}}
                    )
                ]
            )
        )
        model = generative_models.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("bad prompt", stream=True)

        with self.assertRaises(generation_types.BlockedPromptException):
            for _ in response:
                pass


class SecurityApiKeyTests(parameterized.TestCase):
    """Tests that API key configuration is handled securely."""

    def setUp(self):
        super().setUp()
        client_lib._client_manager = client_lib._ClientManager()

    def test_api_key_set_in_client_options(self):
        """A directly provided API key should be stored in client options."""
        client_lib.configure(api_key="test-key-direct")
        opts = client_lib._client_manager.client_config["client_options"]
        self.assertEqual(opts.api_key, "test-key-direct")

    def test_both_api_key_and_client_options_api_key_raises(self):
        """Providing an API key in two ways simultaneously should raise ValueError."""
        from google.api_core import client_options as client_options_lib

        co = client_options_lib.ClientOptions(api_key="key-via-opts")
        with self.assertRaises(ValueError):
            client_lib.configure(api_key="key-direct", client_options=co)

    @mock.patch.dict(os.environ, {"GEMINI_API_KEY": "env-key"})
    def test_explicit_key_takes_precedence_over_env_var(self):
        """An explicitly provided API key must override the environment variable."""
        client_lib.configure(api_key="explicit-key")
        opts = client_lib._client_manager.client_config["client_options"]
        self.assertEqual(opts.api_key, "explicit-key")

    @mock.patch.dict(os.environ, {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": "fallback-key"})
    def test_empty_gemini_key_falls_back_to_google_key(self):
        """An empty GEMINI_API_KEY should not shadow GOOGLE_API_KEY."""
        client_lib.configure()
        opts = client_lib._client_manager.client_config["client_options"]
        self.assertEqual(opts.api_key, "fallback-key")


# ---------------------------------------------------------------------------
# Rate / request options tests
# ---------------------------------------------------------------------------


class RateRequestOptionsTests(parameterized.TestCase):
    """Tests that retry and timeout request options are correctly forwarded."""

    def setUp(self):
        self.client = MockGenerativeServiceClient(self)
        client_lib._client_manager.clients["generative"] = self.client

    @property
    def observed_kwargs(self):
        return self.client.observed_kwargs

    @property
    def responses(self):
        return self.client.responses

    def test_generate_content_forwards_timeout(self):
        """generate_content should pass a timeout from request_options to the client."""
        self.responses["generate_content"].append(_simple_response("pong"))
        model = generative_models.GenerativeModel("gemini-1.5-flash")

        model.generate_content("ping", request_options={"timeout": 30})

        self.assertEqual(self.observed_kwargs[0].get("timeout"), 30)

    def test_generate_content_forwards_retry(self):
        """generate_content should pass a retry policy from request_options to the client."""
        retry_policy = api_retry.Retry(initial=1.0, multiplier=2.0, maximum=10.0, timeout=60.0)
        self.responses["generate_content"].append(_simple_response("pong"))
        model = generative_models.GenerativeModel("gemini-1.5-flash")

        model.generate_content(
            "ping", request_options=helper_types.RequestOptions(retry=retry_policy)
        )

        forwarded_retry = self.observed_kwargs[0].get("retry")
        self.assertIsInstance(forwarded_retry, api_retry.Retry)
        self.assertEqual(forwarded_retry._initial, retry_policy._initial)
        self.assertEqual(forwarded_retry._multiplier, retry_policy._multiplier)
        self.assertEqual(forwarded_retry._maximum, retry_policy._maximum)
        self.assertEqual(forwarded_retry._timeout, retry_policy._timeout)

    def test_generate_content_forwards_timeout_and_retry_together(self):
        """generate_content should forward both timeout and retry when both are set."""
        retry_policy = api_retry.Retry(timeout=60.0)
        self.responses["generate_content"].append(_simple_response("pong"))
        model = generative_models.GenerativeModel("gemini-1.5-flash")

        model.generate_content(
            "ping",
            request_options=helper_types.RequestOptions(timeout=45, retry=retry_policy),
        )

        kwargs = self.observed_kwargs[0]
        self.assertEqual(kwargs.get("timeout"), 45)
        forwarded_retry = kwargs.get("retry")
        self.assertIsInstance(forwarded_retry, api_retry.Retry)
        self.assertEqual(forwarded_retry._timeout, retry_policy._timeout)

    def test_generate_content_no_request_options_sends_empty_kwargs(self):
        """generate_content with no request_options should send empty kwargs to the client."""
        self.responses["generate_content"].append(_simple_response("pong"))
        model = generative_models.GenerativeModel("gemini-1.5-flash")

        model.generate_content("ping")

        self.assertEqual(self.observed_kwargs[0], {})

    def test_streaming_generate_content_forwards_timeout(self):
        """Streaming generate_content should also forward timeout from request_options."""
        chunks = ["first", " second"]
        self.responses["stream_generate_content"].append(
            (_simple_response(text) for text in chunks)
        )
        model = generative_models.GenerativeModel("gemini-1.5-flash")

        response = model.generate_content(
            "ping", stream=True, request_options={"timeout": 60}
        )
        # Consume the iterator
        list(response)

        self.assertEqual(self.observed_kwargs[0].get("timeout"), 60)

    def test_resource_exhausted_propagates(self):
        """A ResourceExhausted error (rate limit) should propagate to the caller."""
        self.responses["generate_content"].append(
            google.api_core.exceptions.ResourceExhausted("quota exceeded")
        )
        model = generative_models.GenerativeModel("gemini-1.5-flash")

        with self.assertRaises(google.api_core.exceptions.ResourceExhausted):
            model.generate_content("ping")

    def test_count_tokens_forwards_timeout(self):
        """count_tokens should forward timeout from request_options."""
        self.responses["count_tokens"].append(protos.CountTokensResponse(total_tokens=5))
        model = generative_models.GenerativeModel("gemini-1.5-flash")

        model.count_tokens(
            [{"role": "user", "parts": ["hello"]}], request_options={"timeout": 20}
        )

        self.assertEqual(self.observed_kwargs[0].get("timeout"), 20)


if __name__ == "__main__":
    absltest.main()

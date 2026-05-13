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
"""Demonstrates how the temperature parameter controls generation output.

The temperature parameter behaves like a physical temperature sensor:
- Low temperature (near 0.0): output is "frozen" — predictable and conservative.
- High temperature (near 2.0): output is "liquid" — fluid, varied, and creative.

This is useful when adapting generation behaviour to different contexts, e.g.
factual Q&A benefits from low temperature while creative writing benefits from
high temperature.
"""
from absl.testing import absltest


class UnitTests(absltest.TestCase):
    def test_temperature_low(self):
        # [START temperature_low]
        import google.generativeai as genai

        # Low temperature produces focused, deterministic responses.
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            "What is the capital of France?",
            generation_config=genai.types.GenerationConfig(
                temperature=0.0,
            ),
        )

        print(response.text)
        # [END temperature_low]

    def test_temperature_high(self):
        # [START temperature_high]
        import google.generativeai as genai

        # High temperature produces varied, creative responses.
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            "Write a short poem about water.",
            generation_config=genai.types.GenerationConfig(
                temperature=1.5,
            ),
        )

        print(response.text)
        # [END temperature_high]

    def test_temperature_comparison(self):
        # [START temperature_comparison]
        import google.generativeai as genai

        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = "Suggest a name for a new color between blue and green."

        # "Frozen" — conservative, repeatable output.
        low_temp_response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.0),
        )

        # "Liquid" — fluid, creative output.
        high_temp_response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=1.8),
        )

        print("Low temperature (frozen):", low_temp_response.text)
        print("High temperature (liquid):", high_temp_response.text)
        # [END temperature_comparison]


if __name__ == "__main__":
    absltest.main()

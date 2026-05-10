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

from absl.testing import absltest
from absl.testing import parameterized
from google.generativeai.types import safety_types
from google.generativeai import protos


class SafetyTests(parameterized.TestCase):
    """Tests are in order with the design doc."""

    @parameterized.named_parameters(
        ["block_threshold", protos.SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE],
        ["block_threshold2", "medium"],
        ["block_threshold3", 2],
        ["dict", {"danger": "medium"}],
        ["dict2", {"danger": 2}],
        ["dict3", {"danger": protos.SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE}],
        [
            "list-dict",
            [
                dict(
                    category=protos.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=protos.SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                ),
            ],
        ],
        [
            "list-dict2",
            [
                dict(category="danger", threshold="med"),
            ],
        ],
    )
    def test_safety_overwrite(self, setting):
        setting = safety_types.to_easy_safety_dict(setting)
        self.assertEqual(
            setting[protos.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT],
            protos.SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        )

    def test_to_easy_safety_dict_none(self):
        result = safety_types.to_easy_safety_dict(None)
        self.assertEqual(result, {})

    def test_to_easy_safety_dict_protos_safety_setting_list(self):
        settings = [
            protos.SafetySetting(
                category=protos.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=protos.SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            )
        ]
        result = safety_types.to_easy_safety_dict(settings)
        self.assertEqual(
            result[protos.HarmCategory.HARM_CATEGORY_HARASSMENT],
            protos.SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        )

    def test_to_easy_safety_dict_invalid_setting_raises(self):
        with self.assertRaises(ValueError):
            safety_types.to_easy_safety_dict([42])

    def test_normalize_safety_settings_none(self):
        result = safety_types.normalize_safety_settings(None)
        self.assertIsNone(result)

    def test_normalize_safety_settings_from_block_threshold(self):
        result = safety_types.normalize_safety_settings("medium")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        # Should have one entry per harm category (excluding unspecified)
        self.assertGreater(len(result), 0)
        for item in result:
            self.assertIn("category", item)
            self.assertIn("threshold", item)

    def test_normalize_safety_settings_from_mapping(self):
        settings = {"harassment": "high"}
        result = safety_types.normalize_safety_settings(settings)
        self.assertIsInstance(result, list)
        self.assertLen(result, 1)
        self.assertEqual(result[0]["category"], protos.HarmCategory.HARM_CATEGORY_HARASSMENT)
        self.assertEqual(
            result[0]["threshold"], protos.SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
        )

    def test_normalize_safety_settings_from_list_of_dicts(self):
        settings = [{"category": "dangerous", "threshold": "low"}]
        result = safety_types.normalize_safety_settings(settings)
        self.assertIsInstance(result, list)
        self.assertLen(result, 1)
        self.assertEqual(
            result[0]["category"], protos.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT
        )
        self.assertEqual(
            result[0]["threshold"], protos.SafetySetting.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE
        )

    def test_convert_filters_to_enums(self):
        filters = [{"reason": 1, "message": "blocked"}]
        result = safety_types.convert_filters_to_enums(filters)
        self.assertLen(result, 1)
        self.assertEqual(
            result[0]["reason"], safety_types.BlockedReason(1)
        )
        self.assertEqual(result[0]["message"], "blocked")

    def test_convert_rating_to_enum(self):
        rating = {"category": 7, "probability": 1}
        result = safety_types.convert_rating_to_enum(rating)
        self.assertEqual(result["category"], protos.HarmCategory.HARM_CATEGORY_HARASSMENT)
        self.assertEqual(
            result["probability"], safety_types.HarmProbability.NEGLIGIBLE
        )

    def test_convert_ratings_to_enum(self):
        ratings = [
            {"category": 7, "probability": 2},
            {"category": 8, "probability": 3},
        ]
        result = safety_types.convert_ratings_to_enum(ratings)
        self.assertLen(result, 2)
        self.assertEqual(result[0]["category"], protos.HarmCategory.HARM_CATEGORY_HARASSMENT)
        self.assertEqual(result[1]["category"], protos.HarmCategory.HARM_CATEGORY_HATE_SPEECH)

    def test_convert_setting_to_enum(self):
        setting = {"category": 7, "threshold": 2}
        result = safety_types.convert_setting_to_enum(setting)
        self.assertEqual(result["category"], protos.HarmCategory.HARM_CATEGORY_HARASSMENT)
        self.assertEqual(
            result["threshold"],
            protos.SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        )

    def test_convert_safety_feedback_to_enums(self):
        feedback = [
            {
                "rating": {"category": 7, "probability": 2},
                "setting": {"category": 7, "threshold": 3},
            }
        ]
        result = safety_types.convert_safety_feedback_to_enums(feedback)
        self.assertLen(result, 1)
        self.assertEqual(
            result[0]["rating"]["category"], protos.HarmCategory.HARM_CATEGORY_HARASSMENT
        )
        self.assertEqual(
            result[0]["setting"]["category"], protos.HarmCategory.HARM_CATEGORY_HARASSMENT
        )

    def test_convert_candidate_enums(self):
        candidates = [
            {
                "safety_ratings": [{"category": 7, "probability": 2}],
                "text": "some text",
            }
        ]
        result = safety_types.convert_candidate_enums(candidates)
        self.assertLen(result, 1)
        self.assertEqual(
            result[0]["safety_ratings"][0]["category"],
            protos.HarmCategory.HARM_CATEGORY_HARASSMENT,
        )

    def test_to_harm_category(self):
        self.assertEqual(
            safety_types.to_harm_category("harassment"),
            protos.HarmCategory.HARM_CATEGORY_HARASSMENT,
        )
        self.assertEqual(
            safety_types.to_harm_category("hate"),
            protos.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        )
        self.assertEqual(
            safety_types.to_harm_category("sex"),
            protos.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        )
        self.assertEqual(
            safety_types.to_harm_category("danger"),
            protos.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        )

    def test_to_block_threshold(self):
        self.assertEqual(
            safety_types.to_block_threshold("low"),
            protos.SafetySetting.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        )
        self.assertEqual(
            safety_types.to_block_threshold("high"),
            protos.SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        )
        self.assertEqual(
            safety_types.to_block_threshold("block_none"),
            protos.SafetySetting.HarmBlockThreshold.BLOCK_NONE,
        )


if __name__ == "__main__":
    absltest.main()

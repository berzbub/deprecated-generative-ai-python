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


class ConvertFiltersTests(parameterized.TestCase):

    def test_convert_filters_to_enums(self):
        filters = [
            {"reason": 1, "message": "blocked for harassment"},
            {"reason": 2, "message": "blocked for hate"},
        ]
        result = safety_types.convert_filters_to_enums(filters)
        self.assertLen(result, 2)
        self.assertIsInstance(result[0]["reason"], safety_types.BlockedReason)

    def test_convert_filters_empty(self):
        result = safety_types.convert_filters_to_enums([])
        self.assertEqual(result, [])


class ConvertRatingsTests(parameterized.TestCase):

    def test_convert_rating_to_enum(self):
        rating = {"category": 7, "probability": 3}
        result = safety_types.convert_rating_to_enum(rating)
        self.assertEqual(result["category"], protos.HarmCategory.HARM_CATEGORY_HARASSMENT)
        self.assertIsInstance(result["probability"], safety_types.HarmProbability)

    def test_convert_ratings_to_enum(self):
        ratings = [
            {"category": 7, "probability": 1},
            {"category": 8, "probability": 2},
        ]
        result = safety_types.convert_ratings_to_enum(ratings)
        self.assertLen(result, 2)
        self.assertEqual(result[0]["category"], protos.HarmCategory.HARM_CATEGORY_HARASSMENT)
        self.assertEqual(result[1]["category"], protos.HarmCategory.HARM_CATEGORY_HATE_SPEECH)


class NormalizeSafetySettingsTests(parameterized.TestCase):

    def test_returns_none_for_none(self):
        result = safety_types.normalize_safety_settings(None)
        self.assertIsNone(result)

    def test_from_string_threshold(self):
        result = safety_types.normalize_safety_settings("medium")
        self.assertIsInstance(result, list)
        # Should produce one entry per harm category (minus unspecified)
        self.assertGreater(len(result), 0)
        for entry in result:
            self.assertIn("category", entry)
            self.assertIn("threshold", entry)

    def test_from_int_threshold(self):
        result = safety_types.normalize_safety_settings(2)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_from_harm_block_threshold_enum(self):
        result = safety_types.normalize_safety_settings(
            protos.SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
        )
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_from_mapping(self):
        settings = {
            protos.HarmCategory.HARM_CATEGORY_HARASSMENT: protos.SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            protos.HarmCategory.HARM_CATEGORY_HATE_SPEECH: protos.SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }
        result = safety_types.normalize_safety_settings(settings)
        self.assertLen(result, 2)
        categories = [r["category"] for r in result]
        self.assertIn(protos.HarmCategory.HARM_CATEGORY_HARASSMENT, categories)

    def test_from_list_of_dicts(self):
        settings = [
            {"category": "harassment", "threshold": "medium"},
            {"category": "hate_speech", "threshold": "high"},
        ]
        result = safety_types.normalize_safety_settings(settings)
        self.assertLen(result, 2)

    def test_to_easy_safety_dict_with_proto_safety_setting_in_list(self):
        settings = [
            protos.SafetySetting(
                category=protos.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=protos.SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            )
        ]
        result = safety_types.to_easy_safety_dict(settings)
        self.assertIn(protos.HarmCategory.HARM_CATEGORY_HARASSMENT, result)
        self.assertEqual(
            result[protos.HarmCategory.HARM_CATEGORY_HARASSMENT],
            protos.SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        )

    def test_to_easy_safety_dict_invalid_setting_raises(self):
        with self.assertRaises(ValueError):
            safety_types.to_easy_safety_dict([42])


class ConvertSettingAndFeedbackTests(parameterized.TestCase):

    def test_convert_setting_to_enum(self):
        setting = {"category": 7, "threshold": 2}
        result = safety_types.convert_setting_to_enum(setting)
        self.assertEqual(result["category"], protos.HarmCategory.HARM_CATEGORY_HARASSMENT)
        self.assertIsInstance(result["threshold"], safety_types.HarmBlockThreshold)

    def test_convert_safety_feedback_to_enums(self):
        feedback = [
            {
                "rating": {"category": 7, "probability": 3},
                "setting": {"category": 7, "threshold": 2},
            }
        ]
        result = safety_types.convert_safety_feedback_to_enums(feedback)
        self.assertLen(result, 1)
        self.assertIn("rating", result[0])
        self.assertIn("setting", result[0])
        self.assertEqual(
            result[0]["rating"]["category"], protos.HarmCategory.HARM_CATEGORY_HARASSMENT
        )

    def test_convert_candidate_enums(self):
        candidates = [
            {"safety_ratings": [{"category": 7, "probability": 1}], "content": "hello"},
            {"safety_ratings": [{"category": 8, "probability": 2}], "content": "world"},
        ]
        result = safety_types.convert_candidate_enums(candidates)
        self.assertLen(result, 2)
        self.assertEqual(
            result[0]["safety_ratings"][0]["category"],
            protos.HarmCategory.HARM_CATEGORY_HARASSMENT,
        )
        self.assertEqual(
            result[1]["safety_ratings"][0]["category"],
            protos.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        )

    def test_convert_candidate_enums_empty(self):
        result = safety_types.convert_candidate_enums([])
        self.assertEqual(result, [])


if __name__ == "__main__":
    absltest.main()

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
import copy
import math
from typing import Any
import unittest
import unittest.mock as mock

from google.generativeai import protos

from google.generativeai import answer
from google.generativeai import types as genai_types
from google.generativeai import client
from absl.testing import absltest
from absl.testing import parameterized

from google.generativeai.types import content_types

DEFAULT_ANSWER_MODEL = "models/aqa"


class UnitTests(parameterized.TestCase):
    def setUp(self):
        self.client = unittest.mock.MagicMock()

        client._client_manager.clients["generative"] = self.client
        client._client_manager.clients["model"] = self.client

        self.observed_requests = []

        def add_client_method(f):
            name = f.__name__
            setattr(self.client, name, f)
            return f

        @add_client_method
        def generate_answer(
            request: protos.GenerateAnswerRequest,
            **kwargs,
        ) -> protos.GenerateAnswerResponse:
            self.observed_requests.append(request)
            return protos.GenerateAnswerResponse(
                answer=protos.Candidate(
                    index=1,
                    content=(protos.Content(parts=[protos.Part(text="Demo answer.")])),
                ),
                answerable_probability=0.500,
            )

    def test_make_grounding_passages_mixed_types(self):
        inline_passages = [
            "I am a chicken",
            protos.Content(parts=[protos.Part(text="I am a bird.")]),
            protos.Content(parts=[protos.Part(text="I can fly!")]),
        ]
        x = answer._make_grounding_passages(inline_passages)
        self.assertIsInstance(x, protos.GroundingPassages)
        self.assertEqual(
            protos.GroundingPassages(
                passages=[
                    {
                        "id": "0",
                        "content": protos.Content(parts=[protos.Part(text="I am a chicken")]),
                    },
                    {
                        "id": "1",
                        "content": protos.Content(parts=[protos.Part(text="I am a bird.")]),
                    },
                    {"id": "2", "content": protos.Content(parts=[protos.Part(text="I can fly!")])},
                ]
            ),
            x,
        )

    @parameterized.named_parameters(
        [
            dict(
                testcase_name="grounding_passage",
                inline_passages=protos.GroundingPassages(
                    passages=[
                        {
                            "id": "0",
                            "content": protos.Content(parts=[protos.Part(text="I am a chicken")]),
                        },
                        {
                            "id": "1",
                            "content": protos.Content(parts=[protos.Part(text="I am a bird.")]),
                        },
                        {
                            "id": "2",
                            "content": protos.Content(parts=[protos.Part(text="I can fly!")]),
                        },
                    ]
                ),
            ),
            dict(
                testcase_name="content_object",
                inline_passages=[
                    protos.Content(parts=[protos.Part(text="I am a chicken")]),
                    protos.Content(parts=[protos.Part(text="I am a bird.")]),
                    protos.Content(parts=[protos.Part(text="I can fly!")]),
                ],
            ),
            dict(
                testcase_name="list_of_strings",
                inline_passages=["I am a chicken", "I am a bird.", "I can fly!"],
            ),
        ]
    )
    def test_make_grounding_passages(self, inline_passages):
        x = answer._make_grounding_passages(inline_passages)
        self.assertIsInstance(x, protos.GroundingPassages)
        self.assertEqual(
            protos.GroundingPassages(
                passages=[
                    {
                        "id": "0",
                        "content": protos.Content(parts=[protos.Part(text="I am a chicken")]),
                    },
                    {
                        "id": "1",
                        "content": protos.Content(parts=[protos.Part(text="I am a bird.")]),
                    },
                    {"id": "2", "content": protos.Content(parts=[protos.Part(text="I can fly!")])},
                ]
            ),
            x,
        )

    @parameterized.named_parameters(
        dict(
            testcase_name="dict_of_strings",
            inline_passages={"4": "I am a chicken", "5": "I am a bird.", "6": "I can fly!"},
        ),
        dict(
            testcase_name="tuple_of_strings",
            inline_passages=[("4", "I am a chicken"), ("5", "I am a bird."), ("6", "I can fly!")],
        ),
        dict(
            testcase_name="list_of_grounding_passages",
            inline_passages=[
                protos.GroundingPassage(
                    id="4", content=protos.Content(parts=[protos.Part(text="I am a chicken")])
                ),
                protos.GroundingPassage(
                    id="5", content=protos.Content(parts=[protos.Part(text="I am a bird.")])
                ),
                protos.GroundingPassage(
                    id="6", content=protos.Content(parts=[protos.Part(text="I can fly!")])
                ),
            ],
        ),
    )
    def test_make_grounding_passages_different_id(self, inline_passages):
        x = answer._make_grounding_passages(inline_passages)
        self.assertIsInstance(x, protos.GroundingPassages)
        self.assertEqual(
            protos.GroundingPassages(
                passages=[
                    {
                        "id": "4",
                        "content": protos.Content(parts=[protos.Part(text="I am a chicken")]),
                    },
                    {
                        "id": "5",
                        "content": protos.Content(parts=[protos.Part(text="I am a bird.")]),
                    },
                    {"id": "6", "content": protos.Content(parts=[protos.Part(text="I can fly!")])},
                ]
            ),
            x,
        )

    def test_make_grounding_passages_key_strings(self):
        inline_passages = {
            "first": "I am a chicken",
            "second": "I am a bird.",
            "third": "I can fly!",
        }

        x = answer._make_grounding_passages(inline_passages)
        self.assertIsInstance(x, protos.GroundingPassages)
        self.assertEqual(
            protos.GroundingPassages(
                passages=[
                    {
                        "id": "first",
                        "content": protos.Content(parts=[protos.Part(text="I am a chicken")]),
                    },
                    {
                        "id": "second",
                        "content": protos.Content(parts=[protos.Part(text="I am a bird.")]),
                    },
                    {
                        "id": "third",
                        "content": protos.Content(parts=[protos.Part(text="I can fly!")]),
                    },
                ]
            ),
            x,
        )

    def test_generate_answer_request(self):
        # Should be a list of contents to use to_contents() function.
        contents = [protos.Content(parts=[protos.Part(text="I have wings.")])]

        inline_passages = ["I am a chicken", "I am a bird.", "I can fly!"]
        grounding_passages = protos.GroundingPassages(
            passages=[
                {"id": "0", "content": protos.Content(parts=[protos.Part(text="I am a chicken")])},
                {"id": "1", "content": protos.Content(parts=[protos.Part(text="I am a bird.")])},
                {"id": "2", "content": protos.Content(parts=[protos.Part(text="I can fly!")])},
            ]
        )

        x = answer._make_generate_answer_request(
            model=DEFAULT_ANSWER_MODEL, contents=contents, inline_passages=inline_passages
        )

        self.assertEqual(
            protos.GenerateAnswerRequest(
                model=DEFAULT_ANSWER_MODEL, contents=contents, inline_passages=grounding_passages
            ),
            x,
        )

    def test_generate_answer(self):
        # Test handling return value of generate_answer().
        contents = [protos.Content(parts=[protos.Part(text="I have wings.")])]

        grounding_passages = protos.GroundingPassages(
            passages=[
                {"id": "0", "content": protos.Content(parts=[protos.Part(text="I am a chicken")])},
                {"id": "1", "content": protos.Content(parts=[protos.Part(text="I am a bird.")])},
                {"id": "2", "content": protos.Content(parts=[protos.Part(text="I can fly!")])},
            ]
        )

        a = answer.generate_answer(
            model="models/aqa",
            contents=contents,
            inline_passages=grounding_passages,
            answer_style="ABSTRACTIVE",
        )

        self.assertIsInstance(a, protos.GenerateAnswerResponse)
        self.assertEqual(
            a,
            protos.GenerateAnswerResponse(
                answer=protos.Candidate(
                    index=1,
                    content=(protos.Content(parts=[protos.Part(text="Demo answer.")])),
                ),
                answerable_probability=0.500,
            ),
        )

    def test_generate_answer_called_with_request_options(self):
        self.client.generate_answer = mock.MagicMock()
        request = mock.ANY
        request_options = genai_types.RequestOptions(timeout=120)

        answer.generate_answer(contents=[], inline_passages=[], request_options=request_options)

        self.client.generate_answer.assert_called_once_with(request, **request_options)

    def test_make_generate_answer_request_raises_with_both_sources(self):
        with self.assertRaises(ValueError):
            answer._make_generate_answer_request(
                contents=["question"],
                inline_passages=["some passage"],
                semantic_retriever="corpora/my-corpus",
            )

    def test_make_generate_answer_request_raises_with_no_source(self):
        with self.assertRaises(TypeError):
            answer._make_generate_answer_request(
                contents=["question"],
            )

    def test_make_generate_answer_request_with_answer_style(self):
        contents = [protos.Content(parts=[protos.Part(text="question")])]
        x = answer._make_generate_answer_request(
            model=DEFAULT_ANSWER_MODEL,
            contents=contents,
            inline_passages=["passage"],
            answer_style="VERBOSE",
        )
        self.assertEqual(x.answer_style, answer.AnswerStyle.VERBOSE)

    def test_make_generate_answer_request_with_safety_settings(self):
        contents = [protos.Content(parts=[protos.Part(text="question")])]
        safety = {"dangerous": "medium"}
        x = answer._make_generate_answer_request(
            model=DEFAULT_ANSWER_MODEL,
            contents=contents,
            inline_passages=["passage"],
            safety_settings=safety,
        )
        self.assertIsInstance(x, protos.GenerateAnswerRequest)
        self.assertLen(x.safety_settings, 1)

    def test_make_generate_answer_request_with_temperature(self):
        contents = [protos.Content(parts=[protos.Part(text="question")])]
        x = answer._make_generate_answer_request(
            model=DEFAULT_ANSWER_MODEL,
            contents=contents,
            inline_passages=["passage"],
            temperature=0.5,
        )
        self.assertAlmostEqual(x.temperature, 0.5)

    def test_maybe_get_source_name_from_string(self):
        result = answer._maybe_get_source_name("corpora/my-corpus")
        self.assertEqual(result, "corpora/my-corpus")

    def test_maybe_get_source_name_from_corpus_proto(self):
        corpus = protos.Corpus(name="corpora/my-corpus")
        result = answer._maybe_get_source_name(corpus)
        self.assertEqual(result, "corpora/my-corpus")

    def test_maybe_get_source_name_from_document_proto(self):
        doc = protos.Document(name="corpora/my-corpus/documents/my-doc")
        result = answer._maybe_get_source_name(doc)
        self.assertEqual(result, "corpora/my-corpus/documents/my-doc")

    def test_maybe_get_source_name_from_retriever_corpus(self):
        import datetime
        from google.generativeai.types import retriever_types

        corpus = retriever_types.Corpus(
            name="corpora/my-corpus",
            display_name="My Corpus",
            create_time=datetime.datetime(2024, 1, 1),
            update_time=datetime.datetime(2024, 1, 1),
        )
        result = answer._maybe_get_source_name(corpus)
        self.assertEqual(result, "corpora/my-corpus")

    def test_maybe_get_source_name_unknown_type_returns_none(self):
        result = answer._maybe_get_source_name(12345)
        self.assertIsNone(result)

    def test_make_semantic_retriever_config_from_proto(self):
        src_config = protos.SemanticRetrieverConfig(source="corpora/my-corpus")
        result = answer._make_semantic_retriever_config(src_config, "my question")
        self.assertIs(result, src_config)

    def test_make_semantic_retriever_config_from_dict_with_query_none(self):
        query_content = protos.Content(parts=[protos.Part(text="my question")])
        source_dict = {"source": "corpora/my-corpus", "query": None}
        result = answer._make_semantic_retriever_config(source_dict, query_content)
        self.assertIsInstance(result, protos.SemanticRetrieverConfig)
        self.assertEqual(result.source, "corpora/my-corpus")

    def test_make_semantic_retriever_config_from_dict_with_string_query(self):
        source_dict = {"source": "corpora/my-corpus", "query": "what is this about?"}
        query_content = protos.Content(parts=[protos.Part(text="fallback question")])
        result = answer._make_semantic_retriever_config(source_dict, query_content)
        self.assertIsInstance(result, protos.SemanticRetrieverConfig)

    def test_make_semantic_retriever_config_invalid_source_raises(self):
        with self.assertRaises(TypeError):
            answer._make_semantic_retriever_config(12345, "question")

    def test_make_grounding_passages_invalid_source_raises(self):
        with self.assertRaises(TypeError):
            answer._make_grounding_passages(42)

    def test_generate_answer_with_semantic_retriever_request(self):
        contents = [protos.Content(parts=[protos.Part(text="What birds can fly?")])]
        source_dict = {"source": "corpora/my-corpus", "query": None}

        a = answer.generate_answer(
            model=DEFAULT_ANSWER_MODEL,
            contents=contents,
            semantic_retriever=source_dict,
        )
        self.assertIsInstance(a, protos.GenerateAnswerResponse)


if __name__ == "__main__":
    absltest.main()

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


class UnitTests(absltest.TestCase):
    def test_ibreaviary_translator(self):
        # [START ibreaviary_translator]
        import google.generativeai as genai

        model = genai.GenerativeModel(
            "models/gemini-1.5-flash",
            system_instruction=(
                "You are a translator for the Ibreaviary language, "
                "a fictional language spoken by the birds of the Ibreaviary. "
                "Translate any text the user provides into Ibreaviary. "
                "Ibreaviary is a whimsical language where every word is "
                "replaced with a combination of bird calls and bird-related "
                "words (e.g., 'tweet', 'chirp', 'caw', 'warble', 'coo', "
                "'squawk', 'trill', 'peep'). Maintain the original sentence "
                "structure but replace all words with Ibreaviary equivalents."
            ),
        )
        response = model.generate_content("Hello, how are you today?")
        print(response.text)
        # [END ibreaviary_translator]

    def test_ibreaviary_translator_to_english(self):
        # [START ibreaviary_translator_to_english]
        import google.generativeai as genai

        model = genai.GenerativeModel(
            "models/gemini-1.5-flash",
            system_instruction=(
                "You are a translator for the Ibreaviary language, "
                "a fictional language spoken by the birds of the Ibreaviary. "
                "When the user provides text in Ibreaviary (a whimsical language "
                "made of bird calls such as 'tweet', 'chirp', 'caw', 'warble', "
                "'coo', 'squawk', 'trill', 'peep'), translate it back into English. "
                "If the user provides English text, translate it into Ibreaviary."
            ),
        )
        chat = model.start_chat()
        response = chat.send_message("Hello, how are you today?")
        print("Ibreaviary:", response.text)
        response = chat.send_message(response.text)
        print("Back to English:", response.text)
        # [END ibreaviary_translator_to_english]


if __name__ == "__main__":
    absltest.main()

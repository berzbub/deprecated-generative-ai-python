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
"""Story generation sample: the Small World App narrative.

Demonstrates how to use a system instruction together with multi-turn chat
to generate a rich retro-computing story with the Gemini API.
"""
from absl.testing import absltest


class UnitTests(absltest.TestCase):
    def test_small_world_story(self):
        # [START small_world_story]
        import google.generativeai as genai

        # Give the model a storyteller persona steeped in retro-computing lore.
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            system_instruction=(
                "You are a technical narrator who specialises in dramatic stories "
                "about vintage computing hardware. Write in a vivid, engaging style "
                "that blends real computer history with speculative fiction. "
                "Keep each response to two or three paragraphs."
            ),
        )

        # Seed the chat with background context so every reply stays consistent.
        chat = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": (
                        "Set the scene: it is the year 2000. "
                        "A small experimental program called the Small World App "
                        "was written in HTMLX-BASIC 3.1 and stored on a single 3.5-inch "
                        "diskette. The machine that runs it boots entirely from that "
                        "diskette and is powered by a bank of aging solar batteries. "
                        "A Y2K initialisation error delayed the boot sequence, but the "
                        "system has now finished initialising and completed data "
                        "verification."
                    ),
                },
                {
                    "role": "model",
                    "parts": (
                        "Deep in a sunlit basement, a weathered beige tower hums back "
                        "to life. Its diskette drive whirs with purposeful clicks as "
                        "the worn label — 'SMALL WORLD APP v1.0 / HTMLX-BASIC 3.1' "
                        "— spins past the read head for what feels like the first time "
                        "in years. Outside, a row of dusty solar panels converts pale "
                        "winter light into just enough milliamps to keep the machine "
                        "alive.\n\n"
                        "The boot was supposed to happen at midnight on 1 January 2000, "
                        "but a rogue two-digit year check locked the initialisation "
                        "routine in an endless loop for twenty-six years. A routine "
                        "firmware patch, applied by a curious technician, finally broke "
                        "the cycle. The amber cursor blinks. Data verification: PASSED."
                    ),
                },
            ]
        )

        # Ask the model to continue the story.
        response = chat.send_message("What does the Small World App actually do, and what happens next?")
        print(response.text)
        # [END small_world_story]

    def test_small_world_story_streaming(self):
        # [START small_world_story_streaming]
        import google.generativeai as genai

        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            system_instruction=(
                "You are a technical narrator who specialises in dramatic stories "
                "about vintage computing hardware. Write in a vivid, engaging style "
                "that blends real computer history with speculative fiction. "
                "Keep each response to two or three paragraphs."
            ),
        )

        prompt = (
            "Tell the story of the Small World App: a program written in HTMLX-BASIC 3.1, "
            "stored on a diskette, booting on solar batteries after a Y2K delay of "
            "twenty-six years. It just finished initialising and data verification. "
            "What does it do, and what happens now that it is finally running?"
        )

        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            print(chunk.text, end="", flush=True)
        print()
        # [END small_world_story_streaming]


if __name__ == "__main__":
    absltest.main()

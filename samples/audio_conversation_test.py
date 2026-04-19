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
from absl.testing import absltest

import pathlib

media = pathlib.Path(__file__).parents[1] / "third_party"


class UnitTests(absltest.TestCase):
    def test_audio_conversation_inline(self):
        """Send in-memory WAV audio inline (no file upload) and get a response."""
        # [START audio_conversation_inline]
        import io
        import struct
        import wave
        import google.generativeai as genai

        # Build a minimal valid WAV in memory — nothing is written to disk.
        sample_rate = 16000
        duration_secs = 1
        num_samples = sample_rate * duration_secs
        pcm_data = struct.pack("<" + "h" * num_samples, *([0] * num_samples))

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_data)
        audio_bytes = buf.getvalue()

        model = genai.GenerativeModel("gemini-1.5-flash")

        # Audio is sent inline — it is never uploaded or stored anywhere.
        response = model.generate_content(
            [
                "Please respond to what was said.",
                {"mime_type": "audio/wav", "data": audio_bytes},
            ]
        )
        print(f"{response.text=}")
        # [END audio_conversation_inline]

    def test_audio_conversation_inline_from_existing_audio(self):
        """Demonstrate sending an existing audio file inline (bypassing the File API)."""
        # [START audio_conversation_inline_existing]
        import io
        import google.generativeai as genai

        # Read the file into memory — the bytes are sent inline, not uploaded.
        with open(media / "sample.mp3", "rb") as f:
            audio_bytes = f.read()

        model = genai.GenerativeModel("gemini-1.5-flash")

        response = model.generate_content(
            [
                "Describe this audio clip.",
                {"mime_type": "audio/mpeg", "data": audio_bytes},
            ]
        )
        print(f"{response.text=}")
        # [END audio_conversation_inline_existing]


if __name__ == "__main__":
    absltest.main()

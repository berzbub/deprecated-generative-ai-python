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
"""Live microphone conversation with Gemini — audio is never saved to disk.

Audio captured from the microphone is kept in-memory and sent to the
Gemini API using inline ``blob`` data (not the File Upload API), so nothing
is persisted on the local filesystem or in Google Cloud Storage.

Requirements::

    pip install pyaudio

Usage::

    export GEMINI_API_KEY="YOUR_API_KEY"
    python samples/audio_conversation.py
"""

from __future__ import annotations

import io
import wave

# [START audio_conversation_non_recorded]
import google.generativeai as genai

# pyaudio is only needed when actually capturing from a microphone.
# Install it with: pip install pyaudio
try:
    import pyaudio
    _PYAUDIO_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYAUDIO_AVAILABLE = False


# Audio recording parameters
_CHANNELS = 1
_SAMPLE_RATE = 16000  # 16 kHz — good balance between quality and size
_CHUNK = 1024          # frames per buffer
_RECORD_SECONDS = 5    # seconds to record per turn


def _record_audio_to_memory(seconds: int = _RECORD_SECONDS) -> bytes:
    """Capture microphone audio and return raw WAV bytes — nothing is saved to disk."""
    if not _PYAUDIO_AVAILABLE:
        raise RuntimeError(
            "pyaudio is not installed. Install it with: pip install pyaudio"
        )

    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=_CHANNELS,
        rate=_SAMPLE_RATE,
        input=True,
        frames_per_buffer=_CHUNK,
    )

    print(f"Recording for {seconds} seconds …")
    frames: list[bytes] = []
    for _ in range(0, int(_SAMPLE_RATE / _CHUNK * seconds)):
        frames.append(stream.read(_CHUNK))

    stream.stop_stream()
    stream.close()
    pa.terminate()

    # Write frames to an in-memory WAV buffer — no file on disk.
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(_CHANNELS)
        wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
        wf.setframerate(_SAMPLE_RATE)
        wf.writeframes(b"".join(frames))

    return buf.getvalue()


def _make_wav_bytes_from_pcm(
    pcm_frames: list[bytes],
    sample_rate: int = _SAMPLE_RATE,
    channels: int = _CHANNELS,
    sample_width: int = 2,  # 16-bit = 2 bytes
) -> bytes:
    """Helper used in tests: wrap raw PCM frames in a valid WAV container."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(pcm_frames))
    return buf.getvalue()


def respond_to_audio(audio_bytes: bytes, prompt: str = "Please respond to what was said.") -> str:
    """Send *in-memory* WAV audio inline to Gemini and return the text response.

    The audio is transmitted as inline blob data so it is never uploaded to
    Google Cloud Storage or saved anywhere outside the API request itself.

    Args:
        audio_bytes: Raw WAV file content as a :class:`bytes` object.
        prompt: Instruction sent alongside the audio.

    Returns:
        The model's text response.
    """
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Pass audio inline using a blob dict — no file upload, nothing stored.
    response = model.generate_content(
        [
            prompt,
            {"mime_type": "audio/wav", "data": audio_bytes},
        ]
    )
    return response.text


def run_conversation(turns: int = 3, record_seconds: int = _RECORD_SECONDS) -> None:
    """Run an interactive microphone conversation loop.

    Each turn records audio from the microphone, sends it to Gemini, and
    prints the response.  The audio is held only in memory and discarded
    after the API call — it is never written to disk.

    Args:
        turns: Number of conversation turns to run.
        record_seconds: How many seconds to record per turn.
    """
    print("Starting live audio conversation with Gemini (audio is never saved).\n")
    for turn in range(1, turns + 1):
        print(f"--- Turn {turn} ---")
        audio_bytes = _record_audio_to_memory(seconds=record_seconds)
        response_text = respond_to_audio(audio_bytes)
        print(f"Gemini: {response_text}\n")


# [END audio_conversation_non_recorded]


if __name__ == "__main__":
    run_conversation()

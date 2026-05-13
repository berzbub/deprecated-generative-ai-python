#!/usr/bin/env python3
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
"""Standalone interactive CLI for Google Generative AI (Gemini).

Run directly:
    python gemini_app.py

Or after installing the package:
    gemini

Set the GEMINI_API_KEY environment variable before running, or enter it
when prompted.
"""

from __future__ import annotations

import os
import sys
import textwrap

# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------

try:
    import google.generativeai as genai
except ImportError:
    print(
        "Error: google-generativeai is not installed.\n"
        "Install it with:  pip install google-generativeai",
        file=sys.stderr,
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "gemini-1.5-flash"
WRAP_WIDTH = 80

HELP_TEXT = textwrap.dedent(
    """\
    ┌─────────────────────────────────────────────────────────┐
    │               Gemini AI Assistant - Help                │
    └─────────────────────────────────────────────────────────┘
    Commands (type at the prompt):
      /help          Show this help message
      /new           Start a new conversation (clears history)
      /model         Show or change the active model
                       e.g.  /model gemini-1.5-pro
      /models        List all available generative models
      /file <path>   Upload a local file and attach it to next message
      /files         List files previously uploaded to the API
      /clear         Clear the terminal screen
      /quit  /exit   Exit the application

    Tips:
      • Just type your message and press Enter to chat.
      • Responses are streamed token-by-token.
      • Multi-line input: end a line with \\ to continue on the next line.
    """
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_api_key() -> None:
    """Configure the SDK with an API key from the environment or user prompt."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY environment variable found.")
        try:
            api_key = input("Enter your Gemini API key: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nNo API key provided. Exiting.")
            sys.exit(1)
    if not api_key:
        print("API key is required. Exiting.", file=sys.stderr)
        sys.exit(1)
    genai.configure(api_key=api_key)


def _clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _print_banner() -> None:
    print(
        textwrap.dedent(
            """\
            ╔═══════════════════════════════════════════╗
            ║       Gemini AI Assistant  (CLI)          ║
            ║  Type /help for available commands        ║
            ╚═══════════════════════════════════════════╝
            """
        )
    )


def _list_models() -> None:
    """Print all models that support generateContent."""
    print("Fetching available models …")
    try:
        found = False
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                print(f"  {m.name}")
                found = True
        if not found:
            print("  (no models returned — check your API key)")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"  Error listing models: {exc}", file=sys.stderr)


def _upload_file(path: str) -> genai.types.File | None:
    """Upload a local file to the Gemini Files API and return the File object."""
    path = path.strip()
    if not path:
        print("Usage: /file <path-to-file>")
        return None
    if not os.path.isfile(path):
        print(f"File not found: {path}", file=sys.stderr)
        return None
    print(f"Uploading {path} …", end=" ", flush=True)
    try:
        uploaded = genai.upload_file(path)
        print(f"done  ({uploaded.name})")
        return uploaded
    except Exception as exc:  # pylint: disable=broad-except
        print(f"\nUpload failed: {exc}", file=sys.stderr)
        return None


def _list_uploaded_files() -> None:
    """Print files previously uploaded to the Files API."""
    print("Fetching uploaded files …")
    try:
        files = list(genai.list_files())
        if not files:
            print("  (no files uploaded yet)")
        for f in files:
            print(f"  {f.name}  —  {f.display_name or '(no display name)'}")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"  Error listing files: {exc}", file=sys.stderr)


def _stream_response(chat: genai.ChatSession, message_parts: list) -> None:
    """Send a message and stream the response to stdout."""
    try:
        response = chat.send_message(message_parts, stream=True)
        for chunk in response:
            try:
                text = chunk.text
                if text:
                    print(text, end="", flush=True)
            except Exception:  # pylint: disable=broad-except
                # Chunk may carry only non-text parts (e.g. function calls)
                pass
        print()  # final newline
    except genai.types.StopCandidateException as exc:
        print(f"\n[Generation stopped: {exc}]")
    except genai.types.BlockedPromptException as exc:
        print(f"\n[Prompt blocked: {exc}]")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"\n[Error during generation: {exc}]", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main interactive loop
# ---------------------------------------------------------------------------


def run_cli() -> None:
    """Entry point for the interactive CLI assistant."""
    _setup_api_key()
    _print_banner()

    model_name = DEFAULT_MODEL
    model = genai.GenerativeModel(model_name)
    chat = model.start_chat()
    pending_files: list[genai.types.File] = []

    print(f"Model: {model_name}  (change with /model <name>)\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        # Handle multi-line continuation (trailing backslash)
        while user_input.endswith("\\"):
            user_input = user_input[:-1] + "\n"
            try:
                continuation = input("... ")
            except (EOFError, KeyboardInterrupt):
                continuation = ""
            user_input += continuation

        # ── Commands ─────────────────────────────────────────────────────
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd in ("/quit", "/exit"):
                print("Goodbye!")
                break

            elif cmd == "/help":
                print(HELP_TEXT)

            elif cmd == "/clear":
                _clear_screen()
                _print_banner()
                print(f"Model: {model_name}\n")

            elif cmd == "/new":
                chat = model.start_chat()
                pending_files.clear()
                print("[New conversation started]")

            elif cmd == "/models":
                _list_models()

            elif cmd == "/model":
                if not arg:
                    print(f"Current model: {model_name}")
                    print("Usage: /model <model-name>")
                else:
                    model_name = arg.strip()
                    if not model_name.startswith("models/"):
                        model_name = "models/" + model_name
                    try:
                        model = genai.GenerativeModel(model_name)
                        chat = model.start_chat()
                        pending_files.clear()
                        print(f"[Switched to model: {model_name}]")
                    except Exception as exc:  # pylint: disable=broad-except
                        print(f"Failed to load model '{model_name}': {exc}", file=sys.stderr)

            elif cmd == "/file":
                uploaded = _upload_file(arg)
                if uploaded is not None:
                    pending_files.append(uploaded)
                    print(
                        f"[File queued — it will be included with your next message. "
                        f"{len(pending_files)} file(s) pending]"
                    )

            elif cmd == "/files":
                _list_uploaded_files()

            else:
                print(f"Unknown command: {cmd}  (type /help for a list of commands)")

            continue

        # ── Regular message ───────────────────────────────────────────────
        message_parts: list = []
        if pending_files:
            message_parts.extend(pending_files)
            pending_files.clear()
        message_parts.append(user_input)

        print("Gemini: ", end="", flush=True)
        _stream_response(chat, message_parts)


# ---------------------------------------------------------------------------
# Script entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_cli()

# [Deprecated] Google AI Python SDK for the Gemini API

With Gemini 2.0, we took the chance to create a single unified SDK for all developers who want to use Google's GenAI models (Gemini, Veo, Imagen, etc). As part of that process, we took all of the feedback from this SDK and what developers like about other SDKs in the ecosystem to create the [Google Gen AI SDK](https://github.com/googleapis/python-genai). 

The full migration guide from the old SDK to new SDK is available in the [Gemini API docs](https://ai.google.dev/gemini-api/docs/migrate).

The Gemini API docs are fully updated to show examples of the new Google Gen AI SDK. We know how disruptive an SDK change can be and don't take this change lightly, but our goal is to create an extremely simple and clear path for developers to build with our models so it felt necessary to make this change.

Thank you for building with Gemini and [let us know](https://discuss.ai.google.dev/c/gemini-api/4) if you need any help!

**Please be advised that this repository is now considered legacy.** For the latest features, performance improvements, and active development, we strongly recommend migrating to the official **[Google Generative AI SDK for Python](https://github.com/googleapis/python-genai)**.

**Support Plan for this Repository:**

*   **Limited Maintenance:** Development is now restricted to **critical bug fixes only**. No new features will be added.
*   **Purpose:** This limited support aims to provide stability for users while they transition to the new SDK.
*   **End-of-Life Date:** All support for this repository (including bug fixes) will permanently end on **August 31st, 2025**.

We encourage all users to begin planning their migration to the [Google Generative AI SDK](https://github.com/googleapis/python-genai) to ensure continued access to the latest capabilities and support.

<!-- 
[START update]
# With Gemini 2 we're launching a new SDK. See the following doc for details.
# https://ai.google.dev/gemini-api/docs/migrate
[END update]
 -->

## Using with Termux on Android

[Termux](https://termux.dev/) is a free and open-source Android terminal emulator that lets you run a Linux environment directly on your Android device — no root required. You can use the Gemini API Python SDK inside Termux.

> **Tip:** For new projects, follow these same steps but install the new [Google Gen AI SDK](https://github.com/googleapis/python-genai) (`pip install google-genai`) instead, and import it as `import google.genai as genai`.

### 1 — Install Termux

Install Termux from [F-Droid](https://f-droid.org/en/packages/com.termux/) (recommended) or from the [Termux GitHub releases](https://github.com/termux/termux-app/releases). The Google Play version is outdated and no longer maintained.

### 2 — Update packages and install Python

Open Termux and run:

```bash
pkg update && pkg upgrade -y
pkg install python -y
```

### 3 — Install the SDK

```bash
pip install google-generativeai
```

### 4 — Set your API key

Get a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey), then export it in Termux:

```bash
export GEMINI_API_KEY="YOUR_API_KEY_HERE"
```

To make the key persist across sessions, add the line above to `~/.bashrc` or `~/.profile`.

### 5 — Run a quick test

```bash
python - <<'EOF'
import google.generativeai as genai
import os

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")
response = model.generate_content("Say hello from Termux!")
print(response.text)
EOF
```

### 6 — Interactive chat session

```bash
python - <<'EOF'
import google.generativeai as genai
import os

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")
chat = model.start_chat()

print("Gemini chat — type 'exit' to quit.\n")
while True:
    user_input = input("You: ")
    if user_input.strip().lower() == "exit":
        break
    response = chat.send_message(user_input)
    print(f"Gemini: {response.text}\n")
EOF
```

### Tips

- If you see `ModuleNotFoundError`, run `pip install google-generativeai` again inside Termux.
- Install `nano` or `vim` (`pkg install nano`) to edit Python scripts directly in Termux.
- Use `pkg install git` to clone repositories inside Termux.

# AI-Powered Hearing Aid App (Swift)

A SwiftUI iOS application that uses Apple's Speech Recognition framework to
transcribe real-time microphone audio and the **Google Gemini API** to provide
context-aware AI insights — making spoken conversations more accessible for
people who are hard of hearing.

## Features

| Feature | Description |
|---|---|
| 🎙️ Live transcription | Continuous speech-to-text via `SFSpeechRecognizer` |
| 🤖 AI insight | Gemini analyzes each utterance and surfaces clarifications, emotional tone, and urgency flags |
| 🕐 Session history | Keeps a scrollable log of every transcription + AI response pair |
| ♿ Accessibility | VoiceOver labels on all interactive controls |
| 🔒 On-device first | Speech recognition can run fully on-device; only final text is sent to Gemini |

## Architecture

```
HearingAidApp (SwiftUI @main)
│
├── ContentView              ← SwiftUI view layer
│   └── HearingAidViewModel  ← @MainActor ObservableObject, orchestrates everything
│       ├── AudioCaptureManager     ← AVAudioEngine microphone tap
│       ├── SpeechRecognitionManager ← SFSpeechRecognizer wrapper
│       └── GeminiAIService         ← google/generative-ai-swift Chat session
```

## Requirements

- Xcode 15+
- iOS 16+ or macOS 13+
- A [Gemini API key](https://aistudio.google.com/app/apikey)

## Getting Started

### 1. Clone and open the package

```bash
git clone https://github.com/google/generative-ai-python.git
cd generative-ai-python/samples/swift/HearingAidApp
open Package.swift   # opens in Xcode
```

### 2. Add your API key

The app reads the key from the `GEMINI_API_KEY` environment variable.

**In Xcode** — Edit Scheme → Run → Arguments → Environment Variables → add:
```
GEMINI_API_KEY = <your-key>
```

**From the command line:**
```bash
export GEMINI_API_KEY="<your-key>"
```

> ⚠️ **Never hard-code API keys in source code.** For production, store the key
> in the iOS Keychain or retrieve it from a secure backend.

### 3. Add required Info.plist entries

Add these keys to your app target's `Info.plist` (required for microphone and
speech access):

```xml
<key>NSMicrophoneUsageDescription</key>
<string>The hearing-aid app needs microphone access to capture speech.</string>

<key>NSSpeechRecognitionUsageDescription</key>
<string>The hearing-aid app uses on-device speech recognition to transcribe audio.</string>
```

### 4. Run on a physical device

Speech recognition requires a real device (iOS simulator has limited support).

```bash
xcodebuild -scheme HearingAidApp -destination 'platform=iOS,name=My iPhone' run
```

## How It Works

1. **Audio capture** — `AVAudioEngine` taps the built-in microphone and streams
   raw PCM buffers.
2. **Speech recognition** — Buffers are fed into `SFSpeechAudioBufferRecognitionRequest`.
   Partial results update the live transcription label instantly.
3. **AI analysis** — On each final speech result the transcription is sent to
   Gemini via a multi-turn `Chat` session.  The system prompt instructs the model
   to act as a hearing-aid assistant: summarizing content, flagging urgency, and
   noting speaker tone.
4. **Display** — The SwiftUI view observes the `@Published` properties on
   `HearingAidViewModel` and re-renders automatically.

## Customisation

| File | What to change |
|---|---|
| `GeminiAIService.swift` | Swap the model name, adjust the system prompt |
| `SpeechRecognitionManager.swift` | Change locale, enable `requiresOnDeviceRecognition` |
| `ContentView.swift` | Adjust UI layout and colour scheme |

## License

Apache 2.0 — see [LICENSE](../../../../LICENSE).

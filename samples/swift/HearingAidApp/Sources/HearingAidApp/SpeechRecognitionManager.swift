// Copyright 2024 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import Speech

/// Wraps `SFSpeechRecognizer` for continuous, on-device speech-to-text.
///
/// Recognized text is delivered incrementally via the ``onPartialResult``
/// and ``onFinalResult`` callbacks, making it straightforward to feed into
/// a downstream AI pipeline.
@MainActor
final class SpeechRecognitionManager: NSObject, ObservableObject {

    // MARK: - Public state

    @Published private(set) var isRecognizing = false
    @Published private(set) var currentTranscription = ""

    /// Called each time the recognizer emits a partial hypothesis.
    var onPartialResult: ((String) -> Void)?
    /// Called when the recognizer produces a final, stable result.
    var onFinalResult: ((String) -> Void)?

    // MARK: - Private

    private let recognizer: SFSpeechRecognizer?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?

    // MARK: - Init

    override init() {
        recognizer = SFSpeechRecognizer(locale: .current)
        super.init()
        recognizer?.delegate = self
    }

    // MARK: - Permissions

    /// Requests speech-recognition authorization from the user.
    func requestPermission() async -> Bool {
        await withCheckedContinuation { continuation in
            SFSpeechRecognizer.requestAuthorization { status in
                continuation.resume(returning: status == .authorized)
            }
        }
    }

    // MARK: - Recognition lifecycle

    /// Prepares a new recognition request ready to accept audio buffers.
    func startRecognition() throws {
        cancelCurrentTask()

        guard let recognizer, recognizer.isAvailable else {
            throw SpeechError.recognizerUnavailable
        }

        let request = SFSpeechAudioBufferRecognitionRequest()
        request.shouldReportPartialResults = true
        request.requiresOnDeviceRecognition = false
        recognitionRequest = request

        recognitionTask = recognizer.recognitionTask(with: request) { [weak self] result, error in
            guard let self else { return }
            Task { @MainActor in
                if let result {
                    let text = result.bestTranscription.formattedString
                    self.currentTranscription = text
                    if result.isFinal {
                        self.onFinalResult?(text)
                        self.isRecognizing = false
                    } else {
                        self.onPartialResult?(text)
                    }
                }
                if let error {
                    self.handleRecognitionError(error)
                }
            }
        }

        isRecognizing = true
    }

    /// Appends an audio buffer from `AudioCaptureManager` to the request.
    func append(buffer: AVAudioPCMBuffer) {
        recognitionRequest?.append(buffer)
    }

    /// Signals end of audio and waits for the final result.
    func finishRecognition() {
        recognitionRequest?.endAudio()
    }

    /// Immediately cancels any in-flight recognition task.
    func stopRecognition() {
        cancelCurrentTask()
        isRecognizing = false
    }

    // MARK: - Helpers

    private func cancelCurrentTask() {
        recognitionTask?.cancel()
        recognitionTask = nil
        recognitionRequest = nil
        currentTranscription = ""
    }

    private func handleRecognitionError(_ error: Error) {
        let nsError = error as NSError
        // Code 1110 is "no speech detected" – treat as a normal end-of-utterance.
        guard nsError.code != 1110 else { return }
        isRecognizing = false
    }
}

// MARK: - SFSpeechRecognizerDelegate

extension SpeechRecognitionManager: SFSpeechRecognizerDelegate {
    nonisolated func speechRecognizer(
        _ speechRecognizer: SFSpeechRecognizer,
        availabilityDidChange available: Bool
    ) {
        Task { @MainActor in
            if !available {
                isRecognizing = false
            }
        }
    }
}

// MARK: - Errors

enum SpeechError: LocalizedError {
    case recognizerUnavailable

    var errorDescription: String? {
        switch self {
        case .recognizerUnavailable:
            return "Speech recognizer is not available on this device or locale."
        }
    }
}

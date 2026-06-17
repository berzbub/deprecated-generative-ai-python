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

import AVFoundation
import Combine
import Foundation

/// Binds together audio capture, speech recognition, and Gemini AI analysis.
///
/// `HearingAidViewModel` is the single source of truth for the SwiftUI layer.
/// It orchestrates the ``AudioCaptureManager`` and ``SpeechRecognitionManager``
/// then forwards completed transcriptions to ``GeminiAIService``.
@MainActor
final class HearingAidViewModel: ObservableObject {

    // MARK: - Published state (consumed by views)

    @Published var liveTranscription = ""
    @Published var aiInsight = ""
    @Published var isListening = false
    @Published var isProcessingAI = false
    @Published var showError = false
    @Published var errorMessage = ""
    @Published private(set) var conversationHistory: [ConversationEntry] = []

    // MARK: - Dependencies

    private let audioCapture = AudioCaptureManager()
    private let speechManager = SpeechRecognitionManager()
    private let aiService: GeminiAIService

    // MARK: - Init

    init() {
        // Read the API key from the environment (set GEMINI_API_KEY before running).
        // In a production app consider using a secure keychain store instead.
        guard let apiKey = ProcessInfo.processInfo.environment["GEMINI_API_KEY"],
              !apiKey.isEmpty
        else {
            fatalError(
                """
                GEMINI_API_KEY environment variable is not set.
                Please set it before running the app:
                  export GEMINI_API_KEY=\"<your-key>\"
                Obtain a key from https://aistudio.google.com/app/apikey
                """
            )
        }
        aiService = GeminiAIService(apiKey: apiKey)
        wireCallbacks()
    }

    // MARK: - Permissions

    /// Requests microphone and speech-recognition permissions at startup.
    func requestPermissions() {
        Task {
            let micGranted = await audioCapture.requestPermission()
            let speechGranted = await speechManager.requestPermission()
            if !micGranted || !speechGranted {
                showError(
                    "Microphone and Speech Recognition access are required for the hearing-aid "
                    + "features. Please enable them in Settings."
                )
            }
        }
    }

    // MARK: - Listening lifecycle

    /// Toggles between actively listening and idle.
    func toggleListening() async {
        if isListening {
            await stopListening()
        } else {
            await startListening()
        }
    }

    private func startListening() async {
        do {
            try speechManager.startRecognition()
            try audioCapture.startCapture { [weak self] buffer in
                self?.speechManager.append(buffer: buffer)
            }
            isListening = true
            liveTranscription = ""
            aiInsight = ""
        } catch {
            showError(error.localizedDescription)
        }
    }

    private func stopListening() async {
        speechManager.finishRecognition()
        audioCapture.stopCapture()
        audioCapture.deactivateAudioSession()
        isListening = false

        // Request final AI analysis for any remaining partial transcription.
        let textToAnalyze = liveTranscription
        if !textToAnalyze.isEmpty {
            await runAIAnalysis(for: textToAnalyze)
        }
    }

    // MARK: - Callbacks

    private func wireCallbacks() {
        speechManager.onPartialResult = { [weak self] text in
            Task { @MainActor [weak self] in
                self?.liveTranscription = text
            }
        }

        speechManager.onFinalResult = { [weak self] text in
            Task { @MainActor [weak self] in
                guard let self else { return }
                self.liveTranscription = text
                await self.runAIAnalysis(for: text)
            }
        }
    }

    // MARK: - AI analysis

    private func runAIAnalysis(for transcription: String) async {
        guard !transcription.isEmpty else { return }
        isProcessingAI = true
        defer { isProcessingAI = false }

        do {
            let insight = try await aiService.analyzeTranscription(transcription)
            aiInsight = insight
            conversationHistory.insert(
                ConversationEntry(transcription: transcription, aiResponse: insight),
                at: 0
            )
        } catch {
            showError("AI analysis failed: \(error.localizedDescription)")
        }
    }

    // MARK: - Session management

    /// Clears the current session history and AI state.
    func clearSession() {
        liveTranscription = ""
        aiInsight = ""
        conversationHistory = []
        aiService.resetSession()
    }

    // MARK: - Error handling

    private func showError(_ message: String) {
        errorMessage = message
        showError = true
    }
}

// MARK: - Supporting types

/// A single round of transcription + AI response, stored in session history.
struct ConversationEntry: Identifiable {
    let id = UUID()
    let transcription: String
    let aiResponse: String
}

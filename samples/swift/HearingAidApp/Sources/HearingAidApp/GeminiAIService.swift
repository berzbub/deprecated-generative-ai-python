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

import GoogleGenerativeAI

/// Sends transcribed speech to the Gemini API and returns context-aware insights.
///
/// The service maintains a multi-turn Chat session so the model can refer to
/// the entire conversation history, enabling richer hearing-aid assistance (e.g.
/// "What did I just miss?", speaker identification cues, noise description).
final class GeminiAIService {

    // MARK: - Configuration

    /// The Gemini model powering the hearing-aid analysis.
    private static let modelName = "gemini-1.5-flash"

    /// System prompt that sets the model's persona as a hearing-aid assistant.
    private static let systemPrompt = """
        You are an AI-powered hearing aid assistant. Your role is to help someone
        who is hard of hearing by:
        1. Clarifying and summarizing spoken transcriptions so they are easy to read.
        2. Identifying important contextual cues (e.g. tone, emotion, speaker count).
        3. Flagging urgent or safety-critical words (e.g. fire alarm, help, emergency).
        4. Answering follow-up questions about what was said.
        5. Providing brief, clear responses suitable for quick reading on a small screen.
        Keep responses concise — three sentences or fewer unless the user asks for more detail.
        """

    // MARK: - Private

    private let model: GenerativeModel
    private var chat: Chat

    // MARK: - Init

    /// Creates a new service instance.
    ///
    /// - Parameter apiKey: Your Gemini API key.  Obtain one from
    ///   [Google AI Studio](https://aistudio.google.com/app/apikey).
    init(apiKey: String) {
        model = GenerativeModel(
            name: Self.modelName,
            apiKey: apiKey,
            systemInstruction: Self.systemPrompt
        )
        chat = model.startChat()
    }

    // MARK: - Public API

    /// Sends a transcription to the model and returns an AI-generated insight.
    ///
    /// The method is designed to be called from a Swift concurrency context.
    /// - Parameter transcription: The speech-to-text string to analyze.
    /// - Returns: A concise AI insight about the transcription.
    func analyzeTranscription(_ transcription: String) async throws -> String {
        let prompt = """
            The user's hearing aid just captured the following speech:
            \"\(transcription)\"

            Provide a helpful, concise insight for the hearing-aid user.
            """
        let response = try await chat.sendMessage(prompt)
        return response.text ?? "(No response)"
    }

    /// Sends a direct question from the user to the model.
    ///
    /// - Parameter question: Free-form user query (e.g. "What did I just miss?").
    /// - Returns: The model's answer.
    func ask(_ question: String) async throws -> String {
        let response = try await chat.sendMessage(question)
        return response.text ?? "(No response)"
    }

    /// Resets the conversation history, starting a fresh session.
    func resetSession() {
        chat = model.startChat()
    }
}

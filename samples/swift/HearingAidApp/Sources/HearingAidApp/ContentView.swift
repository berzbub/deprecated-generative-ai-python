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

import SwiftUI

/// Main entry-point view for the AI-powered hearing aid app.
///
/// Displays live transcription, AI-enhanced context, and audio controls.
struct ContentView: View {
    @StateObject private var viewModel = HearingAidViewModel()

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                statusBar
                ScrollView {
                    VStack(alignment: .leading, spacing: 16) {
                        transcriptionCard
                        if !viewModel.aiInsight.isEmpty {
                            aiInsightCard
                        }
                        if !viewModel.conversationHistory.isEmpty {
                            historyCard
                        }
                    }
                    .padding()
                }
                controlBar
            }
            .navigationTitle("AI Hearing Aid")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        viewModel.clearSession()
                    } label: {
                        Image(systemName: "trash")
                    }
                    .disabled(viewModel.isListening)
                }
            }
            .alert("Error", isPresented: $viewModel.showError) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(viewModel.errorMessage)
            }
        }
        .onAppear {
            viewModel.requestPermissions()
        }
    }

    // MARK: - Subviews

    private var statusBar: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(viewModel.isListening ? Color.red : Color.gray)
                .frame(width: 10, height: 10)
                .scaleEffect(viewModel.isListening ? 1.2 : 1.0)
                .animation(
                    viewModel.isListening
                        ? .easeInOut(duration: 0.6).repeatForever(autoreverses: true)
                        : .default,
                    value: viewModel.isListening
                )
            Text(viewModel.isListening ? "Listening…" : "Idle")
                .font(.caption)
                .foregroundStyle(.secondary)
            Spacer()
            if viewModel.isProcessingAI {
                ProgressView()
                    .scaleEffect(0.7)
                Text("AI thinking…")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
        .background(Color(uiColor: .systemGroupedBackground))
    }

    private var transcriptionCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("Live Transcription", systemImage: "waveform")
                .font(.headline)
            Text(
                viewModel.liveTranscription.isEmpty
                    ? "Start listening to see transcription here…"
                    : viewModel.liveTranscription
            )
            .font(.body)
            .foregroundStyle(viewModel.liveTranscription.isEmpty ? .secondary : .primary)
            .frame(maxWidth: .infinity, alignment: .leading)
            .animation(.easeInOut, value: viewModel.liveTranscription)
        }
        .padding()
        .background(Color(uiColor: .secondarySystemGroupedBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private var aiInsightCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("AI Insight", systemImage: "sparkles")
                .font(.headline)
                .foregroundStyle(.indigo)
            Text(viewModel.aiInsight)
                .font(.body)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding()
        .background(Color.indigo.opacity(0.08))
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.indigo.opacity(0.25), lineWidth: 1)
        )
    }

    private var historyCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("Session History", systemImage: "clock.arrow.circlepath")
                .font(.headline)
            ForEach(viewModel.conversationHistory.indices, id: \.self) { index in
                let entry = viewModel.conversationHistory[index]
                VStack(alignment: .leading, spacing: 4) {
                    Text(entry.transcription)
                        .font(.subheadline)
                        .foregroundStyle(.primary)
                    Text(entry.aiResponse)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding(.vertical, 4)
                if index < viewModel.conversationHistory.count - 1 {
                    Divider()
                }
            }
        }
        .padding()
        .background(Color(uiColor: .secondarySystemGroupedBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private var controlBar: some View {
        HStack(spacing: 24) {
            Spacer()
            Button {
                Task { await viewModel.toggleListening() }
            } label: {
                ZStack {
                    Circle()
                        .fill(viewModel.isListening ? Color.red : Color.accentColor)
                        .frame(width: 72, height: 72)
                        .shadow(radius: viewModel.isListening ? 8 : 4)
                    Image(systemName: viewModel.isListening ? "stop.fill" : "mic.fill")
                        .font(.title)
                        .foregroundStyle(.white)
                }
            }
            .accessibilityLabel(viewModel.isListening ? "Stop listening" : "Start listening")
            Spacer()
        }
        .padding(.vertical, 20)
        .background(Color(uiColor: .systemGroupedBackground))
    }
}

#Preview {
    ContentView()
}

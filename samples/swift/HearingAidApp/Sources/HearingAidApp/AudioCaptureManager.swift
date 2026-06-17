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

/// Manages audio session configuration and microphone capture.
///
/// `AudioCaptureManager` owns the `AVAudioEngine` graph responsible for
/// tapping the microphone input.  Call ``startCapture(onBuffer:)`` to begin
/// receiving raw PCM buffers and ``stopCapture()`` to tear everything down.
@MainActor
final class AudioCaptureManager: NSObject, ObservableObject {

    // MARK: - Public state

    /// Whether the audio engine is currently running.
    @Published private(set) var isCapturing = false

    // MARK: - Private

    private let audioEngine = AVAudioEngine()
    private var inputNode: AVAudioInputNode { audioEngine.inputNode }
    private var bufferCallback: ((AVAudioPCMBuffer) -> Void)?

    // MARK: - Permissions

    /// Requests microphone access if not already granted.
    func requestPermission() async -> Bool {
        switch AVAudioApplication.shared.recordingPermission {
        case .granted:
            return true
        case .denied:
            return false
        case .undetermined:
            return await AVAudioApplication.requestRecordPermission()
        @unknown default:
            return false
        }
    }

    // MARK: - Capture lifecycle

    /// Installs a tap on the input node and starts the audio engine.
    ///
    /// - Parameter onBuffer: Closure invoked on each incoming PCM buffer.
    func startCapture(onBuffer: @escaping (AVAudioPCMBuffer) -> Void) throws {
        guard !audioEngine.isRunning else { return }

        bufferCallback = onBuffer

        let inputFormat = inputNode.outputFormat(forBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 4096, format: inputFormat) {
            [weak self] buffer, _ in
            self?.bufferCallback?(buffer)
        }

        try configureAudioSession()
        try audioEngine.start()
        isCapturing = true
    }

    /// Stops the audio engine and removes the microphone tap.
    func stopCapture() {
        guard audioEngine.isRunning else { return }
        inputNode.removeTap(onBus: 0)
        audioEngine.stop()
        isCapturing = false
    }

    // MARK: - Audio session

    private func configureAudioSession() throws {
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.record, mode: .measurement, options: .duckOthers)
        try session.setActive(true, options: .notifyOthersOnDeactivation)
    }

    /// Deactivates the shared `AVAudioSession` after capture ends.
    func deactivateAudioSession() {
        try? AVAudioSession.sharedInstance().setActive(false,
                                                       options: .notifyOthersOnDeactivation)
    }
}

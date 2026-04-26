// swift-tools-version: 5.9
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

import PackageDescription

let package = Package(
    name: "HearingAidApp",
    platforms: [
        .iOS(.v16),
        .macOS(.v13),
    ],
    products: [
        .executable(name: "HearingAidApp", targets: ["HearingAidApp"]),
    ],
    dependencies: [
        .package(
            url: "https://github.com/google/generative-ai-swift",
            from: "0.5.6"
        ),
    ],
    targets: [
        .executableTarget(
            name: "HearingAidApp",
            dependencies: [
                .product(name: "GoogleGenerativeAI", package: "generative-ai-swift"),
            ],
            path: "Sources/HearingAidApp",
            swiftSettings: [
                .enableExperimentalFeature("StrictConcurrency"),
            ]
        ),
    ]
)

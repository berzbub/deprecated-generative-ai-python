# -*- coding: utf-8 -*-
# Copyright 2023 Google LLC
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
"""DJI Go 4 app integration scaffolding with AI training and adaptive simulation."""

from __future__ import annotations

import dataclasses
import math
from typing import Any

EXCLUDED_DOMINATING_FEATURES = (
    "autonomous-target-prioritization",
    "forceful-pursuit-mode",
    "unbounded-operator-override",
)

LICENSE_CHANGE_REASON = (
    "No repository license change is required. This module remains Apache-2.0 so DJI "
    "integration scaffolding can be shared while avoiding vendor SDK redistribution assumptions."
)


@dataclasses.dataclass
class TrainingModule:
    name: str
    objective: str
    application: str
    reality: str
    material: str


@dataclasses.dataclass
class DJIIntegrationApp:
    aircraft_alias: str = "Mavic Pro"
    companion_app: str = "DJI Go 4"
    ai_framework: str = "gemini-preserved-adaptive-framework"
    excluded_features: tuple[str, ...] = EXCLUDED_DOMINATING_FEATURES
    simulation_state: dict[str, Any] = dataclasses.field(default_factory=dict)
    training_modules: list[TrainingModule] = dataclasses.field(default_factory=list)

    def register_training_module(self, module: TrainingModule) -> None:
        self.training_modules.append(module)

    def adjust_simulation(self, application: str, reality: str, material: str) -> dict[str, Any]:
        scenario = {
            "application": application,
            "reality": reality,
            "material": material,
            "aircraft_alias": self.aircraft_alias,
            "companion_app": self.companion_app,
            "framework": self.ai_framework,
            "excluded_features": list(self.excluded_features),
        }
        self.simulation_state = scenario
        return scenario

    def self_adjust(self, feedback_score: float) -> dict[str, Any]:
        if not isinstance(feedback_score, (int, float)) or not math.isfinite(feedback_score):
            raise ValueError("feedback_score must be a finite number between 0.0 and 1.0")
        if feedback_score < 0.0 or feedback_score > 1.0:
            raise ValueError("feedback_score must be between 0.0 and 1.0")

        if feedback_score < 0.5:
            adaptation = "increase-guidance"
        elif feedback_score > 0.85:
            adaptation = "increase-autonomy"
        else:
            adaptation = "maintain-balance"
        self.simulation_state["adaptation"] = adaptation
        self.simulation_state["feedback_score"] = feedback_score
        return self.simulation_state


def create_dji_app(aircraft_alias: str = "Mavic Pro") -> DJIIntegrationApp:
    app = DJIIntegrationApp(aircraft_alias=aircraft_alias)
    app.register_training_module(
        TrainingModule(
            name="baseline-flight-training",
            objective="integrated-ai-training-modules",
            application="survey",
            reality="mixed",
            material="composite",
        )
    )
    app.adjust_simulation(application="survey", reality="mixed", material="composite")
    return app

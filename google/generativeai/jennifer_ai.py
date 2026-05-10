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
"""JenniferAI scaffolding."""

from __future__ import annotations

import dataclasses
from typing import Protocol


@dataclasses.dataclass(frozen=True)
class Contributor:
    name: str
    role: str


DEFAULT_CONTRIBUTORS: tuple[Contributor, ...] = (
    Contributor(name="Jose Prudencio Castillo Jr.", role="Lead Architect / VP Identity Formation"),
    Contributor(name="Jennifer", role="Analytical Intelligence / Innovative Catalyst"),
    Contributor(name="The Sebastinian Community", role="Historical & Spiritual Foundation"),
)


class JenniferAI:
    version = "2026.5.0"
    contributors = list(DEFAULT_CONTRIBUTORS)

    def partition_video_script(self, script: str) -> list[str]:
        parts = script.split(".")
        return [part.strip() for part in parts if part.strip()]

    def partitionVideoScript(self, script: str) -> list[str]:
        return self.partition_video_script(script)

    def monitor_financial_flow(
        self, revenue: float, destination: str = "San Sebastian College / Steel Basilica"
    ) -> None:
        print(f"Analyzing revenue flow of {revenue} to {destination}.")

    def monitorFinancialFlow(
        self, revenue: float, destination: str = "San Sebastian College / Steel Basilica"
    ) -> None:
        self.monitor_financial_flow(revenue=revenue, destination=destination)


class StudentBodyAppDelegate(Protocol):
    def didUpdateNCAAStandings(self, standings: str) -> None: ...

    def requestUrgentApproval(self, action: str) -> None: ...

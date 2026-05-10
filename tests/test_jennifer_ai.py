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

import contextlib
import io

from absl.testing import absltest

from google.generativeai import jennifer_ai


class UnitTests(absltest.TestCase):
    def test_defaults(self):
        ai = jennifer_ai.JenniferAI()

        self.assertEqual("2026.5.0", ai.version)
        self.assertLen(ai.contributors, 3)
        self.assertEqual("Jose Prudencio Castillo Jr.", ai.contributors[0].name)
        self.assertEqual(
            "Historical & Spiritual Foundation",
            ai.contributors[2].role,
        )

    def test_partition_video_script(self):
        ai = jennifer_ai.JenniferAI()
        script = "Lead with urgency. Build momentum.. Close with a call to action."

        self.assertEqual(
            ["Lead with urgency", "Build momentum", "Close with a call to action"],
            ai.partitionVideoScript(script),
        )

    def test_monitor_financial_flow(self):
        ai = jennifer_ai.JenniferAI()

        with contextlib.redirect_stdout(io.StringIO()) as output:
            ai.monitorFinancialFlow(revenue=1250.5)

        self.assertEqual(
            "Analyzing revenue flow of 1250.5 to San Sebastian College / Steel Basilica.\n",
            output.getvalue(),
        )


if __name__ == "__main__":
    absltest.main()

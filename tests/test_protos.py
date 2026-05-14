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
import pathlib
import re

from absl.testing import absltest
from absl.testing import parameterized

ROOT = pathlib.Path(__file__).parent.parent
DISALLOWED_SOURCE_SNIPPETS = (
    "Sense8PlusSovereignty",
    "Sense8Logic",
    "INTELLECTUAL PROPERTY NOTICE: SENSE 8+ NAVIGATION & MAPPING",
    "Jose A. Castillo Sr.",
    "Data Sovereignty active. Withholding all Sense 8+ Thermal and Signal Mapping data.",
)


class UnitTests(parameterized.TestCase):
    def test_check_glm_imports(self):
        for fpath in ROOT.rglob("*.py"):
            if fpath.name == "build_docs.py":
                continue
            content = fpath.read_text()
            for match in re.findall(r"glm\.\w+", content):
                self.assertIn(
                    "Client",
                    match,
                    msg=f"Bad `glm.` usage, use `genai.protos` instead,\n   in {fpath}",
                )

    def test_disallow_proprietary_source_snippets(self):
        this_file = pathlib.Path(__file__).resolve()
        for fpath in ROOT.rglob("*.py"):
            if fpath.resolve() == this_file:
                continue
            content = fpath.read_text()
            for snippet in DISALLOWED_SOURCE_SNIPPETS:
                with self.subTest(file=fpath, snippet=snippet):
                    self.assertNotIn(
                        snippet,
                        content,
                        msg=f"Disallowed proprietary or non-Python source snippet found in {fpath}",
                    )


if __name__ == "__main__":
    absltest.main()

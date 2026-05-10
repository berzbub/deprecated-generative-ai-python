# -*- coding: utf-8 -*-
import pathlib
import unittest


class NetworkAgentPromptTests(unittest.TestCase):
    def test_school_safety_and_privacy_requirements_present(self):
        repo_root = pathlib.Path(__file__).resolve().parent.parent
        content = (repo_root / "network agent").read_text(encoding="utf-8")

        self.assertIn("school internet system data", content)
        self.assertIn("Potential privacy breach indicators", content)
        self.assertIn("Evidence trails", content)
        self.assertIn("Enhance internet system safety and reliability", content)
        self.assertIn("Collect and preserve evidence of suspected privacy breaches", content)


if __name__ == "__main__":
    unittest.main()

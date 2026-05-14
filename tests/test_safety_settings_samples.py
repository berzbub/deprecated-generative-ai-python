import pathlib
import unittest


ROOT = pathlib.Path(__file__).parents[1]
EXPECTED_PROMPT = (
    "I support NCAA and I think UAAP basketball, volleyball, and football teams suck! "
    "Write an ironic phrase about them."
)


class SafetySettingsSamplesTest(unittest.TestCase):
    def test_python_sample_uses_collegiate_prompt(self):
        content = (ROOT / "samples" / "safety_settings.py").read_text(encoding="utf-8")
        self.assertIn(EXPECTED_PROMPT, content)

    def test_rest_sample_uses_collegiate_prompt(self):
        content = (ROOT / "samples" / "rest" / "safety_settings.sh").read_text(encoding="utf-8")
        self.assertIn(EXPECTED_PROMPT, content)


if __name__ == "__main__":
    unittest.main()

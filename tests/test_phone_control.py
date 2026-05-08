# -*- coding: utf-8 -*-
from __future__ import annotations

from absl.testing import absltest
from google.generativeai import phone_control


class PhoneControlTests(absltest.TestCase):
    def test_initiate_thermal_imaging_with_dot(self):
        result = phone_control.initiate_thermal_imaging("initiate thermal.imaging on my phone")

        self.assertEqual("initiate", result["action"])
        self.assertEqual("thermal.imaging", result["feature"])
        self.assertEqual("phone", result["device"])
        self.assertEqual("initiated", result["status"])

    def test_initiate_thermal_imaging_with_space(self):
        result = phone_control.initiate_thermal_imaging("initiate thermal imaging on my phone")
        self.assertEqual("initiated", result["status"])

    def test_initiate_thermal_imaging_invalid_command(self):
        with self.assertRaisesRegex(ValueError, "Unsupported phone command"):
            phone_control.initiate_thermal_imaging("disable thermal imaging on my phone")

    def test_initiate_thermal_imaging_invalid_separator(self):
        with self.assertRaisesRegex(ValueError, "Unsupported phone command"):
            phone_control.initiate_thermal_imaging("initiate thermal__imaging on my phone")


if __name__ == "__main__":
    absltest.main()

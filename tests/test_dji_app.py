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

from absl.testing import absltest

from google.generativeai import dji_app


class UnitTests(absltest.TestCase):
    def test_create_dji_app_defaults(self):
        app = dji_app.create_dji_app()

        self.assertEqual("Mavic Pro", app.aircraft_alias)
        self.assertIn("autonomous-target-prioritization", app.excluded_features)
        self.assertLen(app.training_modules, 1)
        self.assertEqual("survey", app.simulation_state["application"])

    def test_simulation_adjustment_supports_custom_alias(self):
        app = dji_app.create_dji_app(aircraft_alias="Jennifer-Unique")
        state = app.adjust_simulation(
            application="inspection", reality="digital-twin", material="carbon-fiber"
        )

        self.assertEqual("Jennifer-Unique", state["aircraft_alias"])
        self.assertEqual("digital-twin", state["reality"])
        self.assertEqual("carbon-fiber", state["material"])

    def test_self_adjust_sets_adaptation(self):
        app = dji_app.create_dji_app()

        low_feedback = app.self_adjust(0.3)
        self.assertEqual("increase-guidance", low_feedback["adaptation"])

        high_feedback = app.self_adjust(0.92)
        self.assertEqual("increase-autonomy", high_feedback["adaptation"])

    def test_license_change_reason_is_explicit(self):
        self.assertIn("No repository license change is required", dji_app.LICENSE_CHANGE_REASON)

    def test_self_adjust_rejects_out_of_range_feedback(self):
        app = dji_app.create_dji_app()
        with self.assertRaises(ValueError):
            app.self_adjust(1.1)

    def test_personalize_school_lock_screen(self):
        app = dji_app.create_dji_app()

        lock_screen = app.personalize_school_lock_screen(
            school_name="North Valley School",
            greeting="Welcome back, musicians!",
            background_theme="sunrise-stage",
        )

        self.assertEqual("North Valley School", lock_screen["school_name"])
        self.assertEqual("Welcome back, musicians!", lock_screen["greeting"])
        self.assertEqual("sunrise-stage", app.school_lock_screen_config["background_theme"])

    def test_ad_requests_support_product_campaigns(self):
        app = dji_app.create_dji_app()

        ad = app.submit_ad_request(
            sponsor_name="Echo Audio",
            ad_copy="Now offering student recording kits.",
            product_name="EchoMix Junior",
        )

        self.assertEqual("EchoMix Junior", ad.product_name)
        self.assertEqual(len(app.advertisement_board), 1)

    def test_internet_radio_station_supports_inter_school_hosting(self):
        app = dji_app.create_dji_app()

        station = app.configure_internet_radio_station(frequency="101.7 FM")

        self.assertEqual("School of Rock", station.station_name)
        self.assertEqual("101.7 FM", station.frequency)
        self.assertEqual("inter-school", station.hosting_scope)


if __name__ == "__main__":
    absltest.main()

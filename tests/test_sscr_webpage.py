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

from google.generativeai import sscr_webpage
from google.generativeai.sscr_webpage import PageSection, SSCRWebpage


class SSCRWebpageTests(absltest.TestCase):
    def test_create_sscr_webpage_defaults(self):
        page = sscr_webpage.create_sscr_webpage()

        self.assertEqual("SSCR Webpage", page.title)
        self.assertLen(page.sections, 1)
        self.assertEqual("welcome", page.sections[0].section_id)
        self.assertEqual("Welcome", page.sections[0].title)

    def test_create_sscr_webpage_custom_title(self):
        page = sscr_webpage.create_sscr_webpage(title="My Custom Page")

        self.assertEqual("My Custom Page", page.title)

    def test_add_section_appends_to_sections(self):
        page = SSCRWebpage(title="Test Page")
        section = PageSection(title="Intro", content="Hello world.", section_id="intro")
        page.add_section(section)

        self.assertLen(page.sections, 1)
        self.assertEqual("Intro", page.sections[0].title)

    def test_get_section_by_id_returns_matching_section(self):
        page = sscr_webpage.create_sscr_webpage()
        page.add_section(
            PageSection(title="Details", content="Some details.", section_id="details")
        )

        found = page.get_section_by_id("details")
        self.assertIsNotNone(found)
        self.assertEqual("Details", found.title)

    def test_get_section_by_id_returns_none_for_missing_id(self):
        page = sscr_webpage.create_sscr_webpage()

        self.assertIsNone(page.get_section_by_id("nonexistent"))

    def test_render_html_contains_title(self):
        page = SSCRWebpage(title="Hello Page")
        rendered = page.render_html()

        self.assertIn("<title>Hello Page</title>", rendered)
        self.assertIn("<h1>Hello Page</h1>", rendered)

    def test_render_html_contains_sections(self):
        page = SSCRWebpage(title="My Page")
        page.add_section(PageSection(title="Sec One", content="Content A.", section_id="s1"))
        rendered = page.render_html()

        self.assertIn('<section id="s1">', rendered)
        self.assertIn("<h2>Sec One</h2>", rendered)
        self.assertIn("<p>Content A.</p>", rendered)

    def test_render_html_escapes_special_characters(self):
        page = SSCRWebpage(title="<script>alert('xss')</script>")
        rendered = page.render_html()

        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)

    def test_render_html_section_without_id_has_no_id_attribute(self):
        page = SSCRWebpage(title="No ID Page")
        page.add_section(PageSection(title="Anon", content="No id here."))
        rendered = page.render_html()

        self.assertIn("<section>", rendered)
        self.assertNotIn('id=""', rendered)


if __name__ == "__main__":
    absltest.main()

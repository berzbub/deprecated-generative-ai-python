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
"""SSCR (Simple Structured Content Renderer) webpage module."""

from __future__ import annotations

import dataclasses
import html
from typing import Any, Optional


@dataclasses.dataclass
class PageSection:
    title: str
    content: str
    section_id: str = ""


@dataclasses.dataclass
class SSCRWebpage:
    title: str
    sections: list[PageSection] = dataclasses.field(default_factory=list)
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)

    def add_section(self, section: PageSection) -> None:
        """Append a section to the webpage."""
        self.sections.append(section)

    def get_section_by_id(self, section_id: str) -> Optional[PageSection]:
        """Return the first section matching *section_id*, or None."""
        for section in self.sections:
            if section.section_id == section_id:
                return section
        return None

    def render_html(self) -> str:
        """Render the webpage as an HTML string."""
        escaped_title = html.escape(self.title)
        body_parts: list[str] = []
        for section in self.sections:
            id_attr = f' id="{html.escape(section.section_id)}"' if section.section_id else ""
            body_parts.append(
                f"<section{id_attr}>"
                f"<h2>{html.escape(section.title)}</h2>"
                f"<p>{html.escape(section.content)}</p>"
                f"</section>"
            )
        body = "\n".join(body_parts)
        return (
            f"<!DOCTYPE html>"
            f"<html><head><title>{escaped_title}</title></head>"
            f"<body><h1>{escaped_title}</h1>{body}</body></html>"
        )


def create_sscr_webpage(title: str = "SSCR Webpage") -> SSCRWebpage:
    """Create an SSCRWebpage pre-populated with a default welcome section."""
    page = SSCRWebpage(title=title)
    page.add_section(
        PageSection(
            title="Welcome",
            content="This page was rendered by the Simple Structured Content Renderer.",
            section_id="welcome",
        )
    )
    return page

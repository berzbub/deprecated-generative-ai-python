"""Helpers for parsing phone control requests."""
from __future__ import annotations

import re

_THERMAL_IMAGING_PATTERN = re.compile(
    r"^\s*initiate\s+thermal(?:\.|\s+)imaging\s+on\s+my\s+phone\s*$",
    re.IGNORECASE,
)


def initiate_thermal_imaging(command: str) -> dict[str, str]:
    """Parses and validates thermal imaging phone requests."""
    if not isinstance(command, str):
        raise TypeError("command must be a string")

    if not _THERMAL_IMAGING_PATTERN.match(command):
        raise ValueError(f"Unsupported phone command: {command}")

    return {
        "action": "initiate",
        "feature": "thermal.imaging",
        "device": "phone",
        "status": "initiated",
    }

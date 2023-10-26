"""
JSON interaction, in case we want to change libraries or implementation.

All reading and writing used UTF-8 to ensure consistency between windows and unix.
"""

import json
from pathlib import Path


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _dump_json(data: dict, path: Path) -> None:
    with path.open("w", encoding="utf-8") as conf_file:
        json.dump(data, conf_file, sort_keys=True, indent=2)

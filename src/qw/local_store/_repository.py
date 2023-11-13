"""Configuration for local repository."""

import csv
from collections import defaultdict
from pathlib import Path

from jinja2 import Template
from loguru import logger

from qw.base import QwError


class RequirementComponents:
    """Handle customising components for requirements."""

    def __init__(self, qw_dir: Path):
        """Initialise requirements component."""
        self._component_file = qw_dir / "components.csv"
        self._initial_data = {
            "name": ["System"],
            "short_code": ["X"],
            "description": ["Whole system requirements"],
        }
        self._component_data = self._initial_data
        if self._component_file.exists():
            self._component_data = self._read_component_file(self._component_file)

    def _read_component_file(self, component_file) -> dict[str, list[str]]:
        with component_file.open("r") as handle:
            reader = csv.DictReader(handle)
            return self._parse_csv_data(reader)

    def _parse_csv_data(self, reader):
        output_data = defaultdict(list)
        for row in reader:
            for key in self._initial_data:
                try:
                    output_data[key].append(row[key].strip())
                except KeyError as error:
                    msg = (
                        f"Could not find {key} in component specification in"
                        f"{self._component_file}, please correct the file."
                    )
                    raise QwError(msg) from error
        return output_data

    def write_initial_data_if_not_exists(self):
        """Write initial data to file path if it doesn't exist already."""
        if self._component_file.exists():
            logger.info(
                "File already exists, not overwriting {path}",
                self._component_file,
            )
            return
        with self._component_file.open("w") as handle:
            writer = csv.writer(handle)
            writer.writerow(self._initial_data.keys())
            writer.writerows(zip(*self._initial_data.values(), strict=True))

    def update_requirements_template(
        self,
        template_source: Path,
        template_target: Path,
    ):
        """Update the requirements with the current component data."""
        template = Template(template_source.read_text())
        rendered_text = template.render(components=self._component_data["name"])
        template_target.write_text(rendered_text)

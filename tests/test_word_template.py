"""Replacing fields with data; high-level test."""
from itertools import chain
from tempfile import NamedTemporaryFile

import docx

from qw.cli import filter_data_references
from qw.mergedoc import load_template


def concat(list_of_lists):
    """Return flattened list of lists."""
    return list(chain.from_iterable(list_of_lists))


def test_replace_fields_with_data():
    """Test replacing fields through MergeData."""
    doc = load_template(
        "tests/resources/msword/DocSection_fields.docx",
    )
    with NamedTemporaryFile("w+b") as temp_file:
        data = {
            "software-component": [
                {
                    "id": 12,
                    "name": "twelve",
                    "description": "A one then a two is a twelve.",
                },
                {
                    "id": 25,
                    "name": "twenty-five",
                    "description": "A quarter century.",
                },
                {
                    "id": 100,
                    "name": "one-hundred",
                    "description": "The ton!",
                },
            ],
            "soup": [
                {
                    "id": 42,
                    "name": "python",
                    "description": "Dynamically typed language with batteries included.",
                },
                {
                    "id": 43,
                    "name": "qw",
                    "description": "Regulation checking and documentation tool.",
                },
            ],
        }
        doc.write(temp_file, data, filter_data_references)
        dx = docx.Document(temp_file.name)
        pwf_para = "Paragraph with fields {id} and {name}."
        expecteds = [
            "Heading One",
            *concat(
                [
                    [pwf_para.format(**sc), sc["description"]]
                    for sc in data["software-component"]
                ],
            ),
            "Heading Two",
            "Paragraph C",
            "Unordered list",
            "With some",
            "indents",
            "and more",
            "bullets",
            "Second heading two",
            *concat(
                [
                    ["Soup item {}".format(soup["name"]), soup["description"]]
                    for soup in data["soup"]
                ],
            ),
            "Another top-level heading",
            "Paragraph E",
            "",
        ]
        for p, expected in zip(dx.paragraphs, expecteds, strict=True):
            assert p.text == expected


def test_replace_hierarchical_fields_with_data():
    """Test replacing hierarchical fields through MergeData."""
    doc = load_template(
        "tests/resources/msword/DocSection_two_level_fields.docx",
    )
    with NamedTemporaryFile("w+b") as temp_file:
        data = {
            "requirement": [
                {
                    "internal_id": 1,
                    "title": "Display dose",
                    "description": "Put the dose on the screen.",
                    "user_need": "#101",
                },
                {
                    "internal_id": 2,
                    "title": "Update dose",
                    "description": "The dose on screen is updated as the controls are adjusted.",
                    "user_need": "#101",
                },
                {
                    "internal_id": 3,
                    "title": "Stop plunger",
                    "description": "Stop the plunger as the required dose is met",
                    "user_need": "#102",
                },
            ],
            "user-need": [
                {
                    "internal_id": 101,
                    "title": "Show the dose",
                    "description": "The user needs to be able to read out the dose on a screen.",
                },
                {
                    "internal_id": 102,
                    "title": "Deliver the dose",
                    "description": "The patient needs to receive the expected dose.",
                },
                {
                    "internal_id": 103,
                    "title": "Have a party",
                    "description": "The developers need a break.",
                },
            ],
            "design-output": [
                {
                    "internal_id": 24,
                    "title": "Screen rendering",
                    "description": "Dose rendered on the screen.",
                    "closing_issues": [1, 2],
                },
                {
                    "internal_id": 25,
                    "title": "Plunger control",
                    "description": "Drive plunger according to configuration.",
                    "closing_issues": [3],
                },
            ],
        }
        doc.write(temp_file, data, filter_data_references)
        dx = docx.Document(temp_file.name)
        expecteds = []
        for sysreq in data["user-need"]:
            sysr_id = sysreq["internal_id"]
            expecteds.extend(
                [
                    f"System requirement {sysr_id}",
                    sysreq["title"],
                    sysreq["description"],
                ],
            )
            softreqs = list(
                filter(
                    lambda soft: soft["user_need"] == f"#{sysr_id}",
                    data["requirement"],
                ),
            )
            expecteds.append("Implemented by the following software requirements:")
            if len(softreqs) == 0:
                expecteds.append("None.")
            else:
                for softreq in softreqs:
                    expecteds.extend(
                        [
                            "{internal_id}: {title}".format(**softreq),
                            softreq["description"],
                        ],
                    )

        for design_output in data["design-output"]:
            design_output_id = design_output["internal_id"]
            expecteds.extend(
                [
                    f"Pull request {design_output_id}: {design_output['title']}",
                    design_output["description"],
                ],
            )
            design_output_closings = design_output["closing_issues"]
            softreqs = list(
                filter(
                    lambda soft: soft["internal_id"] in design_output_closings,
                    data["requirement"],
                ),
            )
            expecteds.append("Implement the following software requirements:")
            if len(softreqs) == 0:
                expecteds.append("None.")
            else:
                for softreq in softreqs:
                    expecteds.extend(
                        [
                            "{internal_id}: {title}".format(**softreq),
                            softreq["description"],
                        ],
                    )

        expecteds.extend(
            [
                "Afterword",
                "Some text here.",
                "",
            ],
        )
        for p, expected in zip(dx.paragraphs, expecteds, strict=True):
            assert p.text == expected

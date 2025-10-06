import json
import os
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCHEMAS = ROOT / "contracts"


@pytest.mark.parametrize("schema_file", [
    "approval.schema.json",
    "draft.schema.json",
    "automation.schema.json",
    "note.schema.json",
    "core_memory.schema.json",
])
def test_schema_is_valid(schema_file: str):
    path = SCHEMAS / schema_file
    with open(path, "r") as f:
        schema = json.load(f)
    Draft202012Validator.check_schema(schema)

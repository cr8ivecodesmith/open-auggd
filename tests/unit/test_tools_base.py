"""Unit tests for tools/base.py — ToolResult response data model."""

import importlib
import json

_mod = importlib.import_module("open_auggd.tools.base")
ToolResult = _mod.ToolResult


# ---------------------------------------------------------------------------
# Success shape
# ---------------------------------------------------------------------------


def test_success_dict_contains_ok_and_data():
    result = ToolResult(ok=True, data={"phase": "explore"})
    d = result.to_dict()
    assert d["ok"] is True
    assert d["data"] == {"phase": "explore"}


def test_success_dict_has_no_error_keys():
    result = ToolResult(ok=True, data={"phase": "explore"})
    d = result.to_dict()
    assert "error" not in d
    assert "message" not in d
    assert "missing" not in d


def test_success_with_empty_data_still_emits_data_key():
    result = ToolResult(ok=True, data={})
    d = result.to_dict()
    assert "data" in d
    assert d["data"] == {}


# ---------------------------------------------------------------------------
# Failure shape
# ---------------------------------------------------------------------------


def test_failure_dict_contains_ok_error_message_missing():
    result = ToolResult(
        ok=False,
        error="MISSING_PLAN",
        message="No plan found.",
        missing=["iteration-log.json#1.plan"],
    )
    d = result.to_dict()
    assert d["ok"] is False
    assert d["error"] == "MISSING_PLAN"
    assert d["message"] == "No plan found."
    assert d["missing"] == ["iteration-log.json#1.plan"]


def test_failure_dict_has_no_data_key():
    result = ToolResult(ok=False, error="MISSING_PLAN", message="No plan found.")
    d = result.to_dict()
    assert "data" not in d


def test_failure_missing_defaults_to_empty_list():
    result = ToolResult(ok=False, error="NO_EXPLORE", message="Explore not started.")
    d = result.to_dict()
    assert d["missing"] == []


def test_failure_explicit_missing_list_preserved():
    paths = ["iteration-log.json#0.explore", "attachments/topic.md"]
    result = ToolResult(
        ok=False, error="VALIDATION_FAILED", message="Validation failed.", missing=paths
    )
    d = result.to_dict()
    assert d["missing"] == paths


# ---------------------------------------------------------------------------
# JSON serialization
# ---------------------------------------------------------------------------


def test_to_json_round_trips_success():
    result = ToolResult(ok=True, data={"status": "done"})
    assert json.loads(result.to_json()) == result.to_dict()


def test_to_json_round_trips_failure():
    result = ToolResult(ok=False, error="ERR", message="Something failed.", missing=["x"])
    assert json.loads(result.to_json()) == result.to_dict()


def test_to_json_is_valid_json_success():
    result = ToolResult(ok=True, data={"n": 1})
    parsed = json.loads(result.to_json())  # must not raise
    assert isinstance(parsed, dict)


def test_to_json_is_valid_json_failure():
    result = ToolResult(ok=False, error="E", message="m.")
    parsed = json.loads(result.to_json())  # must not raise
    assert isinstance(parsed, dict)


def test_success_to_json_has_no_error_keys():
    result = ToolResult(ok=True, data={})
    parsed = json.loads(result.to_json())
    assert "error" not in parsed
    assert "message" not in parsed
    assert "missing" not in parsed


def test_failure_to_json_has_no_data_key():
    result = ToolResult(ok=False, error="E", message="m.")
    parsed = json.loads(result.to_json())
    assert "data" not in parsed

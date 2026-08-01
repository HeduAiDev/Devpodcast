# tests/test_archivist.py
import json
import pytest
from scripts.archivist import log_entry, read_entries

def test_log_and_read(tmp_path):
    log_entry(tmp_path, "msg1", kind="note")
    log_entry(tmp_path, "msg2", kind="warning")
    entries = read_entries(tmp_path)
    assert len(entries) == 2
    assert entries[0]["msg"] == "msg1" and entries[0]["kind"] == "note"
    assert "at" in entries[0]

def test_read_entries_missing_file_returns_empty(tmp_path):
    assert read_entries(tmp_path) == []

def test_log_appends_preserving_order(tmp_path):
    log_entry(tmp_path, "first", kind="note")
    log_entry(tmp_path, "second", kind="note")
    log_entry(tmp_path, "third", kind="warning")
    entries = read_entries(tmp_path)
    assert [e["msg"] for e in entries] == ["first", "second", "third"]
    assert entries[-1]["kind"] == "warning"

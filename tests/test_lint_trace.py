import pytest
from scripts.lint_trace import lint_trace
from pathlib import Path

VOICES = {"voice-001": {"claim": "面试要口算"}}

def test_ref_traceable(tmp_path):
    ep = tmp_path / "ep01"
    ep.mkdir()
    (ep / "script.md").write_text("[S1] {{voice:voice-001}} [/S1]\n", encoding="utf-8")
    issues = lint_trace(ep, VOICES)
    assert issues == []

def test_ref_missing_blocking(tmp_path):
    ep = tmp_path / "ep01"
    ep.mkdir()
    (ep / "script.md").write_text("[S1] {{voice:voice-999}} [/S1]\n", encoding="utf-8")
    issues = lint_trace(ep, VOICES)
    assert any("voice-999" in i["msg"] for i in issues)

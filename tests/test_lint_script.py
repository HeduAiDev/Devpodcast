import json
from pathlib import Path
import pytest
from scripts.lint_script import lint_script

VOICES = {"voice-001": {"claim": "面试要口算"}, "voice-002": {"claim": "社区吐槽"}}

def test_voice_refs_must_exist(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] 这里 {{voice:voice-999}} 不存在 [/S1]\n", encoding="utf-8")
    issues = lint_script(p, VOICES, target_minutes=5)
    assert any("voice-999" in i["msg"] and i["level"] == "BLOCKING" for i in issues)

def test_voice_refs_valid_ok(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] 这里 {{voice:voice-001}} 存在 [/S1]\n", encoding="utf-8")
    issues = lint_script(p, VOICES, target_minutes=5)
    assert all("voice-999" not in i["msg"] for i in issues)

def test_unknown_word_warn(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] 开场 [/S1]\n[S2] 主体内容 [/S2]\n", encoding="utf-8")
    issues = lint_script(p, VOICES, target_minutes=5)
    assert any("我不知道" in i["msg"] and i["level"] == "WARN" for i in issues)

def test_unknown_word_present_no_warn(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] 这个我们也没搞清楚，评论区有懂的说说 [/S1]\n[S2] 回应 [/S2]\n", encoding="utf-8")
    issues = lint_script(p, VOICES, target_minutes=5)
    assert not any("我不知道" in i["msg"] for i in issues)

def test_bald_broadcast_warn(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] a [/S1]\n[S1] b [/S1]\n[S1] c [/S1]\n[S2] d [/S2]\n", encoding="utf-8")
    issues = lint_script(p, VOICES, target_minutes=5)
    assert any("30%" in i["msg"] and i["level"] == "WARN" for i in issues)

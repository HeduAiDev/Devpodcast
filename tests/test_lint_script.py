import json
from pathlib import Path
import pytest
from scripts.lint_script import lint_script, main

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
    # S2 仅 1/5=20% < 25% 阈值 → 应触发平衡 WARN
    p.write_text("[S1] a [/S1]\n[S1] b [/S1]\n[S1] c [/S1]\n[S1] c2 [/S1]\n[S2] d [/S2]\n", encoding="utf-8")
    issues = lint_script(p, VOICES, target_minutes=5)
    assert any("25%" in i["msg"] and i["level"] == "WARN" for i in issues)

def test_budget_overrun_blocking_strips_prefix(tmp_path):
    # 60 字 ≈ 15s 口播 > 0.1min×60×1.15=6.9s 余量 → BLOCKING；60 < 200 不触发换气 WARN
    p = tmp_path / "s.md"
    p.write_text(f"[S1] {'字' * 60} [/S1]\n", encoding="utf-8")
    issues = lint_script(p, VOICES, target_minutes=0.1)
    blocking = [i for i in issues if i["level"] == "BLOCKING"]
    assert blocking, f"应产出 BLOCKING 预算超限，实际 issues: {issues}"
    assert "预计" in blocking[0]["msg"]
    assert not blocking[0]["msg"].startswith("BLOCKING: "), "前缀应被剥离"

def test_long_turn_warn_strips_prefix(tmp_path):
    # 250 字 > 200 字换气上限 → WARN；总时长 62.5s 远低于 35min 目标余量 → 无 BLOCKING
    p = tmp_path / "s.md"
    p.write_text(f"[S1] {'字' * 250} [/S1]\n", encoding="utf-8")
    issues = lint_script(p, VOICES, target_minutes=35)
    warn = [i for i in issues if i["level"] == "WARN" and "换气" in i["msg"]]
    assert warn, f"应产出换气 WARN，实际 issues: {issues}"
    assert "长 250 字" in warn[0]["msg"]
    assert not warn[0]["msg"].startswith("WARN: "), "前缀应被剥离"
    assert not any(i["level"] == "BLOCKING" for i in issues)

def test_cli_no_args_usage_returns_2(capsys):
    assert main([]) == 2
    err = capsys.readouterr().err
    assert "usage: python3 scripts/lint_script.py <path>" in err

def test_cli_missing_voices_value_returns_2(capsys, tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] 你好 [/S1]\n", encoding="utf-8")
    assert main([str(p), "--voices"]) == 2

def test_cli_missing_target_value_returns_2(capsys, tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] 你好 [/S1]\n", encoding="utf-8")
    assert main([str(p), "--target-minutes"]) == 2

def test_cli_invalid_target_returns_2(capsys, tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] 你好 [/S1]\n", encoding="utf-8")
    assert main([str(p), "--target-minutes", "abc"]) == 2
    assert "abc" in capsys.readouterr().err

def test_cli_valid_clean_script_returns_0(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] 这个我也不知道，评论区聊聊 {{voice:voice-001}} [/S1]\n"
                 "[S2] 确实是，有懂的来说说 {{voice:voice-002}} [/S2]\n", encoding="utf-8")
    v = tmp_path / "voices.json"
    v.write_text(json.dumps(VOICES), encoding="utf-8")
    assert main([str(p), "--voices", str(v), "--target-minutes", "5"]) == 0

def test_cli_unknown_voice_returns_1(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] 这里 {{voice:voice-999}} 不存在 [/S1]\n", encoding="utf-8")
    v = tmp_path / "voices.json"
    v.write_text(json.dumps(VOICES), encoding="utf-8")
    assert main([str(p), "--voices", str(v)]) == 1

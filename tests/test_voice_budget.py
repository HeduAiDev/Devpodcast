import pytest
from scripts.voice_budget import estimate_duration, estimate_script_duration, budget_check
from scripts.script_parser import parse
from pathlib import Path

def test_estimate_duration_default_speed():
    # 80 字 @ 4字/秒 = 20 秒
    assert estimate_duration("x" * 80) == pytest.approx(20.0)

def test_estimate_duration_custom_speed():
    assert estimate_duration("x" * 80, cps=2.0) == pytest.approx(40.0)

def test_estimate_script_duration(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] " + "x" * 400 + " [/S1]\n", encoding="utf-8")
    s = parse(p)
    assert estimate_script_duration(s) == pytest.approx(100.0)

def test_budget_check_ok(tmp_path):
    # brief 原为 400 字，与 200 字 turn 上限矛盾；改 100 字：25s 在 2min*1.15 内且不超换气上限
    p = tmp_path / "s.md"
    p.write_text("[S1] " + "x" * 100 + " [/S1]\n", encoding="utf-8")
    assert budget_check(parse(p), target_minutes=2.0) == []

def test_budget_check_over(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] " + "x" * 400 + " [/S1]\n", encoding="utf-8")
    issues = budget_check(parse(p), target_minutes=1.0)  # 100s > 69s(1.15x)
    assert len(issues) >= 1

def test_budget_check_long_turn(tmp_path):
    p = tmp_path / "s.md"
    p.write_text("[S1] " + "x" * 300 + " [/S1]\n", encoding="utf-8")
    issues = budget_check(parse(p), target_minutes=5.0)
    assert any("300" in i for i in issues)

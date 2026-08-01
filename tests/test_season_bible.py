# tests/test_season_bible.py
import json
import pytest
from scripts.season_bible import due, register

def test_due_empty_bible(tmp_path):
    p = tmp_path / "arc-map.json"
    p.write_text(json.dumps({"episodes": {}, "foreshadow": {}}), encoding="utf-8")
    assert due(p, "ep01") == []

def test_due_returns_foreshadow_and_payoff(tmp_path):
    p = tmp_path / "arc-map.json"
    p.write_text(json.dumps({
        "episodes": {"ep01": {"foreshadow_due": ["伏笔甲"], "payoff_due": ["伏笔乙"]}}
    }), encoding="utf-8")
    r = due(p, "ep01")
    assert "伏笔甲" in r and "伏笔乙" in r

def test_register_updates_episode(tmp_path):
    p = tmp_path / "arc-map.json"
    p.write_text(json.dumps({"episodes": {"ep01": {}}}), encoding="utf-8")
    register(p, "ep01", {"foreshadow_laid": ["伏笔丙"], "payoff_resolved": ["伏笔乙"]})
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["episodes"]["ep01"]["foreshadow_laid"] == ["伏笔丙"]

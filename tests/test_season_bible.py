# tests/test_season_bible.py
import json
import pytest
from scripts.season_bible import due, main, register

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

def test_cli_register_writes_arc_map(tmp_path):
    p = tmp_path / "arc-map.json"
    p.write_text(json.dumps({"episodes": {"ep01": {}}}), encoding="utf-8")
    rc = main(["register", str(p), "ep01", '{"foreshadow_laid": ["X"]}'])
    assert rc == 0
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["episodes"]["ep01"]["foreshadow_laid"] == ["X"]

def test_cli_register_full_archivist_flow(tmp_path):
    """archivist.md 命令形态：'{"payoff_due": [...]}' 中文内容真落盘。"""
    p = tmp_path / "arc-map.json"
    p.write_text(json.dumps({"episodes": {"ep03": {"payoff_due": []}}}), encoding="utf-8")
    fields = '{"payoff_due": ["ep01 埋的 PagedAttention 回收"], "foreshadow_due": []}'
    rc = main(["register", str(p), "ep03", fields])
    assert rc == 0
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["episodes"]["ep03"]["payoff_due"] == ["ep01 埋的 PagedAttention 回收"]
    assert data["episodes"]["ep03"]["foreshadow_due"] == []

def test_cli_register_missing_fields_arg(tmp_path):
    p = tmp_path / "arc-map.json"
    p.write_text(json.dumps({"episodes": {}}), encoding="utf-8")
    assert main(["register", str(p), "ep01"]) == 2
    assert json.loads(p.read_text(encoding="utf-8"))["episodes"] == {}

def test_cli_register_invalid_json(tmp_path, capsys):
    p = tmp_path / "arc-map.json"
    p.write_text(json.dumps({"episodes": {}}), encoding="utf-8")
    assert main(["register", str(p), "ep01", "{not json"]) == 2
    assert "非法 JSON" in capsys.readouterr().err

def test_cli_register_rejects_non_object_fields(tmp_path, capsys):
    p = tmp_path / "arc-map.json"
    p.write_text(json.dumps({"episodes": {}}), encoding="utf-8")
    assert main(["register", str(p), "ep01", '["a"]']) == 2
    assert "JSON 对象" in capsys.readouterr().err

def test_cli_unknown_command_fails_loudly(tmp_path, capsys):
    """未知命令必须 exit 2 报错，不许静默 no-op。"""
    p = tmp_path / "arc-map.json"
    p.write_text(json.dumps({"episodes": {}}), encoding="utf-8")
    assert main(["frobnicate", str(p), "ep01"]) == 2
    assert "未知命令" in capsys.readouterr().err

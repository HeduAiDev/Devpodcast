import pytest
from scripts.lint_anchors import lint_anchors

def test_valid_link_ok(tmp_path):
    (tmp_path / "episodes" / "ep01-slug").mkdir(parents=True)
    (tmp_path / "episodes" / "ep02-slug").mkdir(parents=True)
    (tmp_path / "episodes" / "ep01-slug" / "script.md").write_text(
        "[S1] 详见 [ep02](../../episodes/ep02-slug/script.md) [/S1]\n", encoding="utf-8")
    (tmp_path / "episodes" / "ep02-slug" / "script.md").write_text("", encoding="utf-8")
    issues = lint_anchors(tmp_path / "episodes" / "ep01-slug", tmp_path)
    assert issues == []

def test_broken_link_blocking(tmp_path):
    (tmp_path / "episodes" / "ep01-slug").mkdir(parents=True)
    (tmp_path / "episodes" / "ep01-slug" / "script.md").write_text(
        "[S1] 详见 [ep02](../../episodes/ep02-ghost/script.md) [/S1]\n", encoding="utf-8")
    issues = lint_anchors(tmp_path / "episodes" / "ep01-slug", tmp_path)
    assert any("ep02-ghost" in i["msg"] and i["level"] == "BLOCKING" for i in issues)

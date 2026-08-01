# tests/test_new_show.py
import json
from pathlib import Path
import pytest
from scripts.new_show import scaffold_show
from scripts.show_resolver import resolve_show

def test_scaffold_creates_structure(tmp_path):
    show_dir = scaffold_show(tmp_path, "demo", "演示节目", "/mnt/fake/repo", "vllm")
    assert (show_dir / "devpodcast.json").is_file()
    assert (show_dir / "SHOW.md").is_file()
    assert (show_dir / "season" / "bible" / "voice-guide.md").is_file()
    assert (show_dir / "trace").is_dir()
    assert (show_dir / "episodes").is_dir()
    assert (show_dir / "voice-samples").is_dir()

def test_scaffold_registers_and_activates(tmp_path):
    scaffold_show(tmp_path, "demo", "演示", "/mnt/fake/repo", "vllm")
    reg = json.loads((tmp_path / "devpodcast.json").read_text(encoding="utf-8"))
    assert reg["active_show"] == "demo"
    assert "demo" in reg["shows"]
    assert resolve_show(tmp_path).name == "demo"

def test_config_embeds_book_source(tmp_path):
    show_dir = scaffold_show(tmp_path, "demo", "演示", "/mnt/fake/repo", "vllm")
    cfg = json.loads((show_dir / "devpodcast.json").read_text(encoding="utf-8"))
    assert cfg["book_source"]["root"] == "/mnt/fake/repo"
    assert cfg["book_source"]["instance"] == "vllm"

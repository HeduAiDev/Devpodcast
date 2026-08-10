import json
from pathlib import Path
import pytest
from scripts.show_resolver import resolve_show, active_show_name, show_config

def test_resolve_active_show(tmp_path):
    (tmp_path / "shows" / "demo").mkdir(parents=True)
    (tmp_path / "shows" / "demo" / "devpodcast.json").write_text(
        json.dumps({"show": "demo"}), encoding="utf-8")
    (tmp_path / "devpodcast.json").write_text(
        json.dumps({"active_show": "demo", "shows": {"demo": {"config": "shows/demo/devpodcast.json"}}}),
        encoding="utf-8")
    assert resolve_show(tmp_path).name == "demo"
    assert active_show_name(tmp_path) == "demo"

def test_show_config_reads_instance_file(tmp_path):
    (tmp_path / "shows" / "demo").mkdir(parents=True)
    (tmp_path / "shows" / "demo" / "devpodcast.json").write_text(
        json.dumps({"show": "demo", "format": {"hosts": 2}}), encoding="utf-8")
    cfg = show_config(tmp_path / "shows" / "demo")
    assert cfg["format"]["hosts"] == 2

def test_resolve_missing_show_raises(tmp_path):
    (tmp_path / "devpodcast.json").write_text(
        json.dumps({"active_show": "nope", "shows": {}}), encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        resolve_show(tmp_path)

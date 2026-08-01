"""活动节目定位：devpodcast.json.active_show 或环境变量 DEVPODCAST_SHOW 覆盖。"""
import json, os
from pathlib import Path

def _root(root=None) -> Path:
    return Path(root) if root else Path(__file__).resolve().parent.parent

def active_show_name(root=None) -> str:
    env = os.environ.get("DEVPODCAST_SHOW")
    if env:
        return env
    reg = json.loads((_root(root) / "devpodcast.json").read_text(encoding="utf-8"))
    return reg["active_show"]

def resolve_show(root=None) -> Path:
    name = active_show_name(root)
    p = _root(root) / "shows" / name
    if not (p / "devpodcast.json").exists():
        raise FileNotFoundError(f"活动节目 {name} 缺少 shows/{name}/devpodcast.json")
    return p

def show_config(show_dir: Path) -> dict:
    return json.loads((Path(show_dir) / "devpodcast.json").read_text(encoding="utf-8"))

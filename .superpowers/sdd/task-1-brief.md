### Task 1: 骨架 — devpodcast.json + show_resolver.py

**Files:**
- Create: `devpodcast.json`
- Create: `scripts/show_resolver.py`
- Test: `tests/test_show_resolver.py`

**Interfaces:**
- Produces: `resolve_show(root=None) -> Path`（活动节目目录）、`active_show_name() -> str`、`show_config(show_dir) -> dict`（读该节目 devpodcast.json）。后续所有脚本经它定位节目。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_show_resolver.py
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
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_show_resolver.py -v`
Expected: FAIL（ModuleNotFoundError: show_resolver）

- [ ] **Step 3: 写实现**

```python
# scripts/show_resolver.py
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
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_show_resolver.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: 写顶层注册表**

```json
// devpodcast.json
{
  "version": "1.0",
  "description": "devpodcast — 把一本技术书变成一季双人对谈播客（议题驱动、批判先行、引真实社区声音、本地 GPU 合成）。",
  "active_show": "vllm-podcast",
  "shows": {
    "vllm-podcast": { "config": "shows/vllm-podcast/devpodcast.json", "title": "把 vLLM 拆开讲" }
  },
  "shared": {
    "operating_doc": "CLAUDE.md",
    "runbook": "docs/superpowers/ARCHITECT-RUNBOOK.md",
    "spec": "docs/superpowers/specs/2026-08-01-devpodcast-design.md",
    "agents_dir": ".claude/agents",
    "workflow_phase_a": ".claude/workflows/season-pipeline.js",
    "workflow_phase_b": ".claude/workflows/episode-pipeline.js",
    "linters": [
      "scripts/lint_script.py", "scripts/lint_voices.py", "scripts/lint_punct.py",
      "scripts/lint_anchors.py", "scripts/lint_trace.py"
    ]
  }
}
```

- [ ] **Step 6: 提交**

```bash
git add devpodcast.json scripts/show_resolver.py tests/test_show_resolver.py
git commit -m "feat: 顶层注册表 + 活动节目定位（show_resolver）"
```

---

### Task 2: BookSource 抽象 + Repo2BookSource

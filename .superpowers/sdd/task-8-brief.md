### Task 8: lint_voices.py — voices 门禁

**Files:**
- Create: `scripts/lint_voices.py`
- Test: `tests/test_lint_voices.py`

**Interfaces:**
- Produces: `lint_voices(voices: dict) -> list[dict]`（`{"level", "msg"}`）；CLI 退出码同 Task 7。
- 校验规则（spec §6.4 的 5 条）：
  1. `source_url` + `source_date` 必填
  2. `anonymized=false` 仅允许 `source_platform` ∈ {official, paper, github-issue}
  3. `confidence=low` 须 `writer_note` 含「未一手核实」
  4. 同 term 至少 2 条不同平台（除非 verified=official），否则 WARN 单一来源
  5. `category=job-seeker` 条目的 `source_platform` 必须在求职者平台集合内

```python
JOB_SEEKER_PLATFORMS = {"zhihu", "v2ex", "niuke", "maimai", "xhs", "bili", "jike",
                        "reddit", "hn", "x", "blind", "linkedin"}
OFFICIAL_PLATFORMS = {"official", "paper", "github-issue"}
```

- [ ] **Step 1: 写失败测试**

```python
# tests/test_lint_voices.py
import pytest
from scripts.lint_voices import lint_voices

def base_voice(**kw):
    v = {"id": "v1", "category": "critical", "term": "t", "claim": "c",
         "verified": "community-only", "source_url": "https://x.example/1",
         "source_date": "2026-07-15", "source_platform": "hn",
         "speaker_handle": "@匿名", "anonymized": True,
         "confidence": "high", "writer_note": ""}
    v.update(kw)
    return v

def test_missing_url_blocking():
    v = base_voice(source_url="")
    issues = lint_voices({"v1": v})
    assert any("source_url" in i["msg"] and i["level"] == "BLOCKING" for i in issues)

def test_missing_date_blocking():
    v = base_voice(source_date="")
    issues = lint_voices({"v1": v})
    assert any("source_date" in i["msg"] and i["level"] == "BLOCKING" for i in issues)

def test_non_anonymous_requires_official_platform():
    v = base_voice(anonymized=False, source_platform="reddit")
    issues = lint_voices({"v1": v})
    assert any("anonymized" in i["msg"] and i["level"] == "BLOCKING" for i in issues)

def test_official_platform_can_be_named():
    v = base_voice(anonymized=False, source_platform="official")
    issues = lint_voices({"v1": v})
    assert not any("anonymized" in i["msg"] for i in issues)

def test_low_confidence_requires_note():
    v = base_voice(confidence="low", writer_note="")
    issues = lint_voices({"v1": v})
    assert any("未一手核实" in i["msg"] and i["level"] == "BLOCKING" for i in issues)

def test_single_source_warn():
    issues = lint_voices({"v1": base_voice()})
    assert any("单一来源" in i["msg"] and i["level"] == "WARN" for i in issues)

def test_two_platforms_no_warn():
    v1 = base_voice()
    v2 = base_voice(id="v2", source_url="https://y.example/2", source_platform="zhihu")
    issues = lint_voices({"v1": v1, "v2": v2})
    assert not any("单一来源" in i["msg"] for i in issues)

def test_verified_official_single_source_ok():
    v = base_voice(verified="official")
    issues = lint_voices({"v1": v})
    assert not any("单一来源" in i["msg"] for i in issues)

def test_job_seeker_platform_rule():
    v = base_voice(category="job-seeker", source_platform="github-issue")
    issues = lint_voices({"v1": v})
    assert any("job-seeker" in i["msg"] and i["level"] == "BLOCKING" for i in issues)

def test_job_seeker_platform_ok():
    v = base_voice(category="job-seeker", source_platform="niuke")
    issues = lint_voices({"v1": v})
    assert not any("job-seeker" in i["msg"] for i in issues)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_lint_voices.py -v`
Expected: FAIL

- [ ] **Step 3: 写实现**

```python
# scripts/lint_voices.py
"""voices 门禁（spec §6.4 五条）：URL/日期必填 / 匿名化 / low-confidence 标注 /
多平台 / 求职者平台约束。"""
import sys
from collections import Counter

JOB_SEEKER_PLATFORMS = {"zhihu", "v2ex", "niuke", "maimai", "xhs", "bili", "jike",
                        "reddit", "hn", "x", "blind", "linkedin"}
OFFICIAL_PLATFORMS = {"official", "paper", "github-issue"}


def lint_voices(voices: dict) -> list[dict]:
    issues: list[dict] = []
    for vid, v in voices.items():
        # ① URL/日期必填
        if not v.get("source_url"):
            issues.append({"level": "BLOCKING", "msg": f"{vid}: source_url 必填"})
        if not v.get("source_date"):
            issues.append({"level": "BLOCKING", "msg": f"{vid}: source_date 必填"})
        # ② 匿名化
        if not v.get("anonymized", True) and v.get("source_platform") not in OFFICIAL_PLATFORMS:
            issues.append({"level": "BLOCKING",
                           "msg": f"{vid}: anonymized=false 仅允许官方/作者/论文/issue 源（当前 {v.get('source_platform')}）"})
        # ③ low confidence 标注
        if v.get("confidence") == "low" and "未一手核实" not in v.get("writer_note", ""):
            issues.append({"level": "BLOCKING", "msg": f"{vid}: confidence=low 须 writer_note 标注「未一手核实」"})
        # ⑤ 求职者平台约束
        if v.get("category") == "job-seeker" and v.get("source_platform") not in JOB_SEEKER_PLATFORMS:
            issues.append({"level": "BLOCKING",
                           "msg": f"{vid}: job-seeker 条目须落在求职者平台集合内（当前 {v.get('source_platform')}）"})
    # ④ 单一来源 warn（按 term 聚合）
    by_term: dict[str, list[str]] = {}
    verified_official = {v["id"] for v in voices.values() if v.get("verified") == "official"}
    for vid, v in voices.items():
        by_term.setdefault(v.get("term", ""), []).append(v.get("source_platform", ""))
    for term, plats in by_term.items():
        if len(set(plats)) < 2 and all(vid not in verified_official for vid in voices if voices[vid].get("term") == term):
            issues.append({"level": "WARN", "msg": f"term「{term}」单一来源（{plats[0]}），建议 ≥2 平台或 verified=official"})
    return issues


def main(argv=None) -> int:
    import json
    from pathlib import Path
    argv = argv if argv is not None else sys.argv[1:]
    voices = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    issues = lint_voices(voices)
    for i in issues:
        print(f"[{i['level']}] {i['msg']}")
    return 1 if any(i["level"] == "BLOCKING" for i in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_lint_voices.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/lint_voices.py tests/test_lint_voices.py
git commit -m "feat: lint_voices 五条门禁（spec §6.4）"
```

---

### Task 9: lint_punct / lint_anchors / lint_trace

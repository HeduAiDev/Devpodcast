# Task 9 Report: lint_punct / lint_anchors / lint_trace

Status: DONE_WITH_CONCERNS

Commit: `fcbadfe` — "feat: lint_punct/anchors/trace 三个门禁" (branch feat/m0-m1)

## What was done

Implemented three independent lint gates (no cross-dependencies between them, none import other `scripts.*` modules):

- `scripts/lint_punct.py` — `lint_punct(text) -> list[dict]`: WARN on halfwidth `,.` / `;` sandwiched between CJK chars; backtick code spans stripped before scanning. Pure WARN — `main()` always returns 0.
- `scripts/lint_anchors.py` — `lint_anchors(ep_dir, show_dir) -> list[dict]`: every `](../../episodes/epNN-xxx/` cross-episode link target must exist (`show_dir/episodes/<slug>/script.md`), else BLOCKING.
- `scripts/lint_trace.py` — `lint_trace(ep_dir, voices) -> list[dict]`: every `{{voice:<id>}}` ref in script.md must exist in the voices dict, else BLOCKING.

CLI pattern carried over from Task 7/8 for all three: repo root inserted into `sys.path` at top (defensive; these modules import no scripts.* packages), no-arg guard prints usage to stderr and returns 2, output as `[BLOCKING] msg` / `[WARN] msg`, exit 0 = pass / 1 = BLOCKING / 2 = usage.

## TDD sequence

1. Wrote the 3 test files from the brief (3 + 2 + 2 = 7 tests).
2. `python3 -m pytest tests/test_lint_punct.py tests/test_lint_anchors.py tests/test_lint_trace.py -v` → FAIL (3 ModuleNotFoundError collection errors — modules absent).
3. Wrote the 3 implementations (brief code + CLI patterns above).
4. First green run: 1 failed / 6 passed. Failure was `test_valid_link_ok`, a test-setup bug (see Concerns).
5. After fixing the test setup: 7 passed.

## Test commands and output

New tests:

```
$ python3 -m pytest tests/test_lint_punct.py tests/test_lint_anchors.py tests/test_lint_trace.py -v
tests/test_lint_punct.py::test_halfwidth_between_cjk_warn PASSED   [ 14%]
tests/test_lint_punct.py::test_fullwidth_ok PASSED                 [ 28%]
tests/test_lint_punct.py::test_code_span_ignored PASSED            [ 42%]
tests/test_lint_anchors.py::test_valid_link_ok PASSED              [ 57%]
tests/test_lint_anchors.py::test_broken_link_blocking PASSED       [ 71%]
tests/test_lint_trace.py::test_ref_traceable PASSED                [ 85%]
tests/test_lint_trace.py::test_ref_missing_blocking PASSED         [100%]
============================== 7 passed in 0.23s ===============================
```

Full suite (no regression):

```
$ python3 -m pytest tests/ -v
============================== 61 passed in 0.94s ===============================
```

CLI smoke tests (not covered by pytest, which only tests library functions):

- `python3 scripts/lint_punct.py` (no args) → usage on stderr, rc=2
- `python3 scripts/lint_punct.py file` → `[WARN] 汉字间半角标点: …`, rc=0
- `python3 scripts/lint_anchors.py` (no args) → usage on stderr, rc=2
- `python3 scripts/lint_anchors.py ep show` broken link → `[BLOCKING] 跨期链接目标不存在: ep02-ghost`, rc=1; valid link → rc=0
- `python3 scripts/lint_trace.py` (no args) → usage on stderr, rc=2
- `python3 scripts/lint_trace.py ep voices.json` unknown ref → `[BLOCKING] 引用了未知 voice id: voice-999`, rc=1; known ref → rc=0

## Concerns

1. **Brief bug in `tests/test_lint_anchors.py::test_valid_link_ok`** — as written in the brief it can never pass: it writes `episodes/ep01-slug/script.md` without creating the `ep01-slug` directory (FileNotFoundError), and it never creates the link target `ep02-slug/script.md` (which the lint correctly requires). Fixed minimally in the test setup: added `(tmp_path / "episodes" / "ep01-slug").mkdir(parents=True)` and `(tmp_path / "episodes" / "ep02-slug").mkdir(parents=True)` plus an empty `ep02-slug/script.md`. Test intent (valid link → no issues) unchanged. Verified the original brief version does indeed fail at `write_text`, so the fix is in the test, not the implementation.
2. **lint_anchors link resolution uses `show_dir/episodes/<slug>/script.md`, ignoring `ep_dir`** — matches the brief implementation exactly; callers must pass the actual show root. CLI default `show_dir = ep_dir.parent.parent` only works for the canonical layout `show/episodes/epNN-x/`.
3. **`main()` in lint_anchors/lint_trace calls the lint function twice** (once for printing, once for the exit code) — kept verbatim per brief; harmless since both are pure.
4. **lint_trace duplicates lint_script rule 1** — intentional per brief (standalone CLI for the workflow; kept consistent).
5. `.superpowers/` remains untracked (as before; briefs/reports live there and were never committed).

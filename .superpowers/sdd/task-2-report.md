# Task 2 Report — BookSource 抽象 + Repo2BookSource

**Status: DONE**

## What was done

TDD per brief Step 1–6:

1. **Step 1 — Fixture**: Created `tests/fixtures/repo2book-mini/` with all 4 files verbatim from the brief (outline-final.json as **list**, glossary.json as **dict** keyed by 中文术语, ch01 dossier with non-empty `mechanisms`, ch02 dossier with **empty** `mechanisms` to exercise tolerance, both narrative `chapter.md` with `# 第N章　<标题>` first line — U+3000 full-width space verified — and a non-section `## 你在这里` heading that must NOT be picked up).
2. **Step 2 — Failing test**: `tests/test_book_source.py` verbatim from the brief (7 tests).
3. **Step 3 — Confirmed failure**: `python3 -m pytest tests/test_book_source.py -v` → collection error `ModuleNotFoundError: No module named 'scripts.book_source'`.
4. **Step 4 — Implementation**: `scripts/book_source.py` verbatim from the brief — `ChapterCard`/`Book` dataclasses (with `as_dict()`), `BookSource(Protocol)`, `Repo2BookSource(root, instance)` with `inst_dir = root/instances/instance` gate (`FileNotFoundError`), sections from `^##\s+(\d+\.\d+)\s+(.+)$` on narrative, title from `^#\s+第\d+章\s+(.+)$`, key_classes/mechanisms from dossier.json (empty-tolerant via `or []`), glossary/outline readers.
5. **Step 5 — Confirmed pass**: 7/7 PASS. Full suite: 10/10 (Task 1's 3 tests unaffected).
6. **Step 6 — Commit**: `7e2334b`, exactly the 8 files from brief Step 6, identity inline `-c user.name="devpodcast" -c user.email="devpodcast@local"`.

## Test commands & output

### Before implementation (Step 3)
```
$ python3 -m pytest tests/test_book_source.py -v
ERROR collecting tests/test_book_source.py
E   ModuleNotFoundError: No module named 'scripts.book_source'
=============================== 1 error in 0.10s ===============================
```

### After implementation (Step 5)
```
$ python3 -m pytest tests/test_book_source.py -v
tests/test_book_source.py::test_load_book PASSED                         [ 14%]
tests/test_book_source.py::test_chapter_cards_sections PASSED            [ 28%]
tests/test_book_source.py::test_empty_mechanisms_tolerated PASSED        [ 42%]
tests/test_book_source.py::test_glossary_dict_shape PASSED               [ 57%]
tests/test_book_source.py::test_outline_is_list PASSED                   [ 71%]
tests/test_book_source.py::test_implements_protocol PASSED               [ 85%]
tests/test_book_source.py::test_missing_instance_raises PASSED           [100%]
============================== 7 passed in 0.16s ===============================
```

### Full suite (regression)
```
$ python3 -m pytest tests/ -v
============================== 10 passed in 0.39s ==============================
```

### Extraction sanity check (fixture → Book)
`load().as_dict()`: title "mini", 2 chapters; ch01 sections `["1.1 Foo 的第一步", "1.2 Foo 的第二步"]` (heading `## 你在这里` correctly skipped), mechanisms `[{"id": "m1", ...}]`; ch02 sections `["2.1 Bar 的唯一一步"]`, mechanisms `[]`. glossary dict `{"连续批处理": "continuous batching", ...}`; outline list with `o[0]["chapter_id"] == "ch01"`.

## Commit

- Hash: `7e2334b`
- Message: `feat: BookSource 抽象 + Repo2BookSource（narrative 小节为要点主源）`
- Files: `scripts/book_source.py`, `tests/test_book_source.py`, 6 fixture files under `tests/fixtures/repo2book-mini/` (8 files, 167 insertions)
- Working tree: clean except untracked `.superpowers/` (sdd workspace, intentionally not committed — same as Task 1)

## Concerns

1. **Brief internal inconsistency — fixture path layout**: brief Step 1 places fixture files directly under `tests/fixtures/repo2book-mini/` (e.g. `repo2book-mini/book/cartography/outline-final.json`), but the brief's own test/implementation code requires `Repo2BookSource(root=repo2book-mini, "mini")` → `root/instances/mini/...` (`test_load_book` would hit the `FileNotFoundError` gate otherwise). Resolved in favor of the code contract: fixture lives at `tests/fixtures/repo2book-mini/instances/mini/` with **all file contents verbatim** from the brief. If a future task recreates a repo2book instance by hand, it must use the `instances/<name>/artifacts|book` layout.
2. **Brief code bug — Protocol isinstance**: brief's `BookSource(Protocol)` without `@runtime_checkable` makes `isinstance(Repo2BookSource(...), BookSource)` raise `TypeError: Instance and class checks can only be used with @runtime_checkable protocols` (verified empirically in this environment). Minimal fix applied: added `@runtime_checkable` decorator to `BookSource`. Interface unchanged; duck-type semantics preserved. Only deliberate deviation from brief Step 4 code.
3. **Fixture omission**: fixture has no dossier `code_spine` usage and no missing-file branches (those are covered by default-return guards, not tests) — acceptable for a mini fixture; Task 3+ real instance will exercise the real repo2book tree.

## Environment notes

- Python 3.11.5 (miniconda), pytest 9.0.3 (as Task 1).
- `python3 -m pytest` from repo root makes `scripts/` importable (namespace package, cwd on sys.path) — no conftest/pyproject needed.

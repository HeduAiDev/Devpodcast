# scripts/ingest_book.py
"""书源快照摄入：BookSource → shows/<name>/source-book/（此后 pipeline 只读快照，不再触碰外部路径）。

Usage:
    python3 scripts/ingest_book.py --show vllm-podcast --root <path> --instance vllm
    python3 scripts/ingest_book.py --show vllm-podcast --root <path> --instance vllm --refresh
"""
import datetime
import hashlib
import json
import sys
from pathlib import Path

from scripts.book_source import BookSource, Repo2BookSource


def compute_digest(show_dir: Path) -> str:
    sb = Path(show_dir) / "source-book"
    if not sb.is_dir():
        raise FileNotFoundError(f"缺少快照目录: {sb}")
    h = hashlib.sha256()
    for p in sorted(sb.rglob("*")):
        if p.is_file():
            h.update(p.relative_to(sb).as_posix().encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def ingest(source: BookSource, show_dir: Path) -> dict:
    show_dir = Path(show_dir)
    sb = show_dir / "source-book"
    cards_dir = sb / "chapter-cards"
    cards_dir.mkdir(parents=True, exist_ok=True)
    book = source.load()
    (sb / "book.json").write_text(
        json.dumps(book.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    (sb / "outline.json").write_text(
        json.dumps(source.outline(), ensure_ascii=False, indent=2), encoding="utf-8")
    (sb / "glossary.json").write_text(
        json.dumps(source.glossary(), ensure_ascii=False, indent=2), encoding="utf-8")
    for card in book.chapters:
        (cards_dir / f"{card.chapter_id}.json").write_text(
            json.dumps(card.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return {"digest": compute_digest(show_dir), "chapters": len(book.chapters), "ingested_at": ""}


# ── CLI ──────────────────────────────────────────────────────────────────────

def _main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]

    show_name = None
    book_root = None
    instance = None
    refresh = False

    i = 0
    while i < len(args):
        if args[i] == "--show" and i + 1 < len(args):
            show_name = args[i + 1]; i += 2
        elif args[i] == "--root" and i + 1 < len(args):
            book_root = args[i + 1]; i += 2
        elif args[i] == "--instance" and i + 1 < len(args):
            instance = args[i + 1]; i += 2
        elif args[i] == "--refresh":
            refresh = True; i += 1
        else:
            i += 1

    if not show_name or not book_root or not instance:
        print("Usage: ingest_book.py --show <name> --root <path> --instance <name> [--refresh]", file=sys.stderr)
        return 2

    # Locate the show dir relative to repo root
    repo_root = Path(__file__).resolve().parent.parent
    show_dir = repo_root / "shows" / show_name
    if not show_dir.is_dir():
        # Fallback: try relative to cwd
        show_dir = Path.cwd() / "shows" / show_name
    if not show_dir.is_dir():
        print(f"ERROR: show '{show_name}' not found at {repo_root / 'shows' / show_name} or {show_dir}", file=sys.stderr)
        return 1

    source_book_dir = show_dir / "source-book"
    if source_book_dir.is_dir() and not refresh:
        print(f"source-book/ already exists. Use --refresh to re-ingest.", file=sys.stderr)
        return 1

    if refresh:
        # Clean old snapshot before re-ingesting
        import shutil
        shutil.rmtree(source_book_dir, ignore_errors=True)
        print(f"[--refresh] removed old {source_book_dir}")

    src = Repo2BookSource(book_root, instance)
    result = ingest(src, show_dir)
    digest_short = result["digest"][:16]
    ingested_at = datetime.date.today().isoformat()

    # Update show config with ingestion metadata
    config_path = show_dir / "devpodcast.json"
    if config_path.is_file():
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
        cfg["book_source"]["ingested_at"] = ingested_at
        cfg["book_source"]["snapshot_digest"] = digest_short
        config_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"ingested {result['chapters']} chapters → {source_book_dir}")
    print(f"digest: {digest_short}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

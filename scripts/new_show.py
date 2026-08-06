# scripts/new_show.py
"""新建一档节目：scaffold 目录 + 配置文件 + 顶层注册。"""
import json
import sys
from pathlib import Path

USAGE = "usage: new_show.py <root> <name> <title> <book_root> <instance>"

VOICE_GUIDE_TEMPLATE = """# voice-guide.md — 声线人格定义（Lead 落笔）

> 本文件是节目灵魂。writer 强制复用；修改需 Lead 批准。

## 说话人
- **S1（老张）——主持人**：读过书但不装懂；替听众问笨问题；爱用生活类比；
  没听懂就明说；主动挑事；禁止假装惊叹、禁止捧哏。
- **S2（阿凯）——嘉宾/技术侧**：真读过源码但知道边界；长句自我打断成短句；
  数字先给量级；不护短；禁止背书、禁止说「这个很简单」。

## 三条内容纪律
1. 每期至少一次「我不知道」——答不上来就明说，反 AI 播客的最强信号。
2. 批判必须有靶子——谁在什么场景踩了什么坑，或牺牲了什么换了什么。
3. 生活场景必须承重——删掉类比听众就答不出「为什么」时，类比才保留。

## 求职者视角
融进 S1 的提问，每期至多两处，必须挂真实 voices 条目，不许凭空说「面试会考」。
"""

SHOW_MD_TEMPLATE = """# SHOW.md — {name} 当前状态

## 书源
- kind: {book_kind}
- root: {book_root}
- instance: {instance}
- 状态: 未摄入（跑 `python3 scripts/ingest_book.py --show {name} --root {book_root} --instance {instance}`）

## 硬规则
- voices 有 3 个月保质期（面经半年就过时），到期刷新。
- TTS 是必经站：环境没配好 = BLOCKED，无降级路径。
- 修改 voice-guide.md 需 Lead 批准。
"""


def scaffold_show(root: Path, name: str, title: str, book_root: str, instance: str) -> Path:
    root = Path(root)
    show_dir = root / "shows" / name
    for sub in ["season/bible", "trace", "voice-samples", "episodes"]:
        (show_dir / sub).mkdir(parents=True, exist_ok=True)

    cfg = {
        "show": name,
        "title": title,
        "book_source": {"kind": "repo2book", "root": book_root, "instance": instance,
                        "ingested_at": "", "snapshot_digest": ""},
        "audience": {"profile": "对 LLM 推理有兴趣的工程师 + 正在准备相关面试的求职者",
                     "assumed_knowledge": ["Python", "Transformer 基本概念"], "language": "zh-CN"},
        "format": {"hosts": 2, "target_minutes": 35, "episodes_planned": None},
        "tts": {"provider": "firered-tts2",
                "voice_map": {"S1": "voice-samples/laozhang.wav", "S2": "voice-samples/akai.wav"},
                "pronunciation": "season/pronunciation.json"},
    }
    (show_dir / "devpodcast.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    (show_dir / "SHOW.md").write_text(
        SHOW_MD_TEMPLATE.format(name=name, book_kind="repo2book", book_root=book_root, instance=instance),
        encoding="utf-8")
    (show_dir / "season" / "bible" / "voice-guide.md").write_text(VOICE_GUIDE_TEMPLATE, encoding="utf-8")

    reg_path = root / "devpodcast.json"
    if reg_path.exists():
        reg = json.loads(reg_path.read_text(encoding="utf-8"))
    else:
        reg = {"version": "1.0", "active_show": "", "shows": {}}
    reg["active_show"] = name
    reg["shows"][name] = {"config": f"shows/{name}/devpodcast.json", "title": title}
    reg_path.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
    return show_dir


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) < 5:
        print(USAGE, file=sys.stderr)
        return 2
    root = Path(argv[0])
    name, title, book_root, instance = argv[1], argv[2], argv[3], argv[4]
    scaffold_show(root, name, title, book_root, instance)
    print(f"scaffolded shows/{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

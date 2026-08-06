#!/usr/bin/env python3
"""生成参数扫描试听页：temp × topk 矩阵，键盘快速 A/B 切换。

用法：
    python scripts/make_listen_page.py _diag/firered_sweep
    # 然后打开 _diag/firered_sweep/listen.html
"""
import argparse
import json
import re
from pathlib import Path

TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>FireRedTTS2 参数试听矩阵</title>
<style>
  body {{ font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif;
         margin: 24px; background: #14161a; color: #e6e6e6; }}
  h1 {{ font-size: 18px; margin: 0 0 4px; }}
  .sub {{ color: #8b93a1; font-size: 13px; margin-bottom: 18px; }}
  table {{ border-collapse: collapse; }}
  th, td {{ border: 1px solid #2a2f38; padding: 8px 10px; text-align: center; font-size: 13px; }}
  th {{ background: #1d2128; color: #9fb0c8; font-weight: 600; }}
  td.cell {{ cursor: pointer; min-width: 118px; }}
  td.cell:hover {{ background: #212734; }}
  td.cell.active {{ background: #2d4a6b; outline: 2px solid #5b9bd5; }}
  td.cell.played {{ border-left: 3px solid #4a8f5b; }}
  .dur {{ color: #8b93a1; font-size: 11px; display: block; margin-top: 2px; }}
  .rate {{ margin-top: 4px; }}
  .rate button {{ background: #262c36; color: #c9d3e0; border: 1px solid #39414e;
                  border-radius: 3px; cursor: pointer; font-size: 11px;
                  width: 20px; height: 20px; padding: 0; }}
  .rate button:hover {{ background: #333b47; }}
  .rate button.on {{ background: #4a8f5b; border-color: #5aa76c; color: #fff; }}
  #player {{ position: sticky; top: 0; background: #14161a; padding: 12px 0 16px;
             z-index: 10; border-bottom: 1px solid #2a2f38; margin-bottom: 16px; }}
  audio {{ width: 100%; max-width: 640px; }}
  #now {{ font-size: 14px; margin-bottom: 6px; color: #5b9bd5; font-weight: 600; }}
  kbd {{ background: #262c36; border: 1px solid #39414e; border-radius: 3px;
         padding: 1px 5px; font-size: 11px; }}
  #export {{ margin-top: 20px; }}
  #export button {{ background: #2d4a6b; color: #fff; border: 1px solid #5b9bd5;
                    border-radius: 4px; padding: 7px 14px; cursor: pointer; font-size: 13px; }}
  pre {{ background: #1a1e25; border: 1px solid #2a2f38; padding: 12px;
         border-radius: 4px; font-size: 12px; overflow-x: auto; color: #b8c4d4; }}
</style>
</head>
<body>
<h1>FireRedTTS2 参数试听矩阵</h1>
<div class="sub">
  同一段 ep01 摘录（6 turns，固定随机种子 1988），只变 temperature / topk。
  点格子播放，<kbd>←</kbd><kbd>→</kbd> 切换，<kbd>空格</kbd> 播放/暂停，<kbd>1</kbd>-<kbd>5</kbd> 打分。
  听点：音色是否自然、双声线是否分得开、有没有把 <code>[S1]</code> 读出来、有没有重复或漂移。
</div>

<div id="player">
  <div id="now">未选择</div>
  <audio id="audio" controls preload="none"></audio>
</div>

{table}

<div id="export">
  <button onclick="exportScores()">导出评分</button>
  <pre id="out" style="display:none"></pre>
</div>

<script>
const CELLS = {cells_json};
let idx = -1;
const scores = {{}};
const audio = document.getElementById('audio');
const now = document.getElementById('now');

function play(i) {{
  if (i < 0 || i >= CELLS.length) return;
  idx = i;
  document.querySelectorAll('td.cell').forEach(td => td.classList.remove('active'));
  const td = document.querySelector(`td.cell[data-i="${{i}}"]`);
  if (td) {{ td.classList.add('active'); td.classList.add('played'); }}
  const c = CELLS[i];
  audio.src = c.file;
  now.textContent = `${{c.label}}  ·  ${{c.duration}}s  ·  ${{i + 1}}/${{CELLS.length}}`;
  audio.play().catch(() => {{}});
}}

function rate(i, score, ev) {{
  if (ev) ev.stopPropagation();
  scores[CELLS[i].label] = score;
  const holder = document.querySelector(`td.cell[data-i="${{i}}"] .rate`);
  if (holder) holder.querySelectorAll('button').forEach(b =>
    b.classList.toggle('on', Number(b.dataset.s) === score));
}}

document.addEventListener('keydown', e => {{
  if (e.key === 'ArrowRight') {{ play(idx + 1); e.preventDefault(); }}
  else if (e.key === 'ArrowLeft') {{ play(idx - 1); e.preventDefault(); }}
  else if (e.key === ' ') {{ audio.paused ? audio.play() : audio.pause(); e.preventDefault(); }}
  else if (/^[1-5]$/.test(e.key) && idx >= 0) {{ rate(idx, Number(e.key) * 2); e.preventDefault(); }}
}});

function exportScores() {{
  const out = document.getElementById('out');
  const rows = CELLS.map(c => ({{
    label: c.label, temperature: c.temp, topk: c.topk,
    duration_s: c.duration, manual_score: scores[c.label] ?? null
  }}));
  out.style.display = 'block';
  out.textContent = JSON.stringify(rows, null, 2);
}}
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description="生成参数扫描试听页")
    ap.add_argument("sweep_dir", help="扫描输出目录（含 t*_k*.wav）")
    args = ap.parse_args()

    d = Path(args.sweep_dir)
    wavs = sorted(d.glob("t*_k*.wav"))
    if not wavs:
        raise SystemExit(f"没找到 wav：{d}/t*_k*.wav")

    import soundfile as sf

    entries = []
    for w in wavs:
        m = re.match(r"t([\d.]+)_k(\d+)\.wav$", w.name)
        if not m:
            continue
        temp, topk = float(m.group(1)), int(m.group(2))
        info = sf.info(w)
        entries.append({
            "temp": temp, "topk": topk, "file": w.name,
            "label": f"temp={temp} topk={topk}",
            "duration": round(info.duration, 1),
        })

    temps = sorted({e["temp"] for e in entries})
    topks = sorted({e["topk"] for e in entries})
    by_key = {(e["temp"], e["topk"]): e for e in entries}

    # 按矩阵顺序编号（行 = temp，列 = topk），键盘左右即沿此顺序
    ordered = []
    for t in temps:
        for k in topks:
            if (t, k) in by_key:
                ordered.append(by_key[(t, k)])
    for i, e in enumerate(ordered):
        e["i"] = i

    head = "".join(f"<th>topk={k}</th>" for k in topks)
    rows = []
    for t in temps:
        tds = []
        for k in topks:
            e = by_key.get((t, k))
            if not e:
                tds.append('<td style="color:#555">—</td>')
                continue
            btns = "".join(
                f'<button data-s="{s}" onclick="rate({e["i"]},{s},event)">{s // 2}</button>'
                for s in (2, 4, 6, 8, 10)
            )
            tds.append(
                f'<td class="cell" data-i="{e["i"]}" onclick="play({e["i"]})">'
                f'▶ t{t}/k{k}<span class="dur">{e["duration"]}s</span>'
                f'<div class="rate">{btns}</div></td>'
            )
        rows.append(f"<tr><th>temp={t}</th>{''.join(tds)}</tr>")

    table = f"<table><tr><th></th>{head}</tr>{''.join(rows)}</table>"
    html = TPL.format(table=table, cells_json=json.dumps(ordered, ensure_ascii=False))

    out = d / "listen.html"
    out.write_text(html, encoding="utf-8")
    print(f"试听页：{out.resolve()}")
    print(f"{len(ordered)} 组（{len(temps)} temp × {len(topks)} topk）")
    print("在浏览器打开，←→ 切换，1-5 打分，听完点「导出评分」")


if __name__ == "__main__":
    main()

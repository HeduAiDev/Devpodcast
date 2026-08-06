# Task 10 Review: audio_qa.py 试听质检

Reviewer 独立验证：读了 brief / report / review.pkg（commit 27a27d2），并在本仓库实际复跑测试、CLI 冒烟、逐项复算偏离声明。评审日期 2026-08-01。

## 1. Spec compliance 判定：✅

对 brief 逐项核对（diff 与 brief 实现逐行比对）：

| Brief 必达物 | 状态 | 说明 |
|---|---|---|
| `AudioQAReport` 7 字段 + `__post_init__` | ✅ | 字段名/类型/默认值全对齐 |
| `analyze(path, expected_minutes=35.0) -> AudioQAReport` | ✅ | 签名一致；立体声 downmix 为额外加分项（brief 未要求，无害） |
| `write_report(report, path)`（audio-qa.json） | ✅ | asdict + ensure_ascii=False + indent=2，与 brief 一致 |
| 4 条检查项（BLOCKING/WARN 文案） | ✅ | 阈值常量 1.20 / -0.1 / 25% / -40dB 逐字照抄 brief，含 issues 文案 |
| 测试 5 用例（合成正弦波） | ✅ | 用例全部保留，语义不变（仅修 2 处 brief 自身漏洞，见裁决） |
| 依赖 soundfile（numpy 随 torch） | ✅ | soundfile 0.14.0 已装，numpy 1.26.4 |
| 独立仓库零跨仓依赖 | ✅ | import 仅 stdlib（json/sys/dataclasses/pathlib）+ numpy + soundfile，无任何 `scripts.*` 跨模块引用 |
| CLI 约定（Task 7/8/9） | ✅ | sys.path 插入、无参守卫 rc2、退出码 0/1/2、`[BLOCKING]/[WARN]` 输出 —— 与 lint_voices.py（`return 2` / `[level] msg` / `1 if BLOCKING else 0`）逐点一致 |
| TDD 纪律 | ✅ | 红（ModuleNotFoundError）→ 绿（5/5）；全量 66 passed 无回归（实测复跑） |
| 提交身份 | ✅ | `git log -1 27a27d2`：author=devpodcast \<devpodcast@local\>；`.superpowers/` 未跟踪；分支 feat/m0-m1 |

缺项：无。多余项：无（无参守卫与 bool() 修复是对 brief 缺陷的修正，不是多余功能）。

## 2. 三处偏离裁决：全部接受

**偏离①（`test_over_duration_blocking` 50s/35min → 90s/expected_minutes=1.0）：接受。**
独立复算：35min × 60 × 1.2 = **2520s** > 50s。实测生成 50s wav + `analyze(expected_minutes=35.0)` → `any("时长" in i ...)` = **False**，brief 原版测试必挂。修正版 90s vs 60×1.2=72s 实测触发。测试语义（超时 → 时长 issue）未变，修正最小化，实现未动。brief 数学错误，修正合理。

**偏离②（测试补 `write_report` import）：接受。**
brief 测试文件 import 行确为 `from scripts.audio_qa import analyze, AudioQAReport`，而 `test_write_report` 调用 `write_report(r, out)` → 必抛 NameError。diff 已补。属 brief 遗漏，修正必要且最小。

**偏离③（`clipping = bool(r.peak_db > CLIP_DB)` + 无参守卫）：接受。**
独立验证类型链：`_db` 内 `np.log10` 返回 **np.float64**（实测 `type(r.peak_db)` = numpy.float64），`np.float64 > float` → **np.bool_**（实测）。`json.dumps(np.bool_(True))` 实测抛 `TypeError: Object of type bool_ is not JSON serializable`；用 brief 版实现（clipping=np.bool_）模拟 `test_write_report` 的 asdict+json.dumps 全链路，同样必挂。bool() 修复与 dataclass 声明的 `bool` 类型一致，最小修复。其余字段（np.float64 是 float 子类）无序列化问题，实测确认。
无参守卫：brief 的 `main()` 直接 `argv[0]`，无参时 IndexError；实测本实现无参 → usage 到 stderr + **rc=2**，与 Task 7/8/9 约定一致。

## 3. 代码质量判定：Approved（无 Critical / Important）

独立审查各计算：
- **dB 计算**：`20*log10(max(x, 1e-10))` 正确（floor 防 log(0)）。峰值取自全波形，PCM16 饱和写回 ±1.0 → peak_db=0.0 > -0.1 触发削波，实测正确。
- **削波检测**：`peak_db > -0.1`，阈值照抄 brief。注意 -0.1dB ≈ 幅值 0.989 而非 1.0（"接近满幅"语义，brief 定义如此，不判偏离）。
- **静音占比**：`|x| < 10^(-45/20) ≈ 0.00562`，正确；`len(sil)/len(x)` 无 overflow 问题。
- **时长逻辑**：`duration_s > target*1.20` 严格大于，"超 20%" 语义正确。
- **write_report 序列化**：bool() 修复后 asdict 全字段 JSON 可序列化，实测 JSON 落盘正确（duration_s/peak_db/clipping/silence_ratio/rms_db/issues/vram_gb 全在）。

Minor 问题（不阻塞）：
1. `_db` 返回 np.float64 而非 Python float（JSON 无碍，但字段注解 float 的纯度）；CLI 格式化亦无碍。
2. `main()` 对 `float(argv[2])` 非法输入 / wav 不存在无 try/except —— 裸 traceback 且 rc=1（误用 BLOCKING 语义码）。lint_script.py 有参数校验守卫模式（USAGE+rc2），此处未跟进。CLI 健壮性缺口，pytest 未覆盖。
3. 空 wav（0 采样）→ `len(sil)/len(x)` ZeroDivisionError。边缘情况。
4. 输出 `[BLOCKING] BLOCKING: …` 前缀冗余（issue 文案自带 BLOCKING:），但与 brief main() 逐字一致，属 brief 设计而非实现问题。
5. `vram_gb` 恒 0.0（analyze 不计算显存）—— brief 本身未定义显存检查，dataclass 字段占位，报告 Concern #5 已如实说明，非实现偏离。

## 4. ⚠️ Cannot verify 清单

1. **TDD 中间态时序**（"首跑 4 passed/1 failed"）：最终 diff 无法证明先红后绿的精确过程。但 brief 版实现必挂点（np.bool_ 序列化）已独立模拟证实，报告可信度高。
2. **"本机缺 soundfile、已 pip install"的历史**：仅能确认现状 soundfile 0.14.0 已装（实测），安装过程无法回溯。对交付无影响。
3. 报告所述 CLI 冒烟细节（/tmp/qa_good.json 各字段值）：已独立重跑 CLI 冒烟（无参 rc=2、正常 rc=0、削波 rc=1 + `[BLOCKING]` 输出 + JSON 字段），结果与报告一致，此项实际已验证，非不可验证项。

---

**结论**：Spec ✅ / 三处偏离全部接受 / 质量 Approved。Critical=0，Important=0，Minor=5（均不阻塞）。

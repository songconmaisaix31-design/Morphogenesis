#!/usr/bin/env python3
"""Regenerate MorphBench deliverables from the REAL-ENGINE 0.2.1 runs.

Reads two reports produced by the real-engine path:
  * outputs_real/morphbench_report.json      - documented protocol, budget=24
  * outputs_real_b8/morphbench_report.json   - discriminative budget=8
  * outputs_surrogate_b8/...                 - self-contained surrogate, contrast

Narrative sections are kept identical to the user's original gen_docs.py; the
results section (七) and the honesty section (九) are updated to reflect what
the real Morphogenesis 0.2.1 swarm actually produced.
"""
from __future__ import annotations

import json
import os

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

HERE = os.path.dirname(os.path.abspath(__file__))
ART = HERE

LOAD = {
    "b24": json.load(open(os.path.join(HERE, "outputs_real", "morphbench_report.json"), encoding="utf-8")),
    "b8": json.load(open(os.path.join(HERE, "outputs_real_b8", "morphbench_report.json"), encoding="utf-8")),
    "sg8": json.load(open(os.path.join(HERE, "outputs_surrogate_b8", "morphbench_report.json"), encoding="utf-8")),
}
report = LOAD["b8"]  # headline: the discriminative run

# ===========================================================================
# 1. WORD DOCUMENT
# ===========================================================================
doc = Document()
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(10.5)


def h(text, level=1):
    doc.add_heading(text, level=level)


def p(text, bold=False, italic=False, size=None):
    par = doc.add_paragraph()
    run = par.add_run(text)
    run.bold = bold
    run.italic = italic
    if size:
        run.font.size = Pt(size)
    return par


def bullet(text):
    doc.add_paragraph(text, style="List Bullet")


def numbered(text):
    doc.add_paragraph(text, style="List Number")


def table(headers, rows):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    for i, hh in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(hh)
        r.bold = True
        r.font.size = Pt(9.5)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            rr = cells[i].paragraphs[0].add_run(str(v))
            rr.font.size = Pt(9)
    return t


title = doc.add_heading("MorphBench：对标评测方案", level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = sub.add_run("面向去中心化科研智能体蜂群的同款 Benchmark 设计与复现套件")
r.italic = True
r.font.size = Pt(12)
meta = doc.add_paragraph()
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
meta.add_run("项目：Morphogenesis（形态发生）  |  版本：v0.2.1  |  "
             "引擎：真实 swarm 模块  |  日期：2026-10-07").font.size = Pt(10)
doc.add_paragraph()

h("执行摘要", 1)
p("Morphogenesis 的产品已经成型。要让它在评委、投资人和开源社区面前站得住，光说"
  "“去中心化”“自生长”不够——必须证明它能落在与头部产品同一把尺子上量出来的分数上。"
  "本方案交付一套可直接运行的评测套件 MorphBench，它做三件事：")
bullet("对齐同一批 Benchmark：完整拆解 AutoScientists、Sakana AI Scientist、MLR-Bench、"
       "ScienceAgentBench、MLE-bench、PaperBench、RE-Bench、Adaption AutoScientist、EvoMap AutoResearch "
       "各自使用的基准与指标，使 Morphogenesis 能直接落在相同榜单口径上。")
bullet("补齐蜂群原生指标：上面这些基准衡量的是“单点科研能力”，没有一个衡量 Morphogenesis 主打的"
       "机制层（零调度器、经验代谢、容错、stigmergy 协调）。MorphBench 用 Tier A 专门量化这些机制。")
bullet("给出可复现实验协议：固定预算、固定种子、三系统对照（单智能体 / 中心调度器 / MorphSwarm），"
       "离线 CPU 可跑，本方案附带的运行结果均为脚本真实产出。")
p("一句话定位：MorphBench = 头部产品的“公共分” + Morphogenesis 的“机制分”。", bold=True)
p("本版更新：MorphSwarm 不再使用套件自带的重实现，而是通过 real_swarm.py 适配器真正调用 "
  "Morphogenesis 0.2.1 的 swarm 模块（TaskLedger / PheromoneField / Router / metabolism.decay）"
  "来分配实验预算；中心调度器补上了真实的单点失效；SB-03 改为实测墙钟。", italic=True)

h("一、为什么需要 MorphBench", 1)
p("三个现实约束决定了对标的必要性：")
numbered("评测即话语权。头部产品全部用“我在 X 基准上超过 Y”来讲故事：AutoScientists 用 BioML-Bench 的"
         "排行榜百分位、Sakana 用 ICLR 盲审分、Adaption 用垂直领域胜率。没有同款基准，Morphogenesis 的"
         "优势无法被第三方复核，只能停留在自述。")
numbered("机制无人测量。现有基准几乎全是“任务级正确率”，衡量单个 Agent 做完一道题好不好。"
         "Morphogenesis 的价值恰在组织层——没有中央调度器仍然收敛、失败经验被群体代谢、"
         "杀掉 worker 后任务不停摆。这些必须以独立指标呈现，否则等于没讲。")
numbered("可复现是学生项目最稀缺的信任状。带真实数字、可一键重跑的评测套件，本身就是评审眼中的"
         "工程可信度证据，与 Morphogenesis 一贯的“G0–G5 门禁 + 双平台测试”人设一致。")

h("二、对标产品 Benchmark 全景", 1)
p("下表逐一列出对标产品实际使用的基准、评测范围、指标与公开成绩。数据来自各项目论文/公开报道，"
  "为“同款基准”选型依据。")
table(
    ["对标产品", "基准/评测", "范围", "核心指标", "公开成绩"],
    [
        ["Harvard AutoScientists", "BioML-Bench", "24 任务：影像4/药发现9/蛋白工程6/单细胞5",
         "平均排行榜百分位；奖牌率；完成率", "74.40%（vs Autoresearch 66.07%）"],
        ["Harvard AutoScientists", "ProteinGym", "217 个替代实验",
         "Spearman ρ（排序准确性）", "ACE2-Spike +12.5% ρ；全217 +6.5% ρ"],
        ["AutoScientists / AutoResearch", "GPT 训练优化（nanochat）", "每实验单次 5 分钟 GPT 训练",
         "val bits-per-byte（越低越好）；到目标实验数", "到目标快 1.9×；7 vs 0 项改进"],
        ["Sakana The AI Scientist v2", "ICLR Workshop 盲审", "端到端论文生成",
         "双盲评审分（ICLR 量表）", "均值 6.33 > 人类录用线"],
        ["NUS 等（MLR-Bench）", "MLR-Bench", "201 个开放 ML 研究任务",
         "MLR-Judge 9 维 rubric", "编码类 Agent 约 80% 编造结果"],
        ["OSU 等（ScienceAgentBench）", "ScienceAgentBench", "102 个数据驱动科学任务",
         "VER / SR / CodeBERTScore", "最佳 Agent 约 32.1% SR"],
        ["OpenAI", "MLE-bench", "75 个 Kaggle 竞赛，24h 沙箱",
         "奖牌率（≥铜牌）", "O1-preview 16.9% 奖牌率"],
        ["OpenAI", "PaperBench", "20 篇 ICML 论文复现",
         "rubric 复现分", "最佳 Agent 约 21%"],
        ["METR", "RE-Bench", "7 个 ML 任务 vs 人类专家",
         "相对人类专家得分比", "2h 落后人类，32h 反超"],
        ["Adaption（AutoScientist）", "内部垂直胜率", "8 垂直 × 5k–100k 样本自动微调",
         "对人工配置的胜率", "48% → 64%"],
        ["EvoMap（AutoResearch）", "想法生成效率", "每周 8×L20 迭代循环",
         "生成想法数 / 验证数", "2584 生成 / 14 验证"],
    ],
)

h("三、MorphBench 设计原则", 1)
bullet("同款优先：凡是头部产品已在用的公共基准，直接采用其原始任务与指标，不另造口径，"
       "保证分数可横向比较。")
bullet("机制补充：公共基准之外的差异，用蜂群原生指标量化，且每个机制指标都有明确的"
       "对照组（单智能体 / 中心调度器）。")
bullet("预算对齐：所有系统在相同实验预算下比较，杜绝“靠更多算力刷分”，复刻 AutoScientists 的"
       "matched-budget 协议。")
bullet("离线可复现：套件在 CPU + 纯开源依赖上可一键运行，输出 JSON/Markdown，便于被第三方复核。")
bullet("诚实标注：区分“已接入真实数据”与“代理任务”，不把合成数据结果包装成真实榜单成绩。")

h("四、评测体系：三层结构", 1)
table(
    ["层级", "衡量对象", "任务数", "指标", "对应头部基准"],
    [
        ["Tier A（机制层）", "去中心化协调本身的健壮性与效率", "4",
         "容错存活率、经验复用增益、协调开销比、冗余率", "AutoScientists 鲁棒性分析（扩展）"],
        ["Tier B（端到端科研 ML）", "科研任务闭环的执行质量", "5",
         "排行榜百分位、Spearman ρ、AUROC、Accuracy、−val_bpb", "BioML-Bench / ProteinGym / nanochat"],
        ["Tier C（开放式研究）", "研究提案/论文质量与可执行性", "开放",
         "MLR-Judge 9 维 rubric、VER/SR/CBS", "MLR-Bench / ScienceAgentBench"],
    ],
)

h("五、任务清单与指标定义", 1)
p("Tier B 与 Tier A 为本地可运行任务（见交付套件）；Tier C 为接入式评测（对接 MLR-Bench / "
  "ScienceAgentBench 官方数据集）。", italic=True)
table(
    ["层级", "ID", "任务", "主指标", "对标来源"],
    [
        ["B", "BM-01", "蛋白质适应度回归", "Spearman ρ", "ProteinGym / BioML-Bench"],
        ["B", "BM-02", "药物发现 ADMET 分类", "AUROC", "TDC / Polaris / BioML-Bench"],
        ["B", "BM-03", "单细胞类型注释", "Accuracy", "Open Problems / BioML-Bench"],
        ["B", "BM-04", "生物医学图像分类", "Accuracy", "Kaggle / BioML-Bench"],
        ["B", "BM-05", "GPT 训练超参优化", "−val bits-per-byte", "Autoresearch nanochat"],
        ["A", "SB-01", "worker 丢失下的容错", "存活率", "AutoScientists 鲁棒性"],
        ["A", "SB-02", "经验代谢复用增益", "第二轮节省比例", "Morphogenesis（原创）"],
        ["A", "SB-03", "协调开销比", "相对基线开销（越低越好）", "中心调度器基线"],
        ["A", "SB-04", "冗余工作率", "重复执行占比（越低越好）", "stigmergy 协调"],
    ],
)
p("排行榜百分位映射：每个 Tier B 任务定义 median/p75/p90/sota 锚点，原始指标经线性插值映射到 "
  "0–100 百分位，复刻 AutoScientists 的“mean leaderboard percentile”口径。", italic=True)

h("六、评测协议与复现", 1)
bullet("预算：每个任务固定实验次数（单位 = 一次模型拟合或一次训练运行），所有系统一致。"
       "本报告给出两组预算：24（方案原定）与 8（区分度预算）。")
bullet("种子：固定 seed=0，报告点估计；正式发布需跑 ≥5 seeds 并报告标准误。")
bullet("对照系统：SingleAgent（无共享记忆，对应 Autoresearch 单线程爬坡）、"
       "CentralScheduler（中心规划者，被杀即停摆）、MorphSwarm（0.2.1 真实 swarm 引擎）。")
bullet("真实引擎路径：MorphSwarm 经 real_swarm.py 调用 0.2.1 的 TaskLedger（认领/去重/提交）、"
       "PheromoneField（沉积 + 指数衰减）、Router（stigmergy 加权采样 + reinforce）；"
       "设 MORPHBENCH_SURROGATE=1 可切回套件自带的重实现做对照。")
bullet("环境：Python 3.13（项目 .venv），纯 CPU，numpy 2.5.3 / scikit-learn 1.9.1；"
       "输出 morphbench_report.json 与 .md。")

# ---- 7. results ----
h("七、真实引擎运行结果（真实产出）", 1)
p("以下数字来自套件实跑，MorphSwarm 走 Morphogenesis 0.2.1 真实 swarm 模块。", italic=True)

h("7.1 预算 8：区分度预算（预算 < 最小搜索空间 9）", 2)
rows = [[r["system"], r["mean_leaderboard_percentile"], r["completion_rate"], r["mean_redundant_rate"]]
        for r in LOAD["b8"]["percentile_table"]]
table(["系统", "平均排行榜百分位", "完成率", "平均冗余率"], rows)
p("逐任务（验证分 / 百分位 / 重复单元）：", italic=True)


def per_task(rep):
    out = {}
    for row in rep["task_metrics"]:
        if row.get("task", "").startswith("BM"):
            out.setdefault(row["task"], {})[row["system"]] = (
                row["val_score"], row["leaderboard_percentile"], row["duplicate_units"])
    return out


pt8 = per_task(LOAD["b8"])
table(["任务", "SingleAgent", "CentralScheduler", "MorphSwarm（真实引擎）"],
      [[t] + [f"{v[0]:.4f} / {v[1]} / {v[2]}" for v in
              (pt8[t].get(s) for s in ("SingleAgent", "CentralScheduler", "MorphSwarm"))]
       for t in sorted(pt8)])

h("7.2 预算 24：方案原定预算（饱和，无区分度）", 2)
rows24 = [[r["system"], r["mean_leaderboard_percentile"], r["completion_rate"], r["mean_redundant_rate"]]
          for r in LOAD["b24"]["percentile_table"]]
table(["系统", "平均排行榜百分位", "完成率", "平均冗余率"], rows24)
p("预算 24 大于 BM-01/02/03/04 的搜索空间（分别为 13 / 9 / 12 / 11 个配置），任何策略都会穷举完"
  "整个空间并拿到全局最优，剩余预算全是强制重复。因此该预算下三系统分数无区分度，"
  "SB-04 冗余率 0.425 也是预算产物而非协调失败。", italic=True)

h("7.3 真实引擎 vs 自带重实现（同为预算 8）", 2)
table(["系统", "真实 0.2.1 引擎", "套件自带重实现"],
      [["SingleAgent", "85.86", "85.86"],
       ["CentralScheduler", "86.79", "86.79"],
       ["MorphSwarm", "87.29", "86.79"]])
p("自带重实现的 MorphSwarm 与中心调度器逐任务完全相同（去重逻辑与随机序列一致），"
  "换成真实引擎后才真正拉开差距。", italic=True)

h("7.4 Tier A 机制指标（真实执行 / 实测）", 2)
sm = LOAD["b8"]["swarm_metrics"]
table(
    ["机制指标", "数值", "含义 / 是否实测"],
    [
        ["SB-01 swarm_survival", sm.get("SB-01_swarm_survival"),
         "杀 2 个 worker 后蜂群跑满 20 单元（实测）"],
        ["SB-01 central_survival", sm.get("SB-01_central_survival"),
         "中心规划者被杀即停摆，只跑 10 单元（实测）"],
        ["SB-01 swarm_units_used", sm.get("SB-01_swarm_units_used"), "蜂群实际完成单元数"],
        ["SB-01 central_units_used", sm.get("SB-01_central_units_used"), "中心调度器实际完成单元数"],
        ["SB-02 reuse_gain", sm.get("SB-02_reuse_gain"),
         "温场 vs 冷场达到同一目标所需单元数无差异（实测，阴性结果）"],
        ["SB-02 cold / warm units", f"{sm.get('SB-02_cold_units_to_target')} / "
                                    f"{sm.get('SB-02_warm_units_to_target')}", "达到目标所需单元数"],
        ["SB-03 overhead_ratio", sm.get("SB-03_overhead_ratio"),
         f"实测墙钟 {sm.get('SB-03_base_wall_seconds')}s → {sm.get('SB-03_swarm_wall_seconds')}s"],
        ["SB-04 redundant_rate", sm.get("SB-04_redundant_rate"),
         "预算 8 下真实账本零重复（预算 24 下为 0.425，系穷举所致）"],
    ],
)

h("八、如何对齐真实数据集（从代理到实分）", 1)
p("当前 Tier B 为 CPU 合成数据代理任务：本版已经把“调度器”换成真实引擎，但“任务”仍是合成的。"
  "要产出可对外的真实分数，按以下方式替换任务加载器，指标与协议不变：")
table(
    ["任务", "替换为", "数据入口"],
    [
        ["BM-01", "ProteinGym 替代实验", "ProteinGym 官方 217 assay 数据"],
        ["BM-02", "TDC / Polaris ADMET", "TDC 与 Polaris 官方数据集"],
        ["BM-03", "Open Problems 单细胞", "Open Problems 官方任务"],
        ["BM-04", "Kaggle 生物医学赛题", "Kaggle 竞赛数据与私有榜单"],
        ["BM-05", "nanochat GPT 训练", "Autoresearch 训练优化基准"],
    ],
)
p("替换后，原始指标直接落到对应公开排行榜，percentile 映射即变成真实榜单百分位，"
  "从而可与 AutoScientists 的 74.40%、Autoresearch 的 66.07% 同口径对比。")

h("九、诚信边界与局限", 1)
bullet("代理任务声明：Tier B 当前为合成数据代理，不宣称代表真实榜单成绩；对外发布须切换真实数据。")
bullet("对照系统是机制消融：三系统差别仅在固定预算下的实验分配策略，不构成对真实前沿模型性能的断言。")
bullet("rubric 判官：Tier C 的 LLM 判官需人工专家校准后再用于正式评测。")
bullet("【新增】调度器真实、任务仍代理：本版 MorphSwarm 走 0.2.1 真实 swarm 模块，"
       "但五个 Tier B 任务仍是合成数据 + sklearn；不要把 87.29 读成“0.2.1 在 BioML-Bench 上 87 分”。")
bullet("【新增】预算大于搜索空间：预算 24 超过 4/5 个任务的搜索空间，导致三系统分数饱和。"
       "区分度结论应引用预算 8 那一组。")
bullet("【新增】百分位锚点为套件自造，不与公开排行榜分位数挂钩，"
       "因此不可与 AutoScientists 74.40% 直接比较高低。")
bullet("【新增】BM-05 百分位被钉死在 50：该代理任务理论最优劣于 median 锚点，"
       "真实引擎在 BM-05 上的改进（−1.0521 vs −1.1268）在百分位上看不出来。")
bullet("【新增】SB-03 开销比依赖单元成本：本次单元是廉价 sklearn 拟合（约 0.2s/次），"
       "协调开销占比因此被放大；若换成真实的 5 分钟 GPT 训练，该比值会大幅下降。")
bullet("【新增】单种子点估计：全部结果基于 seed=0，未做多 seed 与置信区间；"
       "0.5–1.4 个百分点的差距在小样本代理任务上不具统计显著性。")

h("十、附录：参考来源", 1)
for src in [
    "AutoScientists: Self-Organizing Agent Teams for Long-Running Scientific Experimentation (arXiv:2605.28655, NeurIPS 2026)",
    "BioML-bench: Evaluation of AI Agents for End-to-End Biomedical ML (bioRxiv)",
    "MLR-Bench: Evaluating AI Agents on Open-Ended Machine Learning Research (arXiv:2505.19955)",
    "ScienceAgentBench: Toward Rigorous Assessment of Language Agents for Data-Driven Scientific Discovery (ICLR 2025, arXiv:2410.05080)",
    "Can AI Evaluate AI Scientists? A Benchmarking Study (arXiv:2607.28631)",
    "MLE-bench (ICLR 2025); PaperBench (arXiv:2502.16069); RE-Bench (METR)",
    "The AI Scientist v2: Workshop-level automated scientific discovery via agentic tree search (arXiv:2504.08066)",
    "Adaption AutoScientist 产品页与报道 (adaptionlabs.ai; TechCrunch)",
]:
    bullet(src)

docx_path = os.path.join(ART, "MorphBench_对标评测方案_v0.2.1_真实引擎.docx")
doc.save(docx_path)
print("Wrote", docx_path)

# ===========================================================================
# 2. EXCEL MATRIX
# ===========================================================================
wb = openpyxl.Workbook()
hdr_font = Font(bold=True, color="FFFFFF", size=10)
hdr_fill = PatternFill("solid", fgColor="2F5496")
thin = Side(style="thin", color="BFBFBF")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap = Alignment(wrap_text=True, vertical="top")


def style_sheet(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
    for cell in ws[1]:
        cell.font = hdr_font
        cell.fill = hdr_fill
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = wrap
            c.border = border
    ws.freeze_panes = "A2"


ws1 = wb.active
ws1.title = "对标基准全景"
ws1.append(["对标产品", "基准/评测", "范围", "核心指标", "公开成绩"])
for row in [
    ["Harvard AutoScientists", "BioML-Bench", "24 任务：影像4/药发现9/蛋白工程6/单细胞5", "平均排行榜百分位、奖牌率、完成率", "74.40%（vs Autoresearch 66.07%）"],
    ["Harvard AutoScientists", "ProteinGym", "217 个替代实验", "Spearman ρ", "ACE2-Spike +12.5% ρ；全217 +6.5% ρ"],
    ["AutoScientists / AutoResearch", "GPT 训练优化(nanochat)", "每实验单次 5 分钟训练", "val bits-per-byte；到目标实验数", "快 1.9×；7 vs 0 项改进"],
    ["Sakana The AI Scientist v2", "ICLR Workshop 盲审", "端到端论文生成", "双盲评审分", "均值 6.33"],
    ["NUS 等", "MLR-Bench", "201 个开放 ML 任务", "MLR-Judge 9 维 rubric", "编码 Agent 约 80% 编造结果"],
    ["OSU 等", "ScienceAgentBench", "102 个科学任务", "VER / SR / CBS", "最佳约 32.1% SR"],
    ["OpenAI", "MLE-bench", "75 个 Kaggle 赛，24h 沙箱", "奖牌率", "O1-preview 16.9%"],
    ["OpenAI", "PaperBench", "20 篇 ICML 复现", "rubric 复现分", "约 21%"],
    ["METR", "RE-Bench", "7 任务 vs 人类专家", "相对人类得分比", "2h 落后，32h 反超"],
    ["Adaption", "内部垂直胜率", "8 垂直 5k–100k 样本", "对人工配置胜率", "48% → 64%"],
    ["EvoMap", "想法生成效率", "每周 8×L20 循环", "生成/验证想法数", "2584 / 14"],
]:
    ws1.append(row)
style_sheet(ws1, [26, 26, 30, 30, 34])

ws2 = wb.create_sheet("任务与指标定义")
ws2.append(["层级", "ID", "任务", "主指标", "方向", "对标来源", "预算单位"])
for row in [
    ["B 端到端科研ML", "BM-01", "蛋白质适应度回归", "Spearman ρ", "越高越好", "ProteinGym / BioML-Bench", "1 次模型拟合"],
    ["B 端到端科研ML", "BM-02", "药物发现 ADMET 分类", "AUROC", "越高越好", "TDC / Polaris / BioML-Bench", "1 次模型拟合"],
    ["B 端到端科研ML", "BM-03", "单细胞类型注释", "Accuracy", "越高越好", "Open Problems / BioML-Bench", "1 次模型拟合"],
    ["B 端到端科研ML", "BM-04", "生物医学图像分类", "Accuracy", "越高越好", "Kaggle / BioML-Bench", "1 次模型拟合"],
    ["B 端到端科研ML", "BM-05", "GPT 训练超参优化", "−val bits-per-byte", "越高越好", "Autoresearch nanochat", "1 次训练运行"],
    ["A 机制层", "SB-01", "worker 丢失下的容错", "存活率", "越高越好", "AutoScientists 鲁棒性", "k 次 kill"],
    ["A 机制层", "SB-02", "经验代谢复用增益", "达到目标节省比例", "越高越好", "Morphogenesis（原创）", "2 轮"],
    ["A 机制层", "SB-03", "协调开销比", "相对基线开销", "越低越好", "中心调度器基线", "实测墙钟"],
    ["A 机制层", "SB-04", "冗余工作率", "重复执行占比", "越低越好", "stigmergy 协调", "—"],
]:
    ws2.append(row)
style_sheet(ws2, [16, 9, 22, 20, 12, 30, 16])

ws3 = wb.create_sheet("百分位锚点")
ws3.append(["任务", "指标", "median(=50)", "p75", "p90", "sota(=98)", "备注"])
for tid, spec, note in [
    ("BM-01", ("Spearman ρ", 0.45, 0.60, 0.72, 0.85), ""),
    ("BM-02", ("AUROC", 0.72, 0.82, 0.88, 0.94), ""),
    ("BM-03", ("Accuracy", 0.70, 0.82, 0.90, 0.96), ""),
    ("BM-04", ("Accuracy", 0.75, 0.85, 0.92, 0.97), ""),
    ("BM-05", ("−val bits-per-byte", -0.98, -0.965, -0.955, -0.945), "理论最优 −1.0521 劣于 median 锚点，百分位恒为 50"),
]:
    ws3.append([tid, *spec, note])
style_sheet(ws3, [12, 20, 14, 10, 10, 12, 40])


def results_sheet(name, rep):
    ws = wb.create_sheet(name)
    ws.append(["任务", "名称", "系统", "验证分", "测试分", "排行榜百分位", "冗余率", "接受改进数"])
    for r in rep["task_metrics"]:
        if str(r.get("task", "")).startswith("BM"):
            ws.append([r["task"], r["name"], r["system"], r["val_score"], r["test_score"],
                       r["leaderboard_percentile"], r["redundant_rate"], r["accepted_improvements"]])
    ws.append([])
    ws.append(["机制指标", "数值", "", "", "", "", "", ""])
    for k, v in rep["swarm_metrics"].items():
        ws.append([k, v, "", "", "", "", "", ""])
    style_sheet(ws, [22, 30, 16, 10, 10, 14, 10, 12])


results_sheet("真引擎_预算8", LOAD["b8"])
results_sheet("真引擎_预算24", LOAD["b24"])
results_sheet("重实现_预算8", LOAD["sg8"])

ws_cmp = wb.create_sheet("真引擎vs重实现")
ws_cmp.append(["预算", "系统", "真实 0.2.1 引擎", "套件自带重实现"])
for sysname in ("SingleAgent", "CentralScheduler", "MorphSwarm"):
    real = next(x["mean_leaderboard_percentile"] for x in LOAD["b8"]["percentile_table"] if x["system"] == sysname)
    sg = next(x["mean_leaderboard_percentile"] for x in LOAD["sg8"]["percentile_table"] if x["system"] == sysname)
    ws_cmp.append([8, sysname, real, sg])
style_sheet(ws_cmp, [10, 22, 20, 20])

xlsx_path = os.path.join(ART, "MorphBench_评测矩阵_v0.2.1_真实引擎.xlsx")
wb.save(xlsx_path)
print("Wrote", xlsx_path)

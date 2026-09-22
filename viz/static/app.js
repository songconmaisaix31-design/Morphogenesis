/* global echarts */
"use strict";

const byId = (id) => document.getElementById(id);
const text = (id, value) => { byId(id).textContent = String(value); };
const agentLabel = (agent) => agent && typeof agent === "object" ? `${agent.role ?? "unknown"}#${agent.instance ?? "?"}` : String(agent ?? "unknown");
const clear = (id) => { byId(id).replaceChildren(); };
const number = (value, digits = 2) => Number.isFinite(value) ? Number(value).toFixed(digits) : "未知";
const chartFor = (id) => echarts.getInstanceByDom(byId(id)) ?? echarts.init(byId(id));
const shortGeneId = (value) => { const id = String(value ?? "unknown"); return id.length > 14 ? `${id.slice(0, 6)}…${id.slice(-6)}` : id; };
const stageLabel = {
  task_ready: "题目待执行", repair_selected: "首次选路", repair_reviewed: "首次复核", gene_generated: "经验生成",
  awaiting_offline: "等待下线确认", member_offline: "成员已下线", recovery_ready: "恢复任务就绪", recovery_selected: "恢复选路",
  recovery_reviewed: "恢复复核", gene_adopted: "经验已采用", decaying: "权重衰减中", archived: "经验已归档",
  completed: "彩排完成", failed: "彩排已停止",
};

function append(parent, tag, value, className = "") {
  const element = document.createElement(tag); element.textContent = value;
  if (className) element.className = className;
  parent.append(element); return element;
}

function showEmpty(chartId, emptyId, message) {
  byId(chartId).style.display = "none";
  const empty = byId(emptyId); empty.hidden = false; empty.textContent = message;
}

function showChart(chartId, emptyId) {
  byId(chartId).style.display = "block";
  byId(emptyId).hidden = true;
}

function stateCards(acceptance) {
  ["contract_local", "interface_live", "task_live"].forEach((key) => {
    const value = acceptance[key] ?? "not_run";
    const element = byId(key); element.textContent = value;
    element.className = `state-${value}`;
  });
}

function matchingPipe(pipes, current) {
  return pipes.find((pipe) => pipe.src?.role === current.src?.role && pipe.src?.instance === current.src?.instance && pipe.dst?.role === current.dst?.role && pipe.dst?.instance === current.dst?.instance);
}

function topologyGraph(pipes, members) {
  if (!pipes?.length) return showEmpty("story-pipe-chart", "story-pipe-empty", "尚无管道快照");
  showChart("story-pipe-chart", "story-pipe-empty");
  const availability = new Map((members ?? []).map((member) => [agentLabel(member.agent), member]));
  const names = new Set(pipes.flatMap((pipe) => [agentLabel(pipe.src), agentLabel(pipe.dst)]));
  // Labels sit below every node.  With a circular graph this reserves the
  // top edge for the node itself and prevents the upper builder name from
  // being clipped on a 1366px projector.
  const nodes = [...names].map((name) => {
    const member = availability.get(name); const online = member?.available !== false;
    return {
      name, online, symbolSize: 28,
      itemStyle: { color: online ? "#66c2ff" : "#7a8795" },
      label: { color: online ? "#ecf5ff" : "#a8bbcd", position: "bottom" },
    };
  });
  const links = pipes.map((pipe) => ({
    source: agentLabel(pipe.src), target: agentLabel(pipe.dst), active: pipe.active,
    value: `权重 ${number(pipe.weight)} · 流量 ${number(pipe.flow)} · 成功率 ${(Number(pipe.success_rate) * 100).toFixed(0)}% · ${pipe.active ? "在线" : "离线"}`,
    lineStyle: { width: Math.max(2, Math.min(12, 1 + Number(pipe.weight) * 4)), type: pipe.active ? "solid" : "dashed", color: pipe.active ? "#5ebeea" : "#778494", opacity: pipe.active ? 1 : .55 },
  }));
  chartFor("story-pipe-chart").setOption({ animation: false, tooltip: { renderMode: "richText", formatter: (point) => point.data.value || point.name }, series: [{ type: "graph", layout: "circular", roam: false, top: 24, bottom: 32, label: { show: true, distance: 4, fontSize: 10 }, lineStyle: { curveness: .1 }, data: nodes, links }] }, { notMerge: true });
}

function rehearsalBoard(rehearsal) {
  if (!rehearsal) {
    text("rehearsal-mode", "尚未加载彩排快照；不展示预设通过结果。");
    text("story-question", "未加载"); text("story-question-detail", "等待实际题目、已知失败点与来源。");
    text("story-checkpoint-rate", "未加载"); clear("story-checkpoints"); append(byId("story-checkpoints"), "li", "尚无独立 checkpoint 快照");
    clear("story-pipes"); append(byId("story-pipes"), "p", "尚无管道快照"); showEmpty("story-pipe-chart", "story-pipe-empty", "尚无管道快照");
    text("story-offline-member", "未发生 / 未加载"); text("story-offline-reason", "下线原因和恢复 checkpoint 均须来自实际快照。");
    clear("story-genes"); append(byId("story-genes"), "p", "尚无经验池快照");
    return;
  }
  const current = rehearsal.current;
  const history = rehearsal.history ?? [];
  const prior = history.length > 1 ? history[history.length - 2] : null;
  const replay = rehearsal.mode === "replay";
  const modeLabel = replay ? "回放视图" : rehearsal.mode === "mock" ? "模拟快照" : "现场快照";
  text("rehearsal-mode", `${modeLabel} · ${stageLabel[current.stage] ?? "未标记阶段"} · #${current.sequence}${replay ? " · 原始证据只读" : ""}`);
  const recoveryTask = String(current.task_id ?? "").startsWith("recovery-");
  text("story-question", recoveryTask ? "恢复任务（新样例）" : "首次修复任务"); byId("story-question").title = String(current.task_id ?? "");
  text("story-question-detail", recoveryTask ? "移除成员后，另一名构建成员在新坏样例上重新选路。" : "修复 clamp、mean、unique 三个已知 Bug，并交由独立复核。");

  const checkpointList = byId("story-checkpoints"); clear("story-checkpoints");
  if (!current.checkpoints) {
    text("story-checkpoint-rate", "未判定"); append(checkpointList, "li", "尚无独立 checkpoint 快照");
  } else {
    const checks = current.checkpoints;
    text("story-checkpoint-rate", `${checks.passed_count}/${checks.total} · ${(checks.ratio * 100).toFixed(0)}%`);
    checks.checks.forEach((check) => append(checkpointList, "li", `${check.name}：${check.passed === true ? "通过" : check.passed === false ? "失败" : "待判定"}`, `check-${String(check.passed)}`));
  }

  const pipeList = byId("story-pipes"); clear("story-pipes");
  topologyGraph(current.pipes, current.members);
  if (!current.pipes?.length) append(pipeList, "p", "尚无管道快照");
  current.pipes.forEach((pipe) => {
    const before = prior ? matchingPipe(prior.pipes ?? [], pipe) : null;
    const row = document.createElement("div"); row.className = `pipe-row ${pipe.active ? "pipe-active" : "pipe-inactive"}`;
    row.style.setProperty("--pipe-width", `${Math.max(3, Math.min(14, 2 + Number(pipe.weight) * 4))}px`);
    append(row, "strong", `${agentLabel(pipe.src)} → ${agentLabel(pipe.dst)}`);
    append(row, "span", `权重 ${number(pipe.weight)}${before ? `（前 ${number(before.weight)}）` : "（无前序）"} · 流量 ${number(pipe.flow)} · ${(Number(pipe.success_rate) * 100).toFixed(0)}% · ${pipe.active ? "在线" : "离线"}`);
    pipeList.append(row);
  });

  const removed = current.routing?.removed_member;
  const offlineMember = current.members?.find((member) => !member.available);
  text("story-offline-member", removed ? `${agentLabel(removed)} 已下线` : offlineMember ? `${agentLabel(offlineMember.agent)} 已下线` : "尚未发生成员下线");
  if (removed || offlineMember) {
    const member = offlineMember ?? current.members.find((entry) => entry.agent?.role === removed?.role && entry.agent?.instance === removed?.instance);
    const selected = current.routing?.selected_attempt?.agent;
    text("story-offline-reason", `${member?.reason ?? "真实快照未提供原因"}；发生在两任务之间。恢复选路：${selected ? agentLabel(selected) : "尚未选择"}。`);
  } else {
    text("story-offline-reason", "未发生下线；不暗示在途进程被终止或已经恢复。");
  }

  const geneList = byId("story-genes"); clear("story-genes");
  if (!current.genes?.length) append(geneList, "p", "尚无 GeneView 快照");
  current.genes.forEach((gene) => {
    const card = document.createElement("div"); card.className = "gene-fact";
    append(card, "strong", `${shortGeneId(gene.ref?.gene_id)} v${gene.ref?.version ?? 1}`);
    append(card, "span", `生成：${gene.source_attempt ? agentLabel(gene.source_attempt.agent) : "未记录"}`);
    append(card, "span", `采用 ${gene.use_count} · 权重 ${number(gene.weight)}`);
    append(card, "span", `τ ${number(gene.tau_seconds, 1)} 秒 · ${gene.archived_at === null ? "活跃" : "已归档"}`);
    geneList.append(card);
  });
}

function geneGraph(genes, adoptions) {
  if (!genes.length) return showEmpty("gene-chart", "gene-empty", "未导出 T3M GeneView；不能从消息、候选或结果反推谱系。");
  showChart("gene-chart", "gene-empty");
  const nodeName = (gene) => `${gene.ref.gene_id}@v${gene.ref.version ?? 1}`;
  const shortGeneLabel = (gene) => `Gene ${shortGeneId(gene.ref.gene_id)} v${gene.ref.version ?? 1}`;
  const nodes = genes.map((gene) => ({ name: nodeName(gene), shortLabel: shortGeneLabel(gene), value: `${nodeName(gene)}\n采用 ${gene.use_count ?? 0} 次`, symbolSize: 46 }));
  // The shared model has no Gene parent field. Edges show only an explicit
  // source_attempt or precise UseRecord, never an inferred genetic parent.
  const byGeneId = new Map();
  genes.forEach((gene) => { const key = gene.ref.gene_id; byGeneId.set(key, [...(byGeneId.get(key) ?? []), gene]); });
  const edges = [...byGeneId.values()].flatMap((versions) => versions.sort((a, b) => (a.ref.version ?? 1) - (b.ref.version ?? 1)).slice(1).map((gene, index) => ({ source: nodeName(versions[index]), target: nodeName(gene), value: "版本" })));
  genes.forEach((gene) => { if (gene.source_attempt) { const source = `来源 ${agentLabel(gene.source_attempt.agent)}`; nodes.push({ name: source, shortLabel: source, value: source, symbolSize: 32, itemStyle: { color: "#7956d9" } }); edges.push({ source, target: nodeName(gene), value: "source_attempt" }); } });
  adoptions.forEach((use) => { const source = nodeName(use); const target = `采用 ${agentLabel(use.attempt?.agent)}`; if (genes.some((gene) => nodeName(gene) === source)) { nodes.push({ name: target, shortLabel: target, value: target, symbolSize: 30, itemStyle: { color: "#55d6a7" } }); edges.push({ source, target, value: "采用" }); } });
  chartFor("gene-chart").setOption({ backgroundColor: "transparent", tooltip: { renderMode: "richText", formatter: (p) => p.data.value || p.name }, series: [{ type: "graph", layout: "force", roam: true, label: { show: true, position: "bottom", distance: 8, color: "#ecf5ff", formatter: (p) => p.data.shortLabel ?? p.name }, force: { repulsion: 280, edgeLength: [110, 165], gravity: .08 }, lineStyle: { color: "#56b7e9" }, data: nodes, links: edges }] }, { notMerge: true });
}

function messageGraph(events) {
  if (!events.length) return showEmpty("message-chart", "message-empty", "尚未加载 T2 JSONL Envelope 导出；消息流为空。");
  showChart("message-chart", "message-empty");
  const labels = new Set(); const links = [];
  events.forEach((event) => { const source = agentLabel(event.sender); const target = event.receiver === "broadcast" ? "broadcast" : agentLabel(event.receiver); labels.add(source); labels.add(target); links.push({ source, target, value: event.msg_type }); });
  chartFor("message-chart").setOption({ tooltip: { renderMode: "richText", formatter: (p) => p.data.value ? `${p.data.source} → ${p.data.target}\n${p.data.value}` : p.name }, series: [{ type: "graph", layout: "circular", roam: true, label: { show: true, color: "#ecf5ff" }, lineStyle: { color: "#66c2ff", curveness: .15 }, edgeLabel: { show: true, formatter: (p) => p.data.value }, data: [...labels].map((name) => ({ name, symbolSize: 42 })), links }] }, { notMerge: true });
}

function metricChart(metrics) {
  if (!metrics.length || !metrics.some((metric) => metric.history.length)) return showEmpty("metric-chart", "metric-empty", "运行导出未提供历史指标，因此不显示或暗示性能变化。");
  showChart("metric-chart", "metric-empty");
  const metric = metrics.find((item) => item.history.length); const history = metric.history;
  const current = history.at(-1); const mean = history.reduce((sum, value) => sum + value, 0) / history.length; const best = Math.max(...history);
  chartFor("metric-chart").setOption({ tooltip: { renderMode: "richText", trigger: "axis" }, legend: { textStyle: { color: "#dcecff" } }, xAxis: { type: "category", data: history.map((_, i) => `记录 ${i + 1}`), axisLabel: { color: "#b9cfe3" } }, yAxis: { type: "value", axisLabel: { color: "#b9cfe3" } }, series: [{ name: `${metric.name} 历史`, type: "line", data: history, symbolSize: 8 }, { name: "历史均值", type: "line", data: history.map(() => mean), lineStyle: { type: "dashed" }, symbol: "none" }, { name: "历史最佳", type: "line", data: history.map(() => best), lineStyle: { type: "dotted" }, symbol: "none" }, { name: `当前: ${current}${metric.unit ?? ""}`, type: "scatter", data: history.map((value, i) => i === history.length - 1 ? value : "-"), symbolSize: 15 }] }, { notMerge: true });
}

async function main() {
  try {
    const response = await fetch("/api/dashboard", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    text("provenance", `来源：${data.provenance}`); byId("provenance").className = `badge provenance-${data.provenance}`;
    text("source-label", data.source_label); text("hub-status", data.hub_status); stateCards(data.acceptance ?? {}); rehearsalBoard(data.rehearsal);
    const notes = byId("notes"); clear("notes"); (data.notes ?? []).forEach((note) => { const item = document.createElement("li"); item.textContent = note; notes.append(item); });
    geneGraph(data.genes ?? [], data.adoptions ?? []); messageGraph(data.events ?? []); metricChart(data.metrics ?? []);
  } catch (error) {
    text("provenance", "数据不可用"); byId("provenance").className = "badge";
    text("source-label", "当前快照无法读取"); text("hub-status", "状态未知（页面数据不可用）"); stateCards({}); rehearsalBoard(null);
    clear("notes"); append(byId("notes"), "li", `仪表板数据不可用：${error.message}`);
  }
}
window.addEventListener("DOMContentLoaded", () => { main(); window.setInterval(main, 1000); });

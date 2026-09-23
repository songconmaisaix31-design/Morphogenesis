/* global echarts */
"use strict";

const byId = (id) => document.getElementById(id);
const text = (id, value) => { byId(id).textContent = String(value); };
const agentLabel = (agent) => agent && typeof agent === "object" ? `${agent.role ?? "unknown"}#${agent.instance ?? "?"}` : String(agent ?? "unknown");
const clear = (id) => { byId(id).replaceChildren(); };
const number = (value, digits = 2) => Number.isFinite(value) ? Number(value).toFixed(digits) : "未知";
const chartFor = (id) => echarts.getInstanceByDom(byId(id)) ?? echarts.init(byId(id));
const shortGeneId = (value) => { const id = String(value ?? "unknown"); return id.length > 14 ? `${id.slice(0, 6)}…${id.slice(-6)}` : id; };
const reducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const stageLabel = {
  task_ready: "题目待执行", repair_selected: "首次选路", repair_reviewed: "首次复核", gene_generated: "经验生成",
  awaiting_offline: "等待下线确认", member_offline: "成员已下线", recovery_ready: "恢复任务就绪", recovery_selected: "恢复选路",
  recovery_reviewed: "恢复复核", gene_adopted: "经验已采用", decaying: "权重衰减中", archived: "经验已归档",
  completed: "彩排完成", failed: "彩排已停止",
};

/* Linear-derived neutral plot ink; yellow remains a limited data accent. */
const chartColors = {
  nodeOnlineFill: "#101112", nodeRing: "#B9C0D4", nodeOffline: "#62666D",
  labelOnline: "#D0D6E0", labelOffline: "#8A8F98",
  lineActive: "#B9C0D4", lineActiveGlow: "rgba(185, 192, 212, 0.12)", lineInactive: "#62666D",
  labelMain: "#D0D6E0", labelDim: "#8A8F98", axisLabel: "#8A8F98",
  sourceNode: "#8A8F98", adoptNode: "#E6C85D", geneNode: "#D0D6E0", geneLine: "#8A8F98",
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
  return byId(chartId).getBoundingClientRect().width > 0 && byId(chartId).getBoundingClientRect().height > 0;
}

function stateCards(acceptance) {
  ["contract_local", "interface_live", "task_live"].forEach((key) => {
    const value = acceptance[key] ?? "not_run";
    const element = byId(key); element.textContent = value;
    element.className = `state-${value}`;
  });
}

/* Big-number fade: a 300ms CSS animation, only when the tracked value truly
   changes between polls. First render and steady 1s polling never animate;
   prefers-reduced-motion skips it. Displayed values are never altered. */
const bigNumberValues = new Map();
function flashNumber(element) {
  element.classList.remove("num-changed");
  void element.offsetWidth;
  element.classList.add("num-changed");
}
function bigNumberChanged(id, next) {
  const value = String(next);
  const prev = bigNumberValues.get(id);
  bigNumberValues.set(id, value);
  return prev !== undefined && prev !== value;
}
function setBigNumber(id, next) {
  const element = byId(id);
  const value = String(next);
  if (bigNumberChanged(id, value) && !reducedMotion()) flashNumber(element);
  if (element.textContent !== value) element.textContent = value;
}

function matchingPipe(pipes, current) {
  return pipes.find((pipe) => pipe.src?.role === current.src?.role && pipe.src?.instance === current.src?.instance && pipe.dst?.role === current.dst?.role && pipe.dst?.instance === current.dst?.instance);
}

/* The topology re-renders only when the actual graph data changes, keeping
   nodes stable; real updates get a single 300ms transition (0 under
   prefers-reduced-motion). */
let lastTopologySignature = "";

function topologyGraph(pipes, members) {
  if (!pipes?.length) { lastTopologySignature = ""; return showEmpty("story-pipe-chart", "story-pipe-empty", "尚无管道快照"); }
  if (!showChart("story-pipe-chart", "story-pipe-empty")) return;
  const availability = new Map((members ?? []).map((member) => [agentLabel(member.agent), member]));
  const names = new Set(pipes.flatMap((pipe) => [agentLabel(pipe.src), agentLabel(pipe.dst)]));
  // Labels sit below every node.  With a circular graph this reserves the
  // top edge for the node itself and prevents the upper builder name from
  // being clipped.
  const nodes = [...names].map((name) => {
    const member = availability.get(name); const online = member?.available !== false;
    return {
      name, online, symbolSize: online ? 30 : 20,
      itemStyle: online
        ? { color: chartColors.nodeOnlineFill, borderColor: chartColors.nodeRing, borderWidth: 3, shadowBlur: 10, shadowColor: chartColors.lineActiveGlow }
        : { color: chartColors.nodeOffline, opacity: .6 },
      label: { color: online ? chartColors.labelOnline : chartColors.labelOffline, position: "bottom", fontFamily: "Consolas, monospace" },
    };
  });
  const links = pipes.map((pipe) => ({
    source: agentLabel(pipe.src), target: agentLabel(pipe.dst), active: pipe.active,
    value: `权重 ${number(pipe.weight)} · 流量 ${number(pipe.flow)} · 成功率 ${(Number(pipe.success_rate) * 100).toFixed(0)}% · ${pipe.active ? "在线" : "离线"}`,
    lineStyle: pipe.active
      ? { width: Math.max(2, Math.min(12, 1 + Number(pipe.weight) * 4)), type: "solid", color: chartColors.lineActive, opacity: .95, shadowBlur: 10, shadowColor: chartColors.lineActiveGlow }
      : { width: Math.max(2, Math.min(12, 1 + Number(pipe.weight) * 4)), type: "dashed", color: chartColors.lineInactive, opacity: .25 },
  }));
  const signature = JSON.stringify([nodes.map((n) => [n.name, n.online]), links.map((l) => [l.source, l.target, l.active, l.value])]);
  const animate = !reducedMotion();
  const option = { animation: animate, animationDuration: animate ? 300 : 0, animationDurationUpdate: animate ? 300 : 0, animationEasingUpdate: "cubicOut", tooltip: { renderMode: "richText", formatter: (point) => point.data.value || point.name }, series: [{ type: "graph", layout: "circular", roam: false, top: 24, bottom: 32, label: { show: true, distance: 5, fontSize: 11 }, lineStyle: { curveness: .1 }, data: nodes, links }] };
  const chart = chartFor("story-pipe-chart");
  if (signature === lastTopologySignature) return;
  lastTopologySignature = signature;
  chart.setOption(option, { notMerge: true });
}

function geneState(gene, priorGenes) {
  // Archive wins first; then real decay measured against the previous
  // snapshot; then adoption by use_count; then newly generated.
  if (gene.archived_at !== null && gene.archived_at !== undefined) return { key: "archived", label: "已归档" };
  const key = `${gene.ref?.gene_id}@${gene.ref?.version ?? 1}`;
  const prior = priorGenes.get(key);
  if (prior && Number(gene.weight) < Number(prior.weight) - 1e-9) return { key: "decayed", label: "衰减中" };
  if (Number(gene.use_count) > 0) return { key: "adopted", label: "已采用" };
  if (!prior) return { key: "new", label: "新生成" };
  return { key: "active", label: "活跃" };
}

function geneFacts(current, prior) {
  const geneList = byId("story-genes"); clear("story-genes");
  const genes = current.genes ?? [];
  const activeCount = genes.filter((gene) => gene.archived_at === null || gene.archived_at === undefined).length;
  setBigNumber("story-gene-count", genes.length ? activeCount : (current.genes ? 0 : "未知"));
  if (!genes.length) { append(geneList, "p", "尚无 GeneView 快照"); return; }
  const priorGenes = new Map((prior?.genes ?? []).map((gene) => [`${gene.ref?.gene_id}@${gene.ref?.version ?? 1}`, gene]));
  genes.forEach((gene) => {
    const state = geneState(gene, priorGenes);
    const card = document.createElement("div"); card.className = `gene-fact gene-${state.key}`;
    const head = document.createElement("div"); head.className = "gene-head";
    append(head, "span", state.label, "gene-state");
    append(head, "strong", `${shortGeneId(gene.ref?.gene_id)} v${gene.ref?.version ?? 1}`);
    card.append(head);
    append(card, "span", `生成 ${gene.source_attempt ? agentLabel(gene.source_attempt.agent) : "未记录"} · 采用 ${gene.use_count} · 权重 ${number(gene.weight)}`);
    append(card, "span", `τ ${number(gene.tau_seconds, 1)} 秒 · ${gene.archived_at === null || gene.archived_at === undefined ? "未归档" : "已归档"}`);
    // Fixed 0..1 weight scale (1 = full initial weight), so decay shows as a
    // real shrink instead of a per-frame normalized share.
    const bar = document.createElement("div"); bar.className = "gene-weight-bar";
    bar.title = "权重条按 0..1 固定尺度";
    const fill = document.createElement("i"); fill.style.width = `${Math.min(100, Math.max(2, Number(gene.weight) * 100)).toFixed(1)}%`;
    bar.append(fill); card.append(bar);
    geneList.append(card);
  });
}

function eventFeed(history) {
  const feed = byId("event-feed"); clear("event-feed");
  if (!history?.length) { append(feed, "p", "尚无阶段快照"); return; }
  const entries = [...history].reverse();
  entries.forEach((snapshot, index) => {
    const row = document.createElement("div");
    row.className = `KFZpfa_activityListRow event-row event-system${index === 0 ? " event-latest" : ""}`;
    const heading = append(row, "div", "", "backend-event-heading");
    append(heading, "span", stageLabel[snapshot.stage] ?? String(snapshot.stage ?? "未标记阶段"), "event-stage");
    append(heading, "span", `#${snapshot.sequence}`, "event-seq");
    const at = Number(snapshot.at);
    append(row, "span", snapshot.at != null && Number.isFinite(at) ? new Date(at * 1000).toTimeString().slice(0, 8) : "时间未知", "event-time");
    feed.append(row);
  });
}

// A plain export may have Gene bodies and Envelopes without a rehearsal.
// Present those records as exports; never infer members, GeneView lifecycle,
// checkpoint results or token usage from their presence.
function exportedFacts(data) {
  if (data.rehearsal?.current) return;
  const genes = data.genes ?? [];
  if (genes.length) {
    clear("story-genes");
    append(byId("story-genes"), "p", `${genes.length} 份导出正文 · 生命周期未提供 · 来源 ${data.provenance ?? "未知"}`);
    genes.forEach((gene) => {
      const row = append(byId("story-genes"), "div", "", "gene-fact gene-export");
      append(row, "strong", `${gene.ref?.gene_id ?? "未知 Gene"} · v${gene.ref?.version ?? "未知"}`);
      append(row, "span", (gene.strategy ?? []).join(" → ") || "策略正文未提供");
      append(row, "span", `signals · ${(gene.signals_match ?? []).join(", ") || "未提供"}`);
    });
  }
  const events = data.events ?? [];
  if (events.length) {
    clear("event-feed");
    append(byId("event-feed"), "p", `Envelope 导出 · ${data.provenance ?? "未知来源"}`);
    [...events].reverse().forEach((event) => {
      const row = append(byId("event-feed"), "div", "", "KFZpfa_commentCard event-row");
      const heading = append(row, "div", "", "backend-event-heading");
      append(heading, "span", event.msg_type ?? "未知类型", "event-stage");
      append(heading, "span", `#${event.seq ?? "?"}`, "event-seq");
      append(row, "span", `${agentLabel(event.sender)} → ${agentLabel(event.receiver)}`, "event-time");
      row.title = `task ${event.task_id ?? "未知"} · ${event.msg_id ?? "未知消息"}`;
    });
  }
}

function rehearsalBoard(rehearsal, { redrawTopology = true } = {}) {
  if (!rehearsal) {
    text("rehearsal-mode", "尚未加载彩排快照；不展示预设通过结果。");
    text("header-members", "未知"); text("header-round", "未知");
    setBigNumber("metric-tokens", "未知"); setBigNumber("story-gene-count", "未知");
    text("story-question", "尚无运行中的任务"); text("story-question-detail", "等待任务快照。已有导出活动仍可查看。");
    if (bigNumberChanged("story-checkpoint-rate", "未加载") && !reducedMotion()) flashNumber(byId("story-checkpoint-rate"));
    text("story-checkpoint-rate", "未加载"); clear("story-checkpoints"); append(byId("story-checkpoints"), "li", "尚无独立 checkpoint 快照");
    clear("story-pipes"); append(byId("story-pipes"), "p", "尚无管道快照");
    if (redrawTopology) showEmpty("story-pipe-chart", "story-pipe-empty", "尚无管道快照");
    text("story-offline-member", "未发生 / 未加载"); text("story-offline-reason", "下线原因和恢复 checkpoint 均须来自实际快照。");
    clear("story-genes"); append(byId("story-genes"), "p", "尚无经验池快照");
    clear("event-feed"); append(byId("event-feed"), "p", "尚无阶段快照");
    return;
  }
  const current = rehearsal.current;
  const history = rehearsal.history ?? [];
  const prior = history.length > 1 ? history[history.length - 2] : null;
  const replay = rehearsal.mode === "replay";
  const modeLabel = replay ? "回放视图" : rehearsal.mode === "mock" ? "模拟快照" : "现场快照";
  text("rehearsal-mode", `${modeLabel} · ${stageLabel[current.stage] ?? "未标记阶段"} · #${current.sequence}${replay ? " · 原始证据只读" : ""}`);

  const members = current.members ?? [];
  const online = members.filter((member) => member.available !== false).length;
  text("header-members", members.length ? `${online}/${members.length}` : "未知");
  const taskId = String(current.task_id ?? "");
  text("header-round", taskId.startsWith("recovery-") ? "2 · 恢复" : taskId.startsWith("repair-") ? "1 · 修复" : "未知");
  const taskResult = (current.results ?? []).find((result) => result.task_id === current.task_id);
  const tokens = taskResult?.usage?.tokens;
  setBigNumber("metric-tokens", Number.isFinite(tokens) ? tokens : "未知");

  const recoveryTask = taskId.startsWith("recovery-");
  text("story-question", recoveryTask ? "恢复任务（新样例）" : "首次修复任务"); byId("story-question").title = taskId;
  text("story-question-detail", recoveryTask ? "移除成员后，另一名构建成员在新坏样例上重新选路。" : "修复 clamp、mean、unique 三个已知 Bug，并交由独立复核。");

  const checkpointList = byId("story-checkpoints"); clear("story-checkpoints");
  const rateElement = byId("story-checkpoint-rate");
  if (!current.checkpoints) {
    if (bigNumberChanged("story-checkpoint-rate", "未判定") && !reducedMotion()) flashNumber(rateElement);
    text("story-checkpoint-rate", "未判定"); append(checkpointList, "li", "尚无独立 checkpoint 快照");
  } else {
    const checks = current.checkpoints;
    const rateValue = `${checks.passed_count}/${checks.total} · ${(checks.ratio * 100).toFixed(0)}%`;
    const rateChanged = bigNumberChanged("story-checkpoint-rate", rateValue);
    // Giant mono number stays "passed/total"; the percentage follows in small
    // type so the mandated clamp size never wraps inside the Board.
    const big = document.createElement("span"); big.textContent = `${checks.passed_count}/${checks.total}`;
    const pct = document.createElement("span"); pct.className = "count-pct"; pct.textContent = ` · ${(checks.ratio * 100).toFixed(0)}%`;
    // Success green appears only as a transient pulse on a fresh full pass.
    if (checks.ratio === 1 && !rateElement.textContent.startsWith(`${checks.total}/${checks.total}`)) {
      const board = rateElement.closest(".morph-board");
      if (board && !reducedMotion()) { board.classList.add("checkpoint-pulse"); window.setTimeout(() => board.classList.remove("checkpoint-pulse"), 1000); }
    }
    rateElement.replaceChildren(big, pct);
    if (rateChanged && !reducedMotion()) flashNumber(rateElement);
    checks.checks.forEach((check) => append(checkpointList, "li", `${check.name}：${check.passed === true ? "通过" : check.passed === false ? "失败" : "待判定"}`, `check-${String(check.passed)}`));
  }

  const pipeList = byId("story-pipes"); clear("story-pipes");
  if (redrawTopology) {
    // T 轨 SwarmTopology 合入后接管拓扑画布；此处的 ECharts 圆形图是降级视图。
    if (document.body.dataset.swarmModule === "loaded") {
      byId("story-pipe-empty").hidden = true;
    } else {
      topologyGraph(current.pipes, current.members);
    }
  }
  if (!current.pipes?.length) append(pipeList, "p", "尚无管道快照");
  current.pipes.forEach((pipe) => {
    const before = prior ? matchingPipe(prior.pipes ?? [], pipe) : null;
    const row = document.createElement("div"); row.className = `pipe-row ${pipe.active ? "pipe-active" : "pipe-inactive"}`;
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

  geneFacts(current, prior);
  eventFeed(history);
}

function geneGraph(genes, adoptions) {
  if (!genes.length) return showEmpty("gene-chart", "gene-empty", "未导出 T3M GeneView；不能从消息、候选或结果反推谱系。");
  if (!showChart("gene-chart", "gene-empty")) return;
  const nodeName = (gene) => `${gene.ref.gene_id}@v${gene.ref.version ?? 1}`;
  const shortGeneLabel = (gene) => `Gene ${shortGeneId(gene.ref.gene_id)} v${gene.ref.version ?? 1}`;
  const nodes = genes.map((gene) => ({ name: nodeName(gene), shortLabel: shortGeneLabel(gene), value: `${nodeName(gene)}\n采用 ${gene.use_count ?? 0} 次`, symbolSize: 46, itemStyle: { color: chartColors.geneNode } }));
  // The shared model has no Gene parent field. Edges show only an explicit
  // source_attempt or precise UseRecord, never an inferred genetic parent.
  const byGeneId = new Map();
  genes.forEach((gene) => { const key = gene.ref.gene_id; byGeneId.set(key, [...(byGeneId.get(key) ?? []), gene]); });
  const edges = [...byGeneId.values()].flatMap((versions) => versions.sort((a, b) => (a.ref.version ?? 1) - (b.ref.version ?? 1)).slice(1).map((gene, index) => ({ source: nodeName(versions[index]), target: nodeName(gene), value: "版本" })));
  genes.forEach((gene) => { if (gene.source_attempt) { const source = `来源 ${agentLabel(gene.source_attempt.agent)}`; nodes.push({ name: source, shortLabel: source, value: source, symbolSize: 32, itemStyle: { color: chartColors.sourceNode } }); edges.push({ source, target: nodeName(gene), value: "source_attempt" }); } });
  adoptions.forEach((use) => { const source = nodeName(use); const target = `采用 ${agentLabel(use.attempt?.agent)}`; if (genes.some((gene) => nodeName(gene) === source)) { nodes.push({ name: target, shortLabel: target, value: target, symbolSize: 30, itemStyle: { color: chartColors.adoptNode } }); edges.push({ source, target, value: "采用" }); } });
  chartFor("gene-chart").setOption({ backgroundColor: "transparent", animation: !reducedMotion(), tooltip: { renderMode: "richText", formatter: (p) => p.data.value || p.name }, series: [{ type: "graph", layout: "force", roam: true, label: { show: true, position: "bottom", distance: 8, color: chartColors.labelMain, formatter: (p) => p.data.shortLabel ?? p.name }, force: { repulsion: 280, edgeLength: [110, 165], gravity: .08 }, lineStyle: { color: chartColors.geneLine }, data: nodes, links: edges }] }, { notMerge: true });
}

function messageGraph(events) {
  if (!events.length) return showEmpty("message-chart", "message-empty", "尚未加载 T2 JSONL Envelope 导出；消息流为空。");
  if (!showChart("message-chart", "message-empty")) return;
  const labels = new Set(); const links = [];
  events.forEach((event) => { const source = agentLabel(event.sender); const target = event.receiver === "broadcast" ? "broadcast" : agentLabel(event.receiver); labels.add(source); labels.add(target); links.push({ source, target, value: event.msg_type }); });
  chartFor("message-chart").setOption({ animation: !reducedMotion(), tooltip: { renderMode: "richText", formatter: (p) => p.data.value ? `${p.data.source} → ${p.data.target}\n${p.data.value}` : p.name }, series: [{ type: "graph", layout: "circular", roam: true, top: 30, bottom: 48, left: 48, right: 48, label: { show: true, position: "bottom", distance: 8, fontSize: 10, color: chartColors.labelMain }, lineStyle: { color: chartColors.lineActive, curveness: .15 }, edgeLabel: { show: true, color: chartColors.axisLabel, formatter: (p) => p.data.value }, data: [...labels].map((name) => ({ name, symbolSize: 42, itemStyle: { color: chartColors.geneNode } })), links }] }, { notMerge: true });
}

function metricChart(metrics) {
  if (!metrics.length || !metrics.some((metric) => metric.history.length)) return showEmpty("metric-chart", "metric-empty", "运行导出未提供历史指标，因此不显示或暗示性能变化。");
  if (!showChart("metric-chart", "metric-empty")) return;
  const metric = metrics.find((item) => item.history.length); const history = metric.history;
  const current = history.at(-1); const mean = history.reduce((sum, value) => sum + value, 0) / history.length; const best = Math.max(...history);
  chartFor("metric-chart").setOption({ animation: !reducedMotion(), tooltip: { renderMode: "richText", trigger: "axis" }, legend: { textStyle: { color: chartColors.labelMain } }, xAxis: { type: "category", data: history.map((_, i) => `记录 ${i + 1}`), axisLabel: { color: chartColors.axisLabel } }, yAxis: { type: "value", axisLabel: { color: chartColors.axisLabel } }, series: [{ name: `${metric.name} 历史`, type: "line", data: history, symbolSize: 8, lineStyle: { color: chartColors.lineActive }, itemStyle: { color: chartColors.lineActive } }, { name: "历史均值", type: "line", data: history.map(() => mean), lineStyle: { type: "dashed", color: chartColors.labelDim }, symbol: "none" }, { name: "历史最佳", type: "line", data: history.map(() => best), lineStyle: { type: "dotted", color: chartColors.labelDim }, symbol: "none" }, { name: `当前: ${current}${metric.unit ?? ""}`, type: "scatter", data: history.map((value, i) => i === history.length - 1 ? value : "-"), symbolSize: 15, itemStyle: { color: chartColors.lineActive } }] }, { notMerge: true });
}

/* The page shell (viz/frontend/src/App.jsx) owns all network reads and polls
   /api/dashboard once per second. This bridge only renders what it is given:
   - update(data, {redraw, resize}) fills text/DOM zones on every call and
     repaints ECharts canvases only when the swarm view is actually visible
     (redraw === true), so hidden views pause their redraw work;
   - fail(message) keeps the last good snapshot on screen and only flips the
     provenance badge and the connection status line (数据不被清空). */
let lastData = null;

function resizeCharts() {
  ["story-pipe-chart", "gene-chart", "message-chart", "metric-chart"].forEach((id) => {
    const element = byId(id);
    const instance = element ? echarts.getInstanceByDom(element) : null;
    if (instance && element.getBoundingClientRect().width > 0) instance.resize();
  });
}

function update(data, { redraw = true, resize = false } = {}) {
  if (!byId("provenance")) { window.__morphPendingDashboard = { data, redraw, resize }; return; }
  lastData = data;
  // empty_dashboard() reports provenance=live while nothing was loaded: do not
  // let the badge read as live run data when the source label itself says
  // 未加载导出 and no rehearsal.current exists.
  const unloaded = data.source_label === "未加载导出" && !data.rehearsal?.current;
  text("provenance", unloaded ? "未加载导出" : `来源：${data.provenance}`);
  byId("provenance").className = `morph-badge provenance-${unloaded ? "unloaded" : data.provenance}`;
  text("connection-state", "");
  text("source-label", data.source_label); text("hub-status", data.hub_status); stateCards(data.acceptance ?? {});
  rehearsalBoard(data.rehearsal, { redrawTopology: redraw });
  exportedFacts(data);
  const notes = byId("notes"); clear("notes"); (data.notes ?? []).forEach((note) => { const item = document.createElement("li"); item.textContent = note; notes.append(item); });
  if (!redraw) return;
  if (resize) resizeCharts();
  geneGraph(data.genes ?? [], data.adoptions ?? []); messageGraph(data.events ?? []); metricChart(data.metrics ?? []);
}

function fail(message) {
  if (!byId("provenance")) return;
  const badge = byId("provenance");
  if (lastData) {
    badge.textContent = "连接失败"; badge.className = "morph-badge provenance-failed";
    text("connection-state", `连接失败 · 保留上次快照（${message}）`);
  } else {
    // First load already failed: no snapshot exists, say so instead of
    // implying one, and put the cause into the run notes.
    badge.textContent = "数据不可用"; badge.className = "morph-badge provenance-failed";
    text("connection-state", `连接失败 · 尚无快照（${message}）`);
    text("source-label", "当前快照无法读取"); text("hub-status", "状态未知（页面数据不可用）");
    clear("notes"); append(byId("notes"), "li", `仪表板数据不可用：${message}`);
  }
}

// Navigation keeps all bridge-owned zones mounted. Dispose hidden ECharts
// (including force-layout work), then redraw only the newly visible panel.
function refreshVisibleCharts() {
  const visible = !document.hidden && document.querySelector('.morph-backend')?.dataset.active === 'true';
  ["story-pipe-chart", "gene-chart", "message-chart", "metric-chart"].forEach(id => {
    const element = byId(id);
    if (element && (!visible || element.getBoundingClientRect().width === 0)) {
      echarts.getInstanceByDom(element)?.dispose();
      if (id === "story-pipe-chart") lastTopologySignature = "";
    }
  });
  if (!visible || !lastData) return;
  resizeCharts();
  geneGraph(lastData.genes ?? [], lastData.adoptions ?? []);
  messageGraph(lastData.events ?? []);
  metricChart(lastData.metrics ?? []);
  if (document.body.dataset.swarmModule !== "loaded" && lastData.rehearsal?.current) {
    topologyGraph(lastData.rehearsal.current.pipes, lastData.rehearsal.current.members);
  }
}
window.MorphDashboard = { update, fail };
window.addEventListener("morph:panel-visible", refreshVisibleCharts);
document.addEventListener("visibilitychange", refreshVisibleCharts);
window.addEventListener("resize", resizeCharts);
window.addEventListener("DOMContentLoaded", () => {
  const pending = window.__morphPendingDashboard;
  if (pending) { delete window.__morphPendingDashboard; update(pending.data, { redraw: pending.redraw, resize: true }); }
});

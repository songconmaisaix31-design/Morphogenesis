/* global echarts */
"use strict";

const byId = (id) => document.getElementById(id);
const text = (id, value) => { byId(id).textContent = String(value); };
const agentLabel = (agent) => agent && typeof agent === "object" ? `${agent.role ?? "unknown"}#${agent.instance ?? "?"}` : String(agent ?? "unknown");

function showEmpty(chartId, emptyId, message) {
  byId(chartId).style.display = "none";
  const empty = byId(emptyId); empty.hidden = false; empty.textContent = message;
}

function stateCards(acceptance) {
  ["contract_local", "interface_live", "task_live"].forEach((key) => {
    const value = acceptance[key] ?? "not_run";
    const element = byId(key); element.textContent = value;
    element.className = `state-${value}`;
  });
}

function geneGraph(genes) {
  if (!genes.length) return showEmpty("gene-chart", "gene-empty", "未导出 Gene 正文，不能从消息或结果反推谱系。");
  const nodeName = (gene) => `${gene.ref.gene_id}@v${gene.ref.version ?? 1}`;
  const nodes = genes.map((gene) => ({ name: nodeName(gene), value: nodeName(gene), symbolSize: 46 }));
  // Gene has no parent field in the shared contract.  A lineage edge therefore
  // only represents successive declared versions of the same gene_id.
  const byGeneId = new Map();
  genes.forEach((gene) => { const key = gene.ref.gene_id; byGeneId.set(key, [...(byGeneId.get(key) ?? []), gene]); });
  const edges = [...byGeneId.values()].flatMap((versions) => versions.sort((a, b) => (a.ref.version ?? 1) - (b.ref.version ?? 1)).slice(1).map((gene, index) => ({ source: nodeName(versions[index]), target: nodeName(gene) })));
  echarts.init(byId("gene-chart")).setOption({ backgroundColor: "transparent", tooltip: { formatter: (p) => p.data.value || p.name }, series: [{ type: "graph", layout: "force", roam: true, label: { show: true, color: "#ecf5ff" }, force: { repulsion: 180 }, lineStyle: { color: "#56b7e9" }, data: nodes, links: edges }] });
}

function messageGraph(events) {
  if (!events.length) return showEmpty("message-chart", "message-empty", "尚未加载 T2 JSONL Envelope 导出；消息流为空。");
  const labels = new Set(); const links = [];
  events.forEach((event) => { const source = agentLabel(event.sender); const target = event.receiver === "broadcast" ? "broadcast" : agentLabel(event.receiver); labels.add(source); labels.add(target); links.push({ source, target, value: event.msg_type }); });
  echarts.init(byId("message-chart")).setOption({ tooltip: { formatter: (p) => p.data.value ? `${p.data.source} → ${p.data.target}<br>${p.data.value}` : p.name }, series: [{ type: "graph", layout: "circular", roam: true, label: { show: true, color: "#ecf5ff" }, lineStyle: { color: "#66c2ff", curveness: .15 }, edgeLabel: { show: true, formatter: (p) => p.data.value }, data: [...labels].map((name) => ({ name, symbolSize: 42 })), links }] });
}

function metricChart(metrics) {
  if (!metrics.length || !metrics.some((metric) => metric.history.length)) return showEmpty("metric-chart", "metric-empty", "运行导出未提供历史指标，因此不显示或暗示性能变化。");
  const metric = metrics.find((item) => item.history.length); const history = metric.history;
  const current = history.at(-1); const mean = history.reduce((sum, value) => sum + value, 0) / history.length; const best = Math.max(...history);
  echarts.init(byId("metric-chart")).setOption({ tooltip: { trigger: "axis" }, legend: { textStyle: { color: "#dcecff" } }, xAxis: { type: "category", data: history.map((_, i) => `记录 ${i + 1}`), axisLabel: { color: "#b9cfe3" } }, yAxis: { type: "value", axisLabel: { color: "#b9cfe3" } }, series: [{ name: `${metric.name} 历史`, type: "line", data: history, symbolSize: 8 }, { name: "历史均值", type: "line", data: history.map(() => mean), lineStyle: { type: "dashed" }, symbol: "none" }, { name: "历史最佳", type: "line", data: history.map(() => best), lineStyle: { type: "dotted" }, symbol: "none" }, { name: `当前: ${current}${metric.unit ?? ""}`, type: "scatter", data: history.map((value, i) => i === history.length - 1 ? value : "-"), symbolSize: 15 }] });
}

async function main() {
  try {
    const response = await fetch("/api/dashboard", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    text("provenance", `来源：${data.provenance}`); byId("provenance").className = `badge provenance-${data.provenance}`;
    text("source-label", data.source_label); text("hub-status", data.hub_status); stateCards(data.acceptance ?? {});
    const notes = byId("notes"); (data.notes ?? []).forEach((note) => { const item = document.createElement("li"); item.textContent = note; notes.append(item); });
    geneGraph(data.genes ?? []); messageGraph(data.events ?? []); metricChart(data.metrics ?? []);
  } catch (error) { text("provenance", "加载失败"); byId("notes").textContent = `仪表板数据不可用：${error.message}`; }
}
window.addEventListener("DOMContentLoaded", main);

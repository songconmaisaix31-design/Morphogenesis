import React, { useEffect, useMemo, useState } from 'react';
import { deriveSwarmView, LEASE_LABELS, RESERVATION_LABELS } from './derive';
import './swarm.css';

const VIEW_W = 1000;
const VIEW_H = 520;
const GRAPH_PAGE_SIZE = 8;
const NODE_KINDS = ['worker', 'capability', 'task', 'asset'];
const known = (value) => value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value));
const number = (value, digits = 2) => known(value) ? Number(value).toFixed(digits) : '未知';
const timeOf = (ts) => known(ts) ? new Date(Number(ts) * 1000).toLocaleString('zh-CN', { hour12: false }) : '时间未知';
const provenanceLabel = { live: '真实运行记录', mock: '模拟运行记录', replay: '历史回放', unverified: '来源未验证' };

function path(a, b) {
  const x1 = a.x * VIEW_W; const y1 = a.y * VIEW_H;
  const x2 = b.x * VIEW_W; const y2 = b.y * VIEW_H;
  const mx = (x1 + x2) / 2;
  return `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`;
}

function StatePanel({ view, className }) {
  const role = view.state === 'error' ? 'alert' : 'status';
  return <section className={className} aria-label='去中心化蜂群'>
    <header className='swarm-hud'><span className='swarm-badge'>去中心化 · 只读</span><span className='swarm-hud-stage'>GHOST IN THE SWARM</span></header>
    <div className={`swarm-empty swarm-empty-${view.state}`} role={role}>
      <b>{view.state === 'loading' ? '正在读取蜂群' : view.state === 'missing' ? '状态源缺失' : '观察失败'}</b>
      <p>{view.message}</p><small>只展示当前可验证的去中心化蜂群关系。</small>
    </div>
  </section>;
}

function SwarmTopology({ swarm, active = true, reducedMotion = false }) {
  const view = useMemo(() => deriveSwarmView(swarm), [swarm]);
  const [selected, setSelected] = useState(null);
  const [graphPage, setGraphPage] = useState(0);
  const shellClass = `swarm-shell swarm-decentralized${active ? '' : ' swarm-paused'}${reducedMotion ? ' swarm-reduced' : ''}`;
  const nodesByKind = NODE_KINDS.map((kind) => (view.nodes ?? []).filter((node) => node.kind === kind));
  const graphPages = Math.max(1, ...nodesByKind.map((nodes) => Math.ceil(nodes.length / GRAPH_PAGE_SIZE)));
  useEffect(() => { if (graphPage >= graphPages) setGraphPage(graphPages - 1); }, [graphPage, graphPages]);
  if (['loading', 'missing', 'error'].includes(view.state)) return <StatePanel view={view} className={shellClass} />;

  const safePage = Math.min(graphPage, graphPages - 1);
  const graphNodes = nodesByKind.flatMap((nodes) => nodes.slice(safePage * GRAPH_PAGE_SIZE, (safePage + 1) * GRAPH_PAGE_SIZE));
  const graphKeys = new Set(graphNodes.map((node) => node.key));
  const positions = layoutGraphNodes(graphNodes);
  const graphEdges = view.edges.filter((edge) => graphKeys.has(edge.source) && graphKeys.has(edge.target));
  const selectedNode = view.nodes.find((node) => node.key === selected);
  const related = view.edges.filter((edge) => edge.source === selected || edge.target === selected);
  const stale = view.state === 'stale';
  const sourceProblems = Object.entries(view.sources).filter(([, source]) => source.state !== 'ok');
  const reservations = view.budget?.reservations ?? [];
  const selectNode = (key) => setSelected((current) => current === key ? null : key);
  const nodeKeyDown = (event, key) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault(); selectNode(key);
  };

  return <section className={`${shellClass}${stale ? ' swarm-is-stale' : ''}`} aria-label='去中心化蜂群' onKeyDown={(event) => { if (event.key === 'Escape' && selected) setSelected(null); }}>
    <header className='swarm-hud'>
      <span className='swarm-badge'>去中心化 · 只读</span>
        <span className={`swarm-badge swarm-prov-${view.provenance ?? 'unverified'}`}>{provenanceLabel[view.provenance] ?? '来源未验证'}</span>
      {stale && <span className='swarm-badge swarm-stale' role='status'>陈旧快照 · 更新失败</span>}
      <span className='swarm-hud-stage'>GHOST IN THE SWARM</span>
      <span className='swarm-hud-dim'>{view.workers.length} worker · {view.tasks.length} task · {view.signals.length} pheromone</span>
    </header>
    <p className='swarm-thesis'>成员会更替，留下的是可追溯的本地决策、路由偏好、任务依赖与实际采用经验。</p>
    {stale && <p className='swarm-state swarm-state-warning'>最后成功读取：{view.lastSuccessAt ? new Date(view.lastSuccessAt).toLocaleString('zh-CN', { hour12: false }) : '未知'}。{view.message}</p>}
    {view.state === 'empty' && <div className='swarm-empty'><b>状态源为空</b><p>{view.message}</p></div>}
    {sourceProblems.length > 0 && <p className='swarm-source-warning'>部分来源不可用：{sourceProblems.map(([name, source]) => `${name}(${source.state})`).join(' · ')}</p>}

    {view.state !== 'empty' && <div className='swarm-body'>
      <div className='swarm-frame' role='group' aria-label='worker、能力、任务与经验谱系拓扑'>
        <div className='swarm-legend'><span>○ worker</span><span>◇ capability</span><span>□ task / lease</span><span>△ asset lineage</span></div>
        <div className='swarm-graph-nav' aria-label='拓扑分页'>
          <button type='button' disabled={safePage === 0} onClick={() => setGraphPage((page) => Math.max(0, page - 1))}>上一组</button>
          <span>第 {safePage + 1} / {graphPages} 组 · 显示 {graphNodes.length} / {view.nodes.length} 实体</span>
          <button type='button' disabled={safePage >= graphPages - 1} onClick={() => setGraphPage((page) => Math.min(graphPages - 1, page + 1))}>下一组</button>
        </div>
        <svg viewBox={`0 0 ${VIEW_W} ${VIEW_H}`} className='swarm-svg' role='img' aria-label='去中心化蜂群事实图'>
          <g className='swarm-layer'>
            {graphEdges.map((edge) => {
              const a = positions.get(edge.source); const b = positions.get(edge.target);
              if (!a || !b) return null;
              return <path key={edge.key} d={path(a, b)} className={`swarm-edge swarm-edge-${edge.kind}${selected && (edge.source === selected || edge.target === selected) ? ' swarm-edge-hot' : ''}`} strokeWidth={Math.max(1.2, Math.min(7, 1 + Number(edge.weight ?? 0) * 3))}>
                <title>{edge.kind} · {edge.source} → {edge.target}{known(edge.weight) ? ` · 读时权重 ${number(edge.weight)}` : ''}</title>
              </path>;
            })}
            {graphNodes.map((node) => {
              const position = positions.get(node.key); const x = position.x * VIEW_W; const y = position.y * VIEW_H;
              return <g key={node.key} className={`swarm-node swarm-node-${node.kind}${selected === node.key ? ' swarm-node-picked' : ''}`} transform={`translate(${x}, ${y})`} role='button' tabIndex='0' aria-label={`${node.kind} ${node.label}`} aria-pressed={selected === node.key} onKeyDown={(event) => nodeKeyDown(event, node.key)} onClick={() => selectNode(node.key)}>
                {node.kind === 'task' ? <rect x='-22' y='-18' width='44' height='36' rx='4' className='swarm-node-disc' />
                  : node.kind === 'asset' ? <path d='M0 -22 L22 18 L-22 18 Z' className='swarm-node-disc' />
                  : node.kind === 'capability' ? <path d='M0 -21 L21 0 L0 21 L-21 0 Z' className='swarm-node-disc' />
                  : <circle r='23' className='swarm-node-disc' />}
                <text className='swarm-node-label' y='38' textAnchor='middle'>{node.label}</text>
                {node.state && <text className='swarm-node-eligible' y='-31' textAnchor='middle'>{LEASE_LABELS[node.state] ?? node.state}</text>}
              </g>;
            })}
          </g>
        </svg>
      </div>
      <aside className='swarm-detail' aria-label='拓扑实体详情'>
        {selectedNode ? <>
          <div className='swarm-detail-head'><strong>{selectedNode.label}</strong><span className='swarm-pill'>{selectedNode.kind}</span><button className='swarm-detail-close' type='button' aria-label='关闭拓扑实体详情' onClick={() => setSelected(null)}>×</button></div>
          <p>状态：{LEASE_LABELS[selectedNode.state] ?? selectedNode.state ?? '未知'}</p><h4>实际关系（{related.length}）</h4>
          <ul>{related.map((edge) => <li key={edge.key}>{edge.kind} · {edge.source} → {edge.target}{known(edge.weight) ? ` · ${number(edge.weight)}` : ''}</li>)}</ul>
        </> : <><h3>关系结构仍在</h3><p>选择节点查看租约、路由、依赖、信息素与采用谱系。</p><p className='swarm-detail-dim'>选择任一实体，沿可验证事实查看它与蜂群的协作关系。</p></>}
      </aside>
    </div>}

    <div className='swarm-facts'>
      <section className='swarm-fact'><h4>任务 / 租约（{view.tasks.length}）</h4>{view.tasks.length === 0 ? <p className='swarm-detail-dim'>无任务事实。</p> : <ul className='swarm-task-list'>{view.tasks.map((task) => <li key={task.task_id}><b>{task.task_id}</b><span>{LEASE_LABELS[task.lease_state] ?? task.lease_state}</span><small>{task.capability ?? '能力未知'} · {task.owner ? `持有 ${task.owner}` : '无持有者'} · 尝试 {task.attempts ?? 0}</small></li>)}</ul>}</section>
      <section className='swarm-fact'><h4>信息素 / 路由（{view.signals.length} / {view.routes.length}）</h4>{view.signals.length === 0 && view.routes.length === 0 ? <p className='swarm-detail-dim'>无场信号事实。</p> : <ul>{view.signals.map((signal) => <li key={signal.signal_id}>{signal.signal_id} → {signal.task_id ?? '任务未知'} · 浓度 {number(signal.decayed_concentration)}</li>)}{view.routes.map((route, index) => <li key={`${route.worker_id}:${route.pipe_key}:${index}`}>{route.worker_id} → {route.pipe_key} · 权重 {number(route.decayed_weight)} / 原始 {number(route.weight)}</li>)}</ul>}</section>
      <section className='swarm-fact'><h4>依赖 / 衍生（{view.dependsOn.length}）</h4>{view.dependsOn.length === 0 ? <p className='swarm-detail-dim'>无依赖事实。</p> : <ul>{view.dependsOn.map((edge, index) => <li key={`${edge.taskId}:${edge.dependency}:${index}`}>{edge.dependency} → {edge.taskId}</li>)}</ul>}</section>
      <section className='swarm-fact'><h4>采用谱系（{view.assets.length}）</h4>{view.assets.length === 0 ? <p className='swarm-detail-dim'>无实际采用回执。</p> : <ul>{view.assets.map((item, index) => <li key={item.execution_id ?? index}><b>{item.asset_id ?? '源资产未知'}</b> → {item.candidate_asset_id ?? '候选资产未知'}<br />{item.worker_id ?? 'worker 未知'} / {item.task_id ?? 'task 未知'} / result {item.result_id ?? '未知'}</li>)}</ul>}</section>
      <section className='swarm-fact'><h4>预算（{reservations.length}）</h4>{reservations.length === 0 ? <p className='swarm-detail-dim'>无预算记录；模型费用保持未知。</p> : <ul>{reservations.map((item, index) => <li key={item.reservation_id ?? index}><span className={`swarm-reservation-state swarm-reservation-${item.state}`}>{RESERVATION_LABELS[item.state] ?? item.state}</span>{item.task_id} · 保留额度 {number(item.reserved_usd, 6)} USD · {known(item.tokens) || item.usage_metering === 'verified' ? `用量已确认${known(item.tokens) ? ` ${item.tokens} tokens` : ''}` : '用量未知'} · 费用未知{item.state === 'unknown_cost_allowed' ? '（本轮允许继续）' : ''}</li>)}</ul>}</section>
      <section className='swarm-fact'><h4>审计（{view.audit.length + view.workerAudit.length}）</h4>{view.audit.length + view.workerAudit.length === 0 ? <p className='swarm-detail-dim'>无审计事实。</p> : <ul>{view.audit.slice(0, 8).map((item, index) => <li key={item.sequence ?? index}>#{item.sequence ?? '?'} {item.event} · {item.task_id ?? '全局'}</li>)}{view.workerAudit.slice(0, 8).map((item, index) => <li key={`${item.worker_id}:${item.task_id}:${index}`}>{item.worker_id} · {item.task_id} · {item.provenance ?? 'unverified'}{item.requested_model ? ` · 请求 ${item.requested_model}` : ''}{item.returned_model ? ` · 返回 ${item.returned_model}` : ''}</li>)}</ul>}</section>
    </div>
    <footer className='swarm-foot'><span>观察时间 {timeOf(view.observedAt)} · {view.hubStatus}</span><span>contract {view.acceptance?.contract_local ?? 'not_run'} / interface {view.acceptance?.interface_live ?? 'not_run'} / task {view.acceptance?.task_live ?? 'not_run'}</span></footer>
  </section>;
}

export default SwarmTopology;

function layoutGraphNodes(nodes) {
  const columns = NODE_KINDS.map((kind) => nodes.filter((node) => node.kind === kind).map((node) => node.key));
  const populated = columns.filter((column) => column.length);
  const positions = new Map();
  populated.forEach((column, columnIndex) => column.forEach((key, rowIndex) => positions.set(key, {
    x: populated.length === 1 ? 0.5 : 0.08 + (columnIndex / (populated.length - 1)) * 0.84,
    y: column.length === 1 ? 0.5 : 0.15 + (rowIndex / (column.length - 1)) * 0.7,
  })));
  return positions;
}

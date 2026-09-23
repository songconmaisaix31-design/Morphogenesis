// AGENT SWARM topology view. Consumes only the /api/dashboard JSON passed by
// the page shell; all facts are derived in ./derive.js from
// rehearsal.current.members/pipes/routing/results plus events/genes/adoptions.
// SVG is hand-rolled so the view needs no chart dependency in the frontend
// package (lockfile is owned by T0) and stays fully keyboard accessible.
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { deriveSwarm, agentKey, STAGE_LABELS, deriveSwarmView, LEASE_LABELS, RESERVATION_LABELS } from './derive';
import './swarm.css';

const VIEW_W = 1000;
const VIEW_H = 620;

const knownNumber = (value) => value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value));
const number = (value, digits = 2) => knownNumber(value) ? Number(value).toFixed(digits) : '未知';
const percent = (value) => knownNumber(value) ? `${(Number(value) * 100).toFixed(0)}%` : '未知';
const timeOf = (ts) => knownNumber(ts) ? new Date(Number(ts) * 1000).toTimeString().slice(0, 8) : '时间未知';

function edgePath(a, b) {
  const x1 = a.x * VIEW_W; const y1 = a.y * VIEW_H;
  const x2 = b.x * VIEW_W; const y2 = b.y * VIEW_H;
  const mx = (x1 + x2) / 2;
  return `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`;
}

function ghostText(ghost) {
  const name = agentKey(ghost.agent);
  switch (ghost.status) {
    case 'recovered':
      // The literal theme phrase is reserved for a real removed_member whose
      // recovery actually succeeded; name/target details follow it.
      return `Ghost 已离开，任务重路由。${name}（两任务之间移除）→ ${agentKey(ghost.rerouteTarget)}；恢复任务已成功。`;
    case 'rerouted':
      return `${name} 已离开（两任务之间移除），恢复选路 → ${agentKey(ghost.rerouteTarget)}；恢复结果尚未判定，不代表已恢复。`;
    case 'failed':
      return `${name} 已离开；彩排已停止，未完成恢复${ghost.failure ? `：${ghost.failure}` : '。'}`;
    case 'offline':
      return `${name} 不可用；路由快照未记录移除，不涉及重路由。${ghost.reason ? `原因：${ghost.reason}。` : ''}`;
    default:
      return `${name} 已离开；恢复选路尚未完成，等待重路由。${ghost.reason ? `原因：${ghost.reason}。` : ''}`;
  }
}

const GHOST_TAGS = {
  recovered: '已离开 · 已重路由成功',
  rerouted: '已离开 · 已选路待结果',
  failed: '已离开 · 恢复未完成',
  offline: '不可用',
  waiting: '已离开 · 等待重路由',
};

function GhostBanner({ ghost }) {
  if (!ghost) return null;
  return (
    <p className={`swarm-ghost-line swarm-ghost-${ghost.status}`} role={ghost.status === 'failed' ? 'alert' : undefined}>
      {ghostText(ghost)}
    </p>
  );
}

function NodeDetail({ view, nodeKey, onClose }) {
  const node = view.nodes.find((item) => item.key === nodeKey);
  if (!node) return null;
  const edges = view.edges.filter((edge) => edge.source === nodeKey || edge.target === nodeKey);
  const results = view.agentResults(nodeKey);
  const events = view.agentEvents(nodeKey);
  const genes = view.agentGenes(nodeKey);
  const adoptions = view.agentAdoptions(nodeKey);
  return (
    <aside className='swarm-detail' aria-label={`成员 ${nodeKey} 详情`}>
      <div className='swarm-detail-head'>
        <strong>{nodeKey}</strong>
        <span className={`swarm-pill ${node.available === false ? 'swarm-pill-off' : node.available === null ? 'swarm-pill-unknown' : ''}`}>
          {node.available === false ? '已下线' : node.available === null ? '快照未声明' : '在线'}
        </span>
        <button type='button' className='swarm-detail-close' onClick={onClose} aria-label='关闭详情'>×</button>
      </div>
      {node.reason && <p className='swarm-detail-line'>原因：{node.reason}</p>}
      {node.ghost && <p className='swarm-detail-line'>{ghostText(node.ghost)}</p>}
      <h4>管道（{edges.length}）</h4>
      {edges.length === 0 && <p className='swarm-detail-dim'>无管道快照。</p>}
      <ul>{edges.map((edge) => (
        <li key={edge.key} className={edge.active ? '' : 'swarm-detail-dim'}>
          {edge.key} · 权重 {number(edge.weight)} · 流量 {number(edge.flow)} · 成功率 {percent(edge.successRate)} · {edge.active ? '在线' : '离线'}
        </li>
      ))}</ul>
      <h4>任务结果（{results.length}）</h4>
      {results.length === 0 && <p className='swarm-detail-dim'>无该成员的任务结果。</p>}
      <ul>{results.map((result) => (
        <li key={`${result.task_id}:${result.attempt?.attempt ?? 0}`}>
          {result.task_id} · {result.status} · 复核 {result.verdict?.passed === true ? '通过' : result.verdict?.passed === false ? '未通过' : '未判定'}
          {' · tokens '}{number(result.usage?.tokens, 0)}
        </li>
      ))}</ul>
      <h4>事件（{events.length}）</h4>
      {events.length === 0 && <p className='swarm-detail-dim'>无涉及该成员的 Envelope。</p>}
      <ul>{events.slice(-8).map((event) => (
        <li key={event.msg_id}>
          #{event.seq} {event.msg_type} · {agentKey(event.sender)} → {event.receiver === 'broadcast' ? 'broadcast' : agentKey(event.receiver)} · {event.task_id} · {timeOf(event.ts)}
        </li>
      ))}</ul>
      <h4>Gene 来源（{genes.length}）/ 采用（{adoptions.length}）</h4>
      {genes.length === 0 && adoptions.length === 0 && <p className='swarm-detail-dim'>无该成员的 Gene 记录。</p>}
      <ul>
        {genes.map((gene) => <li key={`g-${gene.ref?.gene_id}@${gene.ref?.version ?? 1}`}>生成 {gene.ref?.gene_id} v{gene.ref?.version ?? 1} · 权重 {number(gene.weight)}</li>)}
        {adoptions.map((use) => <li key={`u-${use.ref?.gene_id}@${use.ref?.version ?? 1}-${use.used_at}`}>采用 {use.ref?.gene_id} v{use.ref?.version ?? 1} · {timeOf(use.used_at)}</li>)}
      </ul>
    </aside>
  );
}

function SwarmTopology({ dashboard, active = true, reducedMotion = false, swarm = null }) {
  const view = useMemo(() => deriveSwarm(dashboard), [dashboard]);
  const [selectedKey, setSelectedKey] = useState(null);
  const [hoverKey, setHoverKey] = useState(null);
  const frameRef = useRef(null);

  // The decentralized swarm view supersedes the rehearsal topology only when
  // the /api/swarm payload actually carries facts; otherwise the rehearsal
  // derivation stays (an unconfigured swarm state must not blank the page).
  const hasSwarm = useMemo(() => {
    if (!swarm || typeof swarm !== 'object') return false;
    return ['workers', 'tasks', 'routes', 'signals', 'assets', 'audit']
      .some((key) => Array.isArray(swarm[key]) && swarm[key].length > 0);
  }, [swarm]);

  const layerRef = useRef(null);
  const glowRef = useRef(null);
  const rafRef = useRef(0);

  // Cursor response: gentle parallax on the graph layer plus a tracking glow.
  // No listener at all under reduced motion or while the view is hidden.
  useEffect(() => {
    const frame = frameRef.current;
    if (!frame || reducedMotion || !active || view.state !== 'ready') return undefined;
    const onMove = (event) => {
      const rect = frame.getBoundingClientRect();
      const nx = (event.clientX - rect.left) / rect.width - 0.5;
      const ny = (event.clientY - rect.top) / rect.height - 0.5;
      cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(() => {
        if (layerRef.current) layerRef.current.style.transform = `translate(${(-nx * 10).toFixed(1)}px, ${(-ny * 8).toFixed(1)}px)`;
        if (glowRef.current) {
          glowRef.current.style.opacity = '1';
          glowRef.current.style.transform = `translate(${event.clientX - rect.left}px, ${event.clientY - rect.top}px)`;
        }
      });
    };
    const onLeave = () => {
      cancelAnimationFrame(rafRef.current);
      if (layerRef.current) layerRef.current.style.transform = '';
      if (glowRef.current) glowRef.current.style.opacity = '0';
    };
    frame.addEventListener('pointermove', onMove);
    frame.addEventListener('pointerleave', onLeave);
    return () => {
      cancelAnimationFrame(rafRef.current);
      frame.removeEventListener('pointermove', onMove);
      frame.removeEventListener('pointerleave', onLeave);
    };
  }, [reducedMotion, active, view.state]);

  useEffect(() => { setSelectedKey(null); setHoverKey(null); }, [view.taskId, view.sequence]);

  const onGraphKeyDown = useCallback((event) => {
    if (view.state !== 'ready' || !view.nodes.length) return;
    const keys = view.nodes.map((node) => node.key);
    const index = selectedKey ? keys.indexOf(selectedKey) : -1;
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
      event.preventDefault();
      setSelectedKey(keys[(index + 1) % keys.length]);
    } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
      event.preventDefault();
      setSelectedKey(keys[(index - 1 + keys.length) % keys.length]);
    } else if (event.key === 'Escape') {
      setSelectedKey(null);
    }
  }, [view, selectedKey]);

  const shellClass = [
    'swarm-shell',
    active ? '' : 'swarm-paused',
    reducedMotion ? 'swarm-reduced' : '',
  ].filter(Boolean).join(' ');

  if (hasSwarm) return <SwarmFacts swarm={swarm} active={active} reducedMotion={reducedMotion} />;

  if (view.state === 'disconnected') {
    return <section className={shellClass} aria-label='Agent Swarm 拓扑'><p className='swarm-state swarm-state-error' role='alert'>{view.message}</p></section>;
  }
  if (view.state === 'empty') {
    return (
      <section className={shellClass} aria-label='Agent Swarm 拓扑'>
        <header className='swarm-hud'>
          <span className={`swarm-badge swarm-prov-${view.provenance ?? 'unknown'}`}>{view.modeLabel}</span>
          <span className='swarm-hud-dim'>AGENT SWARM · 空态</span>
        </header>
        <p className='swarm-state'>{view.message}</p>
      </section>
    );
  }

  const positions = new Map(view.nodes.map((node) => [node.key, node.position]));
  const hoverEdges = new Set(
    hoverKey ? view.edges.filter((edge) => edge.source === hoverKey || edge.target === hoverKey).map((edge) => edge.key) : [],
  );

  return (
    <section className={shellClass} aria-label='Agent Swarm 拓扑'>
      <header className='swarm-hud'>
        <span className={`swarm-badge swarm-prov-${view.provenance ?? 'unknown'}`}>{view.modeLabel}{view.replay ? ' · 只读' : ''}</span>
        <span className='swarm-hud-stage'>{view.stageLabel} · 快照 #{view.sequence}</span>
        {view.taskId && <span className='swarm-hud-dim' title={view.taskDescription}>{view.taskId}</span>}
      </header>
      {view.failure && <p className='swarm-state swarm-state-error' role='alert'>彩排失败：{view.failure}</p>}
      <GhostBanner ghost={view.ghost} />
      <div className='swarm-body'>
        <div
          className='swarm-frame'
          ref={frameRef}
          role='group'
          aria-label='蜂群拓扑图；方向键切换成员，Escape 取消选中'
          tabIndex={0}
          onKeyDown={onGraphKeyDown}
        >
          <div className='swarm-glow' ref={glowRef} aria-hidden='true' />
          <svg viewBox={`0 0 ${VIEW_W} ${VIEW_H}`} className='swarm-svg' role='img' aria-label='成员与管道拓扑'>
            <g ref={layerRef} className='swarm-layer'>
              {view.edges.map((edge) => {
                const a = positions.get(edge.source); const b = positions.get(edge.target);
                if (!a || !b) return null;
                const width = Math.max(1.5, Math.min(9, 1 + Number(edge.weight ?? 0) * 5));
                const cls = [
                  'swarm-edge',
                  edge.active ? 'swarm-edge-active' : 'swarm-edge-off',
                  hoverEdges.has(edge.key) ? 'swarm-edge-hot' : '',
                  hoverKey && !hoverEdges.has(edge.key) ? 'swarm-edge-dim' : '',
                ].filter(Boolean).join(' ');
                return (
                  <path key={edge.key} d={edgePath(a, b)} className={cls} strokeWidth={width}>
                    <title>{edge.key} · 权重 {number(edge.weight)} · 流量 {number(edge.flow)} · 成功率 {percent(edge.successRate)} · {edge.active ? '在线' : '离线'}</title>
                  </path>
                );
              })}
              {view.edges.length === 0 && (
                <text x={VIEW_W / 2} y={VIEW_H - 24} className='swarm-svg-note' textAnchor='middle'>尚无管道快照；成员位置来自 members，未虚构边。</text>
              )}
              {view.nodes.map((node) => {
                const { x, y } = node.position;
                const cx = x * VIEW_W; const cy = y * VIEW_H;
                const cls = [
                  'swarm-node',
                  node.available === false ? 'swarm-node-off' : '',
                  node.available === null ? 'swarm-node-unknown' : '',
                  node.ghost ? 'swarm-node-ghost' : '',
                  node.selected ? 'swarm-node-selected-attempt' : '',
                  selectedKey === node.key ? 'swarm-node-picked' : '',
                ].filter(Boolean).join(' ');
                return (
                  <g
                    key={node.key}
                    className={cls}
                    transform={`translate(${cx}, ${cy})`}
                    onClick={() => setSelectedKey(selectedKey === node.key ? null : node.key)}
                    onPointerEnter={() => setHoverKey(node.key)}
                    onPointerLeave={() => setHoverKey(null)}
                  >
                    <circle r={node.ghost ? 26 : 30} className='swarm-node-disc' />
                    {node.selected && <circle r={38} className='swarm-node-ring' />}
                    <text className='swarm-node-label' y={52} textAnchor='middle'>{node.key}</text>
                    {node.ghost && <text className='swarm-node-ghost-tag' y={-40} textAnchor='middle'>{GHOST_TAGS[node.ghost.status] ?? GHOST_TAGS.waiting}</text>}
                    {node.eligible && <text className='swarm-node-eligible' y={-52} textAnchor='middle'>eligible</text>}
                    <title>{node.key} · {node.available === false ? '已下线' : node.available === null ? '快照未声明可用性' : '在线'}</title>
                  </g>
                );
              })}
            </g>
          </svg>
        </div>
        <div className='swarm-member-list' aria-label='按成员查看拓扑详情'>
          {view.nodes.map(node => (
            <button key={node.key} type='button' aria-pressed={selectedKey === node.key}
              onClick={() => setSelectedKey(selectedKey === node.key ? null : node.key)}>
              {node.key}<span>{node.available === false ? '已下线' : node.available === null ? '未知' : '在线'}</span>
            </button>
          ))}
        </div>
        {selectedKey
          ? <NodeDetail view={view} nodeKey={selectedKey} onClose={() => setSelectedKey(null)} />
          : (
            <aside className='swarm-detail swarm-detail-hint' aria-label='成员详情'>
              <p>点击或用方向键选中成员，查看其管道、任务结果、事件与 Gene 记录。</p>
              <p className='swarm-detail-dim'>全部事实来自 /api/dashboard；无记录的区域保持空态。</p>
            </aside>
          )}
      </div>
      <footer className='swarm-foot'>
        <span>阶段：{view.stageLabel}（{STAGE_LABELS[view.stage] ? view.stage : 'unknown'}）</span>
        {view.message && <span>{view.message}</span>}
      </footer>
    </section>
  );
}

const SWARM_VIEW_W = 1000;
const SWARM_VIEW_H = 360;

const LEASE_SORT = { leased: 0, partial: 1, expired: 2, handoff: 3, available: 4, failed: 5, completed: 6 };

function swarmEdgePath(a, b) {
  const x1 = a.x * SWARM_VIEW_W; const y1 = a.y * SWARM_VIEW_H;
  const x2 = b.x * SWARM_VIEW_W; const y2 = b.y * SWARM_VIEW_H;
  const mx = (x1 + x2) / 2;
  return `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`;
}

function SwarmFacts({ swarm, active = true, reducedMotion = false }) {
  const view = useMemo(() => deriveSwarmView(swarm), [swarm]);
  const [selected, setSelected] = useState(null);

  const shellClass = [
    'swarm-shell', 'swarm-decentralized',
    active ? '' : 'swarm-paused', reducedMotion ? 'swarm-reduced' : '',
  ].filter(Boolean).join(' ');

  if (view.state === 'disconnected') {
    return <section className={shellClass} aria-label='去中心化蜂群'><p className='swarm-state swarm-state-error' role='alert'>{view.message}</p></section>;
  }
  if (view.state === 'empty') {
    return (
      <section className={shellClass} aria-label='去中心化蜂群'>
        <header className='swarm-hud'>
          <span className='swarm-badge'>去中心化 · 只读</span>
          <span className='swarm-hud-dim'>AGENT SWARM · 空态</span>
        </header>
        <p className='swarm-state'>{view.message}</p>
      </section>
    );
  }

  const positions = new Map(view.nodes.map((node) => [node.key, node.position]));
  const selectedNode = view.nodes.find((node) => node.key === selected) ?? null;
  const selectedRoutes = view.routes.filter((route) => route.worker_id === selected || route.pipe_key === selected);
  const selectedTasks = view.tasks.filter((task) => task.owner === selected);
  const tasks = [...view.tasks].sort((a, b) => {
    const la = LEASE_SORT[a.lease_state] ?? 9;
    const lb = LEASE_SORT[b.lease_state] ?? 9;
    return la - lb || (a.task_id < b.task_id ? -1 : 1);
  });
  const leaseLabel = (state) => LEASE_LABELS[state] ?? String(state ?? '未知');

  const budgetReservations = view.budget?.reservations ?? [];
  const budgetTotals = view.budget?.totals ?? {};

  return (
    <section className={shellClass} aria-label='去中心化蜂群'>
      <header className='swarm-hud'>
        <span className='swarm-badge'>去中心化 · 只读</span>
        <span className='swarm-hud-stage'>AGENT SWARM · {view.health === 'ok' ? '健康' : '部分'} · {timeOf(view.observedAt)}</span>
        <span className='swarm-hud-dim'>{view.workers.length} worker · {view.tasks.length} task · {view.routes.length} route</span>
      </header>
      <div className='swarm-body'>
        <div className='swarm-frame' role='group' aria-label='去中心化蜂群拓扑：worker 节点与路由边' tabIndex={0}>
          <svg viewBox={`0 0 ${SWARM_VIEW_W} ${SWARM_VIEW_H}`} className='swarm-svg' role='img' aria-label='worker 与路由拓扑'>
            <g className='swarm-layer'>
              {view.edges.map((edge) => {
                const a = positions.get(edge.source); const b = positions.get(edge.target);
                if (!a || !b) return null;
                const width = Math.max(1.5, Math.min(9, 1 + Number(edge.weight ?? 0) * 5));
                return (
                  <path key={edge.key} d={swarmEdgePath(a, b)}
                    className={`swarm-edge${selected && (edge.source === selected || edge.target === selected) ? ' swarm-edge-hot' : ''}`} strokeWidth={width}>
                    <title>{edge.source} → {edge.target} · 读时衰减权重 {number(edge.weight)}（原始 {number(edge.rawWeight)}） · 采样 {edge.samples ?? '未知'}</title>
                  </path>
                );
              })}
              {view.edges.length === 0 && (
                <text x={SWARM_VIEW_W / 2} y={SWARM_VIEW_H - 16} className='swarm-svg-note' textAnchor='middle'>尚无路由偏好快照；worker 与能力位置来自 SwarmView，未虚构边。</text>
              )}
              {view.nodes.map((node) => {
                const { x, y } = node.position;
                const cx = x * SWARM_VIEW_W; const cy = y * SWARM_VIEW_H;
                const isPipe = node.kind === 'pipe';
                return (
                  <g key={node.key} className={`swarm-node${isPipe ? ' swarm-node-pipe' : ''}${selected === node.key ? ' swarm-node-picked' : ''}`}
                    transform={`translate(${cx}, ${cy})`} onClick={() => setSelected(selected === node.key ? null : node.key)}>
                    <circle r={isPipe ? 18 : 26} className='swarm-node-disc' />
                    <text className='swarm-node-label' y={isPipe ? 34 : 44} textAnchor='middle'>{node.key}</text>
                    {!isPipe && node.state !== 'unknown' && <text className='swarm-node-eligible' y={-36} textAnchor='middle'>{node.state ?? '未知'}</text>}
                    <title>{node.key} · {isPipe ? '能力/管道' : `worker（${node.state ?? '未知'}）`}</title>
                  </g>
                );
              })}
            </g>
          </svg>
        </div>
        <div className='swarm-member-list' aria-label='按成员查看详情'>
          {view.nodes.map((node) => (
            <button key={node.key} type='button' aria-pressed={selected === node.key}
              onClick={() => setSelected(selected === node.key ? null : node.key)}>
              {node.key}<span>{node.kind === 'pipe' ? '能力' : (node.state ?? '未知')}</span>
            </button>
          ))}
        </div>
        {selectedNode ? (
          <aside className='swarm-detail' aria-label={`${selected} 详情`}>
            <div className='swarm-detail-head'>
              <strong>{selected}</strong>
              <span className='swarm-pill'>{selectedNode.kind === 'pipe' ? '能力' : 'worker'}</span>
              <button type='button' className='swarm-detail-close' onClick={() => setSelected(null)} aria-label='关闭详情'>×</button>
            </div>
            {selectedNode.kind === 'worker' && selectedTasks.length > 0 && <h4>任务（{selectedTasks.length}）</h4>}
            <ul>{selectedTasks.map((task) => <li key={task.task_id}>{task.task_id} · {leaseLabel(task.lease_state)}</li>)}</ul>
            <h4>路由（{selectedRoutes.length}）</h4>
            {selectedRoutes.length === 0 && <p className='swarm-detail-dim'>无该成员/能力的路由偏好。</p>}
            <ul>{selectedRoutes.map((route, index) => (
              <li key={`${route.worker_id}:${route.pipe_key}:${index}`}>
                {route.worker_id} → {route.pipe_key} · 读时衰减 {number(route.decayed_weight ?? route.weight)} · 采样 {route.samples ?? '未知'}
              </li>
            ))}</ul>
          </aside>
        ) : (
          <aside className='swarm-detail swarm-detail-hint' aria-label='成员详情'>
            <p>点击或选中 worker/能力节点，查看其路由与任务。</p>
            <p className='swarm-detail-dim'>全部事实来自 /api/swarm；无记录的区域保持空态。</p>
          </aside>
        )}
      </div>

      <div className='swarm-facts'>
        <section className='swarm-fact' aria-label='任务与租约'>
          <h4>任务与租约（{tasks.length}）</h4>
          {tasks.length === 0 && <p className='swarm-detail-dim'>尚无任务快照。</p>}
          <ul className='swarm-task-list'>
            {tasks.map((task) => (
              <li key={task.task_id} className={`swarm-task swarm-task-${task.lease_state ?? 'available'}`}>
                <span className='swarm-task-id'>{task.task_id}</span>
                <span className='swarm-task-lease'>{leaseLabel(task.lease_state)}</span>
                <span className='swarm-task-meta'>{task.kind ?? '任务'} · {task.module ?? '未知模块'} · 尝试 {task.attempts ?? 0}</span>
                <span className='swarm-task-meta'>{task.owner ? `持有 ${task.owner}` : '无持有者'}{task.dependencies?.length ? ` · 依赖 ${task.dependencies.join(', ')}` : ''}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className='swarm-fact' aria-label='依赖关系'>
          <h4>depends_on 依赖（{view.dependsOn.length}）</h4>
          {view.dependsOn.length === 0 && <p className='swarm-detail-dim'>无任务依赖。</p>}
          <ul>{view.dependsOn.map((edge, index) => (
            <li key={`${edge.taskId}:${edge.dependency}:${index}`}>{edge.taskId} → {edge.dependency}</li>
          ))}</ul>
        </section>

        <section className='swarm-fact' aria-label='预算预留'>
          <h4>预算预留（{budgetReservations.length}）</h4>
          {view.budget?.breaker && <p className='swarm-state swarm-state-error'>熔断：{view.budget.breaker}</p>}
          {budgetReservations.length === 0 && <p className='swarm-detail-dim'>无预算预留记录。</p>}
          <ul className='swarm-reservation-list'>
            {budgetReservations.map((reservation, index) => (
              <li key={reservation.reservation_id ?? reservation.request_id ?? `r-${index}`}>
                <span className={`swarm-reservation-state swarm-reservation-${reservation.state}`}>{RESERVATION_LABELS[reservation.state] ?? reservation.state}</span>
                {reservation.worker_id} · {reservation.task_id} · 预留 {number(reservation.reserved_usd, 6)} USD · 计入 {number(reservation.admitted_usd, 6)} · tokens {number(reservation.tokens, 0)} · {reservation.cost ?? 'cost 未知'}
              </li>
            ))}
          </ul>
          <p className='swarm-detail-dim'>占用 {number(budgetTotals.total_hold_usd, 6)} USD（pending {number(budgetTotals.pending_hold_usd, 6)} / unknown {number(budgetTotals.unknown_hold_usd, 6)}）· 计入 {number(budgetTotals.admitted_usd, 6)} USD · {budgetTotals.reserved ?? 0} 预留 / {budgetTotals.settled ?? 0} 结算 / {budgetTotals.unknown ?? 0} 未知</p>
        </section>

        <section className='swarm-fact' aria-label='审计流'>
          <h4>审计流（{view.audit.length} 事件 / {view.workerAudit.length} 记录）</h4>
          {view.audit.length === 0 && view.workerAudit.length === 0 && <p className='swarm-detail-dim'>尚无审计事件。</p>}
          <ul className='swarm-audit-list'>
            {view.audit.slice(0, 20).map((event, index) => (
              <li key={`a-${event.sequence ?? index}`}>#{event.sequence ?? '?'} {event.event} · {event.task_id ?? '全局'} · {timeOf(event.at)}</li>
            ))}
            {view.workerAudit.slice(0, 20).map((record, index) => (
              <li key={`w-${record.task_id ?? ''}-${index}`}>{record.worker_id ?? '?'} · {record.task_id ?? '?'} · {record.outcome ?? '?'} · 资产 {record.asset_id ?? '无'} · {record.provenance ?? '?'}</li>
            ))}
          </ul>
        </section>

        <section className='swarm-fact' aria-label='资产采用链'>
          <h4>资产采用链（{view.assets.length} 采用 / {view.promotions.length} 晋级）</h4>
          {view.assets.length === 0 && view.promotions.length === 0 && <p className='swarm-detail-dim'>尚无资产采用或晋级记录。</p>}
          <ul className='swarm-asset-list'>
            {view.assets.map((adoption, index) => (
              <li key={`${adoption.execution_id ?? adoption.asset_id ?? index}`}>
                采用 {adoption.asset_id} → 由 {adoption.worker_id ?? '?'} 任务 {adoption.task_id ?? '?'} · {timeOf(adoption.adopted_at)}
              </li>
            ))}
            {view.promotions.map((promotion, index) => (
              <li key={`p-${promotion.asset_id ?? index}`}>晋级 {promotion.asset_id} · {promotion.policy_version ?? '策略未知'} · {timeOf(promotion.promoted_at)}</li>
            ))}
          </ul>
        </section>
      </div>

      <footer className='swarm-foot'>
        <span>去中心化蜂群 · 严格只读 · {view.hubStatus}</span>
        {view.provenance && <span>provenance {view.provenance}</span>}
      </footer>
    </section>
  );
}

export default SwarmTopology;
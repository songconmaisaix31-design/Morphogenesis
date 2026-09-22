// AGENT SWARM topology view. Consumes only the /api/dashboard JSON passed by
// the page shell; all facts are derived in ./derive.js from
// rehearsal.current.members/pipes/routing/results plus events/genes/adoptions.
// SVG is hand-rolled so the view needs no chart dependency in the frontend
// package (lockfile is owned by T0) and stays fully keyboard accessible.
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { deriveSwarm, agentKey, STAGE_LABELS } from './derive';
import './swarm.css';

const VIEW_W = 1000;
const VIEW_H = 620;

const number = (value, digits = 2) =>
  Number.isFinite(Number(value)) ? Number(value).toFixed(digits) : '未知';
const percent = (value) =>
  Number.isFinite(Number(value)) ? `${(Number(value) * 100).toFixed(0)}%` : '未知';
const timeOf = (ts) =>
  Number.isFinite(Number(ts)) ? new Date(Number(ts) * 1000).toTimeString().slice(0, 8) : '时间未知';

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
      return `${name} 已离开（两任务之间移除），任务重路由 → ${agentKey(ghost.rerouteTarget)}；恢复任务已成功。`;
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

function SwarmTopology({ dashboard, active = true, reducedMotion = false }) {
  const view = useMemo(() => deriveSwarm(dashboard), [dashboard]);
  const [selectedKey, setSelectedKey] = useState(null);
  const [hoverKey, setHoverKey] = useState(null);
  const frameRef = useRef(null);
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

export default SwarmTopology;

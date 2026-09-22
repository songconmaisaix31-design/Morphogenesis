// Pure derivation of the SwarmTopology view model from the /api/dashboard JSON.
// Every fact comes from rehearsal.current.members/pipes/routing/results or the
// top-level events/genes/adoptions lists. Nothing here invents nodes, edges,
// tasks, messages, or recovery outcomes; absence stays absence.

export const STAGE_LABELS = {
  task_ready: '题目待执行', repair_selected: '首次选路', repair_reviewed: '首次复核',
  gene_generated: '经验生成', awaiting_offline: '等待下线确认', member_offline: '成员已下线',
  recovery_ready: '恢复任务就绪', recovery_selected: '恢复选路', recovery_reviewed: '恢复复核',
  gene_adopted: '经验已采用', decaying: '权重衰减中', archived: '经验已归档',
  completed: '彩排完成', failed: '彩排已停止',
};

export const PROVENANCE_LABELS = { live: '现场快照', replay: '回放视图', mock: '模拟快照' };

const ROLE_ORDER = { planner: 0, builder: 1, reviewer: 2, aggregator: 3 };

export const agentKey = (agent) =>
  agent && typeof agent === 'object' ? `${agent.role ?? 'unknown'}#${agent.instance ?? '?'}` : String(agent ?? 'unknown');

const sameAgent = (a, b) =>
  a && b && typeof a === 'object' && typeof b === 'object' && a.role === b.role && a.instance === b.instance;

// Deterministic aesthetic layout: role lanes flow left → right
// (planner → builder fan → reviewer → aggregator), unknown roles fall back to
// a ring. Positions are fractions of the viewBox so the SVG scales freely.
export function layoutNodes(keys) {
  const byRole = new Map();
  keys.forEach((key) => {
    const role = key.split('#')[0];
    const lane = ROLE_ORDER[role];
    if (!byRole.has(lane)) byRole.set(lane, []);
    byRole.get(lane).push(key);
  });
  const lanes = [...byRole.keys()].filter((lane) => lane !== undefined).sort((a, b) => a - b);
  const positions = new Map();
  if (lanes.length) {
    lanes.forEach((lane, laneIndex) => {
      const members = byRole.get(lane).sort();
      const x = lanes.length === 1 ? 0.5 : 0.12 + (laneIndex / (lanes.length - 1)) * 0.76;
      members.forEach((key, i) => {
        const y = members.length === 1 ? 0.5 : 0.2 + (i / (members.length - 1)) * 0.6;
        positions.set(key, { x, y });
      });
    });
  }
  const unknown = byRole.get(undefined) ?? [];
  unknown.sort().forEach((key, i) => {
    const angle = (i / Math.max(1, unknown.length)) * Math.PI * 2 - Math.PI / 2;
    positions.set(key, { x: 0.5 + Math.cos(angle) * 0.34, y: 0.5 + Math.sin(angle) * 0.34 });
  });
  return positions;
}

function deriveGhost(current) {
  // A member is only shown as "left, task re-routed" when the routing fact
  // records a real removal between tasks AND a recovery selection naming a
  // different, eligible member. Removal without selection is "waiting".
  const routing = current.routing ?? null;
  const removed = routing?.removed_member ?? null;
  const offline = (current.members ?? []).filter((member) => member.available === false);
  if (!removed && !offline.length) return null;
  const selected = routing?.selected_attempt ?? null;
  const rerouted = Boolean(
    removed && selected && !sameAgent(selected.agent, removed),
  );
  const ghostAgent = removed ?? offline[0]?.agent ?? null;
  const reason = offline.find((member) => sameAgent(member.agent, ghostAgent))?.reason
    ?? (removed ? '路由快照记录了移除，未提供成员原因' : null);
  return {
    agent: ghostAgent,
    removedAt: routing?.removed_at ?? null,
    boundary: routing?.boundary ?? null,
    reason,
    rerouted,
    rerouteTarget: rerouted ? selected.agent : null,
    stage: current.stage,
  };
}

export function deriveSwarm(dashboard) {
  if (!dashboard || typeof dashboard !== 'object') {
    return { state: 'disconnected', message: '仪表板数据不可用；拓扑不保留旧画面。' };
  }
  const rehearsal = dashboard.rehearsal ?? null;
  const current = rehearsal?.current ?? null;
  const events = Array.isArray(dashboard.events) ? dashboard.events : [];
  const genes = Array.isArray(dashboard.genes) ? dashboard.genes : [];
  const adoptions = Array.isArray(dashboard.adoptions) ? dashboard.adoptions : [];
  const provenance = dashboard.provenance ?? rehearsal?.mode ?? null;
  const modeLabel = PROVENANCE_LABELS[provenance] ?? '来源未知';

  if (!current) {
    return {
      state: 'empty', provenance, modeLabel,
      message: events.length
        ? '未加载彩排快照；仅有事件导出，成员拓扑保持空态。'
        : '未加载彩排快照；不展示预设节点或边。',
      events, genes, adoptions,
    };
  }

  const members = Array.isArray(current.members) ? current.members : [];
  const pipes = Array.isArray(current.pipes) ? current.pipes : [];
  const results = Array.isArray(current.results) ? current.results : [];
  const routing = current.routing ?? null;

  const memberByKey = new Map(members.map((member) => [agentKey(member.agent), member]));
  const keys = new Set(memberByKey.keys());
  pipes.forEach((pipe) => { keys.add(agentKey(pipe.src)); keys.add(agentKey(pipe.dst)); });
  const positions = layoutNodes([...keys]);

  const ghost = deriveGhost(current);
  const nodes = [...keys].sort().map((key) => {
    const member = memberByKey.get(key) ?? null;
    const isGhost = Boolean(ghost?.agent && key === agentKey(ghost.agent));
    return {
      key,
      role: key.split('#')[0],
      position: positions.get(key),
      available: member ? member.available !== false : null, // null = 快照未声明
      reason: member?.reason ?? null,
      changedAt: member?.changed_at ?? null,
      ghost: isGhost ? ghost : null,
      eligible: Boolean(routing?.eligible_members?.some((agent) => agentKey(agent) === key)),
      selected: Boolean(routing?.selected_attempt && agentKey(routing.selected_attempt.agent) === key),
    };
  });

  const edges = pipes.map((pipe) => ({
    key: `${agentKey(pipe.src)}→${agentKey(pipe.dst)}`,
    source: agentKey(pipe.src), target: agentKey(pipe.dst),
    weight: pipe.weight ?? null, flow: pipe.flow ?? null,
    successRate: pipe.success_rate ?? null,
    active: pipe.active !== false,
  }));

  const agentEvents = (key) => events.filter((event) =>
    agentKey(event.sender) === key || (event.receiver !== 'broadcast' && agentKey(event.receiver) === key) || (event.receiver === 'broadcast'));
  const agentResults = (key) => results.filter((result) => agentKey(result.attempt?.agent) === key);
  const agentGenes = (key) => genes.filter((gene) => gene.source_attempt && agentKey(gene.source_attempt.agent) === key);
  const agentAdoptions = (key) => adoptions.filter((use) => agentKey(use.attempt?.agent) === key);

  return {
    state: 'ready',
    provenance, modeLabel,
    replay: rehearsal.mode === 'replay',
    sequence: current.sequence,
    stage: current.stage,
    stageLabel: STAGE_LABELS[current.stage] ?? String(current.stage ?? '未标记阶段'),
    taskId: current.task_id ?? null,
    taskDescription: current.task_description ?? '',
    failure: current.failure ?? null,
    message: current.message ?? '',
    nodes, edges, ghost, routing,
    events, genes, adoptions, results,
    agentEvents, agentResults, agentGenes, agentAdoptions,
  };
}

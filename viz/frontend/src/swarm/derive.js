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
  // "已离开，任务重路由" requires BOTH a real removed_member in the routing
  // fact AND a recovery selection naming a different member (RoutingFact
  // already guarantees the selection is eligible and not the removed member).
  // Four states stay distinct and never imply a failure recovered:
  //   waiting   — removed, no selection yet
  //   rerouted  — selection made, but no recovery result is recorded yet
  //   recovered — the recovery task's own TaskResult succeeded
  //   failed    — stage failed / failure text present, or the recovery result
  //               is recorded without success; never shown as recovered
  // A member that is merely unavailable without a routing removal is only
  // "offline": the view must not speak about re-routing at all.
  const routing = current.routing ?? null;
  const removed = routing?.removed_member ?? null;
  const offline = (current.members ?? []).filter((member) => member.available === false);
  if (!removed && !offline.length) return null;

  const failed = Boolean(current.failure) || current.stage === 'failed';
  const selected = routing?.selected_attempt ?? null;
  const selectedOther = Boolean(removed && selected && !sameAgent(selected.agent, removed));
  const recoveryResult = selectedOther
    ? (current.results ?? []).find((result) =>
        result.task_id === routing.task_id && sameAgent(result.attempt?.agent, selected.agent))
    : null;

  let status;
  if (failed || (recoveryResult && recoveryResult.status !== 'succeeded')) {
    status = 'failed';
  } else if (!removed) {
    status = 'offline';
  } else if (!selectedOther) {
    status = 'waiting';
  } else if (recoveryResult?.status === 'succeeded' || current.stage === 'completed') {
    status = 'recovered';
  } else {
    status = 'rerouted';
  }

  const ghostAgent = removed ?? offline[0]?.agent ?? null;
  const reason = offline.find((member) => sameAgent(member.agent, ghostAgent))?.reason
    ?? (removed ? '路由快照记录了移除，未提供成员原因' : null);
  return {
    agent: ghostAgent,
    removedAt: routing?.removed_at ?? null,
    boundary: routing?.boundary ?? null,
    reason,
    status,
    rerouteTarget: selectedOther ? selected.agent : null,
    recoveryStatus: recoveryResult?.status ?? null,
    failure: current.failure ?? null,
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

// --- Decentralized swarm view (/api/swarm) ---------------------------------
// Every fact comes from the SwarmView JSON; nothing here invents a worker,
// route, task, budget hold, audit event or adoption. Absence stays absence.

export const LEASE_LABELS = {
  available: '待认领', leased: '已租约', completed: '已完成', expired: '已过期',
  partial: '提交中', handoff: '已交接', failed: '已失败',
};
export const LEASE_ORDER = { leased: 0, partial: 1, expired: 2, handoff: 3, available: 4, completed: 5, failed: 6 };
export const RESERVATION_LABELS = { reserved: '已预留', settled: '已结算', unknown: '未知', unknown_cost_allowed: '费用未知 · 允许继续' };

// Deterministic bipartite layout: workers on the left, capability pipes on the
// right; a single population falls back to a full-width row.
export function layoutSwarmNodes(columns) {
  const positions = new Map();
  const placeColumn = (ids, x) => {
    const n = ids.length;
    if (!n) return;
    ids.forEach((id, i) => {
      positions.set(id, { x, y: n === 1 ? 0.5 : 0.12 + (i / (n - 1)) * 0.76 });
    });
  };
  const populated = columns.filter((ids) => ids.length);
  populated.forEach((ids, index) => placeColumn(ids, populated.length === 1 ? 0.5 : 0.08 + (index / (populated.length - 1)) * 0.84));
  return positions;
}

export function deriveSwarmView(transport) {
  if (!transport || typeof transport !== 'object') {
    return { state: 'error', message: '蜂群数据暂时不可用，请稍后重试。' };
  }
  const transportState = transport.state ?? 'error';
  const swarm = transport.data;
  if (!swarm || typeof swarm !== 'object') return {
    state: transportState, message: transportState === 'loading' ? '正在读取 /api/swarm…'
      : transportState === 'missing' ? '当前没有可读取的蜂群状态。'
      : `蜂群只读观察失败${transport.detail ? `：${transport.detail}` : '。'}`,
  };
  const workers = Array.isArray(swarm.workers) ? swarm.workers : [];
  const tasks = Array.isArray(swarm.tasks) ? swarm.tasks : [];
  const routes = Array.isArray(swarm.routes) ? swarm.routes : [];
  const signals = Array.isArray(swarm.signals) ? swarm.signals : [];
  const audit = Array.isArray(swarm.audit) ? swarm.audit : [];
  const workerAudit = Array.isArray(swarm.worker_audit) ? swarm.worker_audit : [];
  const assets = Array.isArray(swarm.assets) ? swarm.assets : [];
  const promotions = Array.isArray(swarm.promotions) ? swarm.promotions : [];
  const budget = swarm.budget ?? null;

  if (swarm.health === 'missing') {
    return {
      state: 'missing', message: swarm.notes?.[0] ?? '当前没有可读取的蜂群状态。',
      health: swarm.health ?? 'partial',
      hubStatus: swarm.hub_status ?? '待发布',
    };
  }

  const workerIds = workers.map((worker) => worker.worker_id).filter(Boolean).map((id) => `worker:${id}`);
  const capabilityIds = [...new Set([
    ...routes.map((route) => route.pipe_key), ...tasks.map((task) => task.capability),
  ].filter(Boolean))].map((id) => `capability:${id}`);
  const taskIds = tasks.map((task) => task.task_id).filter(Boolean).map((id) => `task:${id}`);
  const assetIds = [...new Set(assets.flatMap((asset) => [asset.asset_id, asset.candidate_asset_id]).filter(Boolean))].map((id) => `asset:${id}`);
  const positions = layoutSwarmNodes([workerIds, capabilityIds, taskIds, assetIds]);

  const nodes = [
    ...workerIds.map((key) => {
      const id = key.slice(7); const worker = workers.find((item) => item.worker_id === id) ?? {};
      return {
        key, label: id, kind: 'worker', position: positions.get(key),
        state: worker.state ?? 'unknown', remainingEnergy: worker.remaining_energy ?? null,
        completed: worker.completed ?? null, provenance: worker.provenance ?? null,
      };
    }),
    ...capabilityIds.map((key) => ({ key, label: key.slice(11), kind: 'capability', position: positions.get(key) })),
    ...taskIds.map((key) => {
      const task = tasks.find((item) => item.task_id === key.slice(5)) ?? {};
      return { key, label: key.slice(5), kind: 'task', position: positions.get(key), state: task.lease_state ?? task.status ?? 'unknown' };
    }),
    ...assetIds.map((key) => ({ key, label: key.slice(6), kind: 'asset', position: positions.get(key) })),
  ];

  const routeEdges = routes.map((route, index) => ({
    key: `route:${route.worker_id}→${route.pipe_key}#${index}`, kind: 'route',
    source: `worker:${route.worker_id}`, target: `capability:${route.pipe_key}`,
    weight: route.decayed_weight ?? route.weight ?? null,
    rawWeight: route.weight ?? null,
    samples: route.samples ?? null,
    tau: route.tau_seconds ?? null,
  }));

  const dependsOn = [];
  tasks.forEach((task) => (task.dependencies ?? []).forEach((dependency) => {
    dependsOn.push({ taskId: task.task_id, dependency });
  }));
  const taskEdges = tasks.flatMap((task) => {
    const edges = [];
    if (task.capability) edges.push({ key: `cap:${task.capability}:${task.task_id}`, kind: 'capability', source: `capability:${task.capability}`, target: `task:${task.task_id}` });
    if (task.owner) edges.push({ key: `lease:${task.owner}:${task.task_id}`, kind: 'lease', source: `worker:${task.owner}`, target: `task:${task.task_id}` });
    (task.dependencies ?? []).forEach((dependency) => edges.push({ key: `dep:${dependency}:${task.task_id}`, kind: 'dependency', source: `task:${dependency}`, target: `task:${task.task_id}` }));
    if (task.derived_from) edges.push({ key: `derived:${task.derived_from}:${task.task_id}`, kind: 'lineage', source: `task:${task.derived_from}`, target: `task:${task.task_id}` });
    return edges;
  });
  const signalEdges = signals.filter((signal) => signal.task_id).map((signal) => ({
    key: `signal:${signal.signal_id}:${signal.task_id}`, kind: 'pheromone', source: `capability:${tasks.find((task) => task.task_id === signal.task_id)?.capability}`, target: `task:${signal.task_id}`,
    weight: signal.decayed_concentration ?? signal.concentration ?? null,
  })).filter((edge) => positions.has(edge.source));
  const assetEdges = assets.flatMap((asset, index) => {
    const edges = [];
    if (asset.asset_id && asset.candidate_asset_id) edges.push({ key: `adopt:${index}`, kind: 'adoption', source: `asset:${asset.asset_id}`, target: `asset:${asset.candidate_asset_id}` });
    if (asset.task_id && asset.candidate_asset_id) edges.push({ key: `result:${index}`, kind: 'lineage', source: `task:${asset.task_id}`, target: `asset:${asset.candidate_asset_id}` });
    return edges;
  });
  const edges = [...routeEdges, ...taskEdges, ...signalEdges, ...assetEdges];
  const hasFacts = nodes.length || edges.length || signals.length || audit.length || workerAudit.length || promotions.length || (budget?.reservations?.length ?? 0);

  return {
    state: transportState === 'stale' ? 'stale' : hasFacts ? 'ready' : 'empty',
    message: hasFacts ? transport.detail : '状态目录可读，但当前没有蜂群事实。',
    schema: swarm.schema,
    health: swarm.health ?? 'partial',
    hubStatus: swarm.hub_status ?? '待发布',
    observedAt: swarm.observed_at ?? null,
    provenance: swarm.acceptance?.provenance ?? null,
    acceptance: swarm.acceptance ?? null,
    nodes, edges, positions,
    workers, tasks, routes, signals,
    budget, audit, workerAudit, assets, promotions, dependsOn,
    boundaries: Array.isArray(swarm.boundaries) ? swarm.boundaries : [],
    sources: swarm.sources ?? {}, lastSuccessAt: transport.lastSuccessAt ?? null,
  };
}

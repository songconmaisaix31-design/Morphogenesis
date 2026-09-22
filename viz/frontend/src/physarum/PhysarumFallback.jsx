// Static degraded view for PhysarumField: no WebGL, no animation, no RAF.
// Used when WebGL2 is unavailable, the context is lost, the device is too
// slow, or the user prefers reduced motion. Layout is deterministic so it
// never re-renders differently.

import React from 'react';

// Deterministic pseudo-random (mulberry32) so the static network is stable.
const seeded = (seed) => () => {
  seed |= 0;
  seed = (seed + 0x6d2b79f5) | 0;
  let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

const NODES = (() => {
  const rnd = seeded(20260923);
  const nodes = [];
  for (let i = 0; i < 14; i++) {
    nodes.push({ x: 6 + rnd() * 88, y: 10 + rnd() * 80, r: 1.6 + rnd() * 2.6 });
  }
  const links = [];
  for (let i = 0; i < nodes.length; i++) {
    // Link each node to its nearest earlier neighbour: branching, not a mesh.
    let best = -1;
    let bestD = Infinity;
    for (let j = 0; j < i; j++) {
      const dx = nodes[i].x - nodes[j].x;
      const dy = nodes[i].y - nodes[j].y;
      const d = dx * dx + dy * dy;
      if (d < bestD) {
        bestD = d;
        best = j;
      }
    }
    if (best >= 0) links.push([i, best]);
    if (rnd() < 0.3 && i > 1) links.push([i, Math.floor(rnd() * i)]);
  }
  return { nodes, links };
})();

const REASON_LABELS = {
  'reduced-motion': '已按减少动态效果设置显示静态视图',
  'webgl2-unavailable': '当前浏览器不支持 WebGL2，已切换静态视图',
  'float-buffer-unavailable': '缺少浮点渲染能力，已切换静态视图',
  'context-lost': 'WebGL 上下文丢失，已切换静态视图',
  'low-performance': '设备性能不足，已切换静态视图',
};

const PhysarumFallback = ({ reason }) => (
  <div className='physarum-fallback' role='img' aria-label='黏菌网络静态视图（动画已停用）'>
    <svg viewBox='0 0 100 100' preserveAspectRatio='xMidYMid slice'>
      {NODES.links.map(([a, b], i) => (
        <line
          key={`l${i}`}
          x1={NODES.nodes[a].x}
          y1={NODES.nodes[a].y}
          x2={NODES.nodes[b].x}
          y2={NODES.nodes[b].y}
        />
      ))}
      {NODES.nodes.map((n, i) => (
        <circle key={`n${i}`} cx={n.x} cy={n.y} r={n.r} />
      ))}
    </svg>
    <span className='physarum-fallback-note'>{REASON_LABELS[reason] || '黏菌模拟已降级为静态视图'}</span>
  </div>
);

export default PhysarumFallback;

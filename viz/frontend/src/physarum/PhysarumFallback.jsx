// Static degraded view for PhysarumField: no WebGL, no animation, no RAF.
// Used when WebGL2 is unavailable, the context is lost, the device is too
// slow, or the user prefers reduced motion. Layout is deterministic so it
// never re-renders differently.

import React from 'react';

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
      <path className='physarum-fallback-sheet' d='M38 48 C48 45 55 38 63 26 Q75 18 88 30 Q94 40 91 52 Q88 70 76 72 Q65 72 60 61 C52 56 46 55 38 53 Z' />
      <path className='physarum-fallback-vein' d='M4 55 C17 52 22 48 38 50 C50 50 58 49 68 46 C77 43 85 38 90 31 M18 73 C27 61 35 56 49 51 M30 28 C35 39 43 44 52 48 M51 51 C61 54 73 59 83 68 M59 49 C67 39 74 33 83 28' />
    </svg>
    <span className='physarum-fallback-note'>{REASON_LABELS[reason] || '黏菌模拟已降级为静态视图'}</span>
  </div>
);

export default PhysarumFallback;

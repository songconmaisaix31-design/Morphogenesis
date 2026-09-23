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
    <svg viewBox='0 0 160 90' preserveAspectRatio='xMidYMid meet'>
      <path className='physarum-fallback-sheet' d='M83 44 Q89 38 96 34 Q102 29 109 32 Q114 27 120 31 Q127 27 133 33 Q139 30 143 39 Q146 44 141 48 Q146 53 140 57 Q137 63 130 60 Q125 65 118 61 Q113 66 106 60 Q99 62 96 56 Q88 54 83 49 Z' />
      <path className='physarum-fallback-vein' d='M18 52 C32 49 39 44 53 47 S70 46 86 46 M29 60 C39 54 46 51 56 51 C69 53 75 50 89 47 M39 35 C46 43 49 44 57 46 C68 45 75 42 87 44 M52 66 C56 57 62 54 72 51 C82 49 85 47 93 46 M62 30 C64 38 70 41 78 44 C83 45 90 43 98 42 M70 59 C77 55 81 55 85 52 C92 48 99 45 108 42' />
      <path className='physarum-fallback-vein physarum-fallback-vein-fine' d='M40 48 C42 52 46 53 50 53 M49 45 C53 40 57 40 63 42 M58 49 C60 45 65 44 70 43 M65 54 C68 58 73 56 78 53 M77 43 C79 39 83 39 87 41 M85 50 C89 56 94 57 100 55 M94 42 Q99 37 107 36 Q114 38 120 34 M94 47 Q100 50 107 47 Q114 45 122 41 Q132 38 140 40 M97 51 Q103 56 111 53 Q120 50 127 54 Q134 56 141 53 M106 59 Q111 56 116 57 Q122 58 127 60 M111 35 Q116 42 119 46 Q124 48 133 47' />
    </svg>
    <span className='physarum-fallback-note'>{REASON_LABELS[reason] || '黏菌模拟已降级为静态视图'}</span>
  </div>
);

export default PhysarumFallback;

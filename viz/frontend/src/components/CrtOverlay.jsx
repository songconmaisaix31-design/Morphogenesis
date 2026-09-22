import React from 'react';

// Global CRT scanline veil: opacity stays inside the agreed 0.03–0.05 band,
// never intercepts pointer events, and freezes under reduced motion.
const CrtOverlay = ({ enabled, reducedMotion }) => {
  if (!enabled) return null;
  return <div className={`crt-overlay${reducedMotion ? ' is-static' : ''}`} aria-hidden='true' />;
};

export default React.memo(CrtOverlay);

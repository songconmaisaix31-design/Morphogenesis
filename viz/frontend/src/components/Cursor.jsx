import React, { useEffect, useRef, useState } from 'react';

// Custom pointer: a small dot glued to the real position plus a trailing ring.
// Enabled only for fine pointers (mouse/trackpad) without reduced motion, and
// only where the shell activates it: the hero view belongs to the P track's
// own food cursor, so this global cursor is active in the swarm view only.
const INTERACTIVE = 'button, a, [role="button"], input, select, textarea, summary, [data-cursor]';

const Cursor = ({ reducedMotion, active }) => {
  const dotRef = useRef(null);
  const ringRef = useRef(null);
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    const fine = window.matchMedia('(pointer: fine)').matches;
    const root = document.documentElement;
    if (!fine || reducedMotion || !active) {
      setEnabled(false);
      root.classList.remove('morph-custom-cursor');
      return undefined;
    }
    setEnabled(true);
    root.classList.add('morph-custom-cursor');

    let x = window.innerWidth / 2;
    let y = window.innerHeight / 2;
    let rx = x;
    let ry = y;
    let raf = 0;
    let shown = false;

    const setShown = (next) => {
      shown = next;
      const opacity = next ? '1' : '0';
      if (dotRef.current) dotRef.current.style.opacity = opacity;
      if (ringRef.current) ringRef.current.style.opacity = opacity;
    };
    const onMove = (event) => {
      x = event.clientX;
      y = event.clientY;
      if (!shown) setShown(true);
      const hover = Boolean(event.target?.closest?.(INTERACTIVE));
      ringRef.current?.classList.toggle('is-hover', hover);
    };
    const onLeave = () => setShown(false);
    const loop = () => {
      rx += (x - rx) * 0.16;
      ry += (y - ry) * 0.16;
      if (dotRef.current) dotRef.current.style.transform = `translate(${x}px, ${y}px)`;
      if (ringRef.current) ringRef.current.style.transform = `translate(${rx}px, ${ry}px)`;
      raf = window.requestAnimationFrame(loop);
    };

    window.addEventListener('mousemove', onMove, { passive: true });
    document.addEventListener('mouseleave', onLeave);
    raf = window.requestAnimationFrame(loop);
    return () => {
      window.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseleave', onLeave);
      window.cancelAnimationFrame(raf);
      root.classList.remove('morph-custom-cursor');
    };
  }, [reducedMotion, active]);

  if (!enabled) return null;
  return (
    <>
      <div ref={ringRef} className='cursor-ring' aria-hidden='true' />
      <div ref={dotRef} className='cursor-dot' aria-hidden='true' />
    </>
  );
};

export default React.memo(Cursor);

// PhysarumField: ambient homepage WebGL slime-mold field.
//
// Props (contract from docs/FRONTEND_REFACTOR_PLAN.md):
//   active        — false pauses the RAF loop and simulation (view hidden)
//   reducedMotion — true renders the static fallback, no animation at all
//   onError       — called once per distinct failure as
//                   onError({ reason, message }) with reason one of
//                   'webgl2-unavailable' | 'float-buffer-unavailable' |
//                   'shader-compile' | 'program-link' | 'framebuffer' |
//                   'context-lost' | 'low-performance' | 'init-failure';
//                   the component always degrades to the static fallback
//                   itself, onError is purely informational.
//
// Behavior: pointer input does not affect the background. The simulation
// pauses while the tab is hidden or `active` is false, and all WebGL resources
// are disposed on unmount. Touch (coarse pointer) devices start at reduced quality;
// sustained low frame rates degrade quality once and then fall back.

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { PhysarumSim, PhysarumUnavailable, QUALITY_LEVELS } from './simulation';
import PhysarumFallback from './PhysarumFallback';
import './physarum.css';

const PERF_CHECK_MS = 2500;
// Sustained frame time above this on the default quality triggers one
// degrade step; if it persists at reduced quality, fall back entirely.
const SLOW_FRAME_MS = 28;
const SLOW_CHECKS_NEEDED = 3;

const PhysarumField = ({ active = true, reducedMotion = false, onError }) => {
  const containerRef = useRef(null);
  const simRef = useRef(null);
  const activeRef = useRef(active);
  const [failure, setFailure] = useState(null);
  const [quality, setQuality] = useState(() =>
    typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(pointer: coarse)').matches ? 1 : 0
  );

  const fail = useCallback(
    (info) => {
      setFailure((prev) => {
        if (prev && prev.reason === info.reason) return prev;
        if (onError) onError(info);
        return info;
      });
    },
    [onError]
  );

  useEffect(() => {
    activeRef.current = active;
    const sim = simRef.current;
    if (!sim) return;
    if (active && !document.hidden) {
      sim.start();
    } else {
      sim.stop();
    }
  }, [active]);

  useEffect(() => {
    if (reducedMotion || failure) return undefined;
    const container = containerRef.current;
    if (!container) return undefined;

    let disposed = false;
    let slowChecks = 0;
    const canvas = document.createElement('canvas');
    canvas.className = 'physarum-canvas';
    canvas.setAttribute('aria-hidden', 'true');
    container.appendChild(canvas);

    let sim;
    try {
      sim = new PhysarumSim(canvas, QUALITY_LEVELS[quality] || QUALITY_LEVELS[0]);
    } catch (err) {
      canvas.remove();
      const reason = err instanceof PhysarumUnavailable ? err.reason : 'init-failure';
      fail({ reason, message: String((err && err.message) || err) });
      return undefined;
    }
    simRef.current = sim;
    sim.onContextLost = () => fail({ reason: 'context-lost', message: 'WebGL context lost' });

    const applySize = () => {
      const rect = container.getBoundingClientRect();
      sim.resize(rect.width, rect.height);
    };
    applySize();

    let resizeTimer = 0;
    const observer = new ResizeObserver(() => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(applySize, 150);
    });
    observer.observe(container);

    const onVisibility = () => {
      if (document.hidden) {
        sim.stop();
      } else if (activeRef.current) {
        sim.start();
      }
    };
    document.addEventListener('visibilitychange', onVisibility);

    // Sustained slowness: degrade once (fewer agents, DPR 1), then fall back.
    const perfTimer = setInterval(() => {
      if (disposed || !sim.running) return;
      if (sim.getAverageFrameMs() > SLOW_FRAME_MS) {
        slowChecks += 1;
      } else {
        slowChecks = 0;
      }
      if (slowChecks >= SLOW_CHECKS_NEEDED) {
        if (quality === 0) {
          setQuality(1);
        } else {
          fail({ reason: 'low-performance', message: `sustained ${sim.getAverageFrameMs().toFixed(1)} ms/frame at reduced quality` });
        }
      }
    }, PERF_CHECK_MS);

    if (activeRef.current && !document.hidden) sim.start();

    // Test/integration handle: read-only snapshot of live sim state.
    container.__physarum = {
      isRunning: () => sim.running,
      getFoodStrength: () => sim.food.strength,
      getFood: () => ({ x: sim.food.x, y: sim.food.y }),
      getAverageFrameMs: () => sim.getAverageFrameMs(),
      getViewSize: () => ({ width: sim.viewWidth, height: sim.viewHeight }),
      getAgentStats: () => sim.getAgentStats(),
      getQuality: () => quality,
    };

    return () => {
      disposed = true;
      delete container.__physarum;
      clearInterval(perfTimer);
      clearTimeout(resizeTimer);
      observer.disconnect();
      document.removeEventListener('visibilitychange', onVisibility);
      sim.dispose();
      simRef.current = null;
      canvas.remove();
    };
  }, [reducedMotion, failure, quality, fail]);

  if (reducedMotion || failure) {
    return (
      <div className='physarum-field' ref={containerRef}>
        <PhysarumFallback reason={reducedMotion ? 'reduced-motion' : failure.reason} />
      </div>
    );
  }

  return <div className='physarum-field' ref={containerRef} />;
};

export default PhysarumField;

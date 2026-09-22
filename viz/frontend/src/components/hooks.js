import { useEffect, useState } from 'react';

// P/T track modules are merged later; glob stays empty until then and the
// shell keeps running on its own fallback views.
const TRACK_ENTRIES = {
  physarum: import.meta.glob(['../physarum/index.{js,jsx}', '../physarum/PhysarumField.{js,jsx}']),
  swarm: import.meta.glob(['../swarm/index.{js,jsx}', '../swarm/SwarmTopology.{js,jsx}']),
};

export function useTrackComponent(track) {
  const [state, setState] = useState({ Component: null, error: null });
  useEffect(() => {
    let cancelled = false;
    const loaders = Object.values(TRACK_ENTRIES[track] ?? {});
    if (!loaders.length) return undefined;
    loaders[0]()
      .then((mod) => {
        if (!cancelled) setState(mod?.default ? { Component: mod.default, error: null } : { Component: null, error: new Error(`${track} 模块缺少默认导出`) });
      })
      .catch((error) => { if (!cancelled) setState({ Component: null, error }); });
    return () => { cancelled = true; };
  }, [track]);
  return state;
}

export function useReducedMotion() {
  const [reduced, setReduced] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  useEffect(() => {
    const query = window.matchMedia('(prefers-reduced-motion: reduce)');
    const onChange = () => setReduced(query.matches);
    query.addEventListener('change', onChange);
    return () => query.removeEventListener('change', onChange);
  }, []);
  return reduced;
}

// Standalone preview harness for the AGENT SWARM view (development and
// browser verification only; not imported by the finals shell build, whose
// lib entry is src/shell.jsx). Data comes from window.__SWARM_DASHBOARD__
// when a harness page embeds a fixture, otherwise from /api/dashboard.
import React from 'react';
import { createRoot } from 'react-dom/client';
import { flushSync } from 'react-dom';
import SwarmTopology from './SwarmTopology';

const props = window.__SWARM_PROPS__ ?? {};
const dashboard = 'dashboard' in props ? props.dashboard : undefined;

const Boot = () => {
  const [data, setData] = React.useState(dashboard);
  React.useEffect(() => {
    if (dashboard !== undefined) return undefined;
    let alive = true;
    fetch('/api/dashboard', { cache: 'no-store' })
      .then((response) => (response.ok ? response.json() : null))
      .then((json) => { if (alive) setData(json); })
      .catch(() => { if (alive) setData(null); });
    return () => { alive = false; };
  }, []);
  return <SwarmTopology dashboard={data} active={props.active !== false} reducedMotion={props.reducedMotion === true} />;
};

flushSync(() => createRoot(document.getElementById('root')).render(<Boot />));

// Entry for the Morphogenesis page shell (hero + agent-swarm dashboard).
// Layout shell adapted from Tencent tdesign-react-starter (MIT)
// src/layouts/components/AppLayout.tsx (top layout) and src/pages/Dashboard/Base.
// The shell owns network reads and view state; data zones with ids render once
// with fixed JSX and are filled by viz/static/app.js via window.MorphDashboard.
import React from 'react';
import { createRoot } from 'react-dom/client';
import { flushSync } from 'react-dom';
import 'tdesign-react/es/style/index.css';
import './theme.css';
import App from './App';
import './reference.css';

document.documentElement.setAttribute('theme-mode', 'dark');
// flushSync keeps the static shell in the DOM before the deferred app.js
// bridge installs, so the first pending update always finds its zones.
flushSync(() => createRoot(document.getElementById('root')).render(<App />));

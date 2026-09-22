// Entry for the finals dashboard React shell.
// Layout shell adapted from Tencent tdesign-react-starter (MIT)
// src/layouts/components/AppLayout.tsx (top layout) and src/pages/Dashboard/Base.
// Data and ECharts stay in the standalone viz/static/app.js; this tree renders
// once and never updates, so it cannot clobber the data-owned DOM zones.
import React from 'react';
import { createRoot } from 'react-dom/client';
import { flushSync } from 'react-dom';
import 'tdesign-react/es/style/index.css';
import './theme.css';
import App from './App';

document.documentElement.setAttribute('theme-mode', 'dark');
// flushSync keeps the static shell in the DOM before the deferred script
// finishes, so load-event observers always find the semantic nodes.
flushSync(() => createRoot(document.getElementById('root')).render(<App />));

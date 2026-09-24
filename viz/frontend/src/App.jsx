// Intro choreography and read-only data bridge.
import React, { useCallback, useEffect, useRef, useState } from 'react';
import Hero from './components/Hero';
import GrowthIntro from './intro/GrowthIntro';
import Backend from './backend/Backend';
import { useReducedMotion } from './components/hooks';

const POLL_MS = 1000;
const viewFromHash = () => ['workspace', 'swarm'].includes(window.location.hash.replace(/^#\/?/, '')) ? 'workspace' : 'physarum';

const App = () => {
  const [view, setViewState] = useState(viewFromHash);
  const [dashboard, setDashboard] = useState(null);
  const [swarm, setSwarm] = useState({ state: 'loading', data: null, detail: '', lastSuccessAt: null });
  const [connection, setConnection] = useState({ state: 'loading', detail: '' });
  const [phase, setPhase] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 3 : 0);
  const [evomap, setEvomap] = useState({ state: 'idle' });
  const reducedMotion = useReducedMotion();
  const [visible, setVisible] = useState(() => !document.hidden);
  useEffect(() => {
    const update = () => setVisible(!document.hidden);
    document.addEventListener('visibilitychange', update);
    return () => document.removeEventListener('visibilitychange', update);
  }, []);

  const viewRef = useRef(view);
  const dashboardRef = useRef(null);
  const lastSignatureRef = useRef('');

  const setView = useCallback((next) => {
    if (next === 'physarum') setPhase(reducedMotion ? 3 : 0);
    setViewState(next);
    window.history.replaceState(null, '', next === 'workspace' ? '#/workspace' : '#/physarum');
  }, [reducedMotion]);

  const pushToDataZones = useCallback((data, { redraw, resize = false }) => {
    const bridge = window.MorphDashboard;
    if (bridge?.update) bridge.update(data, { redraw, resize });
    else window.__morphPendingDashboard = { data, redraw, resize };
  }, []);

  // Same-origin dashboard polling. Failures keep the last good snapshot on
  // screen and surface a stale indicator instead of clearing data.
  useEffect(() => {
    let stopped = false;
    let timer = 0;
    const poll = async () => {
      try {
        const response = await fetch('/api/dashboard', { cache: 'no-store' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (stopped) return;
        dashboardRef.current = data;
        const signature = JSON.stringify(data);
        if (signature !== lastSignatureRef.current) {
          lastSignatureRef.current = signature;
          setDashboard(data);
        }
        setConnection({ state: 'ok', detail: '' });
        pushToDataZones(data, { redraw: viewRef.current === 'workspace' && !document.hidden });
      } catch (error) {
        if (stopped) return;
        setConnection({ state: 'failed', detail: error.message });
        if (window.MorphDashboard?.fail) window.MorphDashboard.fail(error.message);
      }
      if (!stopped) timer = window.setTimeout(poll, POLL_MS);
    };
    poll();
    return () => { stopped = true; window.clearTimeout(timer); };
  }, [pushToDataZones]);

  // Same-origin decentralized swarm view. Old facts survive a transport error
  // only as an explicitly stale snapshot; rehearsal data is never substituted.
  useEffect(() => {
    let stopped = false;
    let timer = 0;
    const poll = async () => {
      try {
        const response = await fetch('/api/swarm', { cache: 'no-store' });
        const data = await response.json().catch(() => null);
        if (!response.ok) throw new Error(data?.notes?.[0] ?? `HTTP ${response.status}`);
        if (!stopped) setSwarm({ state: data?.health === 'missing' ? 'missing' : data?.health === 'error' ? 'error' : 'ready', data, detail: '', lastSuccessAt: Date.now() });
      } catch (error) {
        if (!stopped) setSwarm((previous) => ({ ...previous, state: previous.data ? 'stale' : 'error', detail: error.message }));
      }
      if (!stopped) timer = window.setTimeout(poll, POLL_MS);
    };
    poll();
    return () => { stopped = true; window.clearTimeout(timer); };
  }, []);

  // Independent read-only EvoMap explorer; never feeds the runtime topology.
  // Requests fire only on first entry into the info view and on explicit
  // search/refresh — no polling. A sequence guard drops out-of-order
  // responses when the user searches again while a request is in flight.
  const evomapQueryRef = useRef({ q: 'repair', type: undefined, limit: 10 });
  const evomapSeqRef = useRef(0);
  const searchEvomap = useCallback(async (query) => {
    if (query) evomapQueryRef.current = query;
    const params = evomapQueryRef.current;
    const search = new URLSearchParams();
    if (params.q) search.set('q', params.q);
    if (params.type) search.set('type', params.type);
    if (params.limit) search.set('limit', String(params.limit));
    const seq = ++evomapSeqRef.current;
    setEvomap((prev) => ({ ...prev, state: prev.data ? prev.state : 'loading', loading: true }));
    try {
      const response = await fetch(`/api/evomap?${search.toString()}`, { cache: 'no-store' });
      if (seq !== evomapSeqRef.current) return;
      if (response.status === 404) {
        setEvomap({ state: 'missing' });
      } else if (response.status === 400) {
        const body = await response.json().catch(() => null);
        setEvomap((prev) => ({ ...prev, state: 'invalid', detail: body?.detail ?? 'invalid_query', loading: false }));
      } else if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      } else {
        const data = await response.json();
        setEvomap({ state: 'ok', data, loading: false });
      }
    } catch (error) {
      if (seq !== evomapSeqRef.current) return;
      // Keep the last good payload but mark the top-level state as a real
      // failure — old results must never pose as a fresh success.
      setEvomap((prev) => ({ ...prev, state: 'error', detail: error.message, loading: false }));
    }
  }, []);

  // On-demand asset detail: fires only when the user clicks a result's 详情
  // button — never prefetched per card and never on a timer. Frozen E-track
  // contract morph.evomap.asset/1: GET /api/evomap/asset?id=<asset_id> with a
  // sequence guard dropping out-of-order responses.
  const [evomapDetail, setEvomapDetail] = useState({ state: 'idle' });
  const evomapDetailSeqRef = useRef(0);
  const openEvomapAsset = useCallback(async (assetId) => {
    if (!assetId) return;
    const seq = ++evomapDetailSeqRef.current;
    setEvomapDetail({ state: 'loading', assetId });
    try {
      const params = new URLSearchParams({ id: String(assetId) });
      const response = await fetch(`/api/evomap/asset?${params.toString()}`, { cache: 'no-store' });
      if (seq !== evomapDetailSeqRef.current) return;
      if (response.status === 404) {
        // Official single-asset misses surface the fixed asset-not-found code
        // (http_404 inside asset_detail on 200, or the coded 404 body); only an
        // uncoded 404 means the E-track route itself is not merged yet.
        const body = await response.json().catch(() => null);
        const code = body?.error ?? body?.detail;
        if (code === 'asset_not_found' || code === 'http_404') setEvomapDetail({ state: 'not_found', assetId });
        else setEvomapDetail({ state: 'missing', assetId });
      } else if (response.status === 400) {
        const body = await response.json().catch(() => null);
        setEvomapDetail({ state: 'invalid', assetId, detail: body?.detail ?? body?.error ?? 'invalid_asset_id' });
      } else if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      } else {
        const data = await response.json();
        setEvomapDetail({ state: 'ok', assetId, data });
      }
    } catch (error) {
      if (seq !== evomapDetailSeqRef.current) return;
      setEvomapDetail((prev) => ({ ...prev, state: 'error', detail: error.message }));
    }
  }, []);

  // View switch: pause hidden-view redraws, flush the latest snapshot into the
  // freshly visible view on the next frame (charts resize after re-layout).
  useEffect(() => {
    viewRef.current = view;
    document.body.dataset.view = view;
    if (view === 'workspace' && dashboardRef.current) {
      const raf = window.requestAnimationFrame(() => pushToDataZones(dashboardRef.current, { redraw: true, resize: true }));
      return () => window.cancelAnimationFrame(raf);
    }
    return undefined;
  }, [view, pushToDataZones]);

  const evomapRequestedRef = useRef(false);
  useEffect(() => {
    if (view === 'workspace' && !evomapRequestedRef.current) {
      evomapRequestedRef.current = true;
      searchEvomap();
    }
  }, [view, searchEvomap]);

  useEffect(() => {
    const onHash = () => {
      const next = viewFromHash();
      if (next === 'physarum') setPhase(reducedMotion ? 3 : 0);
      setViewState(next);
    };
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, [reducedMotion]);

  // Each phase advances only while the document is visible. A return to the
  // intro starts it again; reduced motion exposes the final state immediately.
  useEffect(() => {
    if (view !== 'physarum') return undefined;
    if (reducedMotion) {
      setPhase(3);
      return undefined;
    }
    setPhase(0);
    let elapsed = 0;
    let started = 0;
    let timer = 0;
    const marks = [0, 3600, 8000, 10400];
    const update = () => {
      if (document.hidden) return;
      started = window.performance.now();
      const next = marks.findIndex((mark) => mark > elapsed);
      setPhase(next < 0 ? 3 : Math.max(0, next - 1));
      if (next < 0) return;
      timer = window.setTimeout(() => {
        elapsed += window.performance.now() - started;
        update();
      }, marks[next] - elapsed);
    };
    const visibility = () => {
      window.clearTimeout(timer);
      if (document.hidden) elapsed += window.performance.now() - started;
      else update();
    };
    document.addEventListener('visibilitychange', visibility);
    update();
    return () => {
      window.clearTimeout(timer);
      document.removeEventListener('visibilitychange', visibility);
    };
  }, [view, reducedMotion]);

  const viewClass = (name) => `morph-view morph-view-${name}${view === name ? ' is-active' : ''}`;

  return (
    <div className='morph-layout' data-document-visible={visible}>
      <main className='morph-stage'>
        <section className={viewClass('physarum')} aria-label='形态发生序幕'
          aria-hidden={view !== 'physarum'} inert={view === 'physarum' ? undefined : ''}>
          <div className={`story-physarum-scene${phase >= 1 ? ' is-past' : ''}`}>
            <Hero active={view === 'physarum' && phase < 1} reducedMotion={reducedMotion} showLabel={phase >= 0} />
          </div>
          <div className={`story-growth-scene${phase >= 1 ? ' is-visible' : ''}${phase >= 2 ? ' has-product' : ''}`}
            aria-hidden={phase < 1}>
            <GrowthIntro key={view === 'physarum' && phase >= 1 ? 'growing' : 'waiting'}
              active={visible && view === 'physarum' && phase >= 1} reducedMotion={reducedMotion} />
            <div className={`story-product${phase >= 2 ? ' is-visible' : ''}`} aria-hidden={phase < 2}>
              <h1><span lang='zh-CN'>形态发生</span><span lang='en'>MORPHOGENESIS</span></h1>
              <button type='button' className={`story-enter${phase >= 3 ? ' is-visible' : ''}`}
                disabled={phase < 3} onClick={() => setView('workspace')}>进入产品后台 <span aria-hidden='true'>↗</span></button>
            </div>
          </div>
          {connection.state === 'failed' && <p className='story-connection' role='status'>数据连接失败：{connection.detail}</p>}
        </section>
        <section className={viewClass('workspace')} aria-label='产品后台'
          aria-hidden={view !== 'workspace'} inert={view === 'workspace' ? undefined : ''}>
          <Backend dashboard={dashboard} swarm={swarm} active={view === 'workspace'} reducedMotion={reducedMotion}
            evomap={evomap} evomapDetail={evomapDetail} onSearch={searchEvomap}
            onOpenAsset={openEvomapAsset} onReturn={() => setView('physarum')} />
        </section>
      </main>
    </div>
  );
};

export default React.memo(App);

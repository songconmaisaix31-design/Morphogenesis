// Morphogenesis page shell: hero (Physarum field) + agent-swarm dashboard.
// The shell owns all network reads (/api/dashboard, /api/evomap) and view
// switching; the data-owned DOM zones with ids stay static in this tree and
// are filled by viz/static/app.js through window.MorphDashboard. React state
// changes never rewrite those zones because their JSX is fixed.
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Layout, Card, Row, Col } from 'tdesign-react';
import Board from './components/Board';
import Hero from './components/Hero';
import Cursor from './components/Cursor';
import CrtOverlay from './components/CrtOverlay';
import EvoMapPanel from './components/EvoMapPanel';
import { useReducedMotion, useTrackComponent } from './components/hooks';

const { Header, Content, Footer } = Layout;

const POLL_MS = 1000;

const viewFromHash = () => (window.location.hash.replace(/^#\/?/, '') === 'swarm' ? 'swarm' : 'physarum');

const FinalsHeader = ({ view, onSwitch, crt, onToggleCrt }) => (
  <Header className='morph-header'>
    <div className='morph-brand'>
      <button type='button' className='morph-brand-name' onClick={() => onSwitch('physarum')}>MORPHOGENESIS</button>
      <span className='morph-brand-sub'>决赛彩排 · 恢复路径</span>
    </div>
    <nav className='morph-nav' aria-label='视图切换'>
      <button type='button' className={`morph-marker${view === 'physarum' ? ' is-current' : ''}`}
        aria-current={view === 'physarum' ? 'page' : undefined} onClick={() => onSwitch('physarum')}>PHYSARUM</button>
      <button type='button' className={`morph-marker${view === 'swarm' ? ' is-current' : ''}`}
        aria-current={view === 'swarm' ? 'page' : undefined} onClick={() => onSwitch('swarm')}>AGENT SWARM</button>
    </nav>
    <div className='morph-header-facts'>
      <span className='morph-header-fact'>在线成员 <b id='header-members'>未知</b></span>
      <span className='morph-header-fact'>任务轮次 <b id='header-round'>未知</b></span>
      <span id='rehearsal-mode' className='morph-header-mode'>等待彩排快照；不预设结果。</span>
      <span id='provenance' className='morph-badge'>加载中</span>
      <span id='connection-state' className='morph-connection' role='status'></span>
      <button type='button' className='morph-crt-toggle' aria-pressed={crt} onClick={onToggleCrt}
        title='CRT 扫描线开关（opacity 0.04，可关闭）'>CRT {crt ? 'ON' : 'OFF'}</button>
    </div>
  </Header>
);

const TopologyPanel = ({ dashboard, active, reducedMotion }) => {
  const { Component: SwarmTopology, error } = useTrackComponent('swarm');
  useEffect(() => {
    document.body.dataset.swarmModule = SwarmTopology && !error ? 'loaded' : 'fallback';
  }, [SwarmTopology, error]);
  return (
    <Card className='morph-panel morph-topology' bordered={false}
      title={<span className='morph-panel-title'>选路拓扑 · 真实权重</span>}
      actions={<span className='morph-panel-side' id='story-offline-member'>未发生 / 未加载</span>}>
      <p className='morph-panel-line'><b id='story-question'>未加载</b><span id='story-question-detail'>等待实际题目、已知失败点与来源。</span></p>
      <p className='morph-panel-line' id='story-offline-reason'>下线原因和恢复 checkpoint 均须来自真实快照。</p>
      <div className='morph-topology-body'>
        <div className='morph-topology-chart'>
          {SwarmTopology && !error
            ? <div className='swarm-topology-slot'><SwarmTopology dashboard={dashboard} active={active} reducedMotion={reducedMotion} /></div>
            : null}
          <div id='story-pipe-chart' className='story-pipe-chart' style={SwarmTopology && !error ? { display: 'none' } : undefined}></div>
          <div id='story-pipe-empty' className='empty pipe-empty' hidden></div>
        </div>
        <div id='story-pipes' className='pipe-list'><p>尚无管道快照</p></div>
      </div>
    </Card>
  );
};

const EventPanel = () => (
  <Card className='morph-panel' bordered={false} title={<span className='morph-panel-title'>事件流 · 真实阶段历史</span>}>
    <div id='event-feed' className='event-feed'><p>尚无阶段快照</p></div>
  </Card>
);

const AcceptanceStrip = () => (
  <section className='morph-strip' aria-label='验收三态与数据来源'>
    <div className='states'>
      <div className='state-row'><span>contract_local</span><b id='contract_local'>not_run</b><small>本地契约</small></div>
      <div className='state-row'><span>interface_live</span><b id='interface_live'>not_run</b><small>真实接口</small></div>
      <div className='state-row'><span>task_live</span><b id='task_live'>not_run</b><small>真实任务</small></div>
    </div>
    <div className='source'><span id='source-label'></span><span id='hub-status'></span></div>
  </section>
);

const GeneLedger = () => (
  <Card className='morph-panel gene-ledger' bordered={false}
    title={<span className='morph-panel-title'>Gene 池 · 生成 / 采用 / 衰减 / 归档</span>}>
    <div id='story-genes' className='gene-ledger-list'><p>尚无 GeneView 快照</p></div>
  </Card>
);

const SecondaryPanel = () => (
  <section className='morph-secondary' aria-label='谱系、消息与指标详情'>
    <Card className='morph-panel' bordered={false} title={<span className='morph-panel-title'>Gene 谱系</span>}>
      <p className='morph-panel-note'>仅使用显式导出的 Gene 正文；无正文时不推断谱系。</p>
      <div id='gene-chart' className='chart'></div><div id='gene-empty' className='empty' hidden></div>
    </Card>
    <Card className='morph-panel' bordered={false} title={<span className='morph-panel-title'>消息流</span>}>
      <p className='morph-panel-note'>按 Envelope 的 sender / receiver / msg_type 可视化。</p>
      <div id='message-chart' className='chart'></div><div id='message-empty' className='empty' hidden></div>
    </Card>
    <Card className='morph-panel morph-secondary-wide' bordered={false} title={<span className='morph-panel-title'>指标：当前、历史均值、历史最佳</span>}>
      <p className='morph-panel-note'>无历史指标导出即保留空态；图表不预设增长方向。</p>
      <div id='metric-chart' className='chart'></div><div id='metric-empty' className='empty' hidden></div>
    </Card>
    <Card className='morph-panel morph-secondary-wide' bordered={false} title={<span className='morph-panel-title'>运行说明</span>}>
      <ul id='notes' className='morph-notes'></ul>
    </Card>
  </section>
);

const Dashboard = ({ dashboard, active, reducedMotion }) => (
  <div className='morph-dashboard'>
    <Row gutter={[12, 12]} className='morph-boards'>
      <Col xs={12} md={4}>
        <Board title='CHECKPOINT 通过率' countId='story-checkpoint-rate' count='未加载'
          desc={<ol id='story-checkpoints' className='checkpoint-list'><li>尚无 checkpoint 快照</li></ol>} />
      </Col>
      <Col xs={12} md={4}>
        <Board title='本轮 TOKENS' countId='metric-tokens' count='未知'
          desc='当前任务实际用量；无记录保持未知。' />
      </Col>
      <Col xs={12} md={4}>
        <Board title='活跃 GENE' countId='story-gene-count' count='未知'
          desc='未归档 Gene 数。' />
      </Col>
    </Row>
    <div className='morph-main'>
      <TopologyPanel dashboard={dashboard} active={active} reducedMotion={reducedMotion} />
      <div className='morph-rail'>
        <EventPanel />
      </div>
    </div>
    <AcceptanceStrip />
    <GeneLedger />
    <SecondaryPanel />
  </div>
);

const App = () => {
  const [view, setViewState] = useState(viewFromHash);
  const [dashboard, setDashboard] = useState(null);
  const [connection, setConnection] = useState({ state: 'loading', detail: '' });
  const [evomap, setEvomap] = useState({ state: 'idle' });
  const [crt, setCrt] = useState(() => window.localStorage.getItem('morph-crt') !== 'off');
  const reducedMotion = useReducedMotion();

  const viewRef = useRef(view);
  const dashboardRef = useRef(null);
  const lastSignatureRef = useRef('');

  const setView = useCallback((next) => {
    setViewState(next);
    window.history.replaceState(null, '', next === 'swarm' ? '#/swarm' : '#/physarum');
  }, []);

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
        pushToDataZones(data, { redraw: viewRef.current === 'swarm' && !document.hidden });
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

  // View switch: pause hidden-view redraws, flush the latest snapshot into the
  // freshly visible view on the next frame (charts resize after re-layout).
  useEffect(() => {
    viewRef.current = view;
    document.body.dataset.view = view;
    if (view === 'swarm' && dashboardRef.current) {
      const raf = window.requestAnimationFrame(() => pushToDataZones(dashboardRef.current, { redraw: true, resize: true }));
      return () => window.cancelAnimationFrame(raf);
    }
    return undefined;
  }, [view, pushToDataZones]);

  const evomapRequestedRef = useRef(false);
  useEffect(() => {
    if (view === 'swarm' && !evomapRequestedRef.current) {
      evomapRequestedRef.current = true;
      searchEvomap();
    }
  }, [view, searchEvomap]);

  useEffect(() => {
    const onHash = () => setViewState(viewFromHash());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  useEffect(() => {
    const onKey = (event) => {
      if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.altKey) return;
      const tag = event.target?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || event.target?.isContentEditable) return;
      if (event.key === '1' || event.key === 'ArrowLeft') setView('physarum');
      else if (event.key === '2' || event.key === 'ArrowRight') setView('swarm');
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [setView]);

  const toggleCrt = useCallback(() => {
    setCrt((prev) => {
      window.localStorage.setItem('morph-crt', prev ? 'off' : 'on');
      return !prev;
    });
  }, []);

  const viewClass = (name) => `morph-view morph-view-${name}${view === name ? ' is-active' : ''}`;

  return (
    <Layout className='morph-layout'>
      <FinalsHeader view={view} onSwitch={setView} crt={crt} onToggleCrt={toggleCrt} />
      <Content className='morph-content'>
        <div className='morph-stage'>
          <section className={viewClass('physarum')} aria-hidden={view !== 'physarum'} inert={view === 'physarum' ? undefined : ''}>
            <Hero active={view === 'physarum'} reducedMotion={reducedMotion} onEnterSwarm={() => setView('swarm')} />
            {connection.state === 'failed' ? <p className='morph-hero-connection'>数据连接失败：{connection.detail} · 切换到 AGENT SWARM 查看保留的最近快照</p> : null}
          </section>
          <section className={viewClass('swarm')} aria-hidden={view !== 'swarm'} inert={view === 'swarm' ? undefined : ''}>
            <Dashboard dashboard={dashboard} active={view === 'swarm'} reducedMotion={reducedMotion} />
            <EvoMapPanel evomap={evomap} onSearch={searchEvomap} />
          </section>
        </div>
      </Content>
      <Footer className='morph-footer'>
        <span>布局外壳适配自 Tencent tdesign-react-starter（MIT，fce97863）· 数据只读来自同源 /api/dashboard · 键盘：1 / ← 回 PHYSARUM，2 / → 进 AGENT SWARM · 参考站点仅取视觉节奏，未复制素材</span>
      </Footer>
      <CrtOverlay enabled={crt} reducedMotion={reducedMotion} />
      <Cursor reducedMotion={reducedMotion} active={view === 'swarm'} />
    </Layout>
  );
};

export default React.memo(App);

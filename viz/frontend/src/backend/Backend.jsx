// Product workspace. The shell owns network requests and calls MorphDashboard;
// its data-owned DOM IDs live here and must remain stable across React renders.
import React, { useEffect, useState } from 'react';
import { Card } from 'tdesign-react';
import Board from '../components/Board';
import EvoMapPanel from '../components/EvoMapPanel';
import { useTrackComponent } from '../components/hooks';
import './backend.css';

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
      <div className={`morph-topology-body${SwarmTopology && !error ? ' has-swarm-module' : ''}`}>
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
  <Card className='morph-panel' bordered={false} title={<span className='morph-panel-title'>事件流</span>}>
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
    title={<span className='morph-panel-title'>Gene 池</span>}>
    <div id='story-genes' className='gene-ledger-list'><p>尚无 GeneView 快照</p></div>
  </Card>
);

const SecondaryPanel = () => (
  <section id='backend-evidence' className='morph-secondary' aria-label='谱系、消息与指标详情'>
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
  </section>
);

const scrollToSection = (id) => document.getElementById(id)?.scrollIntoView({
  behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth',
  block: 'start',
});

const Backend = ({ dashboard, active = true, reducedMotion = false, evomap, evomapDetail, onSearch, onOpenAsset, onReturn }) => {
  const [selectedSection, setSelectedSection] = useState('backend-overview');
  const navigate = (id) => { setSelectedSection(id); scrollToSection(id); };
  return (
  <div className='morph-backend'>
    <header className='backend-topbar'>
      <div className='backend-brand'><span className='backend-brand-mark' aria-hidden='true'>◒</span><span>形态发生</span><small>MORPHOGENESIS</small></div>
      <div className='backend-location'><span>工作台</span><span aria-hidden='true'>/</span><strong>蜂群总览</strong></div>
      <div className='backend-topbar-right'>
        <span id='connection-state' className='morph-connection' role='status'></span>
        <span id='provenance' className='morph-badge'>加载中</span>
        <button type='button' className='backend-return' onClick={onReturn}>返回序幕</button>
      </div>
    </header>
    <div className='backend-grid'>
      <nav className='backend-sidebar' aria-label='工作台导航'>
        <div className='backend-nav-group'><span className='backend-nav-caption'>Workspace</span>
          {[['backend-overview', '◫', '蜂群总览'], ['backend-topology', '◇', '选路拓扑'], ['backend-genes', '⌘', 'Gene 池'], ['backend-evidence', '≋', '证据与指标'], ['backend-evomap', '⌕', 'EvoMap 只读']].map(([id, icon, label]) => (
            <button key={id} type='button' aria-current={selectedSection === id ? 'location' : undefined} onClick={() => navigate(id)}><span aria-hidden='true'>{icon}</span>{label}</button>
          ))}
        </div>
        <div className='backend-nav-group backend-sidebar-status'><span className='backend-nav-caption'>Runtime</span>
          <span>在线成员 <b id='header-members'>未知</b></span>
          <span>任务轮次 <b id='header-round'>未知</b></span>
          <span id='rehearsal-mode'>等待彩排快照；不预设结果。</span>
        </div>
        <p className='backend-sidebar-foot'>仅展示同源数据与显式验收状态。</p>
      </nav>
      <main className='backend-main' id='backend-overview'>
        <div className='backend-document'>
        <div className='backend-heading'><div><span className='backend-project-mark' aria-hidden='true'>◈</span><h1>蜂群总览</h1><p>任务进展、选路关系与 Gene 状态</p></div><span className='backend-heading-tag'>同源只读视图</span></div>
        <section className='backend-metrics' aria-label='运行指标'>
          <Board title='CHECKPOINT 通过率' countId='story-checkpoint-rate' count='未加载'
            desc={<ol id='story-checkpoints' className='checkpoint-list'><li>尚无 checkpoint 快照</li></ol>} />
          <Board title='本轮 TOKENS' countId='metric-tokens' count='未知' desc='当前任务实际用量；无记录保持未知。' />
          <Board title='活跃 GENE' countId='story-gene-count' count='未知' desc='未归档 Gene 数。' />
        </section>
        <section id='backend-topology' className='backend-section'><TopologyPanel dashboard={dashboard} active={active} reducedMotion={reducedMotion} /></section>
        <section id='backend-genes' className='backend-section'><GeneLedger /></section>
        <SecondaryPanel />
        <Card className='morph-panel backend-notes' bordered={false} title={<span className='morph-panel-title'>运行说明</span>}><ul id='notes' className='morph-notes'></ul></Card>
        <section id='backend-evomap' className='backend-evomap'><EvoMapPanel evomap={evomap} detail={evomapDetail} onSearch={onSearch} onOpenAsset={onOpenAsset} /></section>
        </div>
      </main>
      <aside className='backend-context' aria-label='当前上下文'>
        <div className='backend-context-head'><h2>运行上下文</h2><span>Properties</span></div>
        <div className='backend-context-scroll'><AcceptanceStrip /><EventPanel /></div>
      </aside>
    </div>
  </div>
  );
};

export default React.memo(Backend);

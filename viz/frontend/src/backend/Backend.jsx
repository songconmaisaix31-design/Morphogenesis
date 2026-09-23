// Adapted from linear-site HeroIllustration's frame/sidebar/issue DOM and
// IssueListView's location bar. Source classes deliberately remain visible.
// React owns navigation; the existing bridge owns the stable data-zone IDs.
import React, { useEffect, useRef, useState } from 'react';
import EvoMapPanel from '../components/EvoMapPanel';
import { useTrackComponent } from '../components/hooks';
import Icon from './LinearIcons';
import './linear-package.css';
import './backend.css';

const views = [
  ['overview', 'task', '当前任务'], ['topology', 'topology', '蜂群拓扑'],
  ['genes', 'gene', 'Gene 池'], ['evidence', 'metrics', '证据与指标'], ['evomap', 'search', 'EvoMap 只读'],
];
const labels = { passed: '已通过', failed: '未通过', not_run: '未运行' };
const stages = { completed: '已完成', failed: '已停止', awaiting_offline: '等待下线确认', archived: '经验已归档' };
const Property = ({ icon, label, children }) => <div className='KFZpfa_propertyRow'>
  <Icon name={icon} /><span className='property-label'>{label}</span><span className='property-value'>{children}</span>
</div>;

function TopologyPanel({ dashboard, swarm, active, reducedMotion }) {
  const { Component: SwarmTopology, error } = useTrackComponent('swarm');
  useEffect(() => { document.body.dataset.swarmModule = SwarmTopology && !error ? 'loaded' : 'fallback'; }, [SwarmTopology, error]);
  return <>
    <div className='backend-page-heading'><h1>蜂群拓扑</h1><span id='story-offline-member'>未发生 / 未加载</span></div>
    <p className='backend-description' id='story-offline-reason'>尚无运行快照。</p>
    <div className={`morph-topology-body${SwarmTopology && !error ? ' has-swarm-module' : ''}`}>
      {SwarmTopology && !error && <SwarmTopology dashboard={dashboard} swarm={swarm} active={active} reducedMotion={reducedMotion} />}
      <div id='story-pipe-chart' className='story-pipe-chart' style={SwarmTopology && !error ? { display: 'none' } : undefined} />
      <div id='story-pipe-empty' className='empty pipe-empty' hidden />
      <details className='backend-pipe-details'><summary>管道权重详情</summary><div id='story-pipes' className='pipe-list'><p>尚无管道快照</p></div></details>
    </div>
  </>;
}

function Backend({ dashboard, swarm = null, active = true, reducedMotion = false, evomap, evomapDetail, onSearch, onOpenAsset, onReturn }) {
  const [selected, setSelected] = useState(() => window.location.hash === '#/swarm' ? 'topology' : 'overview');
  const [detailsOpen, setDetailsOpen] = useState(false);
  const detailTrigger = useRef(null);
  const closeButton = useRef(null);
  const current = dashboard?.rehearsal?.current;
  const status = current ? stages[current.stage] ?? current.stage ?? '未知' : '未加载';
  const title = views.find(([id]) => id === selected)?.[2];
  const navigate = (id) => setSelected(id);
  useEffect(() => { document.querySelector('.backend-content-scroll')?.scrollTo(0, 0); }, [selected]);
  useEffect(() => {
    const raf = requestAnimationFrame(() => window.dispatchEvent(new Event('morph:panel-visible')));
    return () => cancelAnimationFrame(raf);
  }, [selected, active, detailsOpen]);
  useEffect(() => { if (detailsOpen) closeButton.current?.focus(); }, [detailsOpen]);
  const openDetails = (event) => { detailTrigger.current = event.currentTarget; setDetailsOpen(true); };
  const closeDetails = () => { setDetailsOpen(false); detailTrigger.current?.focus(); };
  const tabKeys = (event) => {
    const index = views.findIndex(([id]) => id === selected);
    const next = event.key === 'ArrowDown' || event.key === 'ArrowRight' ? (index + 1) % views.length
      : event.key === 'ArrowUp' || event.key === 'ArrowLeft' ? (index + views.length - 1) % views.length
      : event.key === 'Home' ? 0 : event.key === 'End' ? views.length - 1 : -1;
    if (next < 0) return;
    event.preventDefault(); setSelected(views[next][0]); document.getElementById(`nav-${views[next][0]}`)?.focus();
  };
  const tab = ([id, icon, label]) => <button key={id} id={`nav-${id}`} type='button' role='tab'
    className='Mmx1Wq_navItem' data-interactive='true' data-active={selected === id}
    aria-selected={selected === id} aria-controls={`backend-${id}`} tabIndex={selected === id ? 0 : -1}
    onKeyDown={tabKeys} onClick={() => navigate(id)}><Icon name={icon} /><span>{label}</span></button>;
  const panelProps = id => ({ id: `backend-${id}`, role: 'tabpanel', 'aria-labelledby': `nav-${id}`,
    hidden: selected !== id, inert: selected !== id ? '' : undefined, tabIndex: 0 });

  return <div className='morph-backend WS84WW_frame' data-active={active} onKeyDown={e => { if (e.key === 'Escape' && detailsOpen) closeDetails(); }}>
    <nav className='Mmx1Wq_sidebar backend-sidebar' aria-label='工作台导航'>
      <div className='backend-sidebar-tools'>
        <button type='button' className='Mmx1Wq_switchWorkspaceButton' onClick={() => navigate('overview')} aria-label='形态发生，当前任务'>
          <span className='Mmx1Wq_logoWrapper morph-brand-symbol'><Icon name='status' /></span><strong>形态发生</strong>
        </button>
        <div className='backend-tool-buttons'>
          <button className='Mmx1Wq_searchButton' type='button' aria-label='搜索 EvoMap' onClick={() => { navigate('evomap'); requestAnimationFrame(() => document.querySelector('.morph-evomap-form input')?.focus()); }}><Icon name='search' /></button>
          <button className='Mmx1Wq_newIssueButton backend-return' type='button' aria-label='返回序幕' title='返回序幕' onClick={onReturn}><Icon name='target' /></button>
        </div>
      </div>
      <div role='tablist' aria-label='工作区视图' aria-orientation='vertical' className='backend-view-tabs'>
        <div className='Mmx1Wq_navItems'>{views.slice(0, 2).map(tab)}</div>
        <div className='backend-nav-group'><span className='Mmx1Wq_navItem Mmx1Wq_collapsible'>工作空间 <Icon name='chevron' /></span><div className='Mmx1Wq_navItems'>{views.slice(2).map(tab)}</div></div>
      </div>
      <div className='backend-sidebar-foot'><Icon name='inbox' /><span>同源工作区 · 只读</span></div>
    </nav>
    <main className='WS84WW_view backend-main'>
      <div className='KFZpfa_panel'>
        <header className='_1uFtza_header _1uFtza_locationBar backend-topbar'>
          <div className='_1uFtza_breadcrumb backend-breadcrumb'><Icon name={views.find(([id]) => id === selected)?.[1]} /><span>{title}</span><span className='backend-breadcrumb-task' title={current?.task_id}>{current?.task_id ?? 'Morphogenesis'}</span></div>
          <div className='backend-toolbar-end'><span id='provenance' className='morph-badge'>加载中</span><button type='button' className='_1uFtza_buttonBase' aria-label='查看运行详情' aria-expanded={detailsOpen} aria-controls='backend-details' onClick={openDetails}><Icon name='more' /></button></div>
        </header>
        <div id='connection-state' className='morph-connection' role='status' />
        <div className='_1uFtza_viewBar backend-viewbar'><span className='backend-run-status'><Icon name='status' />{status}</span><button type='button' className='_1uFtza_pillButton' onClick={openDetails}><Icon name='target' /><span>验收详情</span></button></div>
        <div className='backend-content-scroll'>
          <section {...panelProps('overview')} className='KFZpfa_viewBody backend-overview'>
            <article className='KFZpfa_body KFZpfa_contentColumn'>
              <div className='KFZpfa_title'><h1 className='KFZpfa_titleText' id='story-question'>尚无运行中的任务</h1><p className='KFZpfa_description' id='story-question-detail'>等待实际任务快照。</p></div>
              <section className='backend-activity' aria-label='任务活动'><h2>活动</h2><div id='event-feed' className='KFZpfa_activityList event-feed'><p>尚无阶段快照</p></div></section>
            </article>
            <aside className='KFZpfa_propertiesColumn' aria-label='任务属性'>
              <div className='KFZpfa_category'><h2 className='KFZpfa_categoryTitle'>运行属性</h2>
                <Property icon='status' label='状态'>{status}</Property>
                <Property icon='inbox' label='来源'>{dashboard?.source_label === '未加载导出' ? '未加载' : ({ mock: '模拟数据', replay: '历史回放', live: '现场数据' })[dashboard?.provenance] ?? '未知'}</Property>
                <Property icon='task' label='任务轮次'><span id='header-round'>未知</span></Property>
                <Property icon='topology' label='在线成员'><span id='header-members'>未知</span></Property>
              </div>
              <div className='KFZpfa_category backend-metrics'><h2 className='KFZpfa_categoryTitle'>指标</h2>
                <Property icon='target' label='检查点'><span id='story-checkpoint-rate'>未加载</span></Property>
                <Property icon='activity' label='Tokens'><span id='metric-tokens'>未知</span></Property>
                <Property icon='gene' label='活跃 Gene'><span id='story-gene-count'>未知</span></Property>
              </div>
              <div className='KFZpfa_category'><h2 className='KFZpfa_categoryTitle'>验收</h2>
                {[['contract_local','本地契约'],['interface_live','真实接口'],['task_live','真实任务']].map(([key,label]) => <Property key={key} icon='target' label={label}>{labels[dashboard?.acceptance?.[key] ?? 'not_run'] ?? dashboard.acceptance[key]}</Property>)}
                <button type='button' className='backend-detail-link' onClick={openDetails}>查看来源与完整状态</button>
              </div>
            </aside>
          </section>
          <section {...panelProps('topology')} className='backend-document'><TopologyPanel dashboard={dashboard} swarm={swarm} active={active && selected === 'topology'} reducedMotion={reducedMotion} /></section>
          <section {...panelProps('genes')} className='backend-document'><div className='backend-page-heading'><h1>Gene 池</h1></div><div id='story-genes' className='gene-ledger-list'><p>尚无 Gene 快照</p></div><h2>谱系</h2><div id='gene-chart' className='chart' /><div id='gene-empty' className='empty' hidden /></section>
          <section {...panelProps('evidence')} className='backend-document'><div className='backend-page-heading'><h1>证据与指标</h1></div><h2>消息流</h2><div id='message-chart' className='chart' /><div id='message-empty' className='empty' hidden /><h2>历史指标</h2><div id='metric-chart' className='chart' /><div id='metric-empty' className='empty' hidden /></section>
          <section {...panelProps('evomap')} className='backend-document'><EvoMapPanel evomap={evomap} detail={evomapDetail} onSearch={onSearch} onOpenAsset={onOpenAsset} /></section>
        </div>
      </div>
      <aside id='backend-details' className='KFZpfa_chatBox backend-detail-layer' role='dialog' aria-label='运行详情' hidden={!detailsOpen}>
        <div className='GkoSzG_panel'><header className='NN4GVa_header'><div className='NN4GVa_identity'><Icon name='task' /><strong className='NN4GVa_name'>运行详情</strong><span className='NN4GVa_modelTag'>只读</span></div><button ref={closeButton} type='button' className='_1uFtza_buttonBase' aria-label='关闭运行详情' onClick={closeDetails}>×</button></header>
          <div className='backend-detail-body'>
            <h3>来源</h3><p id='source-label'>未知</p><p id='rehearsal-mode'>等待快照</p><p id='hub-status'>未知</p>
            <h3>验收状态</h3><div className='states'>{['contract_local','interface_live','task_live'].map(key => <div className='state-row' key={key}><code>{key}</code><b id={key}>not_run</b></div>)}</div>
            <h3>检查点</h3><ol id='story-checkpoints' className='checkpoint-list'><li>尚无 checkpoint 快照</li></ol>
            <h3>运行说明</h3><ul id='notes' className='morph-notes' />
          </div>
        </div>
      </aside>
    </main>
  </div>;
}
export default React.memo(Backend);

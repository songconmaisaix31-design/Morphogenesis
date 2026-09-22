// Finals dashboard shell. Composition adapted from tdesign-react-starter (MIT,
// fce97863): AppLayout top-layout (Layout.Header + Layout.Content) and
// Dashboard/Base TopPanel (Row/Col of Board cards). All login/Redux/routes and
// demo statistics removed. Elements with ids are data zones owned by
// viz/static/app.js; this static tree renders once and never re-renders.
import React from 'react';
import { Layout, Card, Row, Col } from 'tdesign-react';
import Board from './components/Board';

const { Header, Content, Footer } = Layout;

const FinalsHeader = () => (
  <Header className='morph-header'>
    <div className='morph-brand'>
      <span className='morph-brand-name'>MORPHOGENESIS</span>
      <span className='morph-brand-sub'>决赛彩排 · 恢复路径</span>
    </div>
    <div className='morph-header-facts'>
      <span className='morph-header-fact'>在线成员 <b id='header-members'>未知</b></span>
      <span className='morph-header-fact'>任务轮次 <b id='header-round'>未知</b></span>
      <span id='rehearsal-mode' className='morph-header-mode'>等待彩排快照；不预设结果。</span>
      <span id='provenance' className='morph-badge'>加载中</span>
    </div>
  </Header>
);

const TopologyPanel = () => (
  <Card className='morph-panel morph-topology' bordered={false}
    title={<span className='morph-panel-title'>选路拓扑 · 真实权重</span>}
    actions={<span className='morph-panel-side' id='story-offline-member'>未发生 / 未加载</span>}>
    <p className='morph-panel-line'><b id='story-question'>未加载</b><span id='story-question-detail'>等待实际题目、已知失败点与来源。</span></p>
    <p className='morph-panel-line' id='story-offline-reason'>下线原因和恢复 checkpoint 均须来自真实快照。</p>
    <div className='morph-topology-body'>
      <div className='morph-topology-chart'>
        <div id='story-pipe-chart' className='story-pipe-chart'></div>
        <div id='story-pipe-empty' className='empty pipe-empty' hidden></div>
      </div>
      <div id='story-pipes' className='pipe-list'><p>尚无管道快照</p></div>
    </div>
  </Card>
);

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

const App = () => (
  <Layout className='morph-layout'>
    <FinalsHeader />
    <Content className='morph-content'>
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
        <TopologyPanel />
        <div className='morph-rail'>
          <EventPanel />
        </div>
      </div>
      <AcceptanceStrip />
      <GeneLedger />
      <SecondaryPanel />
    </Content>
    <Footer className='morph-footer'>
      <span>布局外壳适配自 Tencent tdesign-react-starter（MIT，fce97863）· Apache ECharts 本地锁定版本 · 数据只读来自 /api/dashboard</span>
    </Footer>
  </Layout>
);

export default React.memo(App);

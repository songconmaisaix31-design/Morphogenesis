# 产品后台布局（B 轨）

基于 `ab87ba17625bf27afdaa840e898d48bb5db0003b`。本轨只改 `viz/frontend/src/backend/**`。用户给的 `linear-site.zip` 只用于观察深色顶栏、左导航、中内容与右上下文的比例和信息层级；没有复制其代码、素材、字体或文案。

`Backend` 默认导出，签名为 `Backend({dashboard, active, reducedMotion, evomap, evomapDetail, onSearch, onOpenAsset, onReturn})`。S 轨继续拥有同源 `/api/dashboard` 轮询、`window.MorphDashboard.update/fail`、EvoMap 只读请求、路由及阶段切换。本组件不发网络请求。`active` 传给实际 `SwarmTopology` 以暂停隐藏视图；`onReturn` 回序幕。左侧导航只在当前页面滚动，不改 hash 路由。

原 App 的数据区和全部旧 DOM ID 迁入本组件，包括顶部在线成员、轮次、来源与连接状态，以及 checkpoint、tokens、Gene、拓扑、事件、验收三态、来源、消息、谱系、指标、运行说明。`document.body.dataset.swarmModule` 仍由拓扑组件设置为 `loaded` 或 `fallback`，供旧图表桥接识别。EvoMapPanel 继续独立展示，只读结果不进入运行拓扑。

布局在宽屏分为 206px 左导航、中间数据区、286px 右上下文；小于 1200px 时右侧上下文下移；小于 768px 时导航横排且内容单列。所有实际状态只由原数据桥写入，无快照保持未知或空态。

## 验证

- 原 `App.jsx` 与新 `Backend.jsx` 中 `id='…'` 集合对比：全部原 ID 均保留，新增四个章节定位 ID。
- `node -e "require('esbuild').buildSync({entryPoints:['src/backend/Backend.jsx'],outfile:'NUL',bundle:true,platform:'browser',external:['react','tdesign-react','../components/*'],loader:{'.css':'empty'}})"`：通过，校验独立 JSX 入口。
- `npm run build`：通过，但当前 App 基线尚未接入本组件；集成后的完整视觉与行为验收由 I 轨完成。构建生成的 `viz/static/assets/finals-shell.*` 已还原，未纳入 B 轨提交。

当前证据是本地组件与构建检查；未声称后台已接入 7799，也未触发新真跑或付费请求。

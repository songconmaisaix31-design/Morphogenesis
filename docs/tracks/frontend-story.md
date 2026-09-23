# S 轨：序幕编排与只读后台接线

基线 `ab87ba17625bf27afdaa840e898d48bb5db0003b`。布局参考用户提供的 `christmas-site.zip` 本地截图，只取黑底、大字和留白节奏；未复制素材或代码。中文产品名按计划暂定为「形态发生」。

`#/physarum` 首先显示原生黄色 Physarum 场及渐显的「黏菌 / PHYSARUM」。3.2 秒后切到 G 轨概念拓扑和其自有「自生长 / AGENT SWARM」标签；7.6 秒显示双语产品名，9 秒显示「进入产品后台」按钮。页面隐藏时序幕计时暂停；减弱动态效果时直接显示最后一幕及按钮。动画不会自动进入后台。只有按钮、`#/workspace` 深链或旧 `#/swarm` 链接进入后台；旧键盘 `2` / 右箭头捷径已移除，按钮可用 Tab / Enter / Space 操作。

集成截图复核：按钮进入可点击阶段时立即显示完整黄字与边框；产品名仍缓慢浮现。原 1.5 秒按钮透明度渐显会令刚出现时难读，已取消。按钮常态黄字 `#f5d547` 对 `#070809` 背景的计算对比度约 13.83:1；hover 背景和键盘焦点描边保留。

S 轨保留同源 `/api/dashboard` 轮询和 `window.MorphDashboard.update/fail` 桥，后台隐藏时不重绘拓扑；`/api/evomap` 仅首次进入后台及主动搜索时读，详情仅点击后读，序列保护维持。B 轨 `Backend` 独占旧数据 DOM ID 和 EvoMap 面板；G 轨 `GrowthIntro` 只做概念动画，不从快照构造假节点。所有数据来源、三态验收和错误空态由原桥及 B 轨继续呈现。

前端两个邻轨的固定接口：`GrowthIntro({active,reducedMotion})` 默认导出自 `src/intro/GrowthIntro.jsx`；`Backend({dashboard,active,reducedMotion,evomap,evomapDetail,onSearch,onOpenAsset,onReturn})` 默认导出自 `src/backend/Backend.jsx`。S 轨未修改这两个目录。黄色 Physarum 仍使用已有 `PhysarumField`，无鼠标或触屏输入。

本轨验证需在 G/B 精确合并后补齐完整 Vite 构建与浏览器截图；本轨未执行真实任务、Hub 写入或付费请求。浏览器展示若使用本地 mock，只证明布局与交互。

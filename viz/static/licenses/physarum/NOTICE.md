# Physarum 组件第三方来源声明（P 轨）

## 主要来源：Bewelge/Physarum-WebGL

- 仓库：https://github.com/Bewelge/Physarum-WebGL
- 版本：commit `e621c3ecb60c5c8a4d1b3446c7b389b083ea1908`（2022-09-12，仓库 master 最新提交，本机只读克隆核对）
- 许可证：MIT，Copyright (c) 2021-2022 Benjamin Welge。全文见同目录 `Physarum-WebGL.LICENSE.MIT.txt`（逐字节复制自上游 `LICENSE.txt`）。
- 核验方式：GitHub API `license.spdx_id = MIT`；仓库 `LICENSE.txt` 与 SPDX MIT 模板一致。

实际复用（改写适配，非原样拷贝；MIT 允许修改，署名保留）：

| 上游文件 | 本项目落点 | 适配内容 |
|---|---|---|
| `src/js/Shaders/UpdateDotsFragment.js` | `viz/frontend/src/physarum/shaders.js` `UPDATE_AGENTS_FRAGMENT` | GLSL ES 1.00 → 3.00；保留三物种传感器转向（分支）、占位位移（聚合）；鼠标排斥替换为趋食转向 + 核心减速 + 平滑强度 uniform |
| `src/js/Shaders/DiffuseDecayFragment.js` | `shaders.js` `DIFFUSE_DECAY_FRAGMENT` | GLSL ES 3.00 端口，拖尾扩散/衰减逻辑不变（上游注明其自身适配自 nicoptere/physarum） |
| `src/js/Shaders/RenderDots{Vertex,Fragment}.js` | `shaders.js` `RENDER_POINTS_*` | 顶点拉取位置纹理绘制点精灵，结构不变 |
| `src/js/Shaders/FinalRenderFragment.js` | `shaders.js` `DISPLAY_FRAGMENT` | 物种通道→主题色映射；改为固定 `#070b0d` 背景合成，去掉 GUI 相关 uniform |
| `src/js/physarumRender.js` 渲染管线 | `simulation.js` `PhysarumSim._step` | update → points → diffuse/decay → display 四段管线保留 |
| `src/js/PingPongShader.js` / `Shader.js` | `simulation.js` 纹理/FBO 管理 | 乒乓浮点纹理机制用原生 WebGL2 重写（上游注明机制源自 nicoptere/physarum） |
| `src/js/physarumRender.js` `resetPositions()` | `simulation.js` `seedAgents` | 三簇随机初始布局保留，参数确定化 |

**未使用**：上游捆绑的 Three.js（`src/lib/three.module.js`）、lil-gui、postprocessing/Sobel、stats、全部 Kenney.nl 粒子贴图、InfoDialog/GUI 文案。因此不引入 Three.js 依赖（无需新增 npm 包、不动 `package*.json`）。

## 继承来源：nicoptere/physarum

上游 README 明确声明 PingPongShader / Shader 类逻辑与部分着色器逻辑直接适配自 https://github.com/nicoptere/physarum 。该仓库许可证为 **The Unlicense**（公有领域，GitHub API `license.spdx_id = Unlicense`，2026-09-23 核验）；本项目仅沿用上游 Bewelge 版本已适配的概念与结构，未直接复制 nicoptere 仓库代码，无额外署名义务，此处仅作来源记录。

## 参考但不复制

`christmas-site.zip`（视觉参考包）仅用于观察整体氛围；未复制其中任何模型、字体、脚本或文案。

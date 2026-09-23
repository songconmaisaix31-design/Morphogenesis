# P 轨报告：PhysarumField WebGL 黏菌（趋食首页）

## 当前版本：恢复原背景并取消交互（2026-09-23）

依用户最新指令，动态色彩、粒子运动参数、初始种子、扩散/衰减合成与静态降级外观恢复到 `f5448b8f59ce7a592fc0bf38de002a47b333672d`。后续黄色前缘/脉络提交保留在历史中，本次用新提交回退视觉。下方原始“鼠标趋食”描述是当时的历史交付记录，**不适用于当前运行版本**。

当前 `PhysarumField({active, reducedMotion, onError})` 仅播放环境动画；组件不监听 pointermove/pointerdown/pointerleave/pointercancel，移除光标环，着色器不再包含 food uniform、趋食转向、食物核心减速或投喂占位例外。鼠标与触屏动作均不会设置模拟目标。`active`/页面隐藏暂停、性能降质、WebGL 不可用降级、reduced motion 和卸载清理仍沿用原接口。

隔离 Chromium 1366×768 验证：空闲及移动、按下、拖动鼠标后 `foodStrength=0`、`food=(0,0)`、无光标环、无 WebGL 错误；画面仍按自身 RAF 自然演化，截图见未入库 `.runtime/physarum/ambient-{idle,after-pointer}.png`。减少动态效果显示原青绿静态图且无 canvas，见 `ambient-reduced.png`。组件打包与隔离目录 Vite 构建结果见下方追加验收记录。页面壳集成后的最终视觉仍由集成轨复核。

2026-09-23（Asia/Shanghai） · 实现者：Kimi（P 轨）· 分支 `songconmaisaix31-design/morph-front-physarum` · 基线 972d4ba（origin/codex/morphogenesis-mainline）

交付 `PhysarumField({active, reducedMotion, onError})`（默认导出，`viz/frontend/src/physarum/index.js`）：原生 WebGL2 三物种黏菌模拟，保留上游的分支（传感器转向）、聚合（占位位移 + 核心减速堆积）、拖尾（扩散/衰减乒乓纹理），新增无需按键的鼠标趋食、核心减速、离开平滑恢复、精确坐标映射、卸载清理、隐藏/失活暂停与 WebGL/低性能/触屏/reduced-motion 降级。**零新增 npm 依赖**，未触碰共享 `package*.json` / `App.jsx` / `theme.css` / `vite.config.js`。

## 来源核验

| 项 | 值 |
|---|---|
| 上游 | https://github.com/Bewelge/Physarum-WebGL |
| 版本 | commit `e621c3ecb60c5c8a4d1b3446c7b389b083ea1908`（2022-09-12，master 最新；本机只读克隆 `/tmp/physarum-ref` 核对） |
| 许可证 | MIT（GitHub API `license.spdx_id=MIT` + 仓库 `LICENSE.txt` 全文比对），Copyright (c) 2021-2022 Benjamin Welge |
| 继承来源 | 上游 README 声明 PingPongShader/Shader/部分着色器适配自 nicoptere/physarum；该仓库为 **The Unlicense**（GitHub API 核验），无额外署名义务，仅作来源记录 |
| 参考包 | `christmas-site.zip`（已在 `C:/Users/DW/WorkBuddy/2026-09-23-01-19-38/christmas-site/`）仅只读观察：three.js r164 粒子站点、黑底、固定 canvas、大标题叠层；未复制任何模型/字体/脚本/文案 |

署名落地：MIT 全文逐字节复制到 `viz/static/licenses/physarum/Physarum-WebGL.LICENSE.MIT.txt`；来源/版本/复用映射/未使用部分见同目录 `NOTICE.md`；`shaders.js` / `simulation.js` 文件头保留版权与出处注释。

复用方式：着色器逻辑（UpdateDots → `UPDATE_AGENTS_FRAGMENT`、DiffuseDecay、RenderDots、FinalRender）与四段渲染管线为**改写适配**（GLSL ES 1.00 → 3.00，Three.js → 原生 WebGL2），非原样拷贝；上游捆绑的 Three.js/lil-gui/Sobel/Kenney 贴图一律未用，因此无需新增依赖（也未发依赖 Handoff）。

## 组件契约与集成说明（给 S 轨）

- 引入：`import PhysarumField from './physarum'`；props：`active`（false 暂停 RAF 与模拟）、`reducedMotion`（true 直接渲染静态降级，不起 WebGL）、`onError({reason, message})`（纯通知；组件自身已切降级视图）。reason 枚举：`webgl2-unavailable | float-buffer-unavailable | shader-compile | program-link | framebuffer | context-lost | low-performance | init-failure`。
- 容器：组件撑满父元素（`.physarum-field` 100%×100%，min-height 240px，背景 `#070b0d`），父容器需给定高度。
- 叠层：pointermove 监听在 window 上，按实时 `getBoundingClientRect` 判断是否在黏菌视区内；**标题等纯展示叠层不阻断趋食**（实测），链接/按钮/`input`/`[data-physarum-block]` 上方暂停趋食。S 轨若有自定义可点控件，加 `data-physarum-block` 即可。
- 调试句柄：容器 DOM 上挂只读 `__physarum`（isRunning/getFoodStrength/getFood/getAverageFrameMs/getViewSize/getAgentStats/getQuality），供验收脚本断言；卸载即删除。
- 主题色令牌取自计划文档（`#070b0d` / `#65d9c7` / `#e8efed` / `#8ca3a0`），未改 `theme.css`。

## 行为实现要点

- **趋食（无需按键）**：`UPDATE_AGENTS_FRAGMENT` 新增 `foodPos/foodStrength/foodCoreRadius/foodTurn` uniform；pointermove → 转向光标（远强近弱），替换上游的鼠标排斥。`foodTurn=0.9rad`、`foodCoreRadius=56px`。
- **核心减速**：速度乘 `smoothstep(0.2r, 1.4r, dist)`（最低 10%），agent 在光标周围堆积成有面积的微动核心。
- **离开平滑恢复**：`pointerleave`/移出视区/悬停交互控件 → 目标强度归 0，CPU 侧按 `1-exp(-3·dt)` 缓动（约 1.5s 收敛），不会出现跳变。
- **聚合与占位**：保留上游 one-agent-per-pixel 位移；趋食强度 >0.5 且距核心 >2r 时允许堆叠，保证长程收敛（实测 4s 内平均距离 357→103px 并稳定）。
- **准确坐标**：client 坐标经实时 `getBoundingClientRect` 映射到中心原点、y 向上、backing 像素空间；DPR≤2；resize 由 ResizeObserver 防抖重建拖尾/占位纹理（agent 状态保留）。
- **卸载清理**：cancel RAF、移除全部监听、删除 program/texture/FBO/VAO、`WEBGL_lose_context` 丢上下文、移除 canvas。
- **隐藏/失活暂停**：`document.hidden` 或 `active=false` → 停 RAF；恢复后续跑。
- **降级**：WebGL2/`EXT_color_buffer_float` 缺失、context lost、着色器编译失败 → 静态降级视图 + onError；触屏（`pointer: coarse`）起始即降质（128²=16k 粒子、DPR≤1，光标环隐藏，点按/拖动短暂投喂后平滑恢复）；连续 3×2.5s 平均帧时 >28ms → 降质一档，再持续 → 静态降级 + `low-performance`。降级视图为确定性 SVG 网络 + 中文原因标注（`PhysarumFallback.jsx`）。
- **过曝修正**（按协调者反馈）：白色物种亮度降至 50%、dotOpacity 0.35→0.2、tonemap `col/(1+0.8col)`、初始种子簇摊散（半径 30~170px）；复核截图无纯白团。

物种参数确定化（上游每页随机）：speed [1.7,2.1,1.4]、sensorDist [6,9,4.5]、rot [0.5,0.65,0.4]、sensorAng [0.5,0.7,0.45]、吸引矩阵对角 1.0 / 非对角 -0.15、decay 0.95。

## 验证（全部真实执行，证据在 `.runtime/physarum/`）

环境：Windows + Chromium 151（`ms-playwright/chromium-1234`）经 Playwright 驱动，vite dev（5199）挂临时 harness（已删，未入库）。

```
PLAYWRIGHT_PATH=... CHROMIUM_PATH=... node .runtime/physarum/check_physarum.cjs <harness-url> .runtime/physarum
node .runtime/physarum/check_physarum_deep.cjs / check_physarum_final.cjs / check_overlay.cjs / check_physarum_slow.cjs 同上
cd viz/frontend && npx esbuild src/physarum/__dev__.jsx --bundle   # 通过（编译检查）
cd viz/frontend && npx vite build --outDir <临时目录> --emptyOutDir # 3892 modules，通过，不触碰 viz/static
```

实测结果：

| 场景 | 结果 |
|---|---|
| 正常启动（1280×800, ANGLE GPU） | RAF 运行，平均帧时 **9.1ms**；初始 foodStrength=0 |
| 趋食聚拢 | 定点悬停后平均食物距离 357→103px（4s 收敛并稳定）；截图 `aggregated.png` 可见核心堆积 |
| 坐标精度 | 中心点与偏心点（1000,200）映射值与期望**逐像素一致**；DPR=2 下 backing 2560×1600 映射仍一致 |
| 离开恢复 | pointerleave 后强度 0.97→0 平滑衰减（0.39/0.15/0.06/0.02/…，约 2s） |
| 叠层（按协调者要求实测） | 标题叠层下强度 0.96（继续趋食）；按钮上 0.02（暂停）；移回 0.95（恢复） |
| 隐藏暂停 | visibilitychange 接线实测 running true→false→true（见局限 1） |
| active=false | running=false，RAF 停止 |
| 卸载 | canvas 移除、根节点清空、0 报错 |
| 无 WebGL | `--disable-webgl` → onError `webgl2-unavailable` + 静态降级 + 中文标注 |
| reducedMotion | 无 canvas、无 RAF，静态视图 + “已按减少动态效果设置显示静态视图” |
| 低性能 | SwiftShader 软渲 1600×1000：91ms/帧 → ~6s 降质（256²→128², DPR 1）→ 仍 ~32ms → ~14s 静态降级，onError `low-performance` |
| 触屏 | coarse 命中，起始 quality=1，光标环隐藏；点按投喂后 0.7s 内平滑恢复；拖动期间强度 0.31→0.97 持续投喂，松手恢复 |

截图证据：`attract.png`（趋食中流纹）、`aggregated.png`（核心堆积）、`recovered.png`、`fallback-nowebgl.png`、`fallback-reduced-motion.png`；数据：`results*.json`。

## 局限与遗留

1. 隐藏暂停：headless Chromium 无法真实切 tab（`Page.setWebLifecycleState` 已废弃，headed 双 tab 在此环境不改变 visibilityState）；已用页面内覆写 `document.hidden` + 派发 `visibilitychange` 验证组件接线（true→停→恢复），真实浏览器原生事件走同一处理器。最终集成验收可在人工浏览器补一刀。
2. 低性能阈值（28ms、3×2.5s）仅在 SwiftShader 软渲下验证；真实低端 GPU 未测。
3. 触屏为 Playwright 模拟（tap/drag 合成事件），未上真机。
4. 官方示例在 2560×1363 仅约 1 FPS（协调者实测）；本实现同分辨率上限受 DPR≤2 + 粒子网格上限约束，并有自动降质兜底。
5. 页面接线（App/shell 引入、CRT 叠层、视图切换）属 S 轨；本轨组件不依赖其完成即可独立运行。

## 变更文件

`viz/frontend/src/physarum/{index.js, PhysarumField.jsx, PhysarumFallback.jsx, simulation.js, shaders.js, physarum.css}`（新增）、`viz/static/licenses/physarum/{Physarum-WebGL.LICENSE.MIT.txt, NOTICE.md}`（新增）、本文档。共享文件零改动（`git status` 仅新增上述路径；`npm ci` 未改锁文件）。
追加构建结果：`npx esbuild src/physarum/PhysarumField.jsx --bundle --outfile=../../.runtime/physarum/ambient-check.js --loader:.js=jsx` 通过；`npx vite build --outDir ../../.runtime/physarum/ambient-build --emptyOutDir` 通过（3892 modules，33.81s，未写共享静态构建产物）。

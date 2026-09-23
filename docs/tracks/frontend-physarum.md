# P 轨报告：PhysarumField WebGL 黏菌（趋食首页）

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

## 2026-09-23 黄色黏菌视觉返修（覆盖上文旧聚拢参数）

用户反馈原“聚拢”像光标处堆积的粒子。旧 `foodTurn=0.9`、核心减速至 10%、远处允许占位重叠，加上三物种分离配色，确实会产生中心点团及放射状拖尾。现改为单一黄色菌体的可视表现：低幅趋食偏转（`foodTurn=0.085`）、不在食物核心刹停、不为趋食放开占位；WebGL 合成层显示连通的后部主脉与分叉/汇合支脉，以及由窄变宽、有不规则边缘的前部扇形薄片。前缘以约 1.25/s 的缓动跟随食物坐标，后部保持连接；脉管宽度与亮度缓慢起伏，薄片含局部纹理和亮边。光标环、WebGL 颜色、静态降级均改为黄色系，背景仍遵守共享 `#070b0d`。

形态与运动依据：实验记录黏菌后部的管状网络与前方生长扇形区域（[eLife 2022](https://elifesciences.org/articles/69745)）；体内往返流与后向前传播的蠕动收缩有关（[研究论文](https://pmc.ncbi.nlm.nih.gov/articles/PMC2267142/)）；扇形前缘与后部脉络在细胞骨架研究中分别观察到（[研究论文](https://pmc.ncbi.nlm.nih.gov/articles/PMC4594612/)）。页面是受其形态启发的实时图形模拟，不宣称真实细胞流体模型或真实运动速度。PBS/NOVA 生长前缘照片仅作视觉核对（[图像](https://www.pbs.org/wgbh/nova/media/images/Physarum_growth_front.width-990_ju4eSk5.jpg)），没有复制图像素材。

本轮隔离测试：`npx esbuild src/physarum/PhysarumField.jsx --bundle --outfile=../../.runtime/physarum/refine-check.js --loader:.js=jsx` 通过；`npx vite build --outDir ../../.runtime/physarum/refine-build --emptyOutDir` 通过（3892 modules，53.30s，不写共享构建产物）。Chromium 1234，1280×800，独立 Vite harness：空闲及向 (1100,190) 悬停 5s 的截图见未入库 `.runtime/physarum/refine-{initial,feeding}.png`；实际观测为黄色连通的脉络/扇形前缘，前缘随光标显著前移，平均帧约 10–14ms，无组件 WebGL 错误。`check_physarum_final.cjs` 的卸载清理、DPR=2 坐标映射、触屏质量检查通过。此截图没有页面标题叠层，不等于最终集成页在 7799 的验收；需集成轨在真实页面检查布局与遮挡。GPU 中的粒子路径仍是简化启发式，前缘/脉络由实时 WebGL 合成层呈现，非对真实黏菌的物理求解。
追加降级检查：Chromium `?reduce` 无 canvas、有黄色 SVG 静态图；`--disable-webgl` 报 `webgl2-unavailable` 并进入同一静态图。均通过。

## 集成页目视返修（第二轮）

集成轨在 7799 页面对第一轮 `2a501ad` 做真实 Chromium 目视检查，发现后部是几条平行平滑金色线、前缘像整块半透明叶片，减少动态效果的 SVG 也像被放大的叶片。第二轮把前缘片体亮度降到只作薄膜背景，并用两组交错、弯曲的细脉构成可见网状结构；后部改成七条起点、汇点、宽度和弯曲程度各异的脉络。SVG 静态图改为固定 160×90 视图内的多脉络网络，避免全屏巨型轮廓。

前缘坐标现被限制在视区内的安全范围，收到真正的 `pointerleave` 后立即将默认位置设为目标、平滑回位。集成轨先前标作“回位失败”的截图实际上是鼠标仍位于全屏黏菌区域内，因此它证明的是持续投喂到左上角，不是离开事件失败。本轮仍验证了明确派发 `pointerleave` 后 2.2 秒返回默认位置。

隔离 Chromium 1366×768 截图：`.runtime/physarum/rework-{idle,hover,recovery,reduced}.png`。实测 WebGL 无错误、平均帧约 21.8ms；`npx esbuild src/physarum/PhysarumField.jsx --bundle --outfile=../../.runtime/physarum/rework-check.js --loader:.js=jsx` 通过，临时目录 Vite build 3892 modules 通过；卸载、DPR2 坐标、触屏质量检查通过；减少动态效果和禁用 WebGL 均显示无 canvas 的静态网状视图。最终集成页叠层与真实 7799 仍需集成轨以本次 SHA 复核。

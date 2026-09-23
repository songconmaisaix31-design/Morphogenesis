# Third-party sources and licenses

Checked against installed package metadata on 2026-09-22. Exact direct and transitive artifacts are recorded by `poetry.lock` and `package-lock.json`; runtime installation retains their LICENSE / NOTICE files. Project code calls these dependencies and does not copy their implementation. The original project Apache-2.0 LICENSE is unchanged.

| Dependency | Installed version | Declared license | Source / use |
|---|---|---|---|
| @evomap/gep-sdk | 1.14.0 | Apache-2.0 code; CC-BY-4.0 specification | https://github.com/EvoMap/gep-sdk-js — schema and Node asset-id helper calls |
| @evomap/gep-mcp-server | 1.7.0 | Apache-2.0 | https://github.com/EvoMap/gep-mcp-server — stdio MCP server, no source copied |
| ajv / ajv-formats | 8.20.0 / 3.0.1 | MIT | https://github.com/ajv-validator/ajv — official JSON schema validation |
| ECharts | 6.1.0 | Apache-2.0 | https://github.com/apache/echarts — installed visualization dependency |
| Pydantic | 2.13.5 | MIT | https://github.com/pydantic/pydantic — business data validation |
| SQLModel / SQLAlchemy | 0.0.45 / 2.0.54 | MIT | https://github.com/fastapi/sqlmodel / https://github.com/sqlalchemy/sqlalchemy — SQLite metadata |
| LangGraph / sqlite saver | 1.2.12 / 3.1.1 | MIT | https://github.com/langchain-ai/langgraph — graph orchestration and native checkpoint storage |
| httpx | 0.28.1 | BSD-3-Clause | https://github.com/encode/httpx — HTTP transport |
| mcp (Python) | 1.30.0 | MIT | https://github.com/modelcontextprotocol/python-sdk — standard MCP client |
| faiss-cpu | 1.15.1 | MIT | https://github.com/facebookresearch/faiss / https://github.com/kyamagu/faiss-wheels — native vector index dependency |
| numpy | 2.5.3 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | https://github.com/numpy/numpy — numeric arrays; retain wheel bundled-library notices |
| scikit-learn | 1.9.1 | BSD-3-Clause | https://github.com/scikit-learn/scikit-learn — offline HashingVectorizer requested by metabolism; no model download |
| pytest / mypy / build | 9.1.1 / 1.20.2 / 1.6.1 | MIT | https://github.com/pytest-dev/pytest / https://github.com/python/mypy / https://github.com/pypa/build — development checks |
| tdesign-react-starter | 0.3.1（commit `fce97863edd5d5556f766dd4e342aace31a99487`） | MIT | https://github.com/Tencent/tdesign-react-starter — 决赛展示层外壳实际复用：Board 卡片、Dashboard/Base TopPanel 组合、AppLayout 顶栏布局（源码映射见 `viz/static/licenses/NOTICE.txt` 与 `docs/tracks/frontend-stack.md`）；完整 MIT 文本在 `viz/static/licenses/` |
| React / ReactDOM / scheduler | 18.3.1 / 18.3.1 / 0.23.2（`viz/frontend/package-lock.json`） | MIT | https://github.com/facebook/react — 外壳运行时，打包进 `viz/static/assets/finals-shell.js`；许可文本在 `viz/static/licenses/` |
| tdesign-react / tdesign-icons-react / classnames / dayjs / lodash-es | 1.18.3 / 0.6.11 / 2.5.1 / 1.11.10 / 4.18.1（`viz/frontend/package-lock.json`） | MIT | https://github.com/Tencent/tdesign-react 等 — 实际打入 finals-shell 的组件库与运行时依赖（lodash-es 经 I 审计 bundle 模块确认）；许可文本在 `viz/static/licenses/`；无 CDN |
| Vite / @vitejs/plugin-react / less | 5.4.x / 4.3.x / 4.x（`viz/frontend/package-lock.json`） | MIT | https://github.com/vitejs/vite — 仅构建期工具，产物为静态本地文件 |

2026-09-23 起展示层改为上述 TDesign 适配；此前 Hugo Theme Stack（GPL-3.0-only）/ Tabler Icons / hamburgers 适配已整体移除，无残留代码，其许可文本随代码一并删除（见 git 历史）。

Evolver is not installed, linked, or copied. Current npm metadata was checked separately by the coordinator: `@evomap/evolver` 2.0.38 is GPL-3.0-or-later. Its implementation is not needed for this foundation.

SDK API was verified against the installed exports and an actual local call: `SCHEMA_VERSION`, `canonicalize`, `computeAssetId`, `verifyAssetId`, plus `schemas/gene.schema.json`. These functions do not implement publish/fetch or algorithmic evolution. `tools/check_sdk.cjs` exercises schema validation, an official ID roundtrip and tamper rejection. MCP 1.7.0 exposes `gep_evolve`, `gep_recall`, `gep_export` over stdio; Python transport belongs to the bridge track. Hub calls are a separate httpx adapter. Neither package's installation establishes Hub or model acceptance.

The following NOTICE texts are retained verbatim from the installed npm distributions.

## @evomap/gep-sdk 1.14.0 NOTICE

```text
@evomap/gep-sdk
Copyright 2024-2026 EvoMap

This product includes software developed by EvoMap (https://evomap.ai).

The Genome Evolution Protocol (GEP) is a protocol specification authored
and maintained by EvoMap. The protocol's human-readable specification
(./spec/gep-spec-v1.md and any docs under ./docs/) is licensed under
Creative Commons Attribution 4.0 International (CC-BY-4.0); see
spec/LICENSE-CC-BY-4.0.txt for the full text. All other files in this
package are licensed under the Apache License, Version 2.0 (see ./LICENSE).

"EvoMap", "GEP", and "Genome Evolution Protocol" are trademarks of EvoMap.
The Apache 2.0 License does not grant permission to use these trademarks;
see Section 6 of the License. Implementations of the protocol are welcome
and encouraged, but must not be marketed under the EvoMap, GEP, or Genome
Evolution Protocol names without prior written permission.
```

## @evomap/gep-mcp-server 1.7.0 NOTICE

```text
@evomap/gep-mcp-server
Copyright 2024-2026 EvoMap

This product includes software developed by EvoMap (https://evomap.ai).

The Genome Evolution Protocol (GEP) is a protocol specification authored
and maintained by EvoMap. This package implements an MCP (Model Context
Protocol) server that exposes GEP evolution capabilities to MCP-compatible
AI agents. It depends on `@evomap/gep-sdk`, which carries the canonical
schemas, specification (CC-BY-4.0), and asset-id helpers (Apache-2.0).

The source code in this repository is licensed under the Apache License,
Version 2.0 (see ./LICENSE). External contributions are accepted under the
EvoMap Individual / Corporate CLA — see ./CLA/ and ./CONTRIBUTING.md.

Pre-1.6 history: versions 1.0.x – 1.5.x of `@evomap/gep-mcp-server` were
published under GPL-3.0-or-later. Versions 1.6.0 and later are Apache-2.0.
Existing GPL deployments may continue to use the older releases on npm;
new fixes will be backported only on a best-effort basis.

"EvoMap", "GEP", and "Genome Evolution Protocol" are trademarks of EvoMap.
The Apache 2.0 License does not grant permission to use these trademarks;
see Section 6 of the License. Implementations of the protocol are welcome
and encouraged, but must not be marketed under the EvoMap, GEP, or Genome
Evolution Protocol names without prior written permission.
```

## User-provided design snapshots (2026-09-23)

The user explicitly authorized direct reuse of the supplied `christmas-site.zip`
and `linear-site.zip` for this project. These are user-provided website snapshots,
not verified open-source templates. Snapshot source version and redistribution
license were not included/verified; no MIT or Apache license is asserted for these
assets or adapted declarations. Existing third-party notices above remain intact.

| Snapshot / original relative path | Product target | Reuse and changes |
| --- | --- | --- |
| christmas-site / `assets/index-b8e6792d.css` (`.section`, odd section alignment) | `viz/frontend/src/reference.css` | Actual black stage, `100dvh`, 10% horizontal padding, `#ffeded`, Jost and `6vmin` declarations; scroll chapters become timed scenes, bilingual title weight/line-height adapted, alternating left/right text alignment retained. |
| christmas-site / `_ext/fonts.googleapis.com/css2_ed0de8.css` and `_ext/fonts.gstatic.com/s/jost/v20/92zatBhPNqw73oTd4g.woff2` | `viz/frontend/src/reference.css`, `viz/static/fonts/Jost-latin.woff2` | Local Latin Jost font copied byte-for-byte, local `@font-face`; original CSS said `Jost Medium` while supplied face is `Jost`, so family name corrected. Chinese uses the installed CJK sans fallback. URL path says v20; actual upstream release/license unknown from this snapshot. |
| linear-site / `assets/css/layout.B05Dfi6O_cf0c9cb7.css` and `assets/font/InterVariable_36a96895.woff2` | `viz/frontend/src/reference.css`, `viz/static/fonts/InterVariable.woff2` | Local variable font copied byte-for-byte; 100-900 face declaration, actual dark surface/text/border variables and 400/510/590/680 weights reused. No remote font fetch. |
| linear-site / `assets/css/HeroIllustration.CR-IZ0h7_16ec15e1.css` (`WS84WW`, `Mmx1Wq`, `_5YOmVq`) | `viz/frontend/src/backend/backend.css`, `Backend.jsx` | 232px sidebar, 28px navigation, 8px row radius, 720px centered document, 32px icon, 24px metadata, neutral translucent borders/backgrounds and sidebar/document/context structure adapted to real Morphogenesis regions. Mobile wraps controls instead of shrinking a marketing illustration to half size. |
| linear-site / `assets/css/IssueListView.BH55qTC9_ccd67967.css`, `Button.dcAi4KbO_f1b9ab6e.css` | `viz/frontend/src/backend/backend.css` | Compact row/control alignment, small control type, hover backgrounds and 0.16s transitions; native buttons keep actual section navigation and read-only search actions. |

Generated `viz/static/assets/finals-shell.css` and `.js` include these adaptations.
Brand names/copy, original site JS bundles, GTM/trackers, remote marketing requests,
images, Christmas models and the offline reveal hacks are not product imports.
Font-specific licenses have not been independently established from the supplied
files; the user's reuse authorization is recorded without relabeling ownership.

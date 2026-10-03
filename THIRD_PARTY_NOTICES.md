# Third-party sources and licenses

## 2026-10-03 R1 frozen export control transport

`docker==7.2.0` (official Docker SDK for Python), source
[`5ad5327fba623897ee9a527d7eee1b01703e0726`](https://github.com/docker/docker-py/tree/5ad5327fba623897ee9a527d7eee1b01703e0726),
is Apache-2.0. The original session uses its Unix/npipe HTTP adapters with the
existing requests transport for bounded, read-only Engine stat/archive calls;
no implementation is copied. Its Windows dependency pywin32>=304 is satisfied
by the existing locked pywin32 312 (PSF license); installed packages retain
their license files. This dependency does not start Docker or authorize a
sandbox/probe. OpenSandbox SDK/server/image versions remain unchanged.

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
| linear-site / `assets/css/HeroIllustration.CR-IZ0h7_16ec15e1.css`, `assets/js/HeroIllustration-DvABf-oD_13f56681.js`, application subtree in `index.html` | `viz/frontend/src/backend/linear-package.css`, `Backend.jsx`, `backend.css` | Selected root CSS rules copied with original selectors: `WS84WW` frame/view, `Mmx1Wq` sidebar, `KFZpfa` issue body/properties/activity/commentCard. Actual frame > sidebar + view > locationBar > viewBody > content/properties DOM organization and grouped interactive navigation adapted to React and real Morphogenesis data. Marketing scale and crop removed; narrow screens scroll navigation and stack properties. |
| linear-site / `assets/css/IssueListView.BH55qTC9_ccd67967.css`, `assets/js/IssueListView-JMvnarPW_152e5db9.js`; `assets/css/Button.dcAi4KbO_f1b9ab6e.css`, `assets/js/Button-C0yyrcbs_a4b21226.js` | `viz/frontend/src/backend/linear-package.css`, `Backend.jsx`, `backend.css` | `_1uFtza` 44px content location bar/view bar, breadcrumb, pill/button controls copied; native button organization retained with working tabs, search, details, and return actions. Source illustration `tabIndex=-1` changed for keyboard access. |
| linear-site / `assets/css/scenarios.bL-CLJt9_84939a09.css`, `assets/js/scenarios-DRvFe3vm_62acb04f.js` | `viz/frontend/src/backend/linear-package.css`, `Backend.jsx` | `GkoSzG_panel` layered surface and `NN4GVa` identity/header CSS and DOM adapted to an explicitly opened read-only run-details panel. Source model labels, chat text, composer, and simulated interactions not imported. |
| linear-site / `index.html` application SVGs and inline `BarChart` symbol | `viz/frontend/src/backend/LinearIcons.jsx` | Eleven SVG geometries extracted for search, activity, inbox, target, topology, Gene, more, status, task, metrics, and chevron. Static React SVG elements with original paths/viewBox; external sprite references resolved locally, source brand logo excluded. |

Generated `viz/static/assets/finals-shell.css` and `.js` include these adaptations.
Source brand names/copy, complete original site runtime bundles, GTM/trackers,
remote marketing requests, images, Christmas models and offline reveal hacks
are not product imports; the component structure and SVG geometry above are adaptations.
Font-specific licenses have not been independently established from the supplied
files; the user's reuse authorization is recorded without relabeling ownership.
# 2026-09-30 native research integration sources

This section records actual runtime adapters and the A/C interface handoffs. It does not replace the historical notices below. No scheduler, Attempt lifecycle, manifest, hashing implementation or completion proof is copied or rebuilt.

| Source | Version / immutable reference | License and use |
|---|---|---|
| Official MCP Python SDK | B's local interpreter 1.28.1; project constraint `mcp>=1.20,<2`, exact deployment version from C's lock | MIT; `mcp.server.fastmcp.FastMCP` stdio server and official SDK client tests, no implementation copied. [v1 source](https://github.com/modelcontextprotocol/python-sdk/blob/v1.x/README.md) |
| stablyai/orca | `85f8d6b5f507df795cd3cef1cdea08124cf801ee` | A source audit: MIT, Copyright 2026 Lovecast Inc.; native launch/session/config behavioral reference. Product has no Orca service/runtime dependency. [source](https://github.com/stablyai/orca/tree/85f8d6b5f507df795cd3cef1cdea08124cf801ee) |
| Codex CLI | npm 0.159.0, A native probes | Apache-2.0; invoke original CLI with its native authentication, no copied HOME or credentials. [source](https://github.com/openai/codex) |
| Claude Code CLI | npm 2.1.238, A native probes | Proprietary Anthropic terms; invoke installed native CLI, no SDK or open-source license claim. [official documentation](https://code.claude.com/docs/en/overview) |
| OpenSandbox SDK / Code Interpreter / service | 1.1.0; release-1.1.0 commit `b1a29cf93a823a95913f7943010febb3f29de05c` (annotated tag object `836b182e208e66c046026fa0f633e089321f1efb`); initial source study `089b59ad48af33fc2733de58bd1a39c687c93b0a` | Apache-2.0; C calls official SDK and deploys official service/image; local configuration adaptations retain source attribution. B calls C's sole contracts and trusted archive reader. [release source](https://github.com/opensandbox-group/OpenSandbox/tree/b1a29cf93a823a95913f7943010febb3f29de05c) |
| nbclient / nbformat | 0.10.4 / 5.10.4, C lock | BSD-3-Clause; C uses NotebookClient and official notebook format, no new kernel executor. [nbclient](https://github.com/jupyter/nbclient), [nbformat](https://github.com/jupyter/nbformat) |
| CPython statistics | 3.12.13 in C's pinned CPU image | PSF-2.0; invoke `statistics.variance`, no implementation copied. [official API](https://docs.python.org/3.12/library/statistics.html#statistics.variance) |
| NIST StRD NumAcc4 | Public 1001-observation constructed dataset; original file SHA256 `ca310dc767f5130f980f8280bbe69e26ba414a4d85a89fc11b6c767b828e5fe4` | Public NIST scientific reference data; preserve [NIST data licensing statements](https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications), no NIST endorsement or invented MIT license. [original data](https://www.itl.nist.gov/div898/strd/univ/data/NumAcc4.dat) |

NumAcc4 cites Simon, Stephen D. and Lesage, James P. (1989), *Assessing the Accuracy of ANOVA Calculations in Statistical Software*, Computational Statistics & Data Analysis 8:325-332. This CPU case tests only declared numerical conditions; it does not establish a general research result. C's source audit and retained SDK/API distinctions are in `docs/experiments/upstream.md` on the integrated branch.

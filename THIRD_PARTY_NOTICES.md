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
| React / ReactDOM | 18.3.x（`viz/frontend/package-lock.json`） | MIT | https://github.com/facebook/react — 外壳运行时，打包进 `viz/static/assets/finals-shell.js` |
| tdesign-react / tdesign-icons-react | 1.15.x / 0.6.x（`viz/frontend/package-lock.json`） | MIT | https://github.com/Tencent/tdesign-react — 外壳组件库与主题变量，随 finals-shell 打包；无 CDN |
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

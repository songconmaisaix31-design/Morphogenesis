# Comparator dependency notices

The adapters use installed official packages; no third-party runtime source or
wheel is bundled in this adapter source folder. The parent delivery should retain
the repository's own license for the new adapter glue.

## AutoGen Core 0.7.5

- Project: Microsoft AutoGen, https://github.com/microsoft/autogen
- Official release: https://pypi.org/project/autogen-core/0.7.5/
- License: MIT; Copyright (c) Microsoft Corporation.
- Exact license text copied from the verified installed wheel:
  `licenses/autogen-core-0.7.5-LICENSE-CODE.txt`.

## LangGraph 1.2.18

- Project: LangChain LangGraph, https://github.com/langchain-ai/langgraph
- Official release: https://pypi.org/project/langgraph/1.2.18/
- License: MIT; Copyright (c) 2024 LangChain, Inc.
- Exact license text copied from the verified installed wheel:
  `licenses/langgraph-1.2.18-LICENSE.txt`.

Transitive dependencies are listed in the install report/environment freeze and
retain their own upstream licenses. If their binaries are redistributed, include
their applicable notices separately; this source-only adapter package does not
redistribute those binaries. No upstream project endorses this benchmark.

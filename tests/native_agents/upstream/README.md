`print-mode-headless-command.ts` is copied byte for byte from
[stablyai/orca at 85f8d6b5f507df795cd3cef1cdea08124cf801ee](https://github.com/stablyai/orca/blob/85f8d6b5f507df795cd3cef1cdea08124cf801ee/src/shared/print-mode-headless-command.ts).
MIT, Copyright (c) 2026 Lovecast Inc.; full license is retained in
`orchestration/native_agents/ORCA_LICENSE.txt`.

`check_print_mode.mjs` is our test-only harness. Node >=22.6's built-in TypeScript
stripping executes the original standalone module without installing Vitest,
Electron or the desktop dependency graph. The Python port is compared with this
original implementation. This is not execution of Orca's full upstream Vitest suite.

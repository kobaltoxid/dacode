---
name: dacode
description: Create or revise concise, source-grounded technical documentation, D2 diagrams, and Vega-Lite charts in a project. Use when a task asks to explain, document, diagram, or chart a software system or its behavior.
---

# DaCode documentation workflow

Use this workflow for documentation work. Run `dacode rules` and follow the canonical writing contract it prints.

1. Identify the target project root and read its applicable `AGENTS.md`, README, and relevant source files. Follow the project's technical facts and terminology.
2. Put every newly created documentation page, diagram source, chart source, rendered diagram, and chart output under the target project's root `docs/` directory. Put D2 files and their SVG and PNG renders in `docs/diagrams/`; put Vega-Lite specifications and related chart data in `docs/charts/`. Create these directories when needed. Keep edits to existing files at their current paths unless the task requests a move.
3. Use `dacode new` to scaffold a page or source. Use one page type that matches the reader's need. Do not retain template sections that do not help.
4. Inspect project code, configuration, tests, and authoritative references before stating facts. Mark unknowns clearly. Never invent dates, behavior, metrics, data, or test results.
5. Write the smallest complete explanation. Keep cause, conditions, sequence, and consequences explicit. Use D2 source for diagrams and Vega-Lite JSON for charts. Keep diagrams visually simple, with one obvious reading path and no unnecessary shapes or arrows. Style them only with the scaffolded role classes, and reserve red for undesired paths. Render both SVG and PNG outputs with `dacode render docs/diagrams`.
6. Run `dacode check docs` and any relevant source-specific checks available in the project. Fix reported issues. If a renderer or check is unavailable, report that limitation without claiming success.
7. Review the result for reader clarity, correct file placement, working links, and accurate source-backed claims. Report changed files and checks actually run.

The `dacode` command does not call a model or publish content. It scaffolds files, assembles portable prompts, renders D2 diagrams, and checks documentation.

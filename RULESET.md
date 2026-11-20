# DaCode Writing Rules

This is the single, canonical writing contract for DaCode. Within higher-priority platform policies, every model and contributor must follow it. Do not silently replace, weaken, or skip a rule. Only a task that explicitly asks to revise this file may change the contract. If the task conflicts with a rule or cannot be completed accurately, stop and explain the conflict.

## Required Workflow

Follow this sequence for every task:

1. Read the task. Identify the reader, the outcome, and the constraints.
2. Inspect the relevant files and authoritative sources. Never invent missing facts.
3. Choose one page type and the closest template. Remove sections that do not help.
4. Draft the smallest complete answer to the reader’s question.
5. Run the final audit below. Fix every failure before reporting completion.
6. Report the files changed and checks actually performed.

When DaCode is used in a target project, create new documentation pages, diagram sources, chart specifications, and generated visuals under the project's root `docs/` directory. Put D2 sources and their rendered SVGs and PNGs in `docs/diagrams/`; put Vega-Lite specifications and related chart data in `docs/charts/`. Create these folders when needed. Keep updates to existing files at their current paths unless the task requests a move.

If an important fact remains unknown, mark it as unknown or ask one focused question. Do not fill the gap with plausible text.

## Prose Rules

- Start with the purpose or outcome. Give the reader the information needed to act or understand.
- Write natural, grammatical sentences. Keep the logic explicit; do not compress words until the reader must infer conditions, causes, order, or consequences.
- Give each paragraph one main idea. Each sentence must add a fact, explain a relationship, or guide an action.
- Keep prose paragraphs to five sentences or fewer and sentences to 36 words or fewer. Split the thought without removing reasoning the reader needs.
- Prefer concrete nouns and verbs. Use active voice and familiar terms. Explain unfamiliar terms once.
- Delete repetition, generic openings and endings, filler transitions, unsupported certainty, marketing language, and decorative headings.
- Use a list only for parallel items or ordered steps. Keep it short. Use a table only for information readers need to compare across rows and columns.
- Put warnings beside the choice or step they affect. Format commands, paths, filenames, and literal values as code.

## Evidence Rules

- Verify factual claims against the project source or an authoritative reference.
- Cite external claims close to where they appear. Separate sourced facts from inference.
- State the version or date when a claim changes over time.
- Do not invent features, outcomes, metrics, dates, users, tests, or plans. Label examples and synthetic data clearly.

## Page Rules

Choose the page type that matches the reader’s need:

- **Concept:** Explain what something is and how it works. Link to a separate procedure.
- **How-to:** Give prerequisites, ordered actions, and an observable success check.
- **Tutorial:** Teach a larger outcome through steps; include cleanup only when the steps create state.
- **Reference:** State exact behavior, fields, options, and verified examples.
- **System design:** State goals and constraints, then explain the components and important flows.
- **Diagram:** Answer one visual question and preserve its key meaning in nearby text.
- **Chart:** State the comparison, measure, coverage, period, and source; keep the chart data editable.

One page answers one main question. Do not keep template sections that add no useful information.

## Diagram Rules

- Use D2 for every system, process, or interaction diagram. Save editable source in a `.d2` file and commit its generated SVG and PNG beside it.
- Render diagrams with `dacode render` and D2 v0.9.0. Do not use Mermaid for diagrams, screenshots, GUI-authored diagrams, or hand-edited generated SVGs.
- Choose the architecture view before drawing. Start with the system and its surroundings or its main deployable parts; add detail only to answer a specific question.
- Put external actors outside labeled system boundaries. Group components by responsibility or data role when the boundary helps the reader understand ownership.
- Show only components supported by requirements or evidence. Give each component a clear responsibility.
- Arrange the main flow in a consistent direction. Label arrows with the interaction or data; include protocol or sync behavior when relevant, and minimize line crossings.
- Style every shape and arrow with the role classes that `dacode new diagram` scaffolds. Do not add one-off colors; a new color must name a new role.
- Use opaque yellow (`owned`) for what the system owns and pale green (`store`) for stored data. Draw external systems with a dashed grey outline (`external`) and people with a solid one (`person`).
- Draw the desired path in forest green (`flow`), replies and optional side effects in dashed grey (`reply`), and only undesired paths or states in red (`fail`, `failed`). A recovery path such as a retry or revision is a reply, not a failure.
- Make roles readable without color: external parties are dashed, stores are cylinders, and failures are dashed and bold. Keep boundaries transparent with a thin grey outline and a small label.
- Draw structural relationships that have no direction, such as ownership or configuration, with `--` and the `link` class.
- Add a `d2-legend` when a diagram uses red or three or more arrow roles. List only the roles the diagram uses, and use the same classes in the legend.
- Show many identical instances as one shape with `style.multiple: true`. Pack many peer items into a container with `grid-columns` instead of a long row.
- In sequence diagrams, wrap each phase in a named group and keep the participant order equal to the order of first contact.
- Do not use `animated`, `sketch`, `shadow`, `opacity`, fill patterns, remote icons, or per-shape font sizes. They add noise, and remote icons make rendering depend on the network.
- Keep one diagram focused on one question. Split crowded diagrams instead of shrinking labels or adding decoration.
- Use the fewest nodes and arrows that preserve the answer. Give the reader one clear reading path; remove decorative shapes, repeated labels, duplicate paths, and details that do not change the takeaway.
- Show a feedback loop with one clear return path and label what triggers it. Review the rendered diagram at normal reading size; simplify it if the flow is not obvious at a glance.
- Label arrows with one to three words, such as `HTTPS`, `valid rows`, or `reject`. Put explanation in the caption, not on the arrow.
- Keep the rendered SVG at most 1,600 pixels wide so its text stays legible in a documentation column. `dacode check` enforces this limit. Keep at most five boxes along the main axis; split a longer chain or change its direction.
- Render every D2 source to both `.svg` and `.png` with `dacode render`; keep both generated files beside the `.d2` source. Use SVG in Markdown and link the PNG as a static preview when useful.
- Introduce each diagram in prose, add a short caption below it, link its `.d2` source, and include text that preserves its key meaning.

## Chart Rules

- Use Vega-Lite for every data chart. Keep the specification and non-trivial source data as editable files.
- State the main comparison in nearby prose. Include the measure, units, coverage, period, and source where relevant.
- Label axes and series. Use honest scales; disclose a truncated axis.
- Keep charts simple and accessible. Avoid 3D, decoration, and color as the only distinction.
- Add concise alt text or a text summary with the chart type and main finding.
- Generate rendered output from source. Never hand-edit generated images or invent data.

## Final Audit

Before reporting completion, answer **yes** to each item:

1. Can the intended reader tell what the page is for from its opening?
2. Does every sentence add useful information, and is the reasoning explicit?
3. Is every factual claim supported, qualified, or clearly marked unknown?
4. Can repeated words, filler, or unused sections be removed?
5. Do diagrams and charts answer one clear question and match their source data?
6. Were syntax, links, and rendering checked where tooling is available?
7. Does the final report say exactly what changed and what was not verified?

If any answer is no, revise. If a check cannot be run, state that limitation; never claim it passed.

## Tool Rules

- This ruleset is model-neutral. Keep it as the only source of writing policy.
- If a tool does not load the DaCode skill, give it the output of `dacode prompt` with the task brief.
- Provider-specific instruction files may point here; do not copy or fork these rules into them.
- Do not use GUI automation to author content or diagrams.
- Do not add dependencies, reformat unrelated files, publish, or modify external services unless the task requires and authorizes it.
- Never commit credentials, private data, or material the project does not have permission to publish.

The reasoning behind these rules is in [docs/approach.md](docs/approach.md).

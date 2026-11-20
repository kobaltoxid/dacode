# Documentation and Diagram Approach

DaCode combines a shared agent workflow with a small CLI for scaffolding and checks. Markdown, D2, and Vega-Lite keep authored content reviewable as text. New pages and visual sources for a target project go under its root `docs/` directory.

## Agent Workflow

The skill is a `SKILL.md` file with supporting scripts and templates. One user-level install gives every agent session the same workflow across projects. Agents without skill support can consume a portable prompt from `dacode prompt`.

## Prose and Page Structure

Use one page for one reader question. Separate concepts, procedures, tutorials, and references because readers use them differently. Keep technical prose accurate, concise, and complete; do not compress away the reasoning a reader needs.

Procedures work best when they give practical steps, exact UI paths or commands, and caveats beside the step they affect.

## Diagrams

D2 is the canonical source for diagrams. Its local CLI renders text files to SVG and PNG with light and dark themes, so an agent needs no external account or token. The project pins D2 v0.9.0 and the ELK layout so reviewed sources render consistently.

Role classes give every color one meaning. Yellow and green fills share one lightness and saturation so they read as one family, and they switch with the viewer's light or dark scheme. Lines and arrows use mid-tones with at least 3:1 contrast on both backgrounds. The [diagram style examples](../examples/diagram-style.md) show each class in an architecture, data flow, sequence, and state diagram.

Choose an architecture view's level of detail before drawing it. Start with the system and the people and systems around it, or with its main deployable parts. Add a component view only when it answers a specific question. Clarify requirements and constraints first, then show major components, data stores, and labeled flows before implementation detail.

Show the system's real boundaries and responsibilities, and group named components inside them. When readers only need to see where a workflow starts and ends, keep intermediate files in the prose. Check every diagram at its embedded size.

DaCode-generated Markdown embeds SVGs and links PNGs as static previews. Other diagram formats are acceptable only when their source is canonical text that can be edited and rendered through code; none is the default.

## Data Charts

Use Vega-Lite for data charts. Its text specifications keep encodings and transformations reviewable. Keep non-trivial data separate from the chart specification, and generate rendered files from those sources. DaCode scaffolds Vega-Lite v6 JSON and checks its basic structure, but leaves chart rendering to the host project.

Chart labels, scale, and surrounding text affect whether a chart communicates accurately. Use clear labels, honest scales, and simple presentation tied to the text around the chart. The [data chart example](../examples/data-chart.md) shows the expected shape.

## Source-Driven Reference Material

When reference content can be generated from structured source, maintain the source and generate the pages instead of copying the same facts by hand. DaCode does not generate API reference pages from project code or schemas; it provides scaffolds and a writing workflow.

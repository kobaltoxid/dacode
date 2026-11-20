#!/usr/bin/env python3
"""Check mechanical writing and structure rules for DaCode Markdown."""

from __future__ import annotations

import re
import sys
from pathlib import Path


FILLER_PHRASES = (
    "delve into",
    "game-changing",
    "in today's fast-paced world",
    "it's worth noting",
    "leverage",
    "seamlessly",
)

REQUIRED_TEMPLATE_HEADINGS = {
    "concept.md": ("How it works",),
    "how-to.md": ("Prerequisites", "Steps", "Verify"),
    "tutorial.md": ("Prerequisites", "Objectives", "Steps", "Verify"),
    "reference.md": ("Example", "Related"),
    "system-design.md": (
        "Goal and constraints",
        "Context",
        "Main components",
        "Primary flow",
        "Trade-offs and failure behavior",
    ),
    "chart-page.md": (),
}

WORD_RE = re.compile(r"\b[\w'-]+\b")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
LINK_LABEL_RE = re.compile(r"!?\[([^\]]*)\]\([^)]+\)")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
REQUIRED_TEMPLATE_MARKERS = {
    "chart-page.md": (
        "**Measure:**",
        "**Coverage:**",
        "**Period:**",
        "**Source:**",
        "**Chart source:**",
        "![",
        "Figure 1.",
    ),
    "diagram.md": (
        "![",
        "Figure 1.",
        "diagram-name.d2",
        "dacode render docs/diagrams",
    ),
}
REQUIRED_DIAGRAMS = {
    "diagrams/project-structure.d2": (
        "DaCode skill + CLI",
        "author -> agent: task",
        "dacode -> agent: rules and checks",
        "agent -> project.source: reads facts",
        "agent -> project.docs: writes",
    ),
    "examples/system-design.d2": (
        "system: URL shortener",
        "visitor -> system.create",
        "visitor -> system.redirect",
        "read on cache miss",
    ),
}
REQUIRED_D2_STYLE = (
    "theme-id: 0",
    "dark-theme-id: 200",
    "  owned: {",
    "  store: {",
    "  external: {",
    "  person: {",
    "  boundary: {",
    "  flow: {",
    "  reply: {",
    "  fail: {",
    "  failed: {",
    "  link: {",
    'owned-light: "#FAECB6"',
    'desired: "#228B22"',
    'undesired: "#E24942"',
)
REQUIRED_DIAGRAM_PAGES = {
    "README.md": ("diagrams/project-structure.svg", "diagrams/project-structure.d2"),
    "examples/system-design.md": ("system-design.svg", "system-design.d2"),
}


def _plain_text(paragraph: str) -> str:
    """Remove Markdown syntax that should not count as prose words."""
    paragraph = re.sub(r"`[^`]*`", " ", paragraph)
    paragraph = LINK_LABEL_RE.sub(r"\1", paragraph)
    paragraph = re.sub(r"https?://\S+", " ", paragraph)
    paragraph = re.sub(r"[*_>#]", " ", paragraph)
    return paragraph.strip()


def _sentence_word_counts(paragraph: str) -> list[int]:
    text = _plain_text(paragraph)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [len(WORD_RE.findall(sentence)) for sentence in sentences if sentence.strip()]


def lint_markdown(path: Path, text: str, root: Path) -> list[str]:
    """Return readable, path-qualified violations for a Markdown file."""
    relative = path.relative_to(root).as_posix()
    errors: list[str] = []
    lines = text.splitlines()
    headings: list[tuple[int, int, str]] = []
    paragraphs: list[tuple[int, str]] = []
    paragraph_lines: list[str] = []
    paragraph_start = 0
    fence: tuple[str, int] | None = None

    def finish_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            paragraphs.append((paragraph_start, " ".join(line.strip() for line in paragraph_lines)))
            paragraph_lines = []

    for number, line in enumerate(lines, start=1):
        fence_match = FENCE_RE.match(line)
        if fence:
            marker = fence[0]
            if fence_match and fence_match.group(1)[0] == marker[0] and len(fence_match.group(1)) >= len(marker):
                fence = None
            continue
        if fence_match:
            finish_paragraph()
            fence = (fence_match.group(1), number)
            continue

        if not line.strip():
            finish_paragraph()
            continue

        heading_match = HEADING_RE.match(line)
        if heading_match:
            finish_paragraph()
            headings.append((number, len(heading_match.group(1)), heading_match.group(2)))
            continue

        if line.lstrip().startswith(("- ", "* ", "+ ", "> ", "|")) or re.match(r"^\s*\d+[.)]\s", line):
            finish_paragraph()
            continue

        if not paragraph_lines:
            paragraph_start = number
        paragraph_lines.append(line)
    finish_paragraph()

    if fence:
        errors.append(f"{relative}:{fence[1]}: unclosed code fence")

    # This template is an embeddable block, not a standalone Markdown page.
    is_fragment = relative == "templates/diagram.md"
    is_template = relative.startswith("templates/")
    if not is_fragment:
        h1s = [heading for heading in headings if heading[1] == 1]
        if len(h1s) != 1:
            errors.append(f"{relative}: expected exactly one level-one heading, found {len(h1s)}")
        elif headings and headings[0] != h1s[0]:
            errors.append(f"{relative}: the first heading must be level one")
    previous_level = 0
    for number, level, _title in headings:
        if previous_level and level > previous_level + 1:
            errors.append(f"{relative}:{number}: heading level skips from H{previous_level} to H{level}")
        previous_level = level

    for number, paragraph in paragraphs:
        sentence_sizes = _sentence_word_counts(paragraph)
        if len(sentence_sizes) > 5:
            errors.append(f"{relative}:{number}: paragraph has more than five sentences")
        for size in sentence_sizes:
            if size > 36:
                errors.append(f"{relative}:{number}: sentence has {size} words; maximum is 36")

    inside_fence = False
    for number, line in enumerate(lines):
        fence_match = FENCE_RE.match(line)
        if fence_match:
            if not inside_fence:
                info = fence_match.group(2).strip().lower()
                inside_fence = True
                if info == "mermaid":
                    errors.append(f"{relative}:{number + 1}: use D2 for diagrams and Vega-Lite for charts")
                continue
            inside_fence = False

    in_code = False
    code_marker = ""
    for number, line in enumerate(lines, start=1):
        match = FENCE_RE.match(line)
        if match:
            marker = match.group(1)
            if not in_code:
                in_code, code_marker = True, marker
            elif marker[0] == code_marker[0] and len(marker) >= len(code_marker):
                in_code = False
            continue
        if in_code:
            continue
        for phrase in FILLER_PHRASES:
            if phrase in line.lower():
                errors.append(f"{relative}:{number}: remove filler phrase {phrase!r}")
        for link_match in LINK_RE.finditer(line):
            target = link_match.group(1).strip().split()[0].strip("<>")
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            if is_template:
                continue
            if "<" in target or ">" in target:
                continue
            link_path = target.split("#", 1)[0].split("?", 1)[0]
            if not link_path:
                continue
            resolved = (path.parent / link_path).resolve()
            if not resolved.exists():
                errors.append(f"{relative}:{number}: local link target does not exist: {link_path}")
        for image_match in IMAGE_RE.finditer(line):
            if not image_match.group(1).strip():
                errors.append(f"{relative}:{number}: image needs descriptive alt text")
            target = image_match.group(2).strip().split()[0].strip("<>")
            if target.split("#", 1)[0].split("?", 1)[0].endswith(".svg"):
                caption_index = number + 1
                while caption_index < len(lines) and not lines[caption_index].strip():
                    caption_index += 1
                if caption_index >= len(lines) or not re.match(r"^Figure\s+\d+\.", lines[caption_index].strip()):
                    errors.append(f"{relative}:{number}: SVG image needs a Figure caption")
                    continue

                if not target.startswith(("http://", "https://")) and "<" not in target and ">" not in target:
                    rendered = (path.parent / target.split("#", 1)[0].split("?", 1)[0]).resolve()
                    source = rendered.with_suffix(".d2")
                    if source.is_file() and not re.search(r"\[[^\]]+\]\([^)]+\.d2(?:[#?][^)]*)?\)", lines[caption_index]):
                        errors.append(f"{relative}:{caption_index + 1}: D2 image caption must link its .d2 source")

    return errors


def lint_required_structure(root: Path) -> list[str]:
    errors: list[str] = []
    for filename, required in REQUIRED_TEMPLATE_HEADINGS.items():
        path = root / "templates" / filename
        if not path.is_file():
            errors.append(f"templates/{filename}: required template is missing")
            continue
        headings = set(re.findall(r"^##\s+(.+?)\s*$", path.read_text(encoding="utf-8"), re.MULTILINE))
        for heading in required:
            if heading not in headings:
                errors.append(f"templates/{filename}: required section is missing: {heading}")
    for filename, markers in REQUIRED_TEMPLATE_MARKERS.items():
        path = root / "templates" / filename
        if not path.is_file():
            errors.append(f"templates/{filename}: required template is missing")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                errors.append(f"templates/{filename}: required content is missing: {marker}")
    for filename, markers in REQUIRED_DIAGRAMS.items():
        path = root / filename
        if not path.is_file():
            errors.append(f"{filename}: required D2 source is missing")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                errors.append(f"{filename}: required diagram content is missing: {marker}")

    for folder in ("diagrams", "examples"):
        for path in sorted((root / folder).rglob("*.d2")):
            text = path.read_text(encoding="utf-8")
            relative = path.relative_to(root).as_posix()
            for marker in REQUIRED_D2_STYLE:
                if marker not in text:
                    errors.append(f"{relative}: required diagram style is missing: {marker}")
            rendered_path = path.with_suffix(".svg")
            if not rendered_path.is_file():
                errors.append(f"{rendered_path.relative_to(root)}: generated diagram is missing")
            elif "prefers-color-scheme:dark" not in rendered_path.read_text(encoding="utf-8"):
                errors.append(f"{rendered_path.relative_to(root)}: SVG must include a dark-mode theme")

    for filename, markers in REQUIRED_DIAGRAM_PAGES.items():
        path = root / filename
        if not path.is_file():
            errors.append(f"{filename}: required diagram page is missing")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                errors.append(f"{filename}: diagram source or rendered image is not linked: {marker}")
    return errors


def check_project(root: Path) -> list[str]:
    errors = lint_required_structure(root)
    markdown_files = sorted(
        path for path in root.rglob("*.md")
        if ".git" not in path.parts and "vendor" not in path.parts
    )
    for path in markdown_files:
        errors.extend(lint_markdown(path, path.read_text(encoding="utf-8"), root))
    return errors


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    errors = check_project(root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        print(f"Writing check failed with {len(errors)} issue(s).", file=sys.stderr)
        return 1
    print("Writing and structure checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Command-line tools for drafting and checking documentation projects."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from check_writing import lint_markdown


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = "docs"
PAGE_KINDS = ("concept", "how-to", "tutorial", "reference", "system-design")
NEW_KINDS = (*PAGE_KINDS, "diagram", "chart")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VEGA_LITE_SCHEMA = "https://vega.github.io/schema/vega-lite/v6.json"
D2_VERSION = "v0.9.0"
# A GitHub README column is about 880px wide. At 1000px, 18px box text still shows at about 16px.
MAX_DIAGRAM_WIDTH = 1000


def _title(slug: str) -> str:
    return " ".join(part[:1].upper() + part[1:] for part in slug.split("-"))


# Shared by every scaffolded diagram. Each class names a role so color always carries meaning:
# yellow for what the system owns, green for stored data, dashed grey for external parties,
# forest green for the desired path, and red only for undesired paths. Fills follow the viewer's
# light or dark scheme; lines use mid-tones that stay readable on both.
DIAGRAM_STYLE = """vars: {
  # Fills sit at the same lightness and saturation so yellow and green read as one family.
  # Lines and arrows are mid-tones with at least 3:1 contrast on both the light and dark canvas.
  colors: {
    owned-light: "#FAECB6"
    owned-dark: "#5B4315"
    store-light: "#C9F4D7"
    store-dark: "#234932"
    owned-line: "#AD8522"
    desired: "#228B22"
    undesired: "#E24942"
    neutral: "#868D95"
  }
  d2-config: {
    theme-id: 0
    dark-theme-id: 200
    # Fills use theme slots so they switch with the viewer's color scheme. Rectangles take
    # B4 to B6 and cylinders AA4 or AA5 depending on nesting depth; B1 draws unclassed lines.
    # Shapes nested three or more boundaries deep take the canvas color instead.
    theme-overrides: {
      B1: ${colors.neutral}
      B2: ${colors.neutral}
      N2: "#4B5563"
      B3: "#E5E8EB"
      B4: ${colors.owned-light}
      B5: ${colors.owned-light}
      B6: ${colors.owned-light}
      AA4: ${colors.store-light}
      AA5: ${colors.store-light}
    }
    dark-theme-overrides: {
      B1: ${colors.neutral}
      B2: ${colors.neutral}
      N2: "#C9D1D9"
      B3: "#3A4148"
      B4: ${colors.owned-dark}
      B5: ${colors.owned-dark}
      B6: ${colors.owned-dark}
      AA4: ${colors.store-dark}
      AA5: ${colors.store-dark}
    }
  }
}

classes: {
  # A component the system owns: the main subject of the diagram. Keep it a rectangle.
  owned: {
    style: {
      font-size: 18
      stroke: ${colors.owned-line}
      stroke-width: 2
      border-radius: 6
      bold: true
    }
  }
  # Stored data: databases, queues, files, caches.
  store: {
    shape: cylinder
    style: {
      font-size: 18
      stroke: ${colors.desired}
      stroke-width: 2
      bold: true
    }
  }
  # Something outside the system: a client, service, or third party.
  external: {
    style: {
      font-size: 18
      fill: transparent
      stroke: ${colors.neutral}
      stroke-width: 2
      stroke-dash: 4
      border-radius: 6
      bold: false
    }
  }
  # A person outside the system. A dashed outline makes the icon look broken, so keep it solid.
  person: {
    shape: person
    style: {
      font-size: 18
      fill: transparent
      stroke: ${colors.neutral}
      stroke-width: 2
    }
  }
  # An ownership or deployment boundary. Its title sits top left so incoming arrows do not cross it.
  boundary: {
    label.near: top-left
    style: {
      fill: transparent
      stroke: ${colors.neutral}
      stroke-width: 1
      font-size: 16
      border-radius: 4
    }
  }
  # The desired path: what should happen.
  flow: {
    style: {
      stroke: ${colors.desired}
      stroke-width: 2
    }
  }
  # A reply, read-back, recovery, or optional side effect.
  reply: {
    style: {
      stroke: ${colors.neutral}
      stroke-width: 2
      stroke-dash: 4
    }
  }
  # A structural relationship with no direction, drawn with --.
  link: {
    style: {
      stroke: ${colors.neutral}
      stroke-width: 1
    }
  }
  # An undesired path: failure, rejection, or error.
  fail: {
    style: {
      stroke: ${colors.undesired}
      font-color: ${colors.undesired}
      stroke-width: 2
      stroke-dash: 4
      bold: true
    }
  }
  # A state or outcome nobody wants: failure, rejection, dead letter.
  failed: {
    style: {
      fill: transparent
      stroke: ${colors.undesired}
      font-color: ${colors.undesired}
      stroke-width: 2
      border-radius: 6
      bold: true
    }
  }
  # Start and end markers for state machines.
  start: {
    shape: circle
    label: ""
    width: 20
    style: {
      fill: ${colors.desired}
      stroke: ${colors.desired}
    }
  }
  end: {
    shape: circle
    label: ""
    width: 24
    style: {
      fill: transparent
      stroke: ${colors.desired}
      stroke-width: 6
    }
  }
}
"""


def _diagram_source(title: str) -> str:
    return f'''direction: right

{DIAGRAM_STYLE}
actor: Person {{
  class: person
}}

system: "{title}" {{
  class: boundary
  component: Main component {{
    class: owned
  }}
  data: Stored data {{
    class: store
  }}
  component -> data: write {{
    class: flow
  }}
}}

actor -> system.component: request {{
  class: flow
}}
'''


def _new_targets(root: Path, kind: str, slug: str) -> list[tuple[Path, str]]:
    title = _title(slug)
    if kind in PAGE_KINDS:
        template_path = REPO_ROOT / "templates" / f"{kind}.md"
        body = template_path.read_text(encoding="utf-8")
        body = re.sub(r"^# .+$", f"# {title}", body, count=1, flags=re.MULTILINE)
        targets = [(root / DOCS_ROOT / f"{slug}.md", body)]
        if kind == "system-design":
            # The template embeds two diagrams; give them page-specific names and scaffold their sources.
            for diagram in ("context", "request-flow"):
                name = f"{slug}-{diagram}"
                body = body.replace(f"diagrams/{diagram}.", f"diagrams/{name}.")
                targets.append((root / DOCS_ROOT / "diagrams" / f"{name}.d2", _diagram_source(_title(name))))
            targets[0] = (targets[0][0], body)
        return targets

    if kind == "diagram":
        return [(root / DOCS_ROOT / "diagrams" / f"{slug}.d2", _diagram_source(title))]

    chart = {
        "$schema": VEGA_LITE_SCHEMA,
        "description": "Replace the example fields and add verified project data.",
        "data": {"values": []},
        "mark": {"type": "bar"},
        "encoding": {
            "x": {"field": "category", "type": "nominal", "title": "Category"},
            "y": {"field": "value", "type": "quantitative", "title": "Value"},
        },
    }
    body = json.dumps(chart, indent=2) + "\n"
    return [(root / DOCS_ROOT / "charts" / f"{slug}.vl.json", body)]


def create_new(root: Path, kind: str, slug: str) -> list[Path]:
    if not SLUG_RE.fullmatch(slug):
        raise ValueError("name must be a lowercase hyphenated slug, such as request-flow")
    targets = _new_targets(root, kind, slug)
    existing = [path for path, _content in targets if path.exists()]
    if existing:
        paths = ", ".join(path.relative_to(root).as_posix() for path in existing)
        raise FileExistsError(f"refusing to overwrite: {paths}")
    for path, content in targets:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as output:
            output.write(content)
    return [path for path, _content in targets]


def _task_text(value: str | None) -> str:
    if value is not None:
        path = Path(value)
        task = path.read_text(encoding="utf-8") if path.is_file() else value
    elif not sys.stdin.isatty():
        task = sys.stdin.read()
    else:
        raise ValueError("provide a task as an argument or on standard input")
    if not task.strip():
        raise ValueError("task is empty")
    return task.strip()


def build_prompt(task: str, template: str | None = None) -> str:
    ruleset = (REPO_ROOT / "RULESET.md").read_text(encoding="utf-8").strip()
    parts = [
        "# DaCode Task\n\n"
        "Follow the canonical writing rules below. Work only on the task at the end. "
        "Inspect project evidence before writing. Put every newly created documentation page, "
        "diagram source, chart source, and rendered visual under the target project's root `docs/` folder. "
        "Do not copy DaCode's rules into the target project.\n\n"
        "## Canonical ruleset\n\n" + ruleset
    ]
    if template:
        template_path = REPO_ROOT / "templates" / f"{template}.md"
        parts.append(f"## Suggested page template: {template}\n\n{template_path.read_text(encoding='utf-8').strip()}")
    parts.append(f"## Task\n\n{task}")
    return "\n\n".join(parts) + "\n"


def _selected_files(root: Path, requested: list[str]) -> tuple[list[Path], list[str]]:
    errors: list[str] = []
    selected: set[Path] = set()
    items = requested or [DOCS_ROOT]
    for item in items:
        path = (root / item).resolve()
        if not path.exists():
            errors.append(f"{item}: path does not exist")
            continue
        if path.is_file():
            selected.add(path)
            continue
        for pattern in ("*.md", "*.d2", "*.vl.json"):
            selected.update(path.rglob(pattern))
    files = sorted(path for path in selected if path.is_file())
    outside = [path for path in files if not path.is_relative_to(root.resolve())]
    errors.extend(f"{path}: target is outside the project root" for path in outside)
    return [path for path in files if path not in outside], errors


def _svg_width(path: Path) -> int | None:
    if not path.is_file():
        return None
    match = re.search(r'<svg[^>]*\swidth="(\d+)', path.read_text(encoding="utf-8", errors="replace")[:2000])
    return int(match.group(1)) if match else None


def check_paths(root: Path, requested: list[str]) -> list[str]:
    files, errors = _selected_files(root, requested)
    if not files and not errors:
        return [f"{DOCS_ROOT}: no Markdown, D2, or Vega-Lite source files found"]

    markdown_files = [path for path in files if path.suffix.lower() == ".md"]
    for path in markdown_files:
        errors.extend(lint_markdown(path, path.read_text(encoding="utf-8"), root.resolve()))

    for path in files:
        relative = path.relative_to(root.resolve()).as_posix()
        if path.suffix.lower() == ".d2" and not path.with_suffix(".svg").is_file():
            errors.append(f"{relative}: rendered SVG is missing; run dacode render {path.parent.relative_to(root.resolve())}")
        if path.suffix.lower() == ".d2" and not path.with_suffix(".png").is_file():
            errors.append(f"{relative}: rendered PNG is missing; run dacode render {path.parent.relative_to(root.resolve())}")
        if path.suffix.lower() == ".d2" and (width := _svg_width(path.with_suffix(".svg"))) and width > MAX_DIAGRAM_WIDTH:
            errors.append(
                f"{relative}: rendered width {width}px exceeds {MAX_DIAGRAM_WIDTH}px; "
                "shorten labels, merge a straight run of steps into one box, or split the diagram"
            )
        if path.name.endswith(".vl.json"):
            try:
                spec = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"{relative}:{exc.lineno}: invalid JSON: {exc.msg}")
                continue
            if not isinstance(spec, dict):
                errors.append(f"{relative}: Vega-Lite specification must be a JSON object")
                continue
            for key in ("$schema", "data", "mark", "encoding"):
                if key not in spec:
                    errors.append(f"{relative}: Vega-Lite specification is missing {key!r}")
            if "$schema" in spec and "vega-lite" not in str(spec["$schema"]):
                errors.append(f"{relative}: $schema must identify Vega-Lite")
            if not isinstance(spec.get("encoding"), dict):
                errors.append(f"{relative}: encoding must be a JSON object")
    return errors


def _d2_executable() -> str:
    candidates = [Path.home() / ".local" / "bin" / "d2"]
    if found := shutil.which("d2"):
        candidates.append(Path(found))
    versions = []
    for candidate in candidates:
        if not (candidate.is_file() and os.access(candidate, os.X_OK)):
            continue
        try:
            version = subprocess.run([str(candidate), "--version"], check=True, capture_output=True, text=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            continue
        if version == D2_VERSION:
            return str(candidate)
        versions.append(f"{candidate} reports {version}")
    if versions:
        raise RuntimeError(f"expected D2 {D2_VERSION}; found " + "; ".join(versions))
    raise RuntimeError(f"D2 {D2_VERSION} is required to render diagrams; run scripts/install_d2.py from the DaCode checkout")


def render_diagrams(root: Path, requested: list[str]) -> list[Path]:
    root = root.resolve()
    executable = _d2_executable()
    files, errors = _selected_files(root, requested or [f"{DOCS_ROOT}/diagrams"])
    if errors:
        raise ValueError("\n".join(errors))
    sources = [path for path in files if path.suffix.lower() == ".d2"]
    if not sources:
        raise ValueError("no D2 source files found")
    outputs = []
    for source in sources:
        for extension in ("svg", "png"):
            output = source.with_suffix(f".{extension}")
            command = [executable, "--layout=elk", "--elk-nodeNodeBetweenLayers=30", "--pad=24", "--theme=0"]
            if extension == "svg":
                # A fixed size, instead of D2's fit-to-window default, lets readers zoom an opened SVG.
                command.extend(["--dark-theme=200", "--scale=1"])
            # Run from the project root so D2 reports short, relative paths.
            subprocess.run([*command, str(source.relative_to(root)), str(output.relative_to(root))], check=True, cwd=root)
            outputs.append(output)
    return outputs


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="dacode", description="Scaffold, render, and check project documentation.")
    commands = result.add_subparsers(dest="command", required=True)

    new = commands.add_parser("new", help="create a documentation page, D2 diagram, or Vega-Lite chart source")
    new.add_argument("kind", choices=NEW_KINDS)
    new.add_argument("name", help="lowercase hyphenated name, such as service-overview")
    new.add_argument("--root", default=".", help="target project root (default: current directory)")

    prompt = commands.add_parser("prompt", help="combine the canonical ruleset with a task for any local agent")
    prompt.add_argument("task", nargs="?", help="task text or a path to a task file; otherwise read standard input")
    prompt.add_argument("--template", choices=PAGE_KINDS, help="include a starter Markdown page template")

    commands.add_parser("rules", help="print the canonical DaCode writing rules")

    check = commands.add_parser("check", help="check writing, links, diagram outputs, and chart specs")
    check.add_argument("paths", nargs="*", help="files or directories to check (default: docs/)")
    check.add_argument("--root", default=".", help="target project root (default: current directory)")

    render = commands.add_parser("render", help="render D2 sources to SVG and PNG with the pinned renderer")
    render.add_argument("paths", nargs="*", help="D2 files or directories (default: docs/diagrams)")
    render.add_argument("--root", default=".", help="target project root (default: current directory)")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "new":
            root = Path(args.root).resolve()
            if not root.is_dir():
                raise ValueError(f"project root is not a directory: {root}")
            created = create_new(root, args.kind, args.name)
            for path in created:
                print(f"Created {path.relative_to(root).as_posix()}")
            return 0
        if args.command == "prompt":
            task = _task_text(args.task)
            sys.stdout.write(build_prompt(task, args.template))
            return 0
        if args.command == "rules":
            sys.stdout.write((REPO_ROOT / "RULESET.md").read_text(encoding="utf-8"))
            return 0
        if args.command == "check":
            root = Path(args.root).resolve()
            errors = check_paths(root, args.paths)
            if errors:
                print("\n".join(errors), file=sys.stderr)
                print(f"DaCode found {len(errors)} issue(s).", file=sys.stderr)
                return 1
            print("Documentation checks passed.")
            return 0
        if args.command == "render":
            outputs = render_diagrams(Path(args.root).resolve(), args.paths)
            for path in outputs:
                print(f"Rendered {path.relative_to(Path(args.root).resolve()).as_posix()}")
            return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"dacode: {exc}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

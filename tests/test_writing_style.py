import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_writing import check_project, lint_markdown, lint_required_structure


class WritingStyleTests(unittest.TestCase):
    def lint(self, markdown: str, files: dict[str, str] | None = None) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "page.md"
            path.write_text(markdown, encoding="utf-8")
            for name, content in (files or {}).items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            return lint_markdown(path, markdown, root)

    def test_accepts_concise_page_with_captioned_diagram(self) -> None:
        markdown = """# Page title

This page explains one behavior in plain language.

![A request moves from A to B.](https://example.org/flow.svg)

Figure 1. The request moves from A to B.
"""
        self.assertEqual(self.lint(markdown), [])

    def test_rejects_mermaid_source(self) -> None:
        errors = self.lint("# Page\n\n```mermaid\nflowchart LR\n    A --> B\n```\n")
        self.assertTrue(any("use D2 for diagrams and Vega-Lite for charts" in error for error in errors))

    def test_rejects_missing_title_and_heading_level_skip(self) -> None:
        errors = self.lint("## Section\n\n#### Nested section\n")
        self.assertTrue(any("exactly one level-one heading" in error for error in errors))
        self.assertTrue(any("skips from H2 to H4" in error for error in errors))

    def test_requires_title_before_other_headings(self) -> None:
        errors = self.lint("## Section\n\n# Page title\n")
        self.assertTrue(any("first heading must be level one" in error for error in errors))

    def test_rejects_long_sentence_and_filler(self) -> None:
        long_sentence = " ".join(["word"] * 37) + "."
        errors = self.lint(f"# Page\n\n{long_sentence}\n\nWe leverage this approach.\n")
        self.assertTrue(any("maximum is 36" in error for error in errors))
        self.assertTrue(any("filler phrase 'leverage'" in error for error in errors))

    def test_rejects_paragraph_with_too_many_sentences(self) -> None:
        paragraph = "One. Two. Three. Four. Five. Six."
        errors = self.lint(f"# Page\n\n{paragraph}\n")
        self.assertTrue(any("more than five sentences" in error for error in errors))

    def test_rejects_missing_svg_caption(self) -> None:
        errors = self.lint("# Page\n\n![Diagram](https://example.org/flow.svg)\n\nSome explanation.\n")
        self.assertTrue(any("SVG image needs a Figure caption" in error for error in errors))

    def test_requires_source_link_for_local_d2_diagram(self) -> None:
        markdown = """# Page

![Diagram](diagram.svg)

Figure 1. A short caption without a source link.
"""
        errors = self.lint(markdown, {"diagram.svg": "<svg/>", "diagram.d2": "a -> b"})
        self.assertTrue(any("caption must link its .d2 source" in error for error in errors))

    def test_rejects_unclosed_fence_and_broken_local_link(self) -> None:
        errors = self.lint("# Page\n\nSee [missing](missing.md) and ![](image.svg).\n\n```text\n")
        self.assertTrue(any("unclosed code fence" in error for error in errors))
        self.assertTrue(any("local link target does not exist" in error for error in errors))
        self.assertTrue(any("image needs descriptive alt text" in error for error in errors))

    def test_templates_and_diagrams_keep_required_structure(self) -> None:
        self.assertEqual(lint_required_structure(ROOT), [])

    def test_all_project_markdown_passes(self) -> None:
        self.assertEqual(check_project(ROOT), [])


if __name__ == "__main__":
    unittest.main()

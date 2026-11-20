import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from dacode import DIAGRAM_STYLE, MAX_DIAGRAM_WIDTH, build_prompt, check_paths, create_new


class DaCodeCliTests(unittest.TestCase):
    def test_new_page_goes_under_project_docs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            created = create_new(root, "how-to", "configure-alerts")

            self.assertEqual(created, [root / "docs/configure-alerts.md"])
            self.assertTrue(created[0].read_text(encoding="utf-8").startswith("# Configure Alerts\n"))

    def test_new_diagram_and_chart_sources_use_docs_subfolders(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            diagram = create_new(root, "diagram", "alert-flow")[0]
            chart = create_new(root, "chart", "requests-by-region")[0]

            self.assertEqual(diagram, root / "docs/diagrams/alert-flow.d2")
            self.assertEqual(chart, root / "docs/charts/requests-by-region.vl.json")
            self.assertIn("theme-id: 0", diagram.read_text(encoding="utf-8"))
            spec = json.loads(chart.read_text(encoding="utf-8"))
            self.assertEqual(spec["$schema"], "https://vega.github.io/schema/vega-lite/v6.json")
            self.assertEqual(spec["mark"]["type"], "bar")

    def test_new_diagram_uses_role_classes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = create_new(Path(directory), "diagram", "alert-flow")[0].read_text(encoding="utf-8")

            self.assertIn(DIAGRAM_STYLE, source)
            for role in ("owned", "store", "external", "person", "boundary", "flow", "reply", "link", "fail", "failed"):
                self.assertIn(f"\n  {role}: {{", DIAGRAM_STYLE)
            for role in ("owned", "store", "person", "boundary", "flow"):
                self.assertIn(f"class: {role}", source)

    def test_new_system_design_scaffolds_its_diagrams(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            created = create_new(root, "system-design", "checkout")

            self.assertEqual(
                created,
                [
                    root / "docs/checkout.md",
                    root / "docs/diagrams/checkout-context.d2",
                    root / "docs/diagrams/checkout-request-flow.d2",
                ],
            )
            page = created[0].read_text(encoding="utf-8")
            self.assertIn("diagrams/checkout-context.svg", page)
            self.assertIn("diagrams/checkout-request-flow.d2", page)

            for source in created[1:]:
                source.with_suffix(".svg").write_text("<svg/>", encoding="utf-8")
                source.with_suffix(".png").write_bytes(b"")
            self.assertEqual(check_paths(root, ["docs"]), [])

    def test_new_refuses_to_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = create_new(root, "concept", "cache-policy")[0]

            with self.assertRaises(FileExistsError):
                create_new(root, "concept", "cache-policy")

            self.assertTrue(target.is_file())

    def test_prompt_contains_task_rules_and_output_location(self) -> None:
        prompt = build_prompt("Document the retry behavior.", "how-to")

        self.assertIn("## Canonical ruleset", prompt)
        self.assertIn("root `docs/` folder", prompt)
        self.assertIn("## Suggested page template: how-to", prompt)
        self.assertTrue(prompt.endswith("## Task\n\nDocument the retry behavior.\n"))

    def test_check_validates_diagram_pair_and_chart_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_new(root, "diagram", "cache-flow")
            chart = create_new(root, "chart", "cache-hits")[0]

            errors = check_paths(root, ["docs"])
            self.assertTrue(any("rendered SVG is missing" in error for error in errors))

            (root / "docs/diagrams/cache-flow.svg").write_text("<svg/>", encoding="utf-8")
            chart.write_text("{bad json", encoding="utf-8")
            errors = check_paths(root, ["docs"])

            self.assertFalse(any("rendered SVG is missing" in error for error in errors))
            self.assertTrue(any("invalid JSON" in error for error in errors))


    def test_check_rejects_diagrams_too_wide_to_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = create_new(root, "diagram", "wide-flow")[0]
            source.with_suffix(".png").write_bytes(b"")
            svg = source.with_suffix(".svg")

            svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{MAX_DIAGRAM_WIDTH}" height="300"/>', encoding="utf-8")
            self.assertEqual(check_paths(root, ["docs"]), [])

            svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{MAX_DIAGRAM_WIDTH + 1}" height="300"/>', encoding="utf-8")
            errors = check_paths(root, ["docs"])
            self.assertTrue(any("exceeds" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

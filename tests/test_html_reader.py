from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
READER = ROOT / "tools" / "build_html_reader.py"
RENDERER = ROOT / "tools" / "render_mermaid.py"
VERIFIER = ROOT / "tools" / "verify_artifacts.py"


class HtmlReaderTests(unittest.TestCase):
    def make_book(self, root: Path, *, diagrams: int = 1) -> Path:
        book = root / "book"
        book.mkdir()
        (book / "SUMMARY.md").write_text("* [A](a.md)\n* [B](b.md)\n", encoding="utf-8")
        blocks = "\n".join(f"```mermaid\ngraph TD\nA{i}-->B{i}\n```" for i in range(diagrams))
        (book / "a.md").write_text(f"# A\n\n{blocks}\n", encoding="utf-8")
        (book / "b.md").write_text("# B\n\nDone.\n", encoding="utf-8")
        return book

    def fake_pandoc(self, root: Path) -> Path:
        binary = root / "bin"
        binary.mkdir(exist_ok=True)
        pandoc = binary / "pandoc"
        pandoc.write_text(
            textwrap.dedent(
                f"""\
                #!{sys.executable}
                import pathlib, re, sys
                args=sys.argv[1:]
                source=pathlib.Path(args[0]).read_text(encoding='utf-8')
                output=pathlib.Path(args[args.index('-o')+1])
                markers=re.findall(r'(?:PGBKZZp\\d+ZZ|MERMAIDZZ\\d+ZZ)', source)
                body=''.join(f'<p>{{marker}}</p>' for marker in markers)
                output.write_text('<html><head><title>Test Guide</title></head><body><main id="content">'+body+'</main></body></html>', encoding='utf-8')
                """
            ),
            encoding="utf-8",
        )
        pandoc.chmod(0o755)
        return binary

    def run_reader(self, book: Path, svg: Path, output: Path, binary: Path, *flags: str):
        env = os.environ.copy()
        env["PATH"] = f"{binary}{os.pathsep}{env['PATH']}"
        return subprocess.run(
            [sys.executable, str(READER), "--book-dir", str(book), "--title", "Test Guide", "--svg-dir", str(svg), "--out", str(output), *flags],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_reader_smoke_requires_complete_inline_mermaid(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            book = self.make_book(root)
            svg = root / "svg"
            svg.mkdir()
            (svg / "d-1.svg").write_text('<svg id="my-svg"><text>ok</text></svg>', encoding="utf-8")
            output = root / "reader.html"
            result = self.run_reader(book, svg, output, self.fake_pandoc(root), "--strict")
            self.assertEqual(result.returncode, 0, result.stderr)
            html = output.read_text(encoding="utf-8")
            self.assertEqual(html.count('class="page"'), 2)
            self.assertEqual(html.count('class="diagram"'), 1)
            self.assertIn("<svg", html)
            self.assertNotRegex(html, r"MERMAIDZZ|PGBKZZ|diagram-fallback")

    def test_reader_is_strict_by_default_and_rejects_summary_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            book = self.make_book(root)
            svg = root / "svg"
            svg.mkdir()
            binary = self.fake_pandoc(root)
            missing = self.run_reader(book, svg, root / "missing.html", binary)
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("missing Mermaid", missing.stderr)

            (root / "outside.md").write_text("# Outside\n", encoding="utf-8")
            (book / "SUMMARY.md").write_text("* [Escape](../outside.md)\n", encoding="utf-8")
            escaped = self.run_reader(book, svg, root / "escaped.html", binary)
            self.assertNotEqual(escaped.returncode, 0)
            self.assertIn("escapes book directory", escaped.stderr)

    def test_mermaid_renderer_is_strict_and_source_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            book = self.make_book(root, diagrams=2)
            overlap = subprocess.run(
                [sys.executable, str(RENDERER), "--book-dir", str(book), "--svg-out", str(book / "svg")],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(overlap.returncode, 0)
            env = os.environ.copy()
            env["CHROME_BIN"] = str(root / "missing-chrome")
            strict = subprocess.run(
                [sys.executable, str(RENDERER), "--book-dir", str(book), "--svg-out", str(root / "svg")],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(strict.returncode, 0)

    def test_renderer_isolates_one_poisoned_diagram(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            book = self.make_book(root, diagrams=3)
            source = (book / "a.md").read_text(encoding="utf-8").replace("A1-->B1", "POISON")
            (book / "a.md").write_text(source, encoding="utf-8")
            binary = root / "bin"
            binary.mkdir()
            chrome = binary / "chrome"
            chrome.write_text("", encoding="utf-8")
            chrome.chmod(0o755)
            mmdc = binary / "mmdc"
            mmdc.write_text(
                textwrap.dedent(
                    f"""\
                    #!{sys.executable}
                    import pathlib, re, sys
                    args = sys.argv[1:]
                    source = pathlib.Path(args[args.index('-i') + 1]).read_text(encoding='utf-8')
                    output = pathlib.Path(args[args.index('-o') + 1])
                    if 'POISON' in source:
                        print('poisoned diagram', file=sys.stderr)
                        raise SystemExit(1)
                    count = len(re.findall(r'```mermaid', source))
                    if count == 1:
                        output.write_text('<svg id="my-svg"></svg>', encoding='utf-8')
                    else:
                        for index in range(1, count + 1):
                            output.with_name(f'{{output.stem}}-{{index}}.svg').write_text('<svg id="my-svg"></svg>', encoding='utf-8')
                    """
                ),
                encoding="utf-8",
            )
            mmdc.chmod(0o755)
            output = root / "svg"
            env = os.environ.copy()
            env.update({"PATH": f"{binary}{os.pathsep}{env['PATH']}", "CHROME_BIN": str(chrome)})
            result = subprocess.run(
                [sys.executable, str(RENDERER), "--book-dir", str(book), "--svg-out", str(output), "--strict"],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue((output / "d-1.svg").is_file())
            self.assertFalse((output / "d-2.svg").exists())
            self.assertTrue((output / "d-3.svg").is_file())
            self.assertIn("[2]", result.stderr)

    def test_locked_mermaid_quadrant_quotes_non_ascii_labels(self):
        text = (ROOT / "02_discovery" / "2.4_scope.md").read_text(encoding="utf-8")
        self.assertNotIn('title "需求切片选择"', text)
        for marker in (
            'x-axis "低学习收益" --> "高学习收益"',
            'y-axis "低业务价值" --> "高业务价值"',
            'quadrant-1 "优先试点"',
            '"异常归因": [0.82, 0.80]',
        ):
            self.assertIn(marker, text)

    def test_artifact_verifier_rejects_html_fallback(self):
        self.assertTrue(VERIFIER.is_file(), VERIFIER)
        spec = importlib.util.spec_from_file_location("fde_verify_artifacts", VERIFIER)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier)
        with tempfile.TemporaryDirectory() as directory:
            html = Path(directory) / "book.html"
            html.write_text('<title>Test Guide</title><pre class="diagram-fallback">x</pre>', encoding="utf-8")
            with self.assertRaises(verifier.ArtifactVerificationError):
                verifier.verify_html(html, "Test Guide", 1)


if __name__ == "__main__":
    unittest.main()

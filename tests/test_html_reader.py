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

    def fake_pandoc(self, root: Path, *, call_marker: Path | None = None) -> Path:
        binary = root / "bin"
        binary.mkdir(exist_ok=True)
        pandoc = binary / "pandoc"
        pandoc.write_text(
            textwrap.dedent(
                f"""\
                #!{sys.executable}
                import pathlib, re, sys
                call_marker={str(call_marker) if call_marker else None!r}
                if call_marker: pathlib.Path(call_marker).write_text('called', encoding='utf-8')
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

    def fake_nonzero_after_write_tools(
        self, root: Path, *, fail_first_only: bool
    ) -> tuple[Path, Path]:
        binary = root / "bin"
        binary.mkdir()
        chrome = binary / "chrome"
        chrome.write_text("", encoding="utf-8")
        attempt = root / "mmdc-attempt"
        mmdc = binary / "mmdc"
        mmdc.write_text(
            textwrap.dedent(
                f"""\
                #!{sys.executable}
                import pathlib, re, sys
                args=sys.argv[1:]; source=pathlib.Path(args[args.index('-i')+1]); output=pathlib.Path(args[args.index('-o')+1])
                count=len(re.findall(r'```mermaid', source.read_text(encoding='utf-8')))
                for index in range(1, count+1): output.with_name(f'{{output.stem}}-{{index}}.svg').write_text('<svg id="my-svg"></svg>', encoding='utf-8')
                attempt=pathlib.Path({str(attempt)!r})
                attempt_count=int(attempt.read_text()) if attempt.exists() else 0
                attempt.write_text(str(attempt_count + 1), encoding='utf-8')
                if {fail_first_only!r} is False or attempt_count == 0:
                    print('renderer reported fatal error', file=sys.stderr)
                    raise SystemExit(1)
                """
            ),
            encoding="utf-8",
        )
        mmdc.chmod(0o755)
        return binary, chrome

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

    def test_reader_rejects_local_resource_escapes_before_pandoc(self):
        variants = {
            "inline": "![outside](../outside.svg)\n",
            "reference": "![outside][asset]\n\n[asset]: ../outside.svg\n",
            "html": '<img src="../outside.svg" alt="outside">\n',
            "absolute": None,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, body in variants.items():
                with self.subTest(name=name):
                    case = root / name
                    case.mkdir()
                    book = self.make_book(case)
                    outside = case / "outside.svg"
                    marker = f"FDE_OUTSIDE_MARKER_{name}"
                    outside.write_text(
                        f'<svg xmlns="http://www.w3.org/2000/svg"><text>{marker}</text></svg>',
                        encoding="utf-8",
                    )
                    if body is None:
                        body = f"![outside]({outside})\n"
                    (book / "a.md").write_text(f"# A\n\n{body}", encoding="utf-8")
                    svg = case / "svg"
                    svg.mkdir()
                    output = case / "reader.html"
                    result = self.run_reader(
                        book, svg, output, self.fake_pandoc(case), "--strict"
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("outside book directory", result.stderr)
                    rendered = output.read_text(encoding="utf-8") if output.exists() else ""
                    self.assertNotIn(marker, rendered)

    def test_reader_rejects_symlinked_resource_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            book = self.make_book(root)
            outside = root / "outside.svg"
            marker = "FDE_SYMLINK_ESCAPE_MARKER"
            outside.write_text(
                f'<svg xmlns="http://www.w3.org/2000/svg"><text>{marker}</text></svg>',
                encoding="utf-8",
            )
            (book / "linked.svg").symlink_to(outside)
            (book / "a.md").write_text(
                "# A\n\n![outside](linked.svg)\n", encoding="utf-8"
            )
            svg = root / "svg"
            svg.mkdir()
            output = root / "reader.html"
            result = self.run_reader(
                book, svg, output, self.fake_pandoc(root), "--strict"
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("outside book directory", result.stderr)
            rendered = output.read_text(encoding="utf-8") if output.exists() else ""
            self.assertNotIn(marker, rendered)

    def test_reader_rejects_every_embeddable_html_resource_before_pandoc(self):
        variants = {
            "script-src": '<script src="../outside.asset"></script>',
            "source-src": '<source src="../outside.asset">',
            "source-srcset": '<source srcset="../outside.asset 1x">',
            "video-src": '<video src="../outside.asset"></video>',
            "video-poster": '<video poster="../outside.asset"></video>',
            "audio-src": '<audio src="../outside.asset"></audio>',
            "object-data": '<object data="../outside.asset"></object>',
            "embed-src": '<embed src="../outside.asset">',
            "input-src": '<input type="image" src="../outside.asset">',
            "link-stylesheet": '<link rel="stylesheet" href="../outside.asset">',
            "svg-href": '<svg><image href="../outside.asset"/></svg>',
            "svg-xlink": '<svg><image xlink:href="../outside.asset"/></svg>',
            "style-attribute": '<div style="background:url(../outside.asset)">x</div>',
            "style-block": '<style>.x { background: url("../outside.asset"); }</style>',
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, body in variants.items():
                with self.subTest(name=name):
                    case = root / name
                    case.mkdir()
                    book = self.make_book(case)
                    marker = f"FDE_OUTSIDE_RESOURCE_{name}"
                    (case / "outside.asset").write_text(marker, encoding="utf-8")
                    (book / "a.md").write_text(f"# A\n\n{body}\n", encoding="utf-8")
                    svg = case / "svg"
                    svg.mkdir()
                    output = case / "reader.html"
                    called = case / "pandoc-called"
                    result = self.run_reader(
                        book,
                        svg,
                        output,
                        self.fake_pandoc(case, call_marker=called),
                        "--strict",
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("outside book directory", result.stderr)
                    self.assertFalse(called.exists(), "resource validation must precede Pandoc")
                    rendered = output.read_text(encoding="utf-8") if output.exists() else ""
                    self.assertNotIn(marker, rendered)

    def test_script_resource_rejects_absolute_encoded_and_symlink_escapes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases = ("absolute", "encoded", "symlink")
            for name in cases:
                with self.subTest(name=name):
                    case = root / name
                    case.mkdir()
                    book = self.make_book(case)
                    outside = case / "outside.js"
                    marker = f"FDE_SCRIPT_ESCAPE_{name}"
                    outside.write_text(marker, encoding="utf-8")
                    if name == "absolute":
                        target = str(outside)
                    elif name == "encoded":
                        target = "%2e%2e/outside.js"
                    else:
                        (book / "linked.js").symlink_to(outside)
                        target = "linked.js"
                    (book / "a.md").write_text(
                        f'# A\n\n<script src="{target}"></script>\n', encoding="utf-8"
                    )
                    svg = case / "svg"
                    svg.mkdir()
                    output = case / "reader.html"
                    called = case / "pandoc-called"
                    result = self.run_reader(
                        book,
                        svg,
                        output,
                        self.fake_pandoc(case, call_marker=called),
                        "--strict",
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("outside book directory", result.stderr)
                    self.assertFalse(called.exists())
                    rendered = output.read_text(encoding="utf-8") if output.exists() else ""
                    self.assertNotIn(marker, rendered)

    def test_ordinary_links_and_non_resource_link_rel_are_not_embedded_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            book = self.make_book(root)
            (root / "outside.html").write_text("outside", encoding="utf-8")
            (book / "a.md").write_text(
                "# A\n\n[ordinary](../outside.html)\n\n"
                '<a href="../outside.html">ordinary HTML link</a>\n\n'
                '<link rel="canonical" href="../outside.html">\n',
                encoding="utf-8",
            )
            svg = root / "svg"
            svg.mkdir()
            output = root / "reader.html"
            called = root / "pandoc-called"
            result = self.run_reader(
                book,
                svg,
                output,
                self.fake_pandoc(root, call_marker=called),
                "--strict",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(called.is_file())

    def test_output_cannot_overwrite_nested_published_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            book = root / "book"
            nested = book / "nested"
            nested.mkdir(parents=True)
            source = nested / "chapter.md"
            marker = "NESTED_SOURCE_MUST_SURVIVE"
            source.write_text(f"# Chapter\n\n{marker}\n", encoding="utf-8")
            (book / "SUMMARY.md").write_text(
                "* [Chapter](nested/chapter.md)\n", encoding="utf-8"
            )
            svg = root / "svg"
            svg.mkdir()
            result = self.run_reader(
                book, svg, source, self.fake_pandoc(root), "--strict"
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("independent .html", result.stderr)
            self.assertIn(marker, source.read_text(encoding="utf-8"))

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

    def test_strict_renderer_rejects_complete_output_from_nonzero_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            book = self.make_book(root)
            binary, chrome = self.fake_nonzero_after_write_tools(
                root, fail_first_only=False
            )
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
            self.assertIn("renderer reported fatal error", result.stderr)
            self.assertIn("RENDERED 0/1", result.stdout)
            self.assertFalse((output / "d-1.svg").exists())

    def test_renderer_recovers_when_single_diagram_retry_succeeds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            book = self.make_book(root)
            binary, chrome = self.fake_nonzero_after_write_tools(
                root, fail_first_only=True
            )
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
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("renderer reported fatal error", result.stderr)
            self.assertIn("RENDERED 1/1", result.stdout)
            self.assertTrue((output / "d-1.svg").is_file())
            self.assertEqual((root / "mmdc-attempt").read_text(), "2")

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

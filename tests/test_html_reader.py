from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from tools import build_html_reader as reader


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

    def run_reader(
        self,
        book: Path,
        svg: Path,
        output: Path,
        binary: Path,
        *flags: str,
        timeout: float | None = None,
    ):
        env = os.environ.copy()
        env["PATH"] = f"{binary}{os.pathsep}{env['PATH']}"
        return subprocess.run(
            [sys.executable, str(READER), "--book-dir", str(book), "--title", "Test Guide", "--svg-dir", str(svg), "--out", str(output), *flags],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
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

    def test_nested_resources_share_one_validation_and_rewrite_pipeline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            book = root / "book"
            chapter = book / "chapter"
            assets = chapter / "assets"
            assets.mkdir(parents=True)
            source = chapter / "a.md"
            names = (
                "inline.png",
                "reference.png",
                "collapsed.png",
                "shortcut.png",
                "img.png",
                "img-1.png",
                "img-2.png",
                "source.bin",
                "video.bin",
                "poster.png",
                "audio.bin",
                "script.js",
                "object.bin",
                "embed.bin",
                "input.png",
                "frame.html",
                "track.vtt",
                "svg-image.png",
                "svg-use.svg",
                "style.css",
                "inline-style.png",
                "block-style.png",
            )
            for name in names:
                (assets / name).write_text(name, encoding="utf-8")
            body = (
                "![inline](assets/inline.png)\n"
                "![reference][asset]\n\n[asset]: assets/reference.png\n"
                "![collapsed][]\n\n[collapsed]: assets/collapsed.png\n"
                "![shortcut]\n\n[shortcut]: assets/shortcut.png\n"
                '<img src="assets/img.png" srcset="assets/img-1.png 1x, '
                'data:image/png;base64,AAAA 2x, assets/img-2.png 3x">\n'
                '<source src="assets/source.bin">\n'
                '<video src="assets/video.bin" poster="assets/poster.png"></video>\n'
                '<audio src="assets/audio.bin"></audio>\n'
                '<script src="assets/script.js"></script>\n'
                '<object data="assets/object.bin"></object>\n'
                '<embed src="assets/embed.bin">\n'
                '<input type="image" src="assets/input.png">\n'
                '<iframe src="assets/frame.html"></iframe>\n'
                '<track src="assets/track.vtt">\n'
                '<svg><image href="assets/svg-image.png"/>'
                '<use xlink:href="assets/svg-use.svg"></use>'
                '<use href="#local-symbol"></use></svg>\n'
                '<link rel="stylesheet" href="assets/style.css">\n'
                '<div style="background:url(\'assets/inline-style.png\')">x</div>\n'
                '<style>.x{background:url(assets/block-style.png)}</style>\n'
                "[ordinary](../outside.html)\n"
                "[ordinary reference][outside]\n\n[outside]: ../outside.html\n"
                '<a href="../outside.html">ordinary</a>\n'
                '<link rel="canonical" href="../outside.html">\n'
                '<img src="https://example.com/remote.png">\n'
                '<img src="data:image/png;base64,AAAA">\n'
            )
            source.write_text(body, encoding="utf-8")

            rewritten, resources = reader.rewrite_published_resources(book, source, body)

            self.assertEqual(resources, {path.resolve() for path in assets.iterdir()})
            for name in names:
                self.assertIn(f"chapter/assets/{name}", rewritten)
            self.assertIn("data:image/png;base64,AAAA 2x", rewritten)
            self.assertIn("https://example.com/remote.png", rewritten)
            self.assertIn('href="#local-symbol"', rewritten)
            self.assertIn("[ordinary](../outside.html)", rewritten)
            self.assertIn("[outside]: ../outside.html", rewritten)
            self.assertIn('<a href="../outside.html">ordinary</a>', rewritten)
            self.assertIn('<link rel="canonical" href="../outside.html">', rewritten)

    @unittest.skipUnless(shutil.which("pandoc"), "Pandoc is required for integration coverage")
    def test_nested_resource_rewrite_controls_real_pandoc_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            book = root / "book"
            chapter = book / "chapter"
            chapter.mkdir(parents=True)
            (book / "SUMMARY.md").write_text(
                "* [Nested](chapter/a.md)\n", encoding="utf-8"
            )
            (book / "shared.js").write_text("SAFE_BOOK_MARKER", encoding="utf-8")
            (root / "shared.js").write_text("OUTSIDE_BOOK_MARKER", encoding="utf-8")
            (root / "outside.html").write_text("ordinary", encoding="utf-8")
            (chapter / "a.md").write_text(
                "# Nested\n\n"
                '<script src="../shared.js"></script>\n\n'
                "[ordinary](../../outside.html)\n",
                encoding="utf-8",
            )
            svg = root / "svg"
            svg.mkdir()
            output = root / "reader.html"

            result = self.run_reader(
                book,
                svg,
                output,
                Path(shutil.which("pandoc")).parent,
                "--strict",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            html = output.read_text(encoding="utf-8")
            self.assertIn("SAFE_BOOK_MARKER", html)
            self.assertNotIn("OUTSIDE_BOOK_MARKER", html)
            self.assertRegex(html, r'href="\.\./\.\./outside\.html"')

    def test_stylesheet_dependencies_decode_css_escapes_and_recurse(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            book = root / "book"
            chapter = book / "chapter"
            assets = chapter / "assets"
            nested = assets / "nested"
            nested.mkdir(parents=True)
            source = chapter / "a.md"
            stylesheet = assets / "root.css"
            child = nested / "child.css"
            spaced = assets / "safe image.png"
            quoted = assets / 'safe"quote.png'
            apostrophe = assets / "safe'quote.png"
            external_literal_entity = assets / "safe&amp;external.png"
            external_entity_decoy = assets / "safe&external.png"
            block_literal_entity = assets / "safe&amp;block.png"
            block_entity_decoy = assets / "safe&block.png"
            attribute_entity = assets / "safe&attribute.png"
            for path, content in (
                (spaced, "SAFE_SPACE"),
                (quoted, "SAFE_DOUBLE_QUOTE"),
                (apostrophe, "SAFE_SINGLE_QUOTE"),
                (external_literal_entity, "SAFE_EXTERNAL_LITERAL_ENTITY"),
                (external_entity_decoy, "DECOY_EXTERNAL_ENTITY"),
                (block_literal_entity, "SAFE_BLOCK_LITERAL_ENTITY"),
                (block_entity_decoy, "DECOY_BLOCK_ENTITY"),
                (attribute_entity, "SAFE_ATTRIBUTE_ENTITY"),
            ):
                path.write_text(content, encoding="utf-8")
            stylesheet.write_text(
                r'@\69mport url("nested/child\2e css");'
                "\n.root { color: black; }\n",
                encoding="utf-8",
            )
            child.write_text(
                ".a { background: url('../safe\\20 image.png'); }\n"
                ".b { background: url('../safe\\\"quote.png'); }\n"
                '.c { background: url("../safe\\27 quote.png"); }\n'
                '.d { background: url("../safe&amp;external.png"); }\n',
                encoding="utf-8",
            )
            body = (
                '<link rel="stylesheet" href="assets/root.css">\n'
                '<style>.block { background: url("assets/safe&amp;block.png"); }</style>\n'
                '<div style="background: url(\'assets/safe&amp;attribute.png\')">x</div>\n'
            )
            source.write_text(body, encoding="utf-8")

            rewritten, resources = reader.rewrite_published_resources(
                book, source, body
            )

            self.assertIn('href="chapter/assets/root.css"', rewritten)
            self.assertEqual(
                resources,
                {
                    stylesheet.resolve(),
                    child.resolve(),
                    spaced.resolve(),
                    quoted.resolve(),
                    apostrophe.resolve(),
                    external_literal_entity.resolve(),
                    block_literal_entity.resolve(),
                    attribute_entity.resolve(),
                },
            )

    def test_stylesheet_outside_remote_and_inline_imports_fail_before_pandoc(self):
        variants = {
            "outside-url": ".x { background: url(../../../outside.bin); }",
            "outside-import-string": '@import "../../../outside.bin";',
            "outside-import-url": "@import url('../../../outside.bin');",
            "escaped-url-keyword": r".x { background: u\72l(../../../outside.bin); }",
            "escaped-import-keyword": r'@\69mport "../../../outside.bin";',
            "remote-url": ".x { background: url(https://example.com/x.png); }",
            "data-import": '@import url("data:text/css,.x%7Bcolor:red%7D");',
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for name, stylesheet_text in variants.items():
                with self.subTest(name=name):
                    case = root / name
                    case.mkdir()
                    book = self.make_book(case)
                    assets = book / "assets"
                    assets.mkdir()
                    (case / "outside.bin").write_text(
                        f"OUTSIDE_CSS_MARKER_{name}", encoding="utf-8"
                    )
                    (assets / "root.css").write_text(
                        stylesheet_text, encoding="utf-8"
                    )
                    (book / "a.md").write_text(
                        '# A\n\n<link rel="stylesheet" href="assets/root.css">\n',
                        encoding="utf-8",
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
                    self.assertNotEqual(result.returncode, 0, name)
                    self.assertFalse(called.exists(), name)
                    self.assertFalse(output.exists(), name)

            case = root / "inline-import"
            case.mkdir()
            book = self.make_book(case)
            assets = book / "assets"
            assets.mkdir()
            (assets / "safe.css").write_text(
                ".safe { color: green; }", encoding="utf-8"
            )
            (book / "a.md").write_text(
                '# A\n\n<style>@import "assets/safe.css";</style>\n',
                encoding="utf-8",
            )
            svg = case / "svg"
            svg.mkdir()
            called = case / "pandoc-called"
            result = self.run_reader(
                book,
                svg,
                case / "reader.html",
                self.fake_pandoc(case, call_marker=called),
                "--strict",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("inline CSS @import", result.stderr)
            self.assertFalse(called.exists())

            encoded_css = {
                "encoded-url-keyword":
                    '<div style="background:&#117;rl(../outside.bin)">x</div>',
                "encoded-import-keyword":
                    '<div style="@&#105;mport &quot;../outside.bin&quot;;">x</div>',
            }
            for name, body in encoded_css.items():
                with self.subTest(name=name):
                    case = root / name
                    case.mkdir()
                    book = self.make_book(case)
                    (case / "outside.bin").write_text(
                        f"OUTSIDE_CSS_MARKER_{name}", encoding="utf-8"
                    )
                    (book / "a.md").write_text(
                        f"# A\n\n{body}\n", encoding="utf-8"
                    )
                    svg = case / "svg"
                    svg.mkdir()
                    called = case / "pandoc-called"
                    result = self.run_reader(
                        book,
                        svg,
                        case / "reader.html",
                        self.fake_pandoc(case, call_marker=called),
                        "--strict",
                    )
                    self.assertNotEqual(result.returncode, 0, name)
                    self.assertIn("encoded CSS syntax", result.stderr, name)
                    self.assertFalse(called.exists(), name)

    def test_stylesheet_cycle_depth_and_size_limits_fail_before_pandoc(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()

            def run_case(name: str, populate):
                case = root / name
                case.mkdir()
                book = self.make_book(case)
                assets = book / "assets"
                assets.mkdir()
                populate(assets)
                (book / "a.md").write_text(
                    '# A\n\n<link rel="stylesheet" href="assets/0.css">\n',
                    encoding="utf-8",
                )
                svg = case / "svg"
                svg.mkdir()
                called = case / "pandoc-called"
                result = self.run_reader(
                    book,
                    svg,
                    case / "reader.html",
                    self.fake_pandoc(case, call_marker=called),
                    "--strict",
                )
                self.assertNotEqual(result.returncode, 0, name)
                self.assertFalse(called.exists(), name)
                return result

            def cycle(assets: Path):
                (assets / "0.css").write_text(
                    '@import "1.css";', encoding="utf-8"
                )
                (assets / "1.css").write_text(
                    '@import "0.css";', encoding="utf-8"
                )

            def deep(assets: Path):
                for index in range(18):
                    tail = (
                        f'@import "{index + 1}.css";'
                        if index < 17
                        else ".done { color: green; }"
                    )
                    (assets / f"{index}.css").write_text(tail, encoding="utf-8")

            def large(assets: Path):
                (assets / "0.css").write_text(
                    ".x{" + " " * (1024 * 1024) + "}", encoding="utf-8"
                )

            self.assertIn("CSS import cycle", run_case("cycle", cycle).stderr)
            self.assertIn("CSS import depth limit", run_case("depth", deep).stderr)
            self.assertIn("CSS size limit", run_case("size", large).stderr)

    @unittest.skipUnless(shutil.which("pandoc"), "Pandoc is required for integration coverage")
    def test_real_pandoc_embeds_only_recursively_validated_stylesheet_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            book = root / "book"
            chapter = book / "chapter"
            assets = chapter / "assets"
            nested = assets / "nested"
            nested.mkdir(parents=True)
            (book / "SUMMARY.md").write_text(
                "* [Nested CSS](chapter/a.md)\n", encoding="utf-8"
            )
            (chapter / "a.md").write_text(
                '# Nested CSS\n\n<link rel="stylesheet" href="assets/root.css">\n',
                encoding="utf-8",
            )
            (assets / "root.css").write_text(
                '@import "nested/child.css";\n.root { color: black; }\n',
                encoding="utf-8",
            )
            (nested / "child.css").write_text(
                '@import url("leaf.css");\n.child { color: green; }\n',
                encoding="utf-8",
            )
            (nested / "leaf.css").write_text(
                '.safe-marker::before { content: "SAFE_CSS_MARKER"; }\n'
                '.safe-image { background: url("../safe.png"); }\n',
                encoding="utf-8",
            )
            (assets / "safe.png").write_bytes(b"SAFE_IMAGE_MARKER")
            (root / "outside.css").write_text(
                "OUTSIDE_CSS_MARKER", encoding="utf-8"
            )
            svg = root / "svg"
            svg.mkdir()
            output = root / "reader.html"

            result = self.run_reader(
                book,
                svg,
                output,
                Path(shutil.which("pandoc")).parent,
                "--strict",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            rendered = output.read_text(encoding="utf-8")
            self.assertIn("SAFE_CSS_MARKER", rendered)
            self.assertIn("data:image/png;base64", rendered)
            self.assertNotIn("OUTSIDE_CSS_MARKER", rendered)
            self.assertNotRegex(rendered, r"@import\b")

    @unittest.skipUnless(shutil.which("pandoc"), "Pandoc is required for integration coverage")
    def test_real_pandoc_never_receives_unsafe_or_cyclic_css(self):
        variants = {
            "outside-url": (
                '<link rel="stylesheet" href="assets/root.css">',
                {"root.css": ".x { background: url(../../../outside.bin); }"},
            ),
            "outside-import": (
                '<link rel="stylesheet" href="assets/root.css">',
                {"root.css": '@import "../../../outside.bin";'},
            ),
            "inline-import": (
                '<style>@import "../../outside.bin";</style>',
                {},
            ),
            "cycle": (
                '<link rel="stylesheet" href="assets/root.css">',
                {
                    "root.css": '@import "child.css";',
                    "child.css": '@import "root.css";',
                },
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for name, (body, stylesheets) in variants.items():
                with self.subTest(name=name):
                    case = root / name
                    book = case / "book"
                    chapter = book / "chapter"
                    assets = chapter / "assets"
                    assets.mkdir(parents=True)
                    (book / "SUMMARY.md").write_text(
                        "* [A](chapter/a.md)\n", encoding="utf-8"
                    )
                    (chapter / "a.md").write_text(
                        f"# A\n\n{body}\n", encoding="utf-8"
                    )
                    for relative, content in stylesheets.items():
                        (assets / relative).write_text(content, encoding="utf-8")
                    (case / "outside.bin").write_text(
                        f"OUTSIDE_CSS_MARKER_{name}", encoding="utf-8"
                    )
                    svg = case / "svg"
                    svg.mkdir()
                    output = case / "reader.html"

                    result = self.run_reader(
                        book,
                        svg,
                        output,
                        Path(shutil.which("pandoc")).parent,
                        "--strict",
                        timeout=10,
                    )

                    self.assertNotEqual(result.returncode, 0, name)
                    self.assertFalse(output.exists(), name)
                    self.assertNotIn(
                        f"OUTSIDE_CSS_MARKER_{name}",
                        result.stdout + result.stderr,
                        name,
                    )

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

#!/usr/bin/env python3
"""Build a single self-contained, GitBook-style PAGED mobile reader — offline-robust.

Works even where JavaScript is disabled (iOS Files/Quick Look): pages are a readable
scroll by default; JS (Safari, Documents app, etc.) upgrades to one-page-at-a-time.
- Math: pandoc --mathml (native WebKit, no JS)
- Mermaid: PRE-RENDERED to static SVG (no JS, no mermaid.js) — pass --svg-dir
- TOC drawer: CSS checkbox hack (opens without JS); prev/next are static anchors
- Images/CSS embedded (--embed-resources) -> one offline file
"""
import argparse, html as html_lib, os, re, subprocess, sys, posixpath, tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

def esc(s):  return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
def escattr(s): return s.replace("&","&amp;").replace('"',"&quot;").replace("<","&lt;")

def parse_summary(book_dir):
    root = Path(book_dir).resolve()
    items, seen = [], set()
    with (root / "SUMMARY.md").open(encoding="utf-8") as f:
        for line in f:
            m = re.match(r'^##\s+(.+?)\s*$', line)
            if m: items.append(("part", m.group(1))); continue
            m = re.match(r'^(\s*)[-*]\s+\[(.*?)\]\(([^)]+?)\)', line)
            if m:
                indent, title, path = m.group(1), m.group(2).strip(), m.group(3).strip()
                path = path.split("#", 1)[0]
                if not path.endswith(".md"):
                    continue
                source = (root / path).resolve()
                if root not in source.parents:
                    raise ValueError(f"SUMMARY entry escapes book directory: {path}")
                relative = source.relative_to(root).as_posix()
                if relative not in seen and source.is_file():
                    seen.add(relative)
                    items.append(("file", relative, title, min(len(indent.replace("\t","  "))//2, 2)))
    return items

INLINE_IMAGE_RE = re.compile(r'!\[[^\]]*\]\(\s*(<[^>\n]+>|[^\s)\n]+)')
REFERENCE_DEFINITION_RE = re.compile(
    r'^\s{0,3}\[([^\]]+)\]:\s*(<[^>\n]+>|[^\s]+)', re.MULTILINE
)
REFERENCE_IMAGE_RE = re.compile(r'!\[([^\]]*)\]\[([^\]]*)\]')
SHORTCUT_IMAGE_RE = re.compile(r'!\[([^\]]+)\](?![\[(])')
CSS_URL_RE = re.compile(
    r'''url\(\s*(?:(?P<quote>["'])(?P<quoted>.*?)(?P=quote)|(?P<bare>[^)]*))\s*\)''',
    re.I | re.S,
)
HTML_RESOURCE_ATTRIBUTES = {
    "img": {"src", "srcset"},
    "source": {"src", "srcset"},
    "video": {"src", "poster"},
    "audio": {"src"},
    "script": {"src"},
    "object": {"data"},
    "embed": {"src"},
    "input": {"src"},
    "iframe": {"src"},
    "track": {"src"},
    "image": {"href", "xlink:href"},
    "use": {"href", "xlink:href"},
}
RESOURCE_LINK_RELS = {
    "stylesheet",
    "icon",
    "apple-touch-icon",
    "mask-icon",
    "manifest",
    "preload",
    "modulepreload",
    "prefetch",
}

def normalize_reference_label(label):
    return " ".join(label.split()).casefold()

def css_resource_targets(value):
    for match in CSS_URL_RE.finditer(value):
        target = match.group("quoted") if match.group("quote") else match.group("bare")
        if target and target.strip():
            yield target.strip()

def srcset_resource_targets(value):
    """Yield srcset URLs without splitting the comma inside a data URI."""
    position, length = 0, len(value)
    while position < length:
        while position < length and (value[position].isspace() or value[position] == ","):
            position += 1
        if position >= length:
            return
        start = position
        is_data = value[position : position + 5].casefold() == "data:"
        while position < length and not value[position].isspace() and (
            is_data or value[position] != ","
        ):
            position += 1
        target = value[start:position]
        ended_with_separator = target.endswith(",")
        target = target.rstrip(",")
        if target:
            yield target
        if ended_with_separator:
            continue
        depth = 0
        while position < length:
            char = value[position]
            if char == "(":
                depth += 1
            elif char == ")" and depth:
                depth -= 1
            elif char == "," and depth == 0:
                position += 1
                break
            position += 1

class HTMLResourceTargetParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.targets = []
        self.style_depth = 0

    def handle_starttag(self, tag, attrs):
        self._handle_tag(tag, attrs)
        if tag.casefold() == "style":
            self.style_depth += 1

    def handle_startendtag(self, tag, attrs):
        self._handle_tag(tag, attrs)

    def handle_endtag(self, tag):
        if tag.casefold() == "style" and self.style_depth:
            self.style_depth -= 1

    def handle_data(self, data):
        if self.style_depth:
            self.targets.extend(css_resource_targets(data))

    def _handle_tag(self, tag, attrs):
        tag = tag.casefold()
        normalized = [
            (name.casefold(), value)
            for name, value in attrs
            if name and value is not None
        ]
        for name, value in normalized:
            if name == "style":
                self.targets.extend(css_resource_targets(value))

        allowed = HTML_RESOURCE_ATTRIBUTES.get(tag, set())
        if tag == "link":
            rels = {
                token.casefold()
                for name, value in normalized
                if name == "rel"
                for token in value.split()
            }
            allowed = {"href"} if rels & RESOURCE_LINK_RELS else set()
        for name, value in normalized:
            if name not in allowed:
                continue
            if name == "srcset":
                self.targets.extend(srcset_resource_targets(value))
            else:
                self.targets.append(value)

def markdown_resource_targets(text):
    for match in INLINE_IMAGE_RE.finditer(text):
        yield match.group(1)

    definitions = {
        normalize_reference_label(match.group(1)): match.group(2)
        for match in REFERENCE_DEFINITION_RE.finditer(text)
    }
    for match in REFERENCE_IMAGE_RE.finditer(text):
        label = match.group(2) or match.group(1)
        target = definitions.get(normalize_reference_label(label))
        if target:
            yield target
    for match in SHORTCUT_IMAGE_RE.finditer(text):
        target = definitions.get(normalize_reference_label(match.group(1)))
        if target:
            yield target

    parser = HTMLResourceTargetParser()
    parser.feed(text)
    parser.close()
    yield from parser.targets

def resolve_local_resource(book_dir, source, raw_target):
    target = html_lib.unescape(raw_target.strip())
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if not target or target.startswith("#"):
        return None
    parsed = urlsplit(target)
    scheme = parsed.scheme.lower()
    if scheme in {"http", "https", "data"}:
        return None
    if scheme or parsed.netloc:
        raise ValueError(f"unsupported resource URI in {source.relative_to(book_dir)}: {raw_target}")
    resource_path = Path(unquote(parsed.path).replace("\\", "/"))
    if resource_path.is_absolute():
        raise ValueError(
            f"local resource outside book directory in {source.relative_to(book_dir)}: {raw_target}"
        )
    resource = (source.parent / resource_path).resolve()
    if resource != book_dir and book_dir not in resource.parents:
        raise ValueError(
            f"local resource outside book directory in {source.relative_to(book_dir)}: {raw_target}"
        )
    if not resource.is_file():
        raise ValueError(
            f"missing local resource in {source.relative_to(book_dir)}: {raw_target}"
        )
    return resource

def validate_published_resources(book_dir, items):
    resources = set()
    for item in items:
        if item[0] != "file":
            continue
        source = (book_dir / item[1]).resolve()
        text = source.read_text(encoding="utf-8")
        for target in markdown_resource_targets(text):
            resource = resolve_local_resource(book_dir, source, target)
            if resource:
                resources.add(resource)
    return resources

def fix_inline_dollar(text):
    def repl(m):
        s, e = m.start(), m.end(); inner = m.group(1)
        if "\n" in inner: return m.group(0)
        ls = text.rfind("\n", 0, s) + 1
        le = text.find("\n", e); le = len(text) if le < 0 else le
        if text[ls:s].strip() == "" and text[e:le].strip() == "": return m.group(0)
        return "$" + inner.strip() + "$"
    return re.sub(r'\$\$(.+?)\$\$', repl, text, flags=re.DOTALL)

def process_file(text, reldir, mermaid_store, path_to_id):
    def grab(m):
        idx = len(mermaid_store); mermaid_store.append(m.group(1))
        return f"\n\nMERMAIDZZ{idx}ZZ\n\n"
    text = re.sub(r'```mermaid[ \t]*\n(.*?)\n[ \t]*```', grab, text, flags=re.DOTALL)
    text = fix_inline_dollar(text)
    text = re.sub(r'\[!\[[^\]]*\]\(https?://[^)]*\)\]\([^)]*\)', '', text)
    text = re.sub(r'!\[[^\]]*\]\(https?://[^)]*\)', '', text)
    text = re.sub(r'^\s*\[\]\([^)]*\)\s*$', '', text, flags=re.M)
    def md_img(m):
        alt, url = m.group(1), m.group(2).strip()
        if url.startswith(("http://","https://","/","data:")): return m.group(0)
        return f"![{alt}]({posixpath.normpath(posixpath.join(reldir, url))})"
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', md_img, text)
    def html_img(m):
        src = m.group(1)
        if src.startswith(("http://","https://","/","data:")): return m.group(0)
        return m.group(0).replace(f'src="{src}"', f'src="{posixpath.normpath(posixpath.join(reldir, src))}"')
    text = re.sub(r'<img\s+[^>]*src="([^"]+)"[^>]*>', html_img, text)
    def md_link(m):
        label, target = m.group(1), m.group(2).strip()
        if "#" in target: target = target.split("#", 1)[0]
        if not target.endswith(".md"): return m.group(0)
        pid = path_to_id.get(posixpath.normpath(posixpath.join(reldir, target)))
        return f"[{label}](#{pid})" if pid else m.group(0)
    text = re.sub(r'(?<!\!)\[([^\]]*)\]\(([^)]+?\.md(?:#[^)]*)?)\)', md_link, text)
    return text

TEMPLATE = r'''<!DOCTYPE html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="$title$">
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0d1117" media="(prefers-color-scheme: dark)">
<title>$title$</title>
<style>
:root{--bg:#fdfdfb;--fg:#1f2328;--muted:#656d76;--link:#0969da;--border:#d8dee4;--code-bg:#eef0ee;--pre-bg:#f6f8fa;--accent:#8250df;--bar:#ffffffe6;--sb:#f7f7f5}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--muted:#9198a1;--link:#4493f8;--border:#30363d;--code-bg:#1c2128;--pre-bg:#161b22;--accent:#bc8cff;--bar:#0d1117e6;--sb:#10141a}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--fg);font-family:-apple-system,BlinkMacSystemFont,"SF Pro SC","PingFang SC","Hiragino Sans GB","Microsoft YaHei",system-ui,sans-serif;font-size:17px;line-height:1.8;letter-spacing:.01em;text-rendering:optimizeLegibility;-webkit-font-smoothing:antialiased}
a{color:var(--link);text-decoration:none}a:active{opacity:.6}
.nav-toggle{position:absolute;opacity:0;pointer-events:none}
.topbar{position:sticky;top:0;z-index:30;display:flex;align-items:center;gap:.6rem;padding:.5rem .8rem;padding-top:max(.5rem,env(safe-area-inset-top));background:var(--bar);backdrop-filter:saturate(180%) blur(12px);-webkit-backdrop-filter:saturate(180%) blur(12px);border-bottom:1px solid var(--border)}
#tocBtn{font-size:1.3rem;color:var(--fg);padding:.1rem .4rem;cursor:pointer;line-height:1;user-select:none}
#crumb{font-size:.95rem;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:1}
#prog{font-size:.8rem;color:var(--muted);white-space:nowrap}
#content{max-width:44rem;margin:0 auto;padding:1rem 1.1rem 2rem}
/* default = readable scroll (works with NO JavaScript). JS upgrades to paged. */
body.js .page{display:none}
body.js .page.active{display:block;animation:fade .2s ease}
body.js .page:not(.active) .pn-wrap{display:none}
@keyframes fade{from{opacity:.4}to{opacity:1}}
h1,h2,h3,h4{line-height:1.35;font-weight:700;scroll-margin-top:4rem}
h1{font-size:1.6rem;margin:1rem 0 1rem;padding-bottom:.4rem;border-bottom:2px solid var(--border)}
h2{font-size:1.32rem;margin:1.8rem 0 .9rem}h3{font-size:1.12rem;margin:1.5rem 0 .7rem}h4{font-size:1rem;color:var(--muted);margin:1.2rem 0 .6rem}
p{margin:.9rem 0}
code{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;font-size:.88em}
:not(pre)>code{background:var(--code-bg);padding:.15em .4em;border-radius:6px;word-break:break-word}
pre{background:var(--pre-bg);border:1px solid var(--border);border-radius:10px;padding:.9rem 1rem;overflow-x:auto;line-height:1.5;font-size:.84rem;-webkit-overflow-scrolling:touch}
pre code{background:none;padding:0;font-size:inherit}
.diagram{text-align:center;margin:1.3rem 0;overflow-x:auto;-webkit-overflow-scrolling:touch}
.diagram svg{max-width:100%;height:auto}
.diagram-fallback{display:block;text-align:left;white-space:pre;overflow-x:auto;background:var(--pre-bg);border:1px dashed var(--border);border-radius:10px;padding:.9rem 1rem;font-size:.8rem;color:var(--muted)}
math{font-size:1.02em}
math[display="block"]{display:block;overflow-x:auto;overflow-y:hidden;max-width:100%;padding:.4rem 0;-webkit-overflow-scrolling:touch}
#content table{display:block;width:max-content;max-width:100%;overflow-x:auto;border-collapse:collapse;font-size:.9rem;margin:1rem 0;-webkit-overflow-scrolling:touch}
th,td{border:1px solid var(--border);padding:.5rem .7rem;text-align:left}th{background:var(--pre-bg);font-weight:600}
img{max-width:100%;height:auto;display:block;margin:1rem auto;border-radius:8px}
blockquote{margin:1rem 0;padding:.3rem 1rem;border-left:4px solid var(--accent);color:var(--muted);background:var(--pre-bg);border-radius:0 8px 8px 0}
hr{border:none;border-top:1px solid var(--border);margin:2rem 0}
ul,ol{padding-left:1.4rem}li{margin:.3rem 0}
.pn-wrap{display:flex;gap:.6rem;margin:2.5rem 0 1rem;border-top:1px solid var(--border);padding-top:1.2rem}
.pn{flex:1;display:flex;flex-direction:column;gap:.2rem;padding:.7rem .9rem;border:1px solid var(--border);border-radius:12px;background:var(--pre-bg);min-width:0}
.pn-next{text-align:right}.pn-empty{visibility:hidden;border:none;background:none}
.pn-dir{font-size:.75rem;color:var(--muted)}
.pn-t{font-size:.9rem;font-weight:600;color:var(--fg);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#sidebar{position:fixed;top:0;left:0;z-index:50;width:84%;max-width:340px;height:100%;background:var(--sb);border-right:1px solid var(--border);overflow-y:auto;transform:translateX(-102%);transition:transform .26s ease;padding-bottom:3rem;-webkit-overflow-scrolling:touch;box-shadow:2px 0 24px #00000022}
.nav-toggle:checked ~ #sidebar{transform:none}
.toc-head{font-weight:700;font-size:1.1rem;padding:max(1rem,env(safe-area-inset-top)) 1.2rem 1rem;border-bottom:1px solid var(--border);position:sticky;top:0;background:var(--sb)}
#sidebar ul{list-style:none;padding:0;margin:.4rem 0}
.toc-part{font-size:.78rem;font-weight:700;color:var(--muted);padding:1rem 1.2rem .3rem;margin-top:.3rem}
.toc-link a{display:block;padding:.4rem 1.2rem;color:var(--fg);font-size:.92rem;line-height:1.4;border-left:3px solid transparent}
.toc-link.lvl1 a{padding-left:2rem;color:var(--muted);font-size:.88rem}
.toc-link.lvl2 a{padding-left:2.8rem;color:var(--muted);font-size:.85rem}
.toc-link a.active{color:var(--accent);border-left-color:var(--accent);background:var(--pre-bg);font-weight:700}
#backdrop{position:fixed;inset:0;z-index:40;background:#00000055;opacity:0;visibility:hidden;transition:opacity .26s}
.nav-toggle:checked ~ #backdrop{opacity:1;visibility:visible}
@media (min-width:1024px){
 #sidebar{transform:none;box-shadow:none}#tocBtn{display:none}#backdrop{display:none}
 .topbar{padding-left:calc(340px + .8rem)}#content{margin-left:340px}
}
</style>
</head>
<body>
<input type="checkbox" id="navToggle" class="nav-toggle">
<header class="topbar"><label for="navToggle" id="tocBtn" aria-label="目录">&#9776;</label><span id="crumb">$title$</span><span id="prog"></span></header>
<label for="navToggle" id="backdrop"></label>
<aside id="sidebar"><!--SIDEBAR--></aside>
<main id="content">
$body$
</main>
<script>
(function(){
 document.body.classList.add('js');
 var pages=[].slice.call(document.querySelectorAll('.page'));
 if(!pages.length)return;
 var order=pages.map(function(p){return p.id});
 var titleById={}; pages.forEach(function(p){titleById[p.id]=p.getAttribute('data-title')||p.id});
 var sb=document.getElementById('sidebar'),crumb=document.getElementById('crumb'),prog=document.getElementById('prog'),toggle=document.getElementById('navToggle');
 function curId(){var a=document.querySelector('.page.active');return a?a.id:order[0]}
 function setToc(id){var ls=sb.querySelectorAll('a[data-target]');for(var i=0;i<ls.length;i++){var on=ls[i].getAttribute('data-target')===id;ls[i].classList.toggle('active',on);if(on)ls[i].scrollIntoView({block:'nearest'})}}
 function show(id){var i=order.indexOf(id);if(i<0){i=0;id=order[0]}for(var k=0;k<pages.length;k++)pages[k].classList.toggle('active',pages[k].id===id);crumb.textContent=titleById[id];prog.textContent=(i+1)+' / '+order.length;setToc(id);if(toggle)toggle.checked=false;var de=document.documentElement,sbv=de.style.scrollBehavior;de.style.scrollBehavior='auto';window.scrollTo(0,0);de.style.scrollBehavior=sbv;if(location.hash!=='#'+id)history.replaceState(null,'','#'+id)}
 document.addEventListener('click',function(e){var a=e.target.closest('a[href^="#"]');if(a){var id=a.getAttribute('href').slice(1);if(titleById[id]){e.preventDefault();show(id)}}});
 window.addEventListener('keydown',function(e){if(e.target.tagName==='INPUT')return;if(e.key==='ArrowRight'){var i=order.indexOf(curId());if(i<order.length-1)show(order[i+1])}else if(e.key==='ArrowLeft'){var j=order.indexOf(curId());if(j>0)show(order[j-1])}});
 window.addEventListener('hashchange',function(){var id=location.hash.slice(1);if(id&&titleById[id]&&id!==curId())show(id)});
 var h=location.hash.slice(1);show(h&&titleById[h]?h:order[0]);
})();
</script>
</body>
</html>
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book-dir", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--svg-dir", required=True, help="dir with pre-rendered d-1.svg .. d-N.svg")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--strict", dest="strict", action="store_true", default=True)
    mode.add_argument("--allow-fallback", dest="strict", action="store_false")
    a = ap.parse_args()
    book_dir = Path(a.book_dir).resolve()
    raw_out_path = Path(a.out).expanduser()
    out_path = raw_out_path.resolve()
    svg_dir = Path(a.svg_dir).resolve()

    if not book_dir.is_dir():
        raise ValueError(f"book directory does not exist: {book_dir}")
    if raw_out_path.suffix.lower() != ".html" or out_path.suffix.lower() != ".html":
        raise ValueError("output must be an independent .html file")
    if out_path.is_dir():
        raise ValueError("output must be an independent .html file")
    markdown_sources = {path.resolve() for path in book_dir.rglob("*.md")}
    if out_path in markdown_sources:
        raise ValueError(f"output path would overwrite book source: {out_path}")

    items = parse_summary(book_dir)
    if not any(item[0] == "file" for item in items):
        raise ValueError("SUMMARY.md contains no readable Markdown entries")
    resources = validate_published_resources(book_dir, items)
    published_sources = {
        (book_dir / item[1]).resolve() for item in items if item[0] == "file"
    }
    if out_path in published_sources | resources:
        raise ValueError(f"output path would overwrite published input: {out_path}")
    page_meta, path_to_id, pidc = [], {}, 0
    for it in items:
        if it[0] == "file":
            _, path, title, lvl = it
            page_meta.append((f"p{pidc}", path, title, lvl))
            path_to_id[posixpath.normpath(path)] = f"p{pidc}"; pidc += 1
    id_to_title = {pi: ti for (pi, _, ti, _) in page_meta}

    mermaid_store, chunks, pi = [], [], 0
    for it in items:
        if it[0] != "file": continue
        _, path, title, lvl = it
        with (book_dir / path).open(encoding="utf-8") as f: txt = f.read()
        txt = process_file(txt, posixpath.dirname(path), mermaid_store, path_to_id)
        chunks.append(f'\n\nPGBKZZp{pi}ZZ\n\n{txt}\n\n'); pi += 1
    combined = "\n".join(chunks)
    print(f"  pages: {len(page_meta)}, mermaid blocks: {len(mermaid_store)}")

    # Load pre-rendered SVGs and namespace ids. Strict mode rejects every miss.
    svgs, missing = [], 0
    for i in range(len(mermaid_store)):
        p = svg_dir / f"d-{i+1}.svg"
        if p.is_file() and p.stat().st_size > 0:
            s = p.read_text(encoding="utf-8")
            j = s.find("<svg"); s = s[j:] if j > 0 else s
            if "<svg" not in s:
                missing += 1
                svgs.append('<pre class="diagram-fallback">' + esc(mermaid_store[i]) + '</pre>')
                continue
            s = s.replace("my-svg", f"mmd{i}")
            svgs.append(s)
        else:
            missing += 1
            svgs.append('<pre class="diagram-fallback">' + esc(mermaid_store[i]) + '</pre>')
    if missing and a.strict:
        raise ValueError(f"missing Mermaid SVGs: {missing}/{len(mermaid_store)}")
    if missing:
        print(f"  WARNING: {missing}/{len(mermaid_store)} diagrams failed to render -> showing source as fallback")

    # sidebar TOC
    sb = ['<div class="toc-head">目录</div><ul>']; fi = 0
    for it in items:
        if it[0] == "part": sb.append(f'<li class="toc-part">{esc(it[1])}</li>')
        else:
            pidi, _, title, lvl = page_meta[fi]; fi += 1
            sb.append(f'<li class="toc-link lvl{lvl}"><a data-target="{pidi}" href="#{pidi}">{esc(title)}</a></li>')
    sb.append('</ul>'); sidebar_html = "".join(sb)

    with tempfile.TemporaryDirectory(prefix="fde-reader-") as directory:
        temporary = Path(directory)
        tmp_md = temporary / "combined.md"
        tpl = temporary / "template.html"
        out_tmp = temporary / "reader.html"
        tmp_md.write_text(combined, encoding="utf-8")
        tpl.write_text(TEMPLATE, encoding="utf-8")
        cmd = ["pandoc", str(tmp_md), "-f", "markdown", "-t", "html5",
               "--standalone", "--embed-resources", "--mathml",
               "--resource-path", str(book_dir),
               "--template", str(tpl), "--metadata", f"title={a.title}", "-o", str(out_tmp)]
        print("  running pandoc ...")
        r = subprocess.run(cmd, cwd=book_dir, capture_output=True, text=True, check=False)
        if r.returncode != 0:
            raise RuntimeError(f"PANDOC FAILED: {(r.stderr or r.stdout)[:4000]}")
        html = out_tmp.read_text(encoding="utf-8")
    # swap mermaid placeholders -> pre-rendered inline SVG (2nd pass catches any not in <p>)
    def mrepl(m): return f'<figure class="diagram">{svgs[int(m.group(1))]}</figure>'
    html = re.sub(r'<p>\s*MERMAIDZZ(\d+)ZZ\s*</p>', mrepl, html)
    html = re.sub(r'MERMAIDZZ(\d+)ZZ', mrepl, html)
    # split <main> into pages, append static prev/next nav per page
    mm = re.search(r'(<main id="content">)(.*?)(</main>)', html, flags=re.DOTALL)
    if not mm:
        raise RuntimeError("Pandoc output has no <main id=\"content\"> container")
    segs = re.split(r'<p>\s*PGBKZZ(p\d+)ZZ\s*</p>', mm.group(2))
    def navhtml(i):
        out = ['<nav class="pn-wrap">']
        if i > 0:
            pid, _, pt, _ = page_meta[i-1]
            out.append(f'<a class="pn pn-prev" href="#{pid}"><span class="pn-dir">&#8592; 上一页</span><span class="pn-t">{esc(pt)}</span></a>')
        else: out.append('<span class="pn pn-empty"></span>')
        if i < len(page_meta)-1:
            nid, _, nt, _ = page_meta[i+1]
            out.append(f'<a class="pn pn-next" href="#{nid}"><span class="pn-dir">下一页 &#8594;</span><span class="pn-t">{esc(nt)}</span></a>')
        out.append('</nav>'); return "".join(out)
    pages_html = []
    for k in range(1, len(segs), 2):
        pid, seg = segs[k], segs[k+1]
        idx = [pm[0] for pm in page_meta].index(pid)
        pages_html.append(f'<section class="page" id="{pid}" data-title="{escattr(id_to_title[pid])}">{seg}{navhtml(idx)}</section>')
    new_main = mm.group(1) + '<div id="pages">' + "".join(pages_html) + '</div>' + mm.group(3)
    html = html[:mm.start()] + new_main + html[mm.end():]
    html = html.replace("<!--SIDEBAR-->", sidebar_html)

    leftover = len(re.findall(r'MERMAIDZZ\d+ZZ|PGBKZZ', html))
    n_svg = html.count('class="diagram"')
    if leftover or len(pages_html) != len(page_meta) or (a.strict and n_svg != len(mermaid_store)):
        raise RuntimeError(
            f"reader completeness failure: pages={len(pages_html)}/{len(page_meta)}, "
            f"Mermaid={n_svg}/{len(mermaid_store)}, placeholders={leftover}"
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    size = out_path.stat().st_size / 1048576
    n_math = html.count('<math'); n_img = html.count('data:image')
    print(f"  pages: {len(pages_html)} | inline svg: {n_svg} | <math>: {n_math} | images: {n_img} | leftover: {leftover}")
    print(f"  OUTPUT: {out_path}  ({size:.2f} MB)")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"HTML reader build failed: {error}", file=sys.stderr)
        raise SystemExit(1)

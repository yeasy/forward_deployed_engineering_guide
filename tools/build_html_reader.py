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
from dataclasses import dataclass
from html.entities import html5 as HTML5_ENTITIES
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

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
CSS_MAX_IMPORT_DEPTH = 16
CSS_MAX_FILE_BYTES = 1024 * 1024
CSS_MAX_TOTAL_BYTES = 4 * 1024 * 1024
CSS_MAX_FILES = 256

@dataclass(frozen=True)
class ResourceToken:
    start: int
    end: int
    target: str
    kind: str = "resource"
    context: str = "plain"
    quote: str = ""
    container_quote: str = ""

@dataclass(frozen=True)
class HTMLAttribute:
    name: str
    start: int
    end: int
    value: str
    quote: str = ""

@dataclass(frozen=True)
class SrcsetCandidate:
    start: int
    end: int
    target_start: int
    target_end: int
    target: str
    descriptors: str

def normalize_reference_label(label):
    return " ".join(label.split()).casefold()

def css_name_char(char):
    return char.isalnum() or char in "_-" or ord(char) >= 128

def css_skip_space_and_comments(value, position):
    length = len(value)
    while position < length:
        if value[position].isspace():
            position += 1
        elif value.startswith("/*", position):
            end = value.find("*/", position + 2)
            position = length if end < 0 else end + 2
        else:
            break
    return position

def css_escape_end(value, position):
    """Return the first position after one CSS escape starting at backslash."""
    position += 1
    if position >= len(value):
        return position
    if value[position] in "\r\n\f":
        if value[position] == "\r" and position + 1 < len(value) and value[position + 1] == "\n":
            position += 1
        return position + 1
    match = re.match(r"[0-9a-fA-F]{1,6}", value[position:])
    if match:
        position += len(match.group(0))
        if position < len(value) and value[position].isspace():
            if value[position] == "\r" and position + 1 < len(value) and value[position + 1] == "\n":
                position += 1
            position += 1
        return position
    return position + 1

def css_identifier_end(value, position):
    while position < len(value):
        if css_name_char(value[position]):
            position += 1
        elif value[position] == "\\":
            position = css_escape_end(value, position)
        else:
            break
    return position

def css_string_span(value, position):
    """Return (content_start, content_end, next_position) for a CSS string."""
    quote_char = value[position]
    position += 1
    start = position
    while position < len(value):
        char = value[position]
        if char == "\\":
            position = css_escape_end(value, position)
        elif char == quote_char:
            return start, position, position + 1
        elif char in "\r\n\f":
            raise ValueError("unterminated CSS string")
        else:
            position += 1
    raise ValueError("unterminated CSS string")

def css_url_token(value, position, offset, kind):
    name_end = css_identifier_end(value, position)
    if name_end == position or css_unescape(value[position:name_end]).casefold() != "url":
        return None
    if position and css_name_char(value[position - 1]):
        return None
    cursor = css_skip_space_and_comments(value, name_end)
    if cursor >= len(value) or value[cursor] != "(":
        return None
    cursor = css_skip_space_and_comments(value, cursor + 1)
    if cursor >= len(value):
        raise ValueError("unterminated CSS url()")
    if value[cursor] in "\"'":
        quote_char = value[cursor]
        start, end, cursor = css_string_span(value, cursor)
        cursor = css_skip_space_and_comments(value, cursor)
        if cursor >= len(value) or value[cursor] != ")":
            raise ValueError("unterminated CSS url()")
        return ResourceToken(
            offset + start,
            offset + end,
            value[start:end],
            kind,
            "css",
            quote_char,
        ), cursor + 1

    start = cursor
    while cursor < len(value):
        char = value[cursor]
        if char == "\\":
            cursor = css_escape_end(value, cursor)
        elif char == ")":
            end = cursor
            while end > start and value[end - 1].isspace():
                end -= 1
            return ResourceToken(
                offset + start,
                offset + end,
                value[start:end],
                kind,
                "css",
            ), cursor + 1
        elif char in "\"'(":
            raise ValueError("invalid unquoted CSS url()")
        else:
            cursor += 1
    raise ValueError("unterminated CSS url()")

def css_resource_tokens(value, offset=0):
    """Yield positioned CSS url() and @import targets, honoring strings/escapes."""
    position = 0
    while position < len(value):
        if value.startswith("/*", position):
            position = css_skip_space_and_comments(value, position)
            continue
        if value[position] in "\"'":
            _, _, position = css_string_span(value, position)
            continue
        import_end = (
            css_identifier_end(value, position + 1)
            if value[position] == "@"
            else position
        )
        is_import = (
            import_end > position + 1
            and css_unescape(value[position + 1 : import_end]).casefold() == "import"
        )
        if is_import:
            cursor = css_skip_space_and_comments(value, import_end)
            if cursor < len(value) and value[cursor] in "\"'":
                start, end, position = css_string_span(value, cursor)
                yield ResourceToken(
                    offset + start,
                    offset + end,
                    value[start:end],
                    "css-import",
                    "css",
                    value[cursor],
                )
                continue
            parsed = css_url_token(value, cursor, offset, "css-import")
            if parsed:
                token, position = parsed
                yield token
                continue
            raise ValueError("CSS @import requires a quoted string or url()")
        parsed = css_url_token(value, position, offset, "css-url")
        if parsed:
            token, position = parsed
            yield token
            continue
        position += 1

def css_unescape(value):
    """Decode CSS escapes in a resource token before URL/path resolution."""
    output = []
    position = 0
    while position < len(value):
        if value[position] != "\\":
            output.append(value[position])
            position += 1
            continue
        position += 1
        if position >= len(value):
            break
        if value[position] in "\r\n\f":
            if value[position] == "\r" and position + 1 < len(value) and value[position + 1] == "\n":
                position += 1
            position += 1
            continue
        match = re.match(r"[0-9a-fA-F]{1,6}", value[position:])
        if match:
            codepoint = int(match.group(0), 16)
            position += len(match.group(0))
            if position < len(value) and value[position].isspace():
                if value[position] == "\r" and position + 1 < len(value) and value[position + 1] == "\n":
                    position += 1
                position += 1
            if codepoint == 0 or codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
                output.append("\N{REPLACEMENT CHARACTER}")
            else:
                output.append(chr(codepoint))
            continue
        output.append(value[position])
        position += 1
    return "".join(output)

def html_unescape_with_spans(value):
    """Decode HTML entities while mapping each decoded character to raw input."""
    output = []
    spans = []
    position = 0
    max_entity_length = max(map(len, HTML5_ENTITIES))
    while position < len(value):
        decoded = None
        end = position + 1
        if value.startswith("&#", position):
            match = re.match(r"&#(?:[xX][0-9a-fA-F]+|[0-9]+);?", value[position:])
            if match:
                end = position + len(match.group(0))
                decoded = html_lib.unescape(value[position:end])
        elif value[position] == "&":
            tail = value[position + 1 : position + 1 + max_entity_length]
            for length in range(len(tail), 0, -1):
                key = tail[:length]
                if key in HTML5_ENTITIES:
                    end = position + 1 + length
                    decoded = HTML5_ENTITIES[key]
                    break
        if decoded is None:
            decoded = value[position]
        output.append(decoded)
        spans.extend([(position, end)] * len(decoded))
        position = end
    text = "".join(output)
    if text != html_lib.unescape(value):
        raise ValueError("unsupported HTML entity form in style attribute")
    return text, spans

def decoded_span_in_raw(spans, start, end, raw_length):
    if start == end:
        boundary = spans[start][0] if start < len(spans) else raw_length
        return boundary, boundary
    return spans[start][0], spans[end - 1][1]

def html_style_resource_tokens(value, offset=0, container_quote=""):
    """Parse style attributes without allowing entities to hide CSS syntax."""
    tokens = list(css_resource_tokens(value))
    decoded, spans = html_unescape_with_spans(value)
    decoded_tokens = list(css_resource_tokens(decoded))
    if len(tokens) != len(decoded_tokens):
        raise ValueError(
            "encoded CSS syntax is not allowed: encoded CSS token structure "
            "changed in style attribute"
        )
    for token, decoded_token in zip(tokens, decoded_tokens):
        mapped_span = decoded_span_in_raw(
            spans, decoded_token.start, decoded_token.end, len(value)
        )
        raw_target = css_unescape(html_lib.unescape(token.target))
        decoded_target = css_unescape(decoded_token.target)
        if (
            token.kind != decoded_token.kind
            or (token.start, token.end) != mapped_span
            or raw_target != decoded_target
        ):
            raise ValueError(
                "encoded CSS syntax is not allowed: encoded CSS token structure "
                "changed in style attribute"
            )
    return [
        ResourceToken(
            offset + token.start,
            offset + token.end,
            token.target,
            f"html-{token.kind}",
            "html-css",
            token.quote,
            container_quote,
        )
        for token in tokens
    ]

def srcset_candidates(value):
    """Parse positioned srcset candidates without splitting a data URI comma."""
    position, length = 0, len(value)
    while position < length:
        while position < length and (value[position].isspace() or value[position] == ","):
            position += 1
        if position >= length:
            return
        candidate_start = position
        target_start = position
        is_data = value[position : position + 5].casefold() == "data:"
        while position < length and not value[position].isspace() and (
            is_data or value[position] != ","
        ):
            position += 1
        target_end = position
        descriptor_start = position
        depth = 0
        while position < length:
            char = value[position]
            if char == "(":
                depth += 1
            elif char == ")" and depth:
                depth -= 1
            elif char == "," and depth == 0:
                candidate_end = position
                position += 1
                break
            position += 1
        else:
            candidate_end = length
        yield SrcsetCandidate(
            candidate_start,
            candidate_end,
            target_start,
            target_end,
            value[target_start:target_end],
            value[descriptor_start:candidate_end],
        )

def srcset_resource_tokens(value, offset=0):
    """Yield positioned URLs from already validated srcset candidate syntax."""
    for candidate in srcset_candidates(value):
        yield ResourceToken(
            offset + candidate.target_start,
            offset + candidate.target_end,
            candidate.target,
            context="srcset",
        )

def normalized_srcset_descriptors(value):
    return tuple(value.split())

def html_srcset_resource_tokens(value, offset=0, container_quote=""):
    """Reject HTML entities that change srcset candidate identity or boundaries."""
    candidates = list(srcset_candidates(value))
    decoded, spans = html_unescape_with_spans(value)
    decoded_candidates = list(srcset_candidates(decoded))
    if len(candidates) != len(decoded_candidates):
        raise ValueError(
            "encoded srcset syntax is not allowed: encoded srcset candidate "
            "identity changed"
        )
    for candidate, decoded_candidate in zip(candidates, decoded_candidates):
        target_span = decoded_span_in_raw(
            spans,
            decoded_candidate.target_start,
            decoded_candidate.target_end,
            len(value),
        )
        candidate_span = decoded_span_in_raw(
            spans,
            decoded_candidate.start,
            decoded_candidate.end,
            len(value),
        )
        if (
            (candidate.target_start, candidate.target_end) != target_span
            or (candidate.start, candidate.end) != candidate_span
            or html_lib.unescape(candidate.target) != decoded_candidate.target
            or normalized_srcset_descriptors(html_lib.unescape(candidate.descriptors))
            != normalized_srcset_descriptors(decoded_candidate.descriptors)
        ):
            raise ValueError(
                "encoded srcset syntax is not allowed: encoded srcset candidate "
                "identity changed"
            )
    return [
        ResourceToken(
            offset + candidate.target_start,
            offset + candidate.target_end,
            candidate.target,
            context="html-attribute",
            quote=container_quote,
        )
        for candidate in candidates
    ]

def html_attributes(raw_tag, offset):
    position, length = 1, len(raw_tag)
    while position < length and not raw_tag[position].isspace() and raw_tag[position] not in "/>":
        position += 1
    while position < length:
        while position < length and raw_tag[position].isspace():
            position += 1
        if position >= length or raw_tag[position] in "/>":
            return
        name_start = position
        while position < length and not raw_tag[position].isspace() and raw_tag[position] not in "=/>":
            position += 1
        name = raw_tag[name_start:position].casefold()
        while position < length and raw_tag[position].isspace():
            position += 1
        if position >= length or raw_tag[position] != "=":
            continue
        position += 1
        while position < length and raw_tag[position].isspace():
            position += 1
        if position >= length:
            return
        quote_char = ""
        if raw_tag[position] in "\"'":
            quote_char = raw_tag[position]
            position += 1
            value_start = position
            while position < length and raw_tag[position] != quote_char:
                position += 1
            value_end = position
            if position < length:
                position += 1
        else:
            value_start = position
            while position < length and not raw_tag[position].isspace() and raw_tag[position] != ">":
                position += 1
            value_end = position
        yield HTMLAttribute(
            name,
            offset + value_start,
            offset + value_end,
            raw_tag[value_start:value_end],
            quote_char,
        )

class HTMLResourceTokenParser(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.tokens = []
        self.style_depth = 0
        self.line_offsets = [0]
        self.line_offsets.extend(match.end() for match in re.finditer("\n", text))

    def absolute_position(self):
        line, column = self.getpos()
        return self.line_offsets[line - 1] + column

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
            self.tokens.extend(css_resource_tokens(data, self.absolute_position()))

    def _handle_tag(self, tag, attrs):
        tag = tag.casefold()
        raw_tag = self.get_starttag_text()
        if not raw_tag:
            return
        attributes = list(html_attributes(raw_tag, self.absolute_position()))
        for attribute in attributes:
            if attribute.name == "style":
                self.tokens.extend(
                    html_style_resource_tokens(
                        attribute.value, attribute.start, attribute.quote
                    )
                )

        allowed = HTML_RESOURCE_ATTRIBUTES.get(tag, set())
        rels = set()
        if tag == "link":
            rels = {
                token.casefold()
                for attribute in attributes
                if attribute.name == "rel"
                for token in html_lib.unescape(attribute.value).split()
            }
            allowed = {"href"} if rels & RESOURCE_LINK_RELS else set()
        for attribute in attributes:
            if attribute.name not in allowed:
                continue
            if attribute.name == "srcset":
                self.tokens.extend(
                    html_srcset_resource_tokens(
                        attribute.value,
                        attribute.start,
                        attribute.quote,
                    )
                )
            else:
                self.tokens.append(
                    ResourceToken(
                        attribute.start,
                        attribute.end,
                        attribute.value,
                        "stylesheet"
                        if tag == "link" and "stylesheet" in rels
                        else "resource",
                        "html-attribute",
                        attribute.quote,
                    )
                )

def markdown_resource_tokens(text):
    tokens = []
    for match in INLINE_IMAGE_RE.finditer(text):
        target = match.group(1)
        tokens.append(
            ResourceToken(
                *match.span(1),
                target,
                context="markdown",
                quote="<" if target.startswith("<") and target.endswith(">") else "",
            )
        )

    definitions = {}
    for match in REFERENCE_DEFINITION_RE.finditer(text):
        target = match.group(2)
        definitions.setdefault(
            normalize_reference_label(match.group(1)),
            ResourceToken(
                *match.span(2),
                target,
                context="markdown",
                quote="<" if target.startswith("<") and target.endswith(">") else "",
            ),
        )
    for match in REFERENCE_IMAGE_RE.finditer(text):
        label = match.group(2) or match.group(1)
        token = definitions.get(normalize_reference_label(label))
        if token:
            tokens.append(token)
    for match in SHORTCUT_IMAGE_RE.finditer(text):
        token = definitions.get(normalize_reference_label(match.group(1)))
        if token:
            tokens.append(token)

    parser = HTMLResourceTokenParser(text)
    parser.feed(text)
    parser.close()
    tokens.extend(parser.tokens)
    return sorted(set(tokens), key=lambda token: (token.start, token.end))

def decoded_resource_target(raw_target, css=False, html_css=False):
    if css:
        target = html_lib.unescape(raw_target) if html_css else raw_target
        target = css_unescape(target.strip())
    else:
        target = html_lib.unescape(raw_target.strip())
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    return target

def html_attribute_replacement(value, quote_char):
    """Encode one URL for its original HTML attribute quote context."""
    quoted = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
    }
    if quote_char == '"':
        quoted['"'] = "&quot;"
    elif quote_char == "'":
        quoted["'"] = "&#39;"
    if quote_char:
        return "".join(quoted.get(char, char) for char in value)

    unquoted = {
        **quoted,
        '"': "&quot;",
        "'": "&#39;",
        "=": "&#61;",
        "`": "&#96;",
    }
    output = []
    for char in value:
        if char.isspace():
            output.append(f"&#{ord(char)};")
        else:
            output.append(unquoted.get(char, char))
    return "".join(output)

def css_replacement(value, quote_char):
    """Encode one URL without changing its value in a CSS url() token."""
    output = []
    for char in value:
        codepoint = ord(char)
        if quote_char:
            if char == "\\":
                output.append("\\\\")
            elif char == quote_char:
                output.append("\\" + char)
            elif char in "\r\n\f" or codepoint == 0:
                output.append(f"\\{(0xFFFD if codepoint == 0 else codepoint):06x}")
            else:
                output.append(char)
        elif (
            char.isspace()
            or char in "\"'()\\"
            or codepoint == 0
            or codepoint < 0x20
            or codepoint == 0x7F
        ):
            output.append(f"\\{(0xFFFD if codepoint == 0 else codepoint):06x}")
        else:
            output.append(char)
    return "".join(output)

def markdown_replacement(value, angle_destination):
    """Percent-encode Markdown destination delimiters and preserve angle form."""
    unsafe = "<>\\\r\n\t "
    if not angle_destination:
        unsafe += "()\"'"
    output = []
    for char in value:
        if char in unsafe or char.isspace():
            output.extend(f"%{byte:02X}" for byte in char.encode("utf-8"))
        else:
            output.append(char)
    replacement = "".join(output)
    return f"<{replacement}>" if angle_destination else replacement

def encode_canonical_target(token, canonical):
    if token.context == "html-attribute":
        return html_attribute_replacement(canonical, token.quote)
    if token.context in {"css", "html-css"}:
        replacement = css_replacement(canonical, token.quote)
        if token.context == "html-css":
            replacement = html_attribute_replacement(
                replacement, token.container_quote
            )
        return replacement
    if token.context == "markdown":
        return markdown_replacement(canonical, token.quote == "<")
    return canonical

def resolve_local_resource(book_dir, source, raw_target, css=False, html_css=False):
    target = decoded_resource_target(raw_target, css=css, html_css=html_css)
    if not target or target.startswith("#"):
        return None
    parsed = urlsplit(target)
    scheme = parsed.scheme.lower()
    if scheme in {"http", "https"} and css:
        raise ValueError(
            f"remote CSS resource is not allowed in strict reader in "
            f"{source.relative_to(book_dir)}: {raw_target}"
        )
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

def canonical_resource_target(book_dir, token, resource, css=False, html_css=False):
    target = decoded_resource_target(token.target, css=css, html_css=html_css)
    parsed = urlsplit(target)
    canonical = quote(resource.relative_to(book_dir).as_posix(), safe="/")
    if parsed.query:
        canonical += f"?{parsed.query}"
    if parsed.fragment:
        canonical += f"#{parsed.fragment}"
    return encode_canonical_target(token, canonical)

class CSSDependencyValidator:
    """Validate the exact local CSS dependency graph Pandoc will traverse."""

    def __init__(self, book_dir):
        self.book_dir = Path(book_dir).resolve()
        self.resources = set()
        self.visited = set()
        self.visiting = []
        self.total_bytes = 0

    def validate(self, stylesheet, depth=0):
        stylesheet = Path(stylesheet).resolve()
        if stylesheet in self.visiting:
            cycle = self.visiting[self.visiting.index(stylesheet) :] + [stylesheet]
            chain = " -> ".join(path.relative_to(self.book_dir).as_posix() for path in cycle)
            raise ValueError(f"CSS import cycle: {chain}")
        if stylesheet in self.visited:
            return
        if depth > CSS_MAX_IMPORT_DEPTH:
            raise ValueError(
                f"CSS import depth limit ({CSS_MAX_IMPORT_DEPTH}) exceeded at "
                f"{stylesheet.relative_to(self.book_dir)}"
            )
        if len(self.visited) + len(self.visiting) >= CSS_MAX_FILES:
            raise ValueError(f"CSS file limit ({CSS_MAX_FILES}) exceeded")
        size = stylesheet.stat().st_size
        if size > CSS_MAX_FILE_BYTES:
            raise ValueError(
                f"CSS size limit ({CSS_MAX_FILE_BYTES} bytes) exceeded at "
                f"{stylesheet.relative_to(self.book_dir)}"
            )
        if self.total_bytes + size > CSS_MAX_TOTAL_BYTES:
            raise ValueError(f"CSS total size limit ({CSS_MAX_TOTAL_BYTES} bytes) exceeded")
        try:
            text = stylesheet.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(
                f"CSS must be UTF-8: {stylesheet.relative_to(self.book_dir)}"
            ) from error
        self.total_bytes += size
        self.visiting.append(stylesheet)
        try:
            for token in css_resource_tokens(text):
                target = decoded_resource_target(token.target, css=True)
                if token.kind == "css-import" and urlsplit(target).scheme.lower() == "data":
                    raise ValueError(
                        f"data CSS @import is not allowed in strict reader in "
                        f"{stylesheet.relative_to(self.book_dir)}"
                    )
                resource = resolve_local_resource(
                    self.book_dir, stylesheet, token.target, css=True
                )
                if resource is None:
                    continue
                self.resources.add(resource)
                if token.kind == "css-import":
                    self.validate(resource, depth + 1)
        finally:
            self.visiting.pop()
        self.visited.add(stylesheet)

def rewrite_published_resources(book_dir, source, text):
    book_dir = Path(book_dir).resolve()
    source = Path(source).resolve()
    resources = set()
    replacements = []
    css_dependencies = CSSDependencyValidator(book_dir)
    for token in markdown_resource_tokens(text):
        if token.kind in {"css-import", "html-css-import"}:
            raise ValueError(
                f"inline CSS @import is not allowed in strict reader in "
                f"{source.relative_to(book_dir)}; use a validated stylesheet link"
            )
        is_css = token.kind in {"css-url", "html-css-url"}
        is_html_css = token.kind.startswith("html-css-")
        resource = resolve_local_resource(
            book_dir,
            source,
            token.target,
            css=is_css,
            html_css=is_html_css,
        )
        if resource:
            resources.add(resource)
            if token.kind == "stylesheet":
                css_dependencies.validate(resource)
            replacements.append(
                (
                    token.start,
                    token.end,
                    canonical_resource_target(
                        book_dir,
                        token,
                        resource,
                        css=is_css,
                        html_css=is_html_css,
                    ),
                )
            )
    rewritten = text
    next_start = len(text)
    for start, end, replacement in reversed(replacements):
        if end > next_start:
            raise ValueError(f"overlapping resource tokens in {source.relative_to(book_dir)}")
        rewritten = rewritten[:start] + replacement + rewritten[end:]
        next_start = start
    resources.update(css_dependencies.resources)
    return rewritten, resources

def rewrite_published_sources(book_dir, items):
    sources = {}
    resources = set()
    for item in items:
        if item[0] != "file":
            continue
        source = (book_dir / item[1]).resolve()
        text = source.read_text(encoding="utf-8")
        rewritten, source_resources = rewrite_published_resources(
            book_dir, source, text
        )
        sources[item[1]] = rewritten
        resources.update(source_resources)
    return sources, resources

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
    rewritten_sources, resources = rewrite_published_sources(book_dir, items)
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
        txt = rewritten_sources[path]
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
        cmd = ["pandoc", str(tmp_md), "-f", "markdown+lists_without_preceding_blankline", "-t", "html5",
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

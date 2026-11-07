"""Build `docs/assets/docs-data.js` from `docs/*.md` using pure Python stdlib.

Ensures the interactive GitHub Pages documentation portal (`docs/guide.html`) is
always 100% synchronized with the Markdown chapters in `docs/*.md`.
"""

from __future__ import annotations

import html
import json
import pathlib
import re


DOCS_DIR = pathlib.Path(__file__).resolve().parent

CHAPTERS = [
    ("zero-to-hero", "0 to Hero: Full Tutorial", "Start Here", "zero-to-hero.md"),
    ("getting-started", "Getting Started", "Start Here", "getting-started.md"),
    ("tutorial-functional", "Functional & Procedural", "Tutorials", "tutorial-functional.md"),
    ("tutorial-oop", "Object-Oriented (OOP)", "Tutorials", "tutorial-oop.md"),
    ("theming-and-styling", "Theming, Accents & Icons", "Tutorials", "theming-and-styling.md"),
    ("concurrency-and-async", "Concurrency & Asyncio", "Tutorials", "concurrency-and-async.md"),
    ("advanced-rendering-and-packaging", "Canvas, GPU & Packaging", "Tutorials", "advanced-rendering-and-packaging.md"),
    ("components-reference", "160+ Components Reference", "API Reference", "components-reference.md"),
]

PY_KW = {
    "import", "from", "as", "def", "class", "return", "if", "elif", "else",
    "for", "in", "while", "with", "try", "finally", "except", "raise",
    "True", "False", "None", "and", "or", "not", "nonlocal", "global",
    "async", "await", "yield", "lambda", "pass", "break", "continue", "assert",
}

TOKEN_RE = re.compile(
    r"(?P<com>#[^\n]*)"
    r"|(?P<str>\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''|\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*')"
    r"|(?P<num>\b\d+(?:\.\d+)?\b)"
    r"|(?P<id>\b[A-Za-z_][A-Za-z0-9_]*\b)"
)


def highlight_code(code: str, lang: str) -> str:
    if lang not in ("python", "py"):
        return html.escape(code)

    out: list[str] = []
    pos = 0
    for m in TOKEN_RE.finditer(code):
        if m.start() > pos:
            out.append(html.escape(code[pos:m.start()]))
        tok = m.group(0)
        esc = html.escape(tok)
        if m.lastgroup == "com":
            out.append(f'<span class="tok-com">{esc}</span>')
        elif m.lastgroup == "str":
            out.append(f'<span class="tok-str">{esc}</span>')
        elif m.lastgroup == "num":
            out.append(f'<span class="tok-num">{esc}</span>')
        elif m.lastgroup == "id":
            if tok in PY_KW:
                out.append(f'<span class="tok-kw">{esc}</span>')
            elif tok[0].isupper():
                out.append(f'<span class="tok-cls">{esc}</span>')
            else:
                out.append(esc)
        pos = m.end()
    if pos < len(code):
        out.append(html.escape(code[pos:]))
    return "".join(out)


def slugify(text: str) -> str:
    clean = re.sub(r"`([^`]+)`", r"\1", text)
    clean = re.sub(r"[^a-zA-Z0-9]+", "-", clean.lower()).strip("-")
    return clean or "section"


def render_inline(text: str) -> str:
    parts = re.split(r"(`[^`]+`)", text)
    rendered: list[str] = []
    for p in parts:
        if p.startswith("`") and p.endswith("`") and len(p) >= 2:
            rendered.append(f"<code>{html.escape(p[1:-1])}</code>")
        else:
            s = html.escape(p)
            # Links [label](target)
            def _link_sub(m: re.Match[str]) -> str:
                lbl, url = m.group(1), m.group(2)
                if url.endswith(".md"):
                    chap_slug = pathlib.Path(url).stem
                    return f'<a href="#{chap_slug}" data-doc-link="{chap_slug}">{lbl}</a>'
                return f'<a href="{url}" target="_blank" rel="noopener">{lbl}</a>'

            s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _link_sub, s)
            s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
            s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
            rendered.append(s)
    return "".join(rendered)


def markdown_to_html(md: str) -> tuple[str, list[dict[str, str]], list[dict[str, str]]]:
    lines = md.splitlines()
    i = 0
    n = len(lines)
    html_parts: list[str] = []
    toc: list[dict[str, str]] = []
    sections_index: list[dict[str, str]] = []
    current_h = "Overview"
    current_slug = ""
    current_text: list[str] = []

    def _flush_section() -> None:
        if current_text:
            sections_index.append({
                "heading": current_h,
                "anchor": current_slug,
                "snippet": " ".join(current_text)[:240],
            })
            current_text.clear()

    while i < n:
        line = lines[i]

        # Fenced code block
        if line.strip().startswith("```"):
            lang = line.strip()[3:].strip() or "text"
            i += 1
            buf: list[str] = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            raw_code = "\n".join(buf)
            hl = highlight_code(raw_code, lang)
            label = "python" if lang in ("python", "py") else lang
            html_parts.append(
                f'<div class="code-panel">'
                f'<div class="code-header"><span>{html.escape(label)}</span>'
                f'<button class="copy-mini" data-copy-code="1" type="button">Copy</button></div>'
                f"<pre><code>{hl}</code></pre></div>"
            )
            continue

        # Horizontal rule
        if re.match(r"^\s*---+\s*$", line):
            html_parts.append("<hr />")
            i += 1
            continue

        # Standalone Markdown Image ![alt](src)
        img_m = re.match(r"^\s*!\[([^\]]*)\]\(([^)]+)\)\s*$", line)
        if img_m:
            alt_txt = html.escape(img_m.group(1).strip())
            src_url = html.escape(img_m.group(2).strip())
            html_parts.append(
                f'<figure class="doc-figure">'
                f'<div class="window-frame">'
                f'<div class="window-bar"><div class="window-dots"><i></i><i></i><i></i></div>'
                f'<span>{alt_txt}</span><span style="width: 42px;"></span></div>'
                f'<img src="{src_url}" alt="{alt_txt}" loading="lazy" decoding="async" />'
                f"</div></figure>"
            )
            i += 1
            continue

        # Headings (H1 - H4)
        hm = re.match(r"^(#{1,4})\s+(.+)$", line)
        if hm:
            _flush_section()
            lvl = len(hm.group(1))
            raw_title = hm.group(2).strip()
            slug = slugify(raw_title)
            current_h = re.sub(r"`([^`]+)`", r"\1", raw_title)
            current_slug = slug if lvl > 1 else ""
            if lvl == 2:
                toc.append({"title": current_h, "id": slug})
            html_parts.append(f'<h{lvl} id="{slug}">{render_inline(raw_title)}</h{lvl}>')
            i += 1
            continue

        # Markdown Table
        if "|" in line and i + 1 < n and re.match(r"^\s*\|?[\s:-]+\|[\s|:-]*$", lines[i + 1]):
            headers = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows: list[list[str]] = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            th_html = "".join(f"<th>{render_inline(h)}</th>" for h in headers)
            tr_html = "".join(
                "<tr>" + "".join(f"<td>{render_inline(c)}</td>" for c in r) + "</tr>"
                for r in rows
            )
            html_parts.append(f"<table><thead><tr>{th_html}</tr></thead><tbody>{tr_html}</tbody></table>")
            continue

        # Blockquote / Callout
        if line.lstrip().startswith(">"):
            q_lines: list[str] = []
            while i < n and lines[i].lstrip().startswith(">"):
                q_lines.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            q_body = " ".join(x.strip() for x in q_lines if x.strip())
            current_text.append(q_body)
            cls_attr = ""
            if q_body.startswith("**Pitfall"):
                cls_attr = ' class="callout-warn"'
            elif q_body.startswith("**Pro Tip"):
                cls_attr = ' class="callout-tip"'
            html_parts.append(f"<blockquote{cls_attr}><p>{render_inline(q_body)}</p></blockquote>")
            continue

        # Unordered or Ordered List
        ul_m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.+)$", line)
        if ul_m:
            ordered = ul_m.group(2).endswith(".")
            tag = "ol" if ordered else "ul"
            items_html: list[str] = []
            while i < n:
                m_it = re.match(r"^(\s*)([-*]|\d+\.)\s+(.+)$", lines[i])
                if not m_it:
                    break
                item_txt = m_it.group(3).strip()
                current_text.append(re.sub(r"`([^`]+)`", r"\1", item_txt))
                i += 1
                # Absorb indented sub-bullets cleanly
                sub_items: list[str] = []
                while i < n and re.match(r"^\s{2,}[-*]\s+(.+)$", lines[i]):
                    sub_txt = re.sub(r"^\s{2,}[-*]\s+", "", lines[i]).strip()
                    current_text.append(re.sub(r"`([^`]+)`", r"\1", sub_txt))
                    sub_items.append(f"<li>{render_inline(sub_txt)}</li>")
                    i += 1
                sub_ul = f"<ul>{''.join(sub_items)}</ul>" if sub_items else ""
                items_html.append(f"<li>{render_inline(item_txt)}{sub_ul}</li>")
            html_parts.append(f"<{tag}>{''.join(items_html)}</{tag}>")
            continue

        # Blank line
        if not line.strip():
            i += 1
            continue

        # Paragraph
        p_lines: list[str] = []
        while i < n and lines[i].strip() and not re.match(r"^(#{1,4}\s|```|---|\s*!\[|\s*[-*]\s|\s*\d+\.\s|\s*>)", lines[i]):
            p_lines.append(lines[i].strip())
            i += 1
        para = " ".join(p_lines)
        current_text.append(re.sub(r"`([^`]+)`", r"\1", para))
        html_parts.append(f"<p>{render_inline(para)}</p>")

    _flush_section()
    return "\n".join(html_parts), toc, sections_index


def build_bundle() -> pathlib.Path:
    chapters_out = []
    search_index = []

    for slug, title, group, filename in CHAPTERS:
        md_text = (DOCS_DIR / filename).read_text(encoding="utf-8")
        rendered_html, toc, sec_idx = markdown_to_html(md_text)
        chapters_out.append({
            "slug": slug,
            "title": title,
            "group": group,
            "source": f"docs/{filename}",
            "html": rendered_html,
            "toc": toc,
        })
        for s in sec_idx:
            search_index.append({
                "slug": slug,
                "chapter": title,
                "heading": s["heading"],
                "anchor": s["anchor"],
                "text": s["snippet"],
            })

    out_path = DOCS_DIR / "assets" / "docs-data.js"
    payload = {
        "chapters": chapters_out,
        "search": search_index,
    }
    out_path.write_text(
        "/* Auto-generated from docs/*.md by docs/build_docs_bundle.py */\n"
        f"window.NEXA_DOCS = {json.dumps(payload, ensure_ascii=False)};\n"
        "window.YAPPS_DOCS = window.NEXA_DOCS;\n",
        encoding="utf-8",
    )
    return out_path


if __name__ == "__main__":
    p = build_bundle()
    print(f"Built {p} ({p.stat().st_size / 1024:.1f} KB)")

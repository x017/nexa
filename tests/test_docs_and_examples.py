"""Regression tests for documentation snippets, accents, and all example views."""

from __future__ import annotations

import ast
import html
import importlib.util
import inspect
import json
import os
import pathlib
import re
import subprocess
import sys
import textwrap

import nexa as ui
from nexa import scopes as nexa_scopes
from nexa import types as nexa_types
from nexa.ui import UI


ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_accent_enum_members_and_count() -> None:
    expected = ["NEUTRAL", "VIOLET", "BLUE", "GREEN", "AMBER", "ORANGE", "CORAL", "ROSE"]
    assert [a.name for a in ui.Accent] == expected
    assert ui.Accent.COUNT == 8
    assert not hasattr(ui.Accent, "MINT")
    assert not hasattr(ui.Accent, "CYAN")
    assert not hasattr(ui.Accent, "TEAL")


def test_oop_application_accepts_positional_and_keyword_title() -> None:
    class PosApp(ui.Application):
        def __init__(self) -> None:
            super().__init__("Positional Title", width=320, height=200, headless=True)

        def build(self, ctx: ui.UI) -> None:
            ctx.label("ok")

    class KwApp(ui.Application):
        def __init__(self) -> None:
            super().__init__(title="Keyword Title", width=320, height=200, headless=True)

        def build(self, ctx: ui.UI) -> None:
            ctx.label("ok")

    for cls in (PosApp, KwApp):
        app = cls()
        try:
            app.run(max_frames=2)
        finally:
            app.app.close()


def test_no_invalid_ui_symbols_in_readme_docs_site_or_examples() -> None:
    targets = [
        ROOT / "README.md",
        *sorted((ROOT / "docs").glob("*.md")),
        ROOT / "docs" / "index.html",
        ROOT / "docs" / "assets" / "site.js",
        *sorted((ROOT / "examples").glob("*.py")),
    ]
    missing: list[str] = []

    for path in targets:
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            if "do **not** exist" in line or "do not exist" in line:
                continue
            for m in re.finditer(r"\bui\.([A-Za-z_][A-Za-z0-9_]*)(?:\.([A-Za-z_][A-Za-z0-9_]*))?", line):
                attr, member = m.group(1), m.group(2)
                if not hasattr(ui, attr):
                    missing.append(f"{path.relative_to(ROOT)}:{lineno} -> ui.{attr}")
                    continue
                obj = getattr(ui, attr)
                if member and isinstance(obj, type) and not hasattr(obj, member):
                    missing.append(f"{path.relative_to(ROOT)}:{lineno} -> ui.{attr}.{member}")

    assert missing == [], f"Invalid ui.* references found: {missing}"


def test_all_markdown_python_blocks_parse_and_standalone_tutorials_run() -> None:
    md_files = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
    fence_re = re.compile(r"```python\n(.*?)```", re.DOTALL)

    standalone_blocks: list[tuple[str, str]] = []
    parsed_count = 0

    for md in md_files:
        content = md.read_text(encoding="utf-8")
        for idx, match in enumerate(fence_re.finditer(content), 1):
            code = textwrap.dedent(match.group(1))
            label = f"{md.name}#block{idx}"
            # Every Python fence in README & docs must be syntactically valid Python
            tree = ast.parse(code, filename=label)
            parsed_count += 1
            # Never allow a snippet to define top-level `def main()` without invoking `main()`
            has_def_main = any(isinstance(n, ast.FunctionDef) and n.name == "main" for n in tree.body)
            if has_def_main:
                assert '__main__' in code or "\nmain()" in code, f"{label} defines main() without calling it"
            if 'if __name__ == "__main__":' in code and "CustomRenderer" not in code:
                standalone_blocks.append((label, code))

    # Also verify all Quickstart paradigm snippets embedded in docs/assets/site.js
    site_js = (ROOT / "docs" / "assets" / "site.js").read_text(encoding="utf-8")
    paradigm_count = 0
    for pm in re.finditer(r'(\w+):\s*\{\s*file:\s*"([^"]+)".*?code:\s*`(.*?)`', site_js, re.DOTALL):
        key, fname, html_code = pm.groups()
        plain = html.unescape(re.sub(r"<[^>]+>", "", html_code))
        label = f"site.js:{key}({fname})"
        tree = ast.parse(plain, filename=label)
        has_def_main = any(isinstance(n, ast.FunctionDef) and n.name == "main" for n in tree.body)
        if has_def_main:
            assert '__main__' in plain or "\nmain()" in plain, f"{label} defines main() without calling it"
        standalone_blocks.append((label, plain))
        paradigm_count += 1

    assert paradigm_count >= 3
    assert parsed_count >= 25
    assert len(standalone_blocks) >= 12

    env = {
        **os.environ,
        "NEXA_HEADLESS": "1",
        "NEXA_MAX_FRAMES": "3",
        "PYTHONUTF8": "1",
        "PYTHONPATH": str(ROOT / "src"),
    }
    for label, code in standalone_blocks:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=15,
        )
        assert proc.returncode == 0, f"{label} failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"


def test_multi_view_examples_exercise_every_route_and_tab() -> None:
    os.environ["NEXA_HEADLESS"] = "1"

    def _load_example(name: str):
        path = ROOT / "examples" / name
        spec = importlib.util.spec_from_file_location(f"_ex_{path.stem}", path)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        return mod

    # 1. SettingsApp across all 9 routes (including AppearanceView with 8 accents)
    settings_mod = _load_example("settings.py")
    s_app = settings_mod.SettingsApp()
    try:
        for route in list(s_app.router._routes.keys()):
            s_app.router.push(route)
            assert s_app.app.frame(wait=False)
            s_app.build(s_app.ui)
        s_app.app.ui.end_frame()
    finally:
        s_app.app.close()

    # 2. Tracker & Gallery: rewrite initial tab index in source and execute all 3 tabs
    env = {
        **os.environ,
        "NEXA_HEADLESS": "1",
        "NEXA_MAX_FRAMES": "3",
        "PYTHONUTF8": "1",
        "PYTHONPATH": str(ROOT / "src"),
    }
    tracker_src = (ROOT / "examples" / "tracker.py").read_text(encoding="utf-8")
    for view_idx in range(3):
        patched = tracker_src.replace("tab = 0", f"tab = {view_idx}", 1)
        res = subprocess.run([sys.executable, "-c", patched], cwd=str(ROOT), env=env, capture_output=True, text=True, encoding="utf-8", timeout=15)
        assert res.returncode == 0, f"tracker.py tab={view_idx} failed:\n{res.stderr}"

    gallery_src = (ROOT / "examples" / "gallery.py").read_text(encoding="utf-8")
    for tab_idx in range(3):
        patched = gallery_src.replace("active_tab = 0", f"active_tab = {tab_idx}", 1)
        res = subprocess.run([sys.executable, "-c", patched], cwd=str(ROOT), env=env, capture_output=True, text=True, encoding="utf-8", timeout=15)
        assert res.returncode == 0, f"gallery.py active_tab={tab_idx} failed:\n{res.stderr}"


def test_docs_bundle_is_in_sync(tmp_path: pathlib.Path) -> None:
    bundle_script = ROOT / "docs" / "build_docs_bundle.py"
    spec = importlib.util.spec_from_file_location("_build_docs_bundle", bundle_script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    docs_dir = ROOT / "docs"
    wiki_dir = ROOT / "wiki"
    generated_files = [
        docs_dir / "assets" / "search-index.js",
        docs_dir / "wiki.html",
        docs_dir / "tutorials.html",
        docs_dir / "guide.html",
        docs_dir / "components.html",
        docs_dir / "changelog.html",
        *[docs_dir / f"{slug}.html" for slug, *_ in mod.CHAPTERS],
        wiki_dir / "Home.md",
        wiki_dir / "_Sidebar.md",
        wiki_dir / "_Footer.md",
        *[wiki_dir / f"{wiki_name}.md" for _s, _t, _g, _f, wiki_name, _n in mod.CHAPTERS],
    ]
    before = {p: p.read_text(encoding="utf-8") for p in generated_files}
    mod.build_bundle()
    after = {p: p.read_text(encoding="utf-8") for p in generated_files}
    assert before == after, "Static docs/wiki HTML, wiki/*.md, or search-index.js is out of sync; run `python3 docs/build_docs_bundle.py`"
    assert not (docs_dir / "assets" / "docs-data.js").exists(), "Legacy 432 KB docs-data.js should not exist"

    # Verify search-index.js parses cleanly and covers all chapters + Wiki
    search_raw = (docs_dir / "assets" / "search-index.js").read_text(encoding="utf-8")
    search_items, _ = json.JSONDecoder().raw_decode(search_raw.split("window.NEXA_SEARCH =", 1)[1].lstrip())
    assert len(search_items) >= 35
    assert any(it["page"] == "wiki.html" for it in search_items)

    # Verify every static HTML page has pre-rendered sidebar + article, clean prose, and valid internal links/anchors
    all_html_pages = sorted(docs_dir.glob("*.html"))
    assert len(all_html_pages) == 14
    page_ids: dict[str, set[str]] = {
        p.name: set(re.findall(r'\bid="([^"]+)"', p.read_text(encoding="utf-8")))
        for p in all_html_pages
    }

    for p in all_html_pages:
        txt = p.read_text(encoding="utf-8")
        if p.name != "index.html":
            nav_m = re.search(r'<nav id="docs-sidebar-nav">(.*?)</nav>', txt, re.DOTALL)
            art_m = re.search(r'<article class="prose" id="docs-article">(.*?)</article>', txt, re.DOTALL)
            assert nav_m and len(nav_m.group(1).strip()) > 200, f"Empty static sidebar in {p.name}"
            assert art_m and len(art_m.group(1).strip()) > 200, f"Empty static article in {p.name}"

            prose = re.sub(r"<pre>.*?</pre>", "", art_m.group(1), flags=re.DOTALL)
            prose_no_code = re.sub(r"<code>.*?</code>", "CODE", prose, flags=re.DOTALL)
            assert "**" not in prose_no_code, f"Unrendered ** bold marker in {p.name}"
            assert not re.search(r"\]\([^)<]+\)", prose_no_code), f"Broken markdown link in {p.name}"
            for img_tag in re.findall(r"<img[^>]+>", art_m.group(1)):
                assert 'width="' in img_tag and 'height="' in img_tag, f"Missing dimensions on {img_tag} in {p.name}"

        # Validate every internal href across all 14 HTML pages!
        for href in re.findall(r'href="([^"]+)"', txt):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            if href.startswith("#"):
                anchor = href[1:]
                assert anchor in page_ids[p.name], f"{p.name} has dead local anchor #{anchor}"
            else:
                rel_part, _, frag = href.partition("#")
                rel_clean = rel_part.split("?")[0]
                target_file = docs_dir / rel_clean
                assert target_file.is_file(), f"{p.name} links to missing file {href}"
                if frag:
                    assert frag in page_ids[target_file.name], (
                        f"{p.name} links to missing anchor #{frag} in {target_file.name}"
                    )

    # Verify GitHub Wiki export generates Home.md, _Sidebar.md, _Footer.md + all 8 chapters cleanly
    wiki_files = mod.export_github_wiki(tmp_path)
    assert len(wiki_files) == 11
    wiki_names = {f.stem for f in wiki_files}
    assert {"Home", "_Sidebar", "_Footer", "Zero-to-Hero", "Getting-Started", "Components-Reference"} <= wiki_names
    for wf in wiki_files:
        wtxt = wf.read_text(encoding="utf-8")
        assert "(assets/screenshots/" not in wtxt, f"Unrewritten relative screenshot in {wf.name}"
        wtxt_no_code = re.sub(r"```[\s\S]*?```|`[^`\n]+`", "", wtxt)
        for m in re.finditer(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)", wtxt_no_code):
            target = m.group(2)
            if not target.startswith(("http://", "https://", "#")):
                page_slug = target.split("#")[0]
                assert page_slug in wiki_names, f"{wf.name} links to unknown Wiki page {target!r}"

    # Ensure copy buttons work over non-HTTPS origins (e.g. http://parsa.x017.ir/nexa/)
    site_js = (docs_dir / "assets" / "site.js").read_text(encoding="utf-8")
    assert 'execCommand("copy")' in site_js and "isSecureContext" in site_js

    # Ensure docs/assets/styles.css has zero undefined var(--...) tokens and scopes .prose link underlines cleanly
    styles_css = (docs_dir / "assets" / "styles.css").read_text(encoding="utf-8")
    defined_vars = set(re.findall(r"(--[a-zA-Z0-9_-]+)\s*:", styles_css)) | set(
        re.findall(r'setProperty\("(--[a-zA-Z0-9_-]+)"', site_js)
    )
    used_vars = set(re.findall(r"var\((--[a-zA-Z0-9_-]+)\)", styles_css))
    assert used_vars <= defined_vars, f"Undefined CSS custom properties: {sorted(used_vars - defined_vars)}"
    assert ".prose a:not([class])" in styles_css

    # Ensure index.html and all docs/wiki HTML pages use matching cache-busting versions on shared assets
    index_html = (docs_dir / "index.html").read_text(encoding="utf-8")
    wiki_html = (docs_dir / "wiki.html").read_text(encoding="utf-8")
    for asset in ("styles.css", "site.js", "dither.js", "favicon.svg"):
        iv = re.findall(rf"assets/{re.escape(asset)}\?v=([0-9.]+)", index_html)
        wv = re.findall(rf"assets/{re.escape(asset)}\?v=([0-9.]+)", wiki_html)
        assert iv and iv == wv, f"Asset version mismatch for {asset}: index={iv} vs wiki={wv}"


def test_all_public_types_scopes_and_reference_signatures_are_exported() -> None:
    # 1. Every public symbol in nexa.types and nexa.scopes must be on top-level `nexa` and in `__all__`
    for mod in (nexa_types, nexa_scopes):
        for attr in dir(mod):
            if attr.startswith("_"):
                continue
            obj = getattr(mod, attr)
            if getattr(obj, "__module__", "") == mod.__name__:
                assert hasattr(ui, attr), f"Missing top-level export: {mod.__name__}.{attr}"
                assert attr in ui.__all__, f"Missing __all__ entry: {attr}"

    # 2. Every Class.MEMBER reference across docs/README/HTML/JS must exist
    targets = [
        ROOT / "README.md",
        *sorted((ROOT / "docs").glob("*.md")),
        ROOT / "docs" / "index.html",
        ROOT / "docs" / "assets" / "site.js",
    ]
    enum_ref_re = re.compile(r"\b([A-Z][A-Za-z0-9_]*)\.([A-Z][A-Za-z0-9_]*)\b")
    for path in targets:
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "do **not** exist" in line or "do not exist" in line:
                continue
            for m in enum_ref_re.finditer(line):
                cls_name, mem_name = m.group(1), m.group(2)
                if hasattr(ui, cls_name):
                    cls_obj = getattr(ui, cls_name)
                    if isinstance(cls_obj, type):
                        assert hasattr(cls_obj, mem_name), f"{path.name}:{lineno} invalid {cls_name}.{mem_name}"

    # 3. Every documented signature in docs/components-reference.md must match UI / nexa
    ref_txt = (ROOT / "docs" / "components-reference.md").read_text(encoding="utf-8")
    sig_re1 = re.compile(r"\*\*`([a-z_][a-z0-9_]*)\(([^`]*)\)")
    sig_re2 = re.compile(r"-\s+`([a-z_][a-z0-9_]*)\(([^`]*)\)")
    checked = 0
    for lineno, line in enumerate(ref_txt.splitlines(), 1):
        for m in [*sig_re1.finditer(line), *sig_re2.finditer(line)]:
            fn_name, params_str = m.group(1), m.group(2)
            target = getattr(UI, fn_name, None) or getattr(ui, fn_name, None)
            assert target is not None, f"components-reference.md:{lineno} missing {fn_name}"
            sig = inspect.signature(target)
            actual_params = set(sig.parameters.keys()) - {"self", "kwargs"}
            has_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
            if not has_var_kw:
                for part in params_str.split(","):
                    part = part.strip()
                    if not part or part == "*" or part.startswith("**"):
                        continue
                    pname = part.split(":")[0].split("=")[0].strip()
                    if pname and re.match(r"^[a-z_][a-z0-9_]*$", pname):
                        assert pname in actual_params, (
                            f"components-reference.md:{lineno} {fn_name} bad param {pname!r} "
                            f"(expected in {sorted(actual_params)})"
                        )
            checked += 1
    assert checked >= 180


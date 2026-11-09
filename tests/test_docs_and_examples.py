"""Regression tests for documentation snippets, accents, and all example views."""

from __future__ import annotations

import ast
import importlib.util
import inspect
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
            # Every Python fence in README & docs must be syntactically valid Python
            ast.parse(code, filename=f"{md.name}#block{idx}")
            parsed_count += 1
            if 'if __name__ == "__main__":' in code and "CustomRenderer" not in code:
                standalone_blocks.append((f"{md.name}#block{idx}", code))

    assert parsed_count >= 25
    assert len(standalone_blocks) >= 8

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


def test_docs_bundle_is_in_sync() -> None:
    bundle_script = ROOT / "docs" / "build_docs_bundle.py"
    spec = importlib.util.spec_from_file_location("_build_docs_bundle", bundle_script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    out_path = ROOT / "docs" / "assets" / "docs-data.js"
    before = out_path.read_text(encoding="utf-8")
    mod.build_bundle()
    after = out_path.read_text(encoding="utf-8")
    assert before == after, "docs/assets/docs-data.js is out of sync; run `python3 docs/build_docs_bundle.py`"


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


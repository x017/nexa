#!/usr/bin/env python3
"""Generate the struct-returning bridges for CUI 1.3's developer tools.

ctypes cannot return a struct by value portably, so every ``cui_*_ex`` that
returns a result struct gets a thin wrapper in ``csrc/nexa_bridge_extra.c``
that writes into a caller-supplied out pointer.  This script derives both the C
wrappers and the ``bind_prototypes`` entries from ``csrc/include/cui/cui.h``.

    python3 tools/gen_devtools_bridge.py           # rewrite both files
    python3 tools/gen_devtools_bridge.py --check   # fail if they are stale
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADER = ROOT / "csrc" / "include" / "cui" / "cui.h"
OUT_C = ROOT / "csrc" / "nexa_bridge_extra.c"
CDEFS = ROOT / "src" / "nexa" / "_cdefs.py"

# Functions whose struct return gets a bridge.  Anything already bound by hand
# (path bar, markdown, terminal, ...) must not appear here.
TARGETS = [
    "cui_problems_ex",
    "cui_pipeline_ex",
    "cui_schedule_picker_ex",
    "cui_keymap_ex",
    "cui_commit_graph_ex",
    "cui_graph_view_ex",
    "cui_waterfall_ex",
    "cui_trace_view_ex",
    "cui_regex_tester_ex",
    "cui_test_explorer_ex",
    "cui_stack_trace_ex",
    "cui_request_bar_ex",
    "cui_uptime_ex",
    "cui_time_histogram_ex",
    "cui_coverage_ex",
    "cui_blame_ex",
    "cui_feature_flags_ex",
    "cui_api_explorer_ex",
]

# simple (non-struct-returning) helpers bound directly, no bridge needed
DIRECT = [
    "cui_kv_editor_ex",
    "cui_query_builder_ex",
    "cui_query_text",
    "cui_query_match",
    "cui_query_op_name",
    "cui_trace_sort",
    "cui_date_to_days",
    "cui_date_from_days",
    "cui_emoji_font_load_memory",
    "cui_log_init",
    "cui_log_appendv",
    "cui_log_get",
    "cui_shortcut_label",
    "cui_flame_span_rect",
    "cui_gradient_eval",
]


def parse_header() -> dict[str, tuple[str, list[tuple[str, str]], str]]:
    """``{name: (return_type, [(type, name), ...], raw)}`` for every public function."""
    text = re.sub(r"/\*.*?\*/", " ", HEADER.read_text(encoding="utf-8"), flags=re.S)
    text = re.sub(r"//[^\n]*", " ", text)
    out: dict[str, tuple[str, list[tuple[str, str]], str]] = {}
    for m in re.finditer(r"CUI_API\s+([^;]*?);", text, flags=re.S):
        raw = " ".join(m.group(1).split())
        raw = re.sub(r"\s*CUI_PRINTF\([^)]*\)\s*$", "", raw)
        hm = re.match(r"^(.*?)\b(\w+)\s*\((.*)\)$", raw)
        if not hm:
            continue
        ret, name, params = hm.group(1).strip(), hm.group(2), hm.group(3).strip()
        if not ret or ret.startswith("#"):
            continue
        if "..." in params:
            continue
        args: list[tuple[str, str]] = []
        for part in split_params(params):
            part = part.strip()
            if not part or part == "void":
                continue
            am = re.match(r"^(.*?[\s*])(\w+)$", part)
            if am:
                args.append((am.group(1).strip(), am.group(2)))
        out[name] = (ret, args, raw)
    return out


def split_params(params: str) -> list[str]:
    depth = 0
    cur = ""
    parts = []
    for ch in params:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return parts


def bridge_name(func: str) -> str:
    base = func[len("cui_"):] if func.startswith("cui_") else func
    if base.endswith("_ex"):
        base = base[: -len("_ex")]
    return f"nexa_{base}_ex"


CTYPES = {
    "int": "c_int",
    "bool": "c_bool",
    "float": "c_float",
    "double": "c_double",
    "size_t": "c_size_t",
    "uint32_t": "c_uint32",
    "uint8_t": "c_uint8",
    "uint64_t": "c_uint64",
    "cui_id": "c_uint32",
}


def ctype_for(c_type: str, name: str) -> str:
    raw = " ".join(c_type.split())
    if raw in ("const char *const *", "const char **", "char *const *"):
        return "P(c_char_p)"
    t = c_type.replace("const ", "").strip()
    if t == "cui_ctx *":
        return "c_void_p"
    if t in ("char *", "const char *"):
        return "c_char_p"
    if t == "void *":
        return "c_void_p"
    if t.startswith("const ") and t.endswith(" *"):
        t = t[len("const "):]
    if t.endswith(" *"):
        inner = t[:-2].strip()
        if inner.startswith("const "):
            inner = inner[len("const "):]
        if inner.startswith("cui_"):
            inner = inner[len("cui_"):]
        cls = "".join(part.capitalize() for part in inner.split("_"))
        if inner in CTYPES:
            return f"P({CTYPES[inner]})"
        return f"P(Cui{cls})"
    return CTYPES.get(t, "c_void_p")


def struct_name(c_type: str) -> str:
    name = c_type.strip()
    if name.startswith("cui_"):
        name = name[len("cui_"):]
    cls = "".join(part.capitalize() for part in name.split("_"))
    return f"Cui{cls}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    fns = parse_header()

    lines = [
        "/* Generated by tools/gen_devtools_bridge.py - do not edit by hand.",
        " * Struct-returning CUI 1.3 components, written into a caller pointer.",
        " */",
        '#include "cui/cui.h"',
        "",
    ]
    sigs: list[str] = []
    for name in TARGETS:
        if name not in fns:
            print(f"warning: {name} not in the header", file=sys.stderr)
            continue
        ret, params, _ = fns[name]
        wrapper = bridge_name(name)
        decl = ", ".join(f"{p[0]} {p[1]}" for p in params)
        call = ", ".join(p[1] for p in params)
        lines.append(f"CUI_API void {wrapper}({decl}, {ret} *out) {{")
        lines.append(f"    *out = {name}({call});")
        lines.append("}")
        lines.append("")
        argtypes = [ctype_for(t, n) for t, n in params] + [f"P({struct_name(ret)})"]
        sigs.append(f'        ("{wrapper}", [{", ".join(argtypes)}], None),')

    for name in DIRECT:
        if name not in fns:
            print(f"warning: {name} not in the header", file=sys.stderr)
            continue
        ret, params, _ = fns[name]
        argtypes = [ctype_for(t, n) for t, n in params]
        rtype = "None" if ret == "void" else ctype_for(ret + " ", "")
        if ret == "const char *":
            rtype = "c_char_p"
        elif ret in CTYPES:
            rtype = CTYPES[ret]
        sigs.append(f'        ("{name}", [{", ".join(argtypes)}], {rtype}),')

    c_text = "\n".join(lines)
    block = (
        "        # ---- CUI 1.3 developer tools ----\n"
        + "\n".join(sigs)
        + "\n"
    )

    if args.check:
        have_c = OUT_C.read_text(encoding="utf-8") if OUT_C.exists() else ""
        have_py = CDEFS.read_text(encoding="utf-8")
        stale = have_c.strip() != c_text.strip() or block.strip() not in have_py
        if stale:
            print("generated bridges are stale; rerun tools/gen_devtools_bridge.py", file=sys.stderr)
        return 1 if stale else 0

    OUT_C.write_text(c_text, encoding="utf-8")
    py = CDEFS.read_text(encoding="utf-8")
    marker = "        # ---- CUI 1.3 developer tools ----"
    tail = "\n\n        # Clip, state & spring animations"
    if marker in py:
        start = py.index(marker)
        end = py.index(tail, start)
        py = py[:start] + block + py[end:]
    else:
        end = py.index(tail)
        py = py[:end] + "\n\n" + block.rstrip("\n") + py[end:]
    CDEFS.write_text(py, encoding="utf-8")
    print(f"wrote {OUT_C.relative_to(ROOT)} ({len(TARGETS)} bridges) and {len(DIRECT)} direct prototypes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

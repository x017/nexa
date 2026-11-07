"""ABI layout parity, symbol binding, minimal stripped builds, and import-footprint tests."""

from __future__ import annotations

import ast
import ctypes
import os
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

import nexa
from nexa import _cdefs
from nexa.build import build_native, find_c_compiler, freeze_flags


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_c_struct_sizeof_parity(tmp_path: pathlib.Path) -> None:
    """Every ctypes.Structure in _cdefs must match exact C sizeof() on this platform."""
    cc = find_c_compiler()
    pairs = []
    for name in dir(_cdefs):
        obj = getattr(_cdefs, name)
        if isinstance(obj, type) and issubclass(obj, ctypes.Structure) and obj is not ctypes.Structure:
            s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
            c_name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
            pairs.append((name, c_name, ctypes.sizeof(obj)))

    assert len(pairs) >= 75

    c_src = tmp_path / "check_sizes.c"
    c_bin = tmp_path / "check_sizes"
    lines = [
        '#include "cui/cui.h"',
        '#include "cui/cui_app.h"',
        '#include "cui/cui_render.h"',
        "#include <stdio.h>",
        "int main(void) {",
    ]
    for py_name, c_name, _ in pairs:
        lines.append(f'    printf("{py_name} %zu\\n", sizeof({c_name}));')
    lines.append("    return 0;\n}")
    c_src.write_text("\n".join(lines))

    subprocess.run([cc, "-std=c99", f"-I{REPO_ROOT / 'csrc' / 'include'}", str(c_src), "-o", str(c_bin)], check=True)
    out = subprocess.check_output([str(c_bin)], text=True)
    c_sizes = {k: int(v) for k, v in (ln.split() for ln in out.strip().splitlines())}

    for py_name, c_name, py_sz in pairs:
        assert py_sz == c_sizes[py_name], f"{py_name} ({c_name}): Python={py_sz} vs C={c_sizes[py_name]}"


def test_ast_native_symbol_and_argcount_parity() -> None:
    """Every native C symbol accessed anywhere in src/nexa/ must exist and match argtypes count."""
    lib = nexa.get_cdll()
    src_dir = REPO_ROOT / "src" / "nexa"

    for py_path in sorted(src_dir.rglob("*.py")):
        tree = ast.parse(py_path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr.startswith(("cui_", "nexa_")):
                assert hasattr(lib, node.attr), f"{py_path}:{node.lineno} references missing symbol {node.attr}"
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr.startswith(("cui_", "nexa_"))
            ):
                fn = getattr(lib, node.func.attr)
                if fn.argtypes is not None:
                    assert len(node.args) == len(fn.argtypes), (
                        f"{py_path}:{node.lineno} {node.func.attr} passed {len(node.args)} args, "
                        f"expected {len(fn.argtypes)}"
                    )


def test_minimal_stripped_builds_and_size(tmp_path: pathlib.Path) -> None:
    """Stripped minimal builds compile cleanly, bind all symbols, and stay compact (<600 KB)."""
    min_so = build_native(output_path=tmp_path / "libnexa_min.so", minimal=True)
    assert min_so.is_file()
    size_kb = min_so.stat().st_size / 1024.0
    assert size_kb < 600.0, f"Expected minimal shared library < 600 KB, got {size_kb:.1f} KB"

    lib = ctypes.CDLL(str(min_so))
    _cdefs.bind_prototypes(lib)
    feats = nexa.BuildFeatures(int(lib.nexa_features()))
    assert nexa.BuildFeatures.SW in feats
    assert nexa.BuildFeatures.GL not in feats
    assert nexa.BuildFeatures.APP not in feats
    assert nexa.BuildFeatures.DEFAULT_FONTS not in feats
    assert nexa.BuildFeatures.STB_IMAGE not in feats


def test_lazy_imports_and_freeze_flags() -> None:
    """Importing nexa in a fresh interpreter must not eagerly pull heavy stdlib modules."""
    code = (
        "import sys, nexa; "
        "assert 'dataclasses' not in sys.modules; "
        "assert 'asyncio' not in sys.modules; "
        "assert 'nexa.build' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], check=True)

    pyi_flags = freeze_flags("pyinstaller")
    assert "--exclude-module" in pyi_flags
    assert "nexa.build" in pyi_flags
    nuitka_flags = freeze_flags("nuitka")
    assert any("--nofollow-import-to=nexa.build" in f for f in nuitka_flags)

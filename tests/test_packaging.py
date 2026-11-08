"""Packaging & release readiness tests for `nexa-ui` (`import nexa`)."""

from __future__ import annotations

import pathlib
import re
import tarfile
import tempfile
import subprocess
import sys

import nexa as ui


ROOT = pathlib.Path(__file__).resolve().parent.parent


def _read_pyproject_text() -> str:
    return (ROOT / "pyproject.toml").read_text(encoding="utf-8")


def test_pyproject_metadata_and_version_sync() -> None:
    text = _read_pyproject_text()
    name_m = re.search(r'^name\s*=\s*"([^"]+)"', text, re.MULTILINE)
    ver_m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    lic_m = re.search(r'^license\s*=\s*"([^"]+)"', text, re.MULTILINE)

    assert name_m and name_m.group(1) == "nexa-ui"
    assert ver_m and ver_m.group(1) == ui.__version__
    assert lic_m and lic_m.group(1) == "MIT"
    assert 'nexa-build = "nexa.build:main"' in text
    assert 'hook-dirs = "nexa._pyinstaller:get_hook_dirs"' in text


def test_release_files_and_bundled_licenses_exist() -> None:
    required = [
        ROOT / "LICENSE",
        ROOT / "THIRD_PARTY.md",
        ROOT / "RELEASING.md",
        ROOT / "MANIFEST.in",
        ROOT / "setup.py",
        ROOT / "src" / "nexa" / "py.typed",
        ROOT / "csrc" / "third_party" / "licenses" / "LICENSE-Inter.txt",
        ROOT / "csrc" / "third_party" / "licenses" / "LICENSE-Geist.txt",
        ROOT / "csrc" / "third_party" / "licenses" / "LICENSE-Lucide.txt",
        ROOT / "csrc" / "third_party" / "licenses" / "LICENSE-Unicode.txt",
        ROOT / ".github" / "workflows" / "release.yml",
        ROOT / ".github" / "workflows" / "ci.yml",
    ]
    for path in required:
        assert path.is_file(), f"Missing required packaging file: {path}"


def test_sdist_excludes_compiled_binaries_and_includes_sources() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = pathlib.Path(tmp)
        proc = subprocess.run(
            [sys.executable, "-m", "build", "--sdist", "--no-isolation", "--outdir", str(out_dir)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=90,
        )
        # Clean up egg-info generated in-tree during `--no-isolation` sdist build
        for egg in (ROOT / "src").glob("*.egg-info"):
            for child in sorted(egg.rglob("*"), reverse=True):
                if child.is_file():
                    child.unlink()
                elif child.is_dir():
                    child.rmdir()
            egg.rmdir()

        assert proc.returncode == 0, f"sdist failed:\n{proc.stdout}\n{proc.stderr}"
        tarballs = list(out_dir.glob("*.tar.gz"))
        assert len(tarballs) == 1

        with tarfile.open(tarballs[0], "r:gz") as tf:
            names = tf.getnames()

        assert not any(n.endswith((".so", ".dylib", ".dll", ".pyd")) for n in names), (
            f"Compiled binary leaked into sdist: {[n for n in names if n.endswith(('.so', '.dylib', '.dll', '.pyd'))]}"
        )
        assert any(n.endswith("csrc/include/cui/cui.h") for n in names)
        assert any(n.endswith("csrc/nexa_bridge.c") for n in names)
        assert any(n.endswith("src/nexa/py.typed") for n in names)
        assert any(n.endswith("THIRD_PARTY.md") for n in names)

"""The loader must refuse libraries built by an older nexa instead of crashing later."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from nexa import _lib, build

ROOT = Path(__file__).resolve().parent.parent
STUB_SOURCE = "int nexa_stub_symbol(void) { return 0; }\n"


@pytest.fixture(scope="module")
def stub_library(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A loadable shared object that exports none of the CUI API."""
    src = tmp_path_factory.mktemp("stub") / "stub.c"
    src.write_text(STUB_SOURCE, encoding="utf-8")
    out = src.with_name(_lib._lib_filename())
    cc = os.environ.get("CC") or "cc"
    subprocess.run(
        [cc, "-shared", "-fPIC", "-o", str(out), str(src)],
        check=True,
        capture_output=True,
    )
    return out


def test_stub_missing_sentinel_symbols(stub_library: Path) -> None:
    missing = _lib.missing_symbols(stub_library)
    assert missing, "a stub library must report missing sentinels"
    assert set(missing) <= set(_lib._SENTINEL_SYMBOLS)


def test_stale_reason_without_stamp(stub_library: Path) -> None:
    csrc = build.find_repo_csrc(ROOT / "src" / "nexa")
    if csrc is None:
        pytest.skip("no csrc/ checkout")
    assert build.read_stamp(stub_library) is None
    assert "stamp" in (_lib.stale_reason(stub_library, csrc) or "")


def test_stale_reason_for_wheel_without_sources(stub_library: Path) -> None:
    assert _lib.stale_reason(stub_library, None) is None


def test_stamp_records_cui_version_and_options() -> None:
    csrc = build.find_repo_csrc(ROOT / "src" / "nexa")
    lib = ROOT / "src" / "nexa" / "_native" / _lib._lib_filename()
    if csrc is None or not lib.is_file():
        pytest.skip("native library not built in this checkout")
    record = build.read_stamp(lib)
    if record is None:
        pytest.skip("library predates build stamps")
    assert record["cui_version"] == build.cui_version(csrc)
    assert record["fingerprint"] == build.source_fingerprint(csrc)
    assert build.stamp_matches(lib, csrc)
    assert isinstance(record["options"], dict)


def test_explicit_stale_library_raises_clear_error(stub_library: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NEXA_LIB_PATH", str(stub_library))
    monkeypatch.setattr(_lib, "_LIB", None)
    monkeypatch.setattr(_lib, "_LIB_PATH", None)
    with pytest.raises(RuntimeError) as excinfo:
        _lib.get_cdll()
    message = str(excinfo.value)
    assert "NEXA_LIB_PATH" in message
    assert "out of date" in message
    assert "python -m nexa.build" in message


def test_source_fingerprint_tracks_sources(tmp_path: Path) -> None:
    csrc = tmp_path / "csrc"
    (csrc / "include" / "cui").mkdir(parents=True)
    (csrc / "src").mkdir()
    (csrc / "include" / "cui" / "cui.h").write_text("#define CUI_VERSION_MAJOR 1\n#define CUI_VERSION_MINOR 4\n#define CUI_VERSION_PATCH 0\n", encoding="utf-8")
    (csrc / "src" / "a.c").write_text("int a(void) { return 1; }\n", encoding="utf-8")
    first = build.source_fingerprint(csrc)
    assert build.cui_version(csrc) == "1.4.0"
    (csrc / "src" / "a.c").write_text("int a(void) { return 2; }\n", encoding="utf-8")
    assert build.source_fingerprint(csrc) != first

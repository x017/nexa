"""Tests for ``tools/doctor.py`` — the pre-flight environmental check.

Each case builds a throw-away tree so the real checkout is never touched. The
scenarios are the ones that have actually broken builds:

- a build directory owned by another user, which makes setuptools' ``egg_info``
  fail with ``Cannot update time stamp of directory 'src/nexa_ui.egg-info'``
  (it calls ``os.utime`` on it and gets EACCES);
- a dangling symlink where a directory is expected (ENOENT, same error);
- a stale compiled library, and an explicitly minimal one that must *not* be
  reported as broken.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _load_doctor():
    spec = importlib.util.spec_from_file_location("_nexa_doctor", ROOT / "tools" / "doctor.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


doctor = _load_doctor()


def _tree(tmp_path: pathlib.Path) -> pathlib.Path:
    (tmp_path / "src" / "nexa").mkdir(parents=True)
    (tmp_path / "csrc").mkdir()
    (tmp_path / "src" / "nexa" / "build.py").write_text(
        "def default_options(env=None):\n    return {'text_shaping': True}\n"
        "def read_stamp(path):\n    return None\n"
        "def source_fingerprint(csrc):\n    return 'abc'\n"
    )
    return tmp_path


def test_clean_tree_passes_except_for_deliberate_warnings(tmp_path: pathlib.Path) -> None:
    rep = doctor.run_checks(_tree(tmp_path))
    assert not rep.failed, rep.render()
    assert any("no compiled library yet" in row["title"] for row in rep.rows)


def test_missing_build_py_does_not_crash(tmp_path: pathlib.Path) -> None:
    tree = _tree(tmp_path)
    (tree / "src" / "nexa" / "build.py").unlink()
    rep = doctor.run_checks(tree)  # must not raise
    assert not rep.failed, rep.render()
    assert not any("could not run" in row["title"] for row in rep.rows), rep.render()


def test_dangling_symlink_is_a_failure(tmp_path: pathlib.Path) -> None:
    tree = _tree(tmp_path)
    (tree / "src" / "nexa_ui.egg-info").symlink_to(tree / "does-not-exist")
    rep = doctor.run_checks(tree)
    assert rep.failed
    assert any("symlink" in row["title"] for row in rep.rows)
    assert any("rm the link" in row["fix"] for row in rep.rows)


@pytest.mark.skipif(
    not hasattr(os, "geteuid") or os.geteuid() == 0,
    reason="needs a non-root user to see a foreign-owned directory",
)
@pytest.mark.skipif(
    os.environ.get("NEXA_DOCTOR_PERM_TEST") != "1",
    reason="set NEXA_DOCTOR_PERM_TEST=1 (needs sudo) to exercise the EACCES path",
)
def test_foreign_owned_directory_is_a_failure(tmp_path: pathlib.Path) -> None:
    tree = _tree(tmp_path)
    egg = tree / "src" / "nexa_ui.egg-info"
    egg.mkdir()
    os.system(f"sudo chown root:root '{egg}'")  # noqa: S605 - test scaffolding
    rep = doctor.run_checks(tree)
    assert rep.failed
    row = next(r for r in rep.rows if "not writable" in r["title"])
    assert "nexa_ui.egg-info" in row["title"]
    assert "Cannot update time stamp" in row["detail"]
    assert "chown" in row["fix"]


def test_minimal_library_is_information_not_staleness(tmp_path: pathlib.Path) -> None:
    tree = _tree(tmp_path)
    native = tree / "src" / "nexa" / "_native"
    native.mkdir(parents=True)
    (native / "libnexa_cui.so").write_bytes(b"\x7fELF")
    (tree / "src" / "nexa" / "build.py").write_text(
        "def default_options(env=None):\n    return {'text_shaping': True}\n"
        "def read_stamp(path):\n"
        "    return {'cui_version': '1.4.0', 'fingerprint': 'abc',"
        " 'options': {'minimal': True, 'text_shaping': False}}\n"
        "def source_fingerprint(csrc):\n    return 'abc'\n"
    )
    rep = doctor.run_checks(tree)
    row = next(r for r in rep.rows if "libnexa_cui.so" in r["title"])
    assert row["level"] == doctor.OK, row
    assert "minimal" in row["title"]
    assert not rep.failed


def test_unshaped_build_is_reported_as_stale(tmp_path: pathlib.Path) -> None:
    tree = _tree(tmp_path)
    native = tree / "src" / "nexa" / "_native"
    native.mkdir(parents=True)
    (native / "libnexa_cui.so").write_bytes(b"\x7fELF")
    (tree / "src" / "nexa" / "build.py").write_text(
        "def default_options(env=None):\n    return {'text_shaping': True}\n"
        "def read_stamp(path):\n"
        "    return {'cui_version': '1.4.0', 'fingerprint': 'abc',"
        " 'options': {'minimal': False, 'text_shaping': False}}\n"
        "def source_fingerprint(csrc):\n    return 'abc'\n"
    )
    rep = doctor.run_checks(tree)
    row = next(r for r in rep.rows if "libnexa_cui.so" in r["title"])
    assert row["level"] == doctor.WARN
    assert "text shaping" in row["title"]


def test_json_output_shape(capsys: pytest.CaptureFixture[str]) -> None:
    import json

    code = doctor.main(["--json"])          # returns the exit status, no SystemExit
    payload = json.loads(capsys.readouterr().out)
    assert payload["root"] == str(ROOT)
    assert isinstance(payload["rows"], list) and payload["rows"]
    assert {"level", "title", "detail", "fix"} <= set(payload["rows"][0])
    assert code in (0, 1)
    assert payload["failed"] == (code == 1)


def test_report_renders_every_level() -> None:
    rep = doctor.Report()
    rep.add(doctor.OK, "fine")
    rep.add(doctor.WARN, "hmm", "detail", "do this")
    text = rep.render()
    assert "fine" in text and "hmm" in text and "fix: do this" in text
    assert not rep.failed
    rep.add(doctor.FAIL, "broken")
    assert rep.failed

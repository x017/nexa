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


# ---------------------------------------------------------------------------
# selective runs, the root guard, and the Makefile wiring that depends on both
# ---------------------------------------------------------------------------

def test_only_runs_the_selected_checks(tmp_path: pathlib.Path) -> None:
    rep = doctor.run_checks(_tree(tmp_path), ["python"])
    assert [row["title"].split(" at ")[0] for row in rep.rows] == [
        f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    ]


def test_unknown_check_name_is_rejected(tmp_path: pathlib.Path) -> None:
    with pytest.raises(SystemExit) as exit_info:
        doctor.run_checks(_tree(tmp_path), ["nope"])
    assert "unknown check" in str(exit_info.value)


def test_quiet_prints_nothing_when_healthy(capsys: pytest.CaptureFixture[str]) -> None:
    code = doctor.main(["--only", "python", "--quiet"])
    assert code == 0
    assert capsys.readouterr().out == ""


@pytest.mark.skipif(
    os.environ.get("NEXA_DOCTOR_PERM_TEST") != "1",
    reason="set NEXA_DOCTOR_PERM_TEST=1 (needs sudo) to exercise the root guard",
)
def test_root_guard_refuses_a_foreign_checkout(tmp_path: pathlib.Path) -> None:
    # as root, pointed at a uid-1001 tree: refuse; the same tree as its owner: allow
    code = doctor.assert_not_root(pathlib.Path("/home/user/nexa"))
    assert code == 1


@pytest.mark.skipif(os.geteuid() == 0 if hasattr(os, "geteuid") else True,
                    reason="only meaningful for a non-root user")
def test_root_guard_never_blocks_a_normal_user(tmp_path: pathlib.Path) -> None:
    assert doctor.assert_not_root(tmp_path) == 0


def test_makefile_guards_builds_and_tolerates_clean() -> None:
    """`make clean` must not die on root-owned leftovers, and builds must refuse sudo."""
    makefile = (ROOT / "Makefile").read_text()
    lines = makefile.splitlines()
    for target in ("native:", "install:", "install-dev:", "sync:", "test:", "examples:"):
        line = next(l for l in lines if l.startswith(target))
        assert "guard" in line, f"{target} is not guarded: {line}"
    assert any(l.startswith("dist:") and "guard" in l for l in lines)
    clean_start = next(i for i, l in enumerate(lines) if l.startswith("clean:"))
    clean_recipe = "\n".join(lines[clean_start:clean_start + 8])
    assert "|| true" in clean_recipe, "clean must tolerate files it cannot remove"
    assert "doctor.py --only writable" in clean_recipe, "clean must report what is left"
    assert any(l.startswith("fix-permissions:") for l in lines)


class _FakeDist:
    version = "1.4.0"

    def __init__(self, url: str | None) -> None:
        self._url = url

    def read_text(self, name: str) -> str | None:
        assert name == "direct_url.json"
        return None if self._url is None else '{"url": "%s", "dir_info": {"editable": true}}' % self._url


def test_install_pointing_at_another_checkout_is_reported(tmp_path: pathlib.Path,
                                                         monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _tree(tmp_path / "repo")
    elsewhere = (tmp_path / "yapps" / "src").resolve()
    elsewhere.mkdir(parents=True)
    monkeypatch.setattr(doctor.importlib.metadata, "distribution",
                        lambda name: _FakeDist(f"file://{elsewhere}"))
    rep = doctor.run_checks(repo, ["install"])
    row = rep.rows[0]
    assert row["level"] == doctor.WARN
    assert "another checkout" in row["title"] and str(elsewhere) in row["title"]
    assert "uv pip uninstall" in row["fix"]


def test_install_editable_from_this_checkout_is_fine(tmp_path: pathlib.Path,
                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _tree(tmp_path / "repo")
    monkeypatch.setattr(doctor.importlib.metadata, "distribution",
                        lambda name: _FakeDist(f"file://{repo.resolve()}"))
    rep = doctor.run_checks(repo, ["install"])
    assert rep.rows[0]["level"] == doctor.OK
    assert "from this checkout" in rep.rows[0]["title"]


def test_install_absent_is_not_a_problem(tmp_path: pathlib.Path,
                                         monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _tree(tmp_path / "repo")

    def missing(name: str):
        raise doctor.importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(doctor.importlib.metadata, "distribution", missing)
    rep = doctor.run_checks(repo, ["install"])
    assert rep.rows[0]["level"] == doctor.OK

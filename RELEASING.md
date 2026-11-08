# Releasing `nexa-ui`

- **PyPI distribution name:** `nexa-ui` (`pip install nexa-ui`)
- **Python import name:** `nexa` (`import nexa as ui`)
- **Wheel ABI:** `py3-none-<platform>` — because `nexa` binds its C99 engine through `ctypes` without linking `libpython`, **one binary wheel per OS/architecture supports Python 3.9 through 3.14+**.

---

## 1. One-Time PyPI Trusted Publisher Setup (60 seconds, no API tokens)

Before cutting your first release, register GitHub Actions as a **Pending Publisher** on PyPI (passwordless OIDC):

1. Sign in to [PyPI Publishing Settings](https://pypi.org/manage/account/publishing/).
2. Under **Add a new pending publisher**, fill in:
   - **PyPI Project Name:** `nexa-ui`
   - **Owner:** `x017`
   - **Repository name:** `nexa` *(must match the current GitHub repository name)*
   - **Workflow name:** `release.yml`
   - **Environment name:** `pypi`
3. Click **Add**. No `PYPI_API_TOKEN` secret is required!

---

## 2. Cutting a Release (Recommended — Automated Cross-Platform CI)

Pushing a `v*.*.*` git tag triggers [`.github/workflows/release.yml`](.github/workflows/release.yml), which automatically:
1. Builds the source tarball (`nexa_ui-<version>.tar.gz`) and validates metadata with `twine check --strict`.
2. Builds LTO-optimized `py3-none-*` binary wheels via `cibuildwheel` across:
   - **Linux x86_64 & ARM64** (`manylinux` + `musllinux`)
   - **macOS Apple Silicon (`arm64`) & Intel (`x86_64`)** (`MACOSX_DEPLOYMENT_TARGET=11.0`)
   - **Windows x64** (`win_amd64` via MSVC)
3. Smoke-tests every wheel in a clean environment (`SoftwareRenderer` frame render check).
4. Creates a **GitHub Release** with auto-generated release notes and attached `.whl` + `.tar.gz` assets.
5. Publishes all wheels + sdist to **PyPI** (`https://pypi.org/project/nexa-ui/`).

### Release commands:

```bash
# 1. Update version in BOTH files so they match:
#    - pyproject.toml        -> version = "1.1.0"
#    - src/nexa/__init__.py  -> __version__ = "1.1.0"

# 2. Run the full verification suite locally:
pytest -v -W error

# 3. Commit, tag, and push:
git commit -am "Release v1.1.0"
git push origin main
git tag v1.1.0
git push origin v1.1.0
```

> **Tip — Dry-Run Before Tagging:** Open **Actions → Release nexa-ui → Run workflow** on GitHub with `publish_to_pypi` unchecked (`false`) to build and download all Linux, macOS, and Windows wheels without publishing to PyPI.

---

## 3. Building & Publishing Locally (Manual `build` + `twine`)

Install packaging tools:

```bash
python3 -m pip install --upgrade build twine auditwheel
```

Build both `sdist` (`.tar.gz`) and a platform wheel (`.whl`) into `dist/`:

```bash
rm -rf dist build
NEXA_LTO=1 python3 -m build
```

> **Linux note:** Raw local Linux wheels carry the `linux_x86_64` / `linux_aarch64` tag, which PyPI rejects until repaired to a `manylinux` tag:
> ```bash
> auditwheel repair dist/*.whl -w dist/
> rm -f dist/*-linux_*.whl
> ```

Validate PyPI metadata and `README.md` rendering:

```bash
twine check --strict dist/*
```

Upload to **TestPyPI** (optional rehearsal) or **PyPI**:

```bash
# TestPyPI:
twine upload --repository testpypi dist/*

# Production PyPI:
twine upload dist/*
```

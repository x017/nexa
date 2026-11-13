# nexa-ui — developer tasks
#
#   make                 list every target
#   make install-dev     editable install with pytest + build + twine
#   make test            run the pytest suite
#   make native          compile the C99 engine (text shaping on by default)
#   make examples        render every example headless into build/screenshots
#   make dist check      build sdist + wheel, then validate with twine
#   make publish PUBLISH=yes
#
# Override anything on the command line, e.g.:
#   make native RTL=0 LTO=1        make test PYTEST_ARGS="-k rtl -x"
#   make examples EXAMPLE=rtl      make python PY=3.12

# prefer a local virtualenv when one exists, else the interpreter on PATH
VENV    ?= .venv
VENV_PY := $(firstword $(wildcard $(VENV)/bin/python $(VENV)/Scripts/python.exe))
PY      ?= $(if $(VENV_PY),$(VENV_PY),python3)
PYTEST  ?= $(PY) -m pytest
TWINE   ?= $(PY) -m twine

# ---- installer: uv or pip -------------------------------------------------
# `uv venv` creates virtualenvs without pip, so `$(PY) -m pip` fails there.
# Prefer uv when it is on PATH (or when INSTALLER=uv); override with
#   make INSTALLER=pip install-dev      make UV=/path/to/uv install-dev
UV        ?= $(shell command -v uv 2>/dev/null)
INSTALLER ?= $(if $(strip $(UV)),uv,pip)

ifeq ($(INSTALLER),uv)
ifeq ($(strip $(UV)),)
$(error INSTALLER=uv but no uv found; install uv or use INSTALLER=pip)
endif
PIP_CMD  := $(UV) pip install --python $(PY)
VENV_CMD := $(UV) venv
else
PIP_CMD  := $(PY) -m pip install
VENV_CMD := $(PY) -m venv
endif
JOBS    ?= $(shell nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2)

# tests and tools import the checkout, installed or not
export PYTHONPATH := src$(if $(PYTHONPATH),:$(PYTHONPATH))
export PYTHONUTF8 := 1

# ---- native build options -------------------------------------------------
RTL      ?= 1          # 1 = BiDi + Arabic shaping (default), 0 = smaller build.
                       # A shapeless build at the default path is recompiled on the
                       # next import; combine with OUT=… + NEXA_LIB_PATH to keep it.
HEADLESS ?= 0          # 1 = no windowing / file dialogs
MINIMAL  ?= 0          # 1 = smallest headless software build
LTO      ?= 0          # 1 = link-time optimisation
DEBUG    ?= 0          # 1 = -O0 with symbols
OUT      ?=            # custom library path

NATIVE_FLAGS :=
ifeq ($(RTL),0)
NATIVE_FLAGS += --no-rtl
endif
ifeq ($(HEADLESS),1)
NATIVE_FLAGS += --headless
endif
ifeq ($(MINIMAL),1)
NATIVE_FLAGS += --minimal
endif
ifeq ($(LTO),1)
NATIVE_FLAGS += --lto
endif
ifeq ($(DEBUG),1)
NATIVE_FLAGS += --debug
endif
ifneq ($(strip $(OUT)),)
NATIVE_FLAGS += -o $(OUT)
endif

EXAMPLES := $(sort $(basename $(notdir $(wildcard examples/*.py))))

.DEFAULT_GOAL := help
.PHONY: help guard install install-dev sync venv native native-info test test-quick examples \
        example docs bridge bridge-check abi verify dist check require-twine testpypi publish \
        clean clean-native clean-dist ci

# ---------------------------------------------------------------------------
help: ## Show this help
	@printf 'nexa-ui developer tasks\n\n'
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) \
		| sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'
	@printf '\nBuild failing? `make doctor` explains why.\n'
	@printf 'Installer: %s%s\n' "$(INSTALLER)" "$(if $(strip $(UV)), ($(UV)),)"
	@printf 'Variables: PY=%s  VENV=%s  RTL=%s  HEADLESS=%s  MINIMAL=%s  LTO=%s  DEBUG=%s  OUT=%s\n' \
		"$(PY)" "$(VENV)" "$(RTL)" "$(HEADLESS)" "$(MINIMAL)" "$(LTO)" "$(DEBUG)" "$(OUT)"

# ---- guards ---------------------------------------------------------------
# Building as root in someone else's checkout leaves root-owned files behind,
# and setuptools then fails with "Cannot update time stamp of directory
# 'src/nexa_ui.egg-info'" on every later build as the real user.
guard:
	@$(PY) tools/doctor.py --assert-not-root

# ---- environment ----------------------------------------------------------
venv: | guard ## Create .venv with uv (no pip needed) or venv+pip
	$(VENV_CMD) $(VENV)
	@echo "created $(VENV) — now run: make install-dev"

install: | guard ## Install the package (editable, runtime only)
	$(PIP_CMD) -e .

install-dev: | guard ## Install editable + dev tools (pytest, build, twine) with uv or pip
	$(PIP_CMD) -e ".[dev]"

sync: | guard ## Create/sync the environment from pyproject (uv sync --extra dev, else pip -e ".[dev]")
ifeq ($(INSTALLER),uv)
	$(UV) sync --extra dev
else
	$(PIP_CMD) -e ".[dev]"
endif

# ---- native engine --------------------------------------------------------
native: | guard ## Compile src/nexa/_native/libnexa_cui (auto-runs on first import too)
	$(PY) -m nexa.build $(NATIVE_FLAGS)

native-info: ## Show which library is loaded and what it was built with
	@$(PY) -c "import nexa, json; from nexa import build, fonts; from pathlib import Path; \
	p = nexa.get_library_path(); \
	print('library   ', p); \
	print('stamp     ', json.dumps(build.read_stamp(p), sort_keys=True)); \
	print('shaping   ', fonts.supports_text_shaping()); \
	print('features  ', nexa.build_features())"

clean-native: ## Delete the compiled library and its build stamp
	rm -f src/nexa/_native/*.so src/nexa/_native/*.dylib src/nexa/_native/*.dll \
	      src/nexa/_native/*.stamp

# ---- tests ----------------------------------------------------------------
test: | guard ## Run the whole pytest suite
	$(PYTEST) tests -q $(PYTEST_ARGS)

test-quick: | guard ## Run everything except the slow native-build and example tests
	$(PYTEST) tests -q -k "not minimal_stripped_builds_and_size" \
		--ignore=tests/test_paradigms_and_async.py \
		--ignore=tests/test_packaging.py $(PYTEST_ARGS)

# ---- examples -------------------------------------------------------------
examples: | guard ## Render every example headless into build/screenshots
	@mkdir -p build/screenshots
	@set -e; for name in $(EXAMPLES); do \
		printf '  %-16s' "$$name"; \
		NEXA_HEADLESS=1 CUI_SCREENSHOT=build/screenshots/$$name.png \
			CUI_SCREENSHOT_FRAMES=6 timeout 60 $(PY) examples/$$name.py \
			&& echo ok || echo FAILED; \
	done
	@echo "screenshots: build/screenshots/"

example: ## Run one example: make example EXAMPLE=rtl
	@test -n "$(EXAMPLE)" || { echo "usage: make example EXAMPLE=<name>"; exit 2; }
	$(PY) examples/$(EXAMPLE).py

# ---- docs & code generation ----------------------------------------------
docs: ## Rebuild the HTML/wiki bundle from README + docs/*.md
	$(PY) docs/build_docs_bundle.py

bridge: ## Regenerate the C struct-returning bridges
	$(PY) tools/gen_devtools_bridge.py

bridge-check: ## Fail if the generated bridges are out of date
	$(PY) tools/gen_devtools_bridge.py --check

abi: ## Regenerate ctypes mirrors from csrc/include/cui/cui.h
	$(PY) tools/gen_abi.py

doctor: ## Diagnose the checkout: ownership/permissions, stale library, compiler, python
	$(PY) tools/doctor.py

verify: ## Smoke-test the installed binding end to end
	@$(PY) -c "import nexa as ui; from nexa import fonts; \
	sw = ui.SoftwareRenderer(threads=1); ctx = ui.UI(width=320, height=200, renderer=sw); \
	ctx.begin_frame(0.016); ctx.heading('nexa-ui', level=2); dd = ctx.end_frame(); \
	px = sw.render(dd); assert len(px) == 320 * 200 * 4; ctx.close(); sw.close(); \
	print('ok —', ui.get_library_path(), '| shaping:', fonts.supports_text_shaping())"

# ---- packaging ------------------------------------------------------------
# twine runs as `$(PY) -m twine`; when the dev extra is missing give the fix
# instead of a raw `No module named twine`.
require-twine: ## Check that twine is installed for $(PY)
	@$(TWINE) --version >/dev/null 2>&1 || { \
		echo "twine is not installed in $(PY)."; \
		echo "  run: make install-dev     (twine ships in the [dev] extra)"; \
		exit 2; }

dist: clean-dist guard ## Build sdist + wheel into dist/
	NEXA_LTO=1 $(PY) -m build

check: require-twine ## Validate dist/ metadata and README rendering (twine --strict)
	@ls dist/* >/dev/null 2>&1 || { echo "no dist/ yet — run 'make dist' first"; exit 2; }
	$(TWINE) check --strict dist/*

testpypi: check ## Upload dist/ to TestPyPI
	$(TWINE) upload --repository testpypi dist/*

publish: check ## Upload dist/ to PyPI (needs PUBLISH=yes)
	@test "$(PUBLISH)" = "yes" || { echo "refusing: run 'make publish PUBLISH=yes'"; exit 2; }
	$(TWINE) upload dist/*

# ---- housekeeping ---------------------------------------------------------
clean-dist: ## Remove dist/ and build/
	rm -rf dist build

clean: clean-dist ## Remove build outputs, caches and compiled libraries
	@rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage \
	       src/*.egg-info *.egg-info 2>/dev/null || true
	@find . -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@rm -f src/nexa/_native/*.so src/nexa/_native/*.dylib src/nexa/_native/*.dll \
	      src/nexa/_native/*.stamp 2>/dev/null || true
	@$(PY) tools/doctor.py --only writable,leftovers --quiet

fix-permissions: ## Hand root-owned leftovers back to you (sudo; repairs a `sudo make` run)
	@echo "chown -R $$(id -u):$$(id -g) $(CURDIR)"
	@sudo chown -R "$$(id -u):$$(id -g)" "$(CURDIR)"
	@$(PY) tools/doctor.py --only writable --quiet && echo "permissions fixed — now run: make install-dev"

ci: | guard
ci: native test docs bridge-check ## What CI runs: build, test, docs, generated-code check
	@echo "all good"

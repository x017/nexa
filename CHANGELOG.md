# Changelog

All notable changes to `nexa-ui` (installed as `nexa-ui`, imported as `nexa`).
The native engine is vendored CUI; engine-level work is listed under the nexa
release that picks it up. The published version of this page is
<http://parsa.x017.ir/nexa/guide.html#changelog>.

## [1.4.0] — unreleased · CUI 1.4

### Added

- **39 components from CUI 1.2–1.4**, taking `nexa.__all__` from 505 to 587
  exports:
  - *Instruments*: `knob`, `fader`, `level_meter`, `radial_gauge`, `readout`,
    `dot_display`, `dot_chart`, `event_track` — each returns the value the user
    dialled in.
  - *Text, media & files*: `terminal` (+`TerminalBuffer`), `file_browser`,
    `file_picker`, `fs_list`, `image_viewer`, `cropper`, `emoji_picker`,
    `month_calendar` (with events), `tour`.
  - *Charts*: `candlestick` for OHLC data, plus `annotations=` on every chart
    (`ui.ChartAnnotation`).
  - *Developer tools (CUI 1.3)*: `problems`, `pipeline`, `trace_view`,
    `waterfall`, `graph_view`, `commit_graph`, `keymap`, `test_explorer`,
    `stack_trace`, `blame`, `coverage`, `regex_tester`, `request_bar`,
    `api_explorer`, `feature_flags`, `uptime_bars`, `time_histogram`,
    `kv_editor`, `query_builder`, `schedule_picker` — plain dicts in, named
    tuples out.
  - *Utilities*: `regex_search`, `cron_next` / `cron_describe`, `url_params` /
    `url_set_params`, `http_reason` / `http_method_name`, `UI.request_wakeup`,
    `set_strings` / `get_strings`, `response_status`, `is_software`.
- **Whole-UI typography.** `UI.load_font()`, `UI.use_font()`,
  `UI.use_system_font()` and `UI.use_rtl_font()` re-face the entire app in one
  call (body/medium/display roles, with fallback chains; MONO and ICONS keep
  their own faces unless asked). `nexa.fonts` gained `find_system_font()`
  (font-directory scan + `fc-match`), `find_rtl_font()`, `list_system_fonts()`,
  `system_font_dirs()` (honours `NEXA_FONT_DIRS`) and
  `supports_text_shaping()`. Fonts can be passed as a path, bytes, or a family
  name.
- **Per-widget colours**, so one control can sit on a tinted bar or a dark hero
  section without a theme change:
  - `heading(content, level=2, color=None, size=0.0, line_height=0.0, width=None,
    align=LEFT, bg=None, pad=None, radius=None)` — `bg` draws a chip that hugs
    the text, or spans the row when `width=ui.FILL`.
  - inputs: `bg`, `text_color`, `placeholder_color`, `border_color`,
    `focus_color`.
  - cards: `bg`, `border_color`.

  Every colour argument accepts a theme token, `"#7c5cff"`, `(r, g, b[, a])`,
  `ui.Color`, or the result of `ui.mix_colors()` / `ui.with_alpha()`.
- **Examples**: `examples/instruments.py` (Reactor Console), `examples/devtools.py`
  (all 20 dev panels across tabs) and `examples/rtl.py` (Persian/Arabic app with
  RTL layout, localized calendar, terminal and charts).
- **Tooling**: a `Makefile` for the everyday tasks (`native`, `test`,
  `examples`, `docs`, `dist`, `check`, `publish`, `ci`, …) that works with
  **uv** (pip-less virtualenvs, `uv pip`/`uv venv`/`uv sync`) or **pip**, and a
  documented rebuild command, `python -m nexa.build`.
- **`make doctor`** — diagnoses a checkout before a build does: root-owned or
  read-only paths (the cause of setuptools' `Cannot update time stamp of
  directory 'src/nexa_ui.egg-info'`), dangling symlinks, a stale compiled
  library, a library built without shaping, a missing C compiler, and a bad
  `NEXA_LIB_PATH` — each with the fix to run. `--json` for CI and bug reports.

### Changed

- **Text shaping is now compiled in by default** — UAX #9 bidi and
  Arabic-script OpenType shaping ship in the stock build (+24 KB, ≈ +2 % of the
  library). `--no-rtl` (or `NEXA_TEXT_SHAPING=0`) opts out; `--minimal` still
  omits it. `build.default_options()` exposes the option set a plain build uses.
- **Latin text is untouched.** Layout direction still defaults to left-to-right
  (`direction=` is opt-in), and `cui__text_needs_shaping()` diverts only runs
  containing Arabic/Hebrew/Arabic-presentation code points, ZWNJ/ZWJ or
  directional controls. A Latin-only frame rasterises to identical pixels
  (A/B rendered: 0 of 540,000 differing pixels with the embedded font, 0 of
  360,000 with DejaVu Sans; same measured widths) and the same frame time
  (7.9 ms → 7.75 ms median at 1280×900 software, i.e. noise).
- **The native library is self-healing.** Each build writes `<lib>.stamp` (CUI
  version, content fingerprint of every `csrc/` source, and the build options).
  `import nexa` compares it with the current tree and recompiles once — printing
  one line — when the library is stale, unshaped, or missing sentinel symbols.
  Wheels (no `csrc/` next to the package) are trusted as before.
- **ABI**: struct-returning CUI calls go through generated pointer bridges
  (`csrc/nexa_bridge_extra.c` + `tools/gen_devtools_bridge.py`), so ctypes never
  passes or receives a struct by value — the libffi hazard on ARM64/Win64 is
  gone. `tools/gen_abi.py` mirrors all 96 `cui.h` structs into
  `src/nexa/_abi14.py` and checks sizes/offsets against a compiler probe.
- **Docs**: shaping is documented as the default instead of an opt-in flag, and
  the RTL section records the engine's real scope — UAX #9 P2/P3, W1–W7, N0–N2,
  I1/I2, L1/L2/L4; GSUB
  `rtla/rtlm/stch/ccmp/locl/isol/fina/medi/init/rlig/calt/rclt/liga/clig/mset`;
  GPOS `curs/kern/mark/mkmk/dist` over GDEF — along with its two limits:
  explicit directional formatting (LRE/RLE/PDF, LRI/RLI/FSI/PDI) is treated as
  boundary-neutral, and the shaper does Arabic-type joining, not Indic-style
  cluster reordering.

### Fixed

- **Persian/Arabic text rendered as disconnected letters on a stock install** —
  shaping was opt-in, so a default build drew every glyph in isolated form.
- **`AttributeError: … undefined symbol: cui_dot_display_ex`** after upgrading a
  checkout: the git-ignored `src/nexa/_native/` library survived the pull. Now
  detected and rebuilt on import (see *Changed*).
- `UI.set_strings()` kept only the `CuiStrings` pointer — the per-frame buffers
  it was given dangled on later frames; the strings and every name are now held
  for the app's lifetime.
- Devtool panels cached path pointers in C state and printed garbage file names
  from the second frame on; packed arrays are now kept per widget id and
  coverage only rebuilds when its data changes. `coverage(low, high)` takes
  percentages like the C API (50/80), and `char**` fields accept a list of
  strings.
- Engine (vendored, see the local deltas noted in `THIRD_PARTY.md`): a stale
  `ui->active` capture is released when the mouse button comes up outside the
  widget, so later clicks are no longer swallowed; modal scrim clicks are read
  before the dialog opens, so clicking outside closes it and the click that
  opens a palette no longer dismisses it.

### Performance

- The colour API costs nothing when unused — inputs/cards only write the colour
  fields that were passed, and `to_c_color()` memoises. On a 1280×900
  software-rendered form with 60 inputs and 12 cards: **5.32 ms/frame** before
  the feature, 5.55 ms in the first cut, 5.32 ms after the fix. Parsing a hex
  string dropped from 1.47 µs to 0.25 µs (0.1 µs once cached).

### Tests

- 66 tests (was 40), including pixel tests for every colour argument, RTL
  shaping invariants (joined `سلام` is narrower than the sum of its isolated
  glyphs), stale-library repair, and generated-code/ABI parity checks.

## [1.1.0] — CUI 1.1

- Multi-split docking workspaces (`dockspace`, `dock_panel`, `dock_save`,
  `dock_load`), editable `path_bar` / `path_bar_menu`, virtualized multi-column
  `tree_table` + `tree_sort`.
- CommonMark/GFM `markdown` with interactive task checkboxes, syntax-highlighted
  `code_editor`, side-by-side/inline `diff_view` with headless `diff_compute` /
  `diff_words`.
- `hex_view`, `flame_graph` + `flame_sort`, `curve_editor` + `curve_eval`,
  `gradient_editor` + `gradient_eval` (OKLab), `timeline_editor`.
- First PyPI release as `nexa-ui` with 505 typed exports and cross-platform
  wheels.

## [1.0.0]

- Initial C99 + Python zero-dependency architecture: 150+ immediate-mode
  components, OpenGL 3.3 and a multi-threaded SIMD software renderer,
  functional/procedural/OOP paradigms, 8 OKLCH accents, GIL-free
  `BackgroundRunner` and `asyncio` integration.

[1.4.0]: https://github.com/x017/nexa/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/x017/nexa/releases/tag/v1.1.0

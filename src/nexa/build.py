"""Build helper & size-optimization CLI for nexa' native C99 engine.

Supports GCC, Clang, MinGW-w64, and MSVC without requiring Python development
headers (``python3-dev``) or X11 development headers (``libx11-dev``).

Environment variables (all honored during ``pip install`` and ``nexa-build``):
    NEXA_MINIMAL=1          Enable minimal build (no embedded fonts/stb_image/app/gl, sw only unless overridden)
    NEXA_DEFAULT_FONTS=0    Omit embedded Inter/Geist/Lucide (~100 KB saved)
    NEXA_STB_IMAGE=0        Omit PNG/JPEG decoder (~25 KB saved)
    NEXA_IMAGE_ALL=1        Add BMP, GIF and TGA decoding (+7 KB)
    NEXA_WITH_APP=0         Omit desktop windowing & native dialogs
    NEXA_WITH_GL=0          Omit OpenGL 3.3 / ES 3.0 renderer
    NEXA_WITH_SW=0          Omit multi-threaded software renderer
    NEXA_PLATFORM=auto      Window backend: auto | x11_dl | x11 | win32 | cocoa | sdl2 | glfw | headless
    NEXA_LTO=1              Enable link-time optimization (-flto / /LTCG) for smallest binaries
    CC                       Override C compiler executable
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Sequence


CORE_C_FILES: Sequence[str] = (
    "src/cui_core.c",
    "src/cui_theme.c",
    "src/cui_draw.c",
    "src/cui_text.c",
    "src/cui_layout.c",
    "src/cui_widgets.c",
    "src/cui_controls.c",
    "src/cui_textedit.c",
    "src/cui_overlay.c",
    "src/cui_data.c",
    "src/cui_charts.c",
    "src/cui_extras.c",
    "src/cui_actions.c",
    "src/cui_pickers.c",
    "src/cui_disclosure.c",
    "src/cui_grid.c",
    "src/cui_treetable.c",
    "src/cui_code.c",
    "src/cui_markdown.c",
    "src/cui_editor.c",
    "src/cui_diff.c",
    "src/cui_tools.c",
    "src/cui_hex.c",
    "src/cui_social.c",
    "src/cui_media.c",
    "src/cui_planning.c",
    "src/cui_chrome.c",
    "src/cui_dock.c",
    "src/cui_viz.c",
    "src/cui_motion.c",
    "src/cui_ai.c",
    "src/cui_image.c",
    "src/cui_nodes.c",
    "src/cui_flame.c",
    "src/cui_curves.c",
    "src/cui_timeline.c",
    "src/cui_dials.c",
    "src/cui_month.c",
    "src/cui_strings.c",
    "src/cui_devtools.c",
    "src/cui_graph.c",
    "src/cui_devpanels.c",
    "src/cui_regex.c",
    "src/cui_devviews.c",
    "src/cui_instrument.c",
    "src/cui_tour.c",
    "src/cui_photo.c",
    "src/cui_files.c",
    "src/cui_terminal.c",
    "src/cui_emoji.c",
    "src/cui_loading.c",
    "src/cui_creative.c",
    "src/cui_canvas.c",
    "src/cui_voice.c",
)


def shared_lib_filename(system_name: Optional[str] = None) -> str:
    sys_name = (system_name or platform.system()).lower()
    if sys_name == "windows":
        return "nexa_cui.dll"
    if sys_name == "darwin":
        return "libnexa_cui.dylib"
    return "libnexa_cui.so"


def _env_bool(env: Dict[str, str], key: str, default: bool) -> bool:
    raw = env.get(key)
    if raw is None:
        return default
    return raw.strip().lower() not in ("0", "false", "off", "no", "")


def find_repo_csrc(start: Optional[Path] = None) -> Optional[Path]:
    here = (start or Path(__file__).resolve()).parent
    for candidate in (here.parent.parent / "csrc", here.parent / "csrc", Path.cwd() / "csrc"):
        if (candidate / "include" / "cui" / "cui.h").is_file():
            return candidate.resolve()
    return None


# --------------------------------------------------------------------------- #
# Build stamp: lets the loader tell a current library from one left over by an
# older checkout (which fails later with "undefined symbol: cui_..._ex").
# --------------------------------------------------------------------------- #

STAMP_FORMAT = 1


def stamp_path(lib_path: Path) -> Path:
    """Sidecar file recording what a compiled library was built from."""
    lib_path = Path(lib_path)
    return lib_path.with_name(lib_path.name + ".stamp")


def cui_version(csrc_dir: Path) -> str:
    """``MAJOR.MINOR.PATCH`` from ``csrc/include/cui/cui.h``."""
    header = Path(csrc_dir) / "include" / "cui" / "cui.h"
    try:
        text = header.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    nums = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "#define" and parts[1].startswith("CUI_VERSION_"):
            key = parts[1][len("CUI_VERSION_") :].lower()
            if key in ("major", "minor", "patch"):
                nums[key] = parts[2]
    if len(nums) != 3:
        return ""
    return f"{nums['major']}.{nums['minor']}.{nums['patch']}"


def source_fingerprint(csrc_dir: Path) -> str:
    """Hash of the path and contents of every C/ObjC/header file in ``csrc``.

    Contents (not mtimes) so a rebuild is only triggered by real edits — git
    rewrites timestamps on every checkout, and some filesystems round mtimes to
    a whole second.
    """
    csrc_dir = Path(csrc_dir)
    digest = hashlib.sha256()
    for pattern in ("*.c", "*.m", "*.h"):
        for path in sorted(csrc_dir.rglob(pattern)):
            try:
                data = path.read_bytes()
            except OSError:
                continue
            digest.update(str(path.relative_to(csrc_dir)).encode("utf-8", "replace"))
            digest.update(b"\0")
            digest.update(hashlib.sha256(data).digest())
    return digest.hexdigest()[:32]


def _write_stamp(output_path: Path, csrc_dir: Path, options: Dict[str, object]) -> None:
    record = {
        "format": STAMP_FORMAT,
        "cui_version": cui_version(csrc_dir),
        "fingerprint": source_fingerprint(csrc_dir),
        "options": dict(options),
    }
    try:
        stamp_path(output_path).write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
    except OSError:
        pass  # read-only install dirs are fine: the library still works


def read_stamp(lib_path: Path) -> Optional[dict]:
    try:
        record = json.loads(stamp_path(lib_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(record, dict) or record.get("format") != STAMP_FORMAT:
        return None
    return record


def stamp_matches(lib_path: Path, csrc_dir: Path) -> bool:
    """True when ``lib_path`` was compiled from the sources currently in ``csrc_dir``."""
    record = read_stamp(lib_path)
    if record is None:
        return False
    if record.get("fingerprint") != source_fingerprint(csrc_dir):
        return False
    version = cui_version(csrc_dir)
    return not version or record.get("cui_version") == version


def default_options(env: Optional[Dict[str, str]] = None) -> Dict[str, object]:
    """Options a plain ``python -m nexa.build`` would use on this machine.

    The loader compares these with a library's stamp: a build made by an older
    nexa (shaping off, for instance) is recompiled instead of silently rendering
    unjoined Persian.
    """
    env = dict(os.environ if env is None else env)
    is_minimal = _env_bool(env, "NEXA_MINIMAL", False)
    return {
        "minimal": is_minimal,
        "fonts": _env_bool(env, "NEXA_DEFAULT_FONTS", not is_minimal),
        "stb_image": _env_bool(env, "NEXA_STB_IMAGE", not is_minimal),
        "text_shaping": _env_bool(env, "NEXA_RTL", False)
        or _env_bool(env, "NEXA_TEXT_SHAPING", not is_minimal),
        "app": _env_bool(env, "NEXA_WITH_APP", not is_minimal),
        "gl": _env_bool(env, "NEXA_WITH_GL", not is_minimal),
        "sw": _env_bool(env, "NEXA_WITH_SW", True),
    }


def _detect_compiler(env: Dict[str, str], sys_name: str) -> str:
    if env.get("CC"):
        return env["CC"]
    if sys_name == "windows":
        for cc in ("cl", "gcc", "clang"):
            if shutil.which(cc):
                return cc
        raise RuntimeError("No C compiler found (install MSVC Build Tools, MinGW-w64 gcc, or clang).")
    if sys_name == "darwin":
        for cc in ("clang", "gcc"):
            if shutil.which(cc):
                return cc
        raise RuntimeError("No C compiler found (run `xcode-select --install`).")
    for cc in ("cc", "gcc", "clang"):
        if shutil.which(cc):
            return cc
    raise RuntimeError("No C compiler found (install gcc or clang).")


def find_c_compiler() -> str:
    return _detect_compiler(dict(os.environ), platform.system().lower())


def build_native(
    *,
    csrc_dir: Optional[Path] = None,
    output_path: Optional[Path] = None,
    minimal: Optional[bool] = None,
    with_app: Optional[bool] = None,
    with_gl: Optional[bool] = None,
    with_sw: Optional[bool] = None,
    default_fonts: Optional[bool] = None,
    stb_image: Optional[bool] = None,
    image_all_formats: Optional[bool] = None,
    text_shaping: Optional[bool] = None,
    backend: Optional[str] = None,
    lto: Optional[bool] = None,
    debug: bool = False,
) -> Path:
    """Compile ``libnexa_cui`` shared library with size-minimizing flags."""
    env = dict(os.environ)
    csrc = (csrc_dir or find_repo_csrc())
    if csrc is None or not csrc.is_dir():
        raise FileNotFoundError("Could not locate `csrc/` directory containing CUI sources.")

    sys_name = platform.system().lower()
    is_minimal = minimal if minimal is not None else _env_bool(env, "NEXA_MINIMAL", False)

    use_fonts = default_fonts if default_fonts is not None else _env_bool(env, "NEXA_DEFAULT_FONTS", not is_minimal)
    use_stb = stb_image if stb_image is not None else _env_bool(env, "NEXA_STB_IMAGE", not is_minimal)
    use_img_all = image_all_formats if image_all_formats is not None else _env_bool(env, "NEXA_IMAGE_ALL", False)
    # shaping is on by default (+~24 KB): without it Persian/Arabic letters never
    # join, which is a correctness bug far more than a size win
    if text_shaping is not None:
        use_shape = text_shaping
    elif _env_bool(env, "NEXA_RTL", False):
        use_shape = True
    elif "NEXA_TEXT_SHAPING" in env:
        use_shape = _env_bool(env, "NEXA_TEXT_SHAPING", True)
    else:
        use_shape = not is_minimal
    use_app = with_app if with_app is not None else _env_bool(env, "NEXA_WITH_APP", not is_minimal)
    use_gl = with_gl if with_gl is not None else _env_bool(env, "NEXA_WITH_GL", not is_minimal)
    use_sw = with_sw if with_sw is not None else _env_bool(env, "NEXA_WITH_SW", True)
    use_lto = lto if lto is not None else _env_bool(env, "NEXA_LTO", False)

    plat_choice = (backend or env.get("NEXA_PLATFORM") or "auto").strip().lower()
    if not use_app or plat_choice in ("none", "headless"):
        plat_choice = "headless"
        use_app = False
    elif plat_choice == "auto":
        if sys_name == "windows":
            plat_choice = "win32"
        elif sys_name == "darwin":
            plat_choice = "cocoa"
        else:
            plat_choice = "x11_dl"

    if output_path is None:
        out_dir = Path(__file__).resolve().parent / "_native"
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / shared_lib_filename(sys_name)
    else:
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

    sources: List[str] = [str(csrc / rel) for rel in CORE_C_FILES]
    sources.append(str(csrc / "nexa_bridge.c"))
    sources.append(str(csrc / "nexa_bridge_extra.c"))  # generated: 1.3 dev tools

    defines: List[str] = ["CUI_SHARED", "CUI_BUILDING"]
    if use_shape:
        sources.append(str(csrc / "src" / "cui_bidi.c"))
        sources.append(str(csrc / "src" / "cui_shape.c"))
        defines.append("CUI_TEXT_SHAPING")

    if use_fonts:
        sources.append(str(csrc / "src" / "cui_font_data.c"))
    # cui_emoji.c inflates its embedded table and the fonts do too, so the
    # decompressor is always needed
    sources.append(str(csrc / "src" / "cui_inflate.c"))
    if not use_fonts:
        defines.append("CUI_NO_DEFAULT_FONTS")

    if not use_stb:
        defines.append("CUI_NO_STB_IMAGE")
    elif use_img_all:
        defines.append("CUI_IMAGE_ALL_FORMATS")

    if use_sw:
        sources.append(str(csrc / "src" / "render" / "cui_render_sw.c"))
    else:
        defines.append("CUI_NO_SW")

    if use_gl:
        sources.append(str(csrc / "src" / "render" / "cui_render_gl.c"))
    else:
        defines.append("CUI_NO_GL")

    if use_app:
        sources.append(str(csrc / "src" / "platform" / "cui_app.c"))
        sources.append(str(csrc / "src" / "platform" / "cui_dialogs.c"))
        if plat_choice == "x11_dl":
            sources.append(str(csrc / "src" / "platform" / "cui_app_x11_dl.c"))
        elif plat_choice == "x11":
            sources.append(str(csrc / "src" / "platform" / "cui_app_x11.c"))
        elif plat_choice == "win32":
            sources.append(str(csrc / "src" / "platform" / "cui_app_win32.c"))
        elif plat_choice == "cocoa":
            sources.append(str(csrc / "src" / "platform" / "cui_app_cocoa.m"))
        elif plat_choice == "sdl2":
            sources.append(str(csrc / "src" / "platform" / "cui_app_sdl2.c"))
        elif plat_choice == "glfw":
            sources.append(str(csrc / "src" / "platform" / "cui_app_glfw.c"))
        else:
            raise ValueError(f"Unsupported NEXA_PLATFORM: {plat_choice!r}")
    else:
        defines.append("CUI_NO_APP")

    options: Dict[str, object] = {
        "backend": plat_choice,
        "minimal": is_minimal,
        "fonts": use_fonts,
        "stb_image": use_stb,
        "image_all_formats": use_img_all,
        "text_shaping": use_shape,
        "app": use_app,
        "gl": use_gl,
        "sw": use_sw,
        "lto": use_lto,
        "debug": debug,
    }

    cc = _detect_compiler(env, sys_name)
    cc_base = Path(cc).stem.lower()
    inc_dirs = [str(csrc / "include"), str(csrc / "src")]

    extra_cflags = shlex.split(env.get("NEXA_CFLAGS", ""))
    extra_ldflags = shlex.split(env.get("NEXA_LDFLAGS", ""))

    if cc_base == "cl":
        cmd: List[str] = [cc, "/nologo", "/LD", "/utf-8", "/Gy", "/Gw"]
        cmd += ["/Od", "/Zi"] if debug else (["/O1", "/GL"] if use_lto else ["/O1"])
        for d in defines + ["_CRT_SECURE_NO_WARNINGS"]:
            cmd.append(f"/D{d}")
        for inc in inc_dirs:
            cmd.append(f"/I{inc}")
        cmd.extend(extra_cflags)
        cmd.extend(sources)
        cmd.append(f"/Fe:{output_path}")
        cmd.append("/link")
        if not debug:
            cmd.extend(["/OPT:REF", "/OPT:ICF"])
            if use_lto:
                cmd.append("/LTCG")
        if use_app and plat_choice == "win32":
            cmd.extend(
                [
                    "user32.lib",
                    "gdi32.lib",
                    "opengl32.lib",
                    "shell32.lib",
                    "imm32.lib",
                    "dwmapi.lib",
                    "comdlg32.lib",
                    "ole32.lib",
                    "advapi32.lib",
                ]
            )
        cmd.extend(extra_ldflags)
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(cmd, cwd=tmpdir, check=True)
        _write_stamp(output_path, csrc, options)
        return output_path
    else:
        cmd = [cc]
        if plat_choice != "cocoa":
            cmd.append("-std=c99")
        if sys_name == "darwin":
            archflags = shlex.split(env.get("ARCHFLAGS", ""))
            if archflags:
                cmd.extend(archflags)
            min_macos = env.get("MACOSX_DEPLOYMENT_TARGET", "").strip()
            if min_macos:
                cmd.append(f"-mmacosx-version-min={min_macos}")
        cmd.extend(["-shared", "-fvisibility=hidden", "-ffunction-sections", "-fdata-sections"])
        if sys_name != "windows":
            cmd.append("-fPIC")
        if debug:
            cmd.extend(["-O0", "-g"])
        else:
            cmd.extend(["-Os", "-fno-unwind-tables", "-fno-asynchronous-unwind-tables"])
            if use_lto:
                cmd.append("-flto=auto" if "gcc" in cc_base or cc_base == "cc" else "-flto")
        for d in defines:
            cmd.append(f"-D{d}")
        for inc in inc_dirs:
            cmd.append(f"-I{inc}")
        if plat_choice == "cocoa":
            cmd.extend(["-DGL_SILENCE_DEPRECATION", "-fobjc-arc"])
        cmd.extend(extra_cflags)
        cmd.extend(sources)

        if sys_name == "darwin":
            if not debug:
                cmd.extend(["-Wl,-dead_strip", "-Wl,-x"])
            cmd.extend(["-lm", "-lpthread"])
            if use_app and plat_choice == "cocoa":
                cmd.extend(["-framework", "Cocoa", "-framework", "QuartzCore", "-framework", "OpenGL"])
        elif sys_name == "windows":
            if "gcc" in cc_base:
                cmd.append("-static")
            if not debug:
                cmd.extend(["-Wl,--gc-sections", "-Wl,-s"])
            if use_app and plat_choice == "win32":
                cmd.extend(
                    [
                        "-luser32",
                        "-lgdi32",
                        "-lopengl32",
                        "-lshell32",
                        "-limm32",
                        "-ldwmapi",
                        "-lcomdlg32",
                        "-lole32",
                        "-ladvapi32",
                    ]
                )
        else:
            if not debug:
                cmd.extend(["-Wl,--gc-sections", "-Wl,-s"])
            cmd.extend(["-lm", "-lpthread", "-ldl"])
            if use_app and plat_choice == "x11":
                cmd.append("-lX11")
            elif use_app and plat_choice == "sdl2":
                cmd.append("-lSDL2")
            elif use_app and plat_choice == "glfw":
                cmd.append("-lglfw")

        cmd.extend(extra_ldflags)
        cmd.extend(["-o", str(output_path)])

    subprocess.run(cmd, check=True)
    _write_stamp(output_path, csrc, options)
    return output_path


PYINSTALLER_EXCLUDES: Sequence[str] = (
    "tkinter",
    "unittest",
    "pydoc",
    "doctest",
    "xmlrpc",
    "multiprocessing",
    "pdb",
    "difflib",
    "bdb",
)


def freeze_flags(tool: str = "pyinstaller", *, uses_async: bool = False) -> List[str]:
    """Return recommended command-line flags for tiny frozen binaries."""
    excludes = list(PYINSTALLER_EXCLUDES)
    if not uses_async:
        excludes.extend(["asyncio", "concurrent", "nexa.aio"])
    excludes.append("nexa.build")
    t = tool.lower()
    if t == "pyinstaller":
        flags = ["--onefile", "--strip", "--noupx"]
        for mod in excludes:
            flags.extend(["--exclude-module", mod])
        return flags
    if t == "nuitka":
        flags = ["--standalone", "--onefile", "--lto=yes"]
        for mod in excludes:
            flags.append(f"--nofollow-import-to={mod}")
        return flags
    raise ValueError(f"Unknown freeze tool: {tool!r} (expected 'pyinstaller' or 'nuitka')")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build nexa native C99 engine with size controls.")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output shared library path")
    parser.add_argument("--minimal", action="store_true", help="Smallest headless software-render build")
    parser.add_argument("--no-fonts", action="store_true", help="Omit embedded Inter/Geist/Lucide fonts")
    parser.add_argument("--no-image", action="store_true", help="Omit stb_image PNG/JPEG decoder")
    parser.add_argument("--all-image-formats", action="store_true", help="Include BMP/GIF/TGA decoding")
    parser.add_argument(
        "--rtl",
        "--text-shaping",
        dest="rtl",
        action="store_true",
        default=None,
        help="Bidirectional paragraphs & Arabic-script OpenType shaping (on by default)",
    )
    parser.add_argument(
        "--no-rtl",
        "--no-text-shaping",
        dest="no_rtl",
        action="store_true",
        help="Drop bidi/shaping (smaller build; Persian/Arabic letters stay unjoined)",
    )
    parser.add_argument("--headless", action="store_true", help="Omit native windowing & file dialogs")
    parser.add_argument("--no-gl", action="store_true", help="Omit OpenGL renderer")
    parser.add_argument("--no-sw", action="store_true", help="Omit software renderer")
    parser.add_argument("--platform", type=str, default=None, help="Backend: auto|x11_dl|x11|win32|cocoa|sdl2|glfw|headless")
    parser.add_argument("--lto", action="store_true", help="Enable Link-Time Optimization (-flto / /LTCG)")
    parser.add_argument("--debug", action="store_true", help="Debug symbols & -O0")
    parser.add_argument("--print-freeze-flags", choices=("pyinstaller", "nuitka"), default=None,
                        help="Print recommended flags for producing small standalone binaries")
    args = parser.parse_args(argv)

    if args.print_freeze_flags:
        print(" ".join(freeze_flags(args.print_freeze_flags)))
        return 0

    out = build_native(
        output_path=args.output,
        with_app=False if (args.minimal or args.headless) else None,
        with_gl=False if (args.minimal or args.no_gl) else None,
        with_sw=False if args.no_sw else None,
        default_fonts=False if (args.minimal or args.no_fonts) else None,
        stb_image=False if (args.minimal or args.no_image) else None,
        image_all_formats=True if args.all_image_formats else None,
        text_shaping=False if args.no_rtl else (True if args.rtl else None),
        backend=args.platform,
        lto=True if args.lto else None,
        debug=args.debug,
    )
    size_kb = out.stat().st_size / 1024.0
    print(f"Built {out} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Theming, Accents, Tones, Colors & Typography

`nexa` ships with a perceptually calibrated **OKLCH / OKLab** design system out of the box—complete with smooth Light/Dark cross-fading, **8 built-in `Accent` palettes**, **9 semantic `Tone`s**, **34 live-editable `Token` slots**, embedded **Inter** & **Geist Mono** typography, and **168 Lucide vector icons**.

---

## 1. Light & Dark Theme Modes (`ui.ThemeMode`)

Switch between Light and Dark modes at startup or dynamically at runtime (surfaces and text smoothly interpolate across frames):

```python
import nexa as ui

# At window creation:
app = ui.App("Demo", theme=ui.ThemeMode.DARK, accent=ui.Accent.VIOLET)

# Inside any frame:
ctx.theme_mode = ui.ThemeMode.LIGHT  # or ui.ThemeMode.DARK
ctx.theme_toggle()                   # Built-in animated Sun/Moon icon button!
mode = ctx.theme_switcher(mode)      # 2-segment Light/Dark pill switcher
```

---

## 2. The 8 Built-In `ui.Accent` Palettes

`ui.Accent` defines **exactly 8 built-in primary highlight palettes** (matching CUI's `cui_accent` enum `0..7`):

| Enum Member | Value | `ui.accent_name(...)` | Dark Mode Hex | Light Mode Hex | Character |
|---|---:|---|---|---|---|
| `ui.Accent.NEUTRAL` | `0` | `"neutral"` | `#e8e8e8` | `#1d1d1d` | Monochrome ink / high-contrast editorial |
| `ui.Accent.VIOLET` | `1` | `"violet"` | `#a78bff` | `#7747ff` | Creative tools, AI workspaces |
| `ui.Accent.BLUE` | `2` | `"blue"` | `#6ba3ff` | `#0562ef` | Default desktop primary accent |
| `ui.Accent.GREEN` | `3` | `"green"` | `#53dca6` | `#00864b` | Finance, emerald/mint telemetry |
| `ui.Accent.AMBER` | `4` | `"amber"` | `#ffcb62` | `#f3ad20` | Warm gold instrumentation |
| `ui.Accent.ORANGE` | `5` | `"orange"` | `#ffad5e` | `#c25300` | Industrial / hardware studio |
| `ui.Accent.CORAL` | `6` | `"coral"` | `#ff9386` | `#d1403a` | Media players, warm creative apps |
| `ui.Accent.ROSE` | `7` | `"rose"` | `#ff8bc5` | `#d23286` | Vibrant magenta / pink highlight |

> **Important:** Only those 8 members exist on `ui.Accent` (`NEUTRAL`, `VIOLET`, `BLUE`, `GREEN`, `AMBER`, `ORANGE`, `CORAL`, `ROSE`). Names like `Accent.MINT`, `Accent.CYAN`, or `Accent.TEAL` do **not** exist on `ui.Accent` (`GREEN` is an emerald-mint `#53dca6` in dark mode, and `Tone.TEAL` exists on `ui.Tone` for badges/events!).
>
> Want **any custom hex or OKLCH brand color** (such as Mint `#10b981` or Cyan `#06b6d4`) as your app's primary accent? Override `Token.ACCENT` directly on `ctx.theme`—see Section 4 below!

### Enumerating All Accents Dynamically

```python
# Clean Python iteration over all 8 accents:
labels = [ui.accent_name(a).capitalize() for a in ui.Accent]
chosen = ctx.segmented("accent_picker", labels, int(ctx.accent))
if chosen != int(ctx.accent):
    ctx.accent = ui.Accent(chosen)
```

---

## 3. Semantic `ui.Tone`s (Badges, Alerts, Toasts, Kanban, Gantt)

While `ui.Accent` controls the *entire window's* primary highlight palette, **`ui.Tone`** colors individual status elements (`badge`, `alert`, `banner`, `toast`, `CalEvent`, `GanttTask`, `SwipeAction`, `status_bar_text`) so semantic meanings stay consistent regardless of theme:

| `ui.Tone` Member | Typical Use |
|---|---|
| `ui.Tone.NEUTRAL` | Default subtle chip/tag |
| `ui.Tone.INFO` | Informational sky-blue notice |
| `ui.Tone.SUCCESS` | Completed, paid, online, passing |
| `ui.Tone.WARNING` | Pending, degraded, caution |
| `ui.Tone.DANGER` | Error, destructive action, overdue |
| `ui.Tone.VIOLET` | Category tag / purple highlight |
| `ui.Tone.TEAL` | Category tag / teal-mint highlight |
| `ui.Tone.ROSE` | Category tag / rose highlight |
| `ui.Tone.ACCENT` | Tracks whichever `ui.Accent` is currently active |

---

## 4. Custom Brand Colors, Live `Token` Overrides & Perceptual OKLCH

Every color in `nexa` can be passed as:
- A **`ui.Color(r, g, b, a=255)`** value
- A hex string: **`"#10b981"`** or **`ui.Color.hex("#10b981")`** (6-digit `#RRGGBB` or 8-digit `#RRGGBBAA`)
- An RGB/RGBA tuple: **`(16, 185, 129)`** or **`(16, 185, 129, 200)`**
- A live semantic **`ui.Token`** or **`ui.Color.ACCENT`** / **`ui.Color.BACKGROUND`** / **`ui.Color.SURFACE`** / **`ui.Color.series(0..5)`** (resolved dynamically against the current Light/Dark theme!)

### Customizing Any Theme Token Live (`ctx.theme[...]`)

```python
# Set a custom Mint/Cyan brand palette on top of Dark mode:
ctx.theme[ui.Token.ACCENT] = ui.Color.hex("#14b8a6")
ctx.theme[ui.Token.ACCENT_STRONG] = ui.Color.hex("#2dd4bf")
ctx.theme[ui.Token.ACCENT_SUBTLE] = ui.with_alpha("#14b8a6", 0.16)
ctx.theme[ui.Token.ACCENT_FOREGROUND] = ui.Color.hex("#042f2e")

# Tweak corner roundness & UI scale:
ctx.theme.radius_control = 8.0   # Buttons, inputs, selects
ctx.theme.radius_surface = 14.0  # Cards
ctx.theme.radius_panel = 16.0    # Dialogs, popovers, sheets
ctx.font_scale = 1.10            # 110% proportional DPI/typography scale
ctx.set_reduced_motion(False)    # True snaps animations for accessibility
```

### Coloring Text, Headings & Their Background

`heading` and `text` take the same color forms as everything else — `color=` is a plain foreground, so it can be a hex string, an RGB(A) tuple, or a live token that follows the active accent and light/dark mode:

```python
# level 1..4 picks the size from ctx.theme.headings[level - 1]
ctx.heading("Reactor Console", level=1, color="#7c5cff")          # hex
ctx.heading("Reactor Console", level=1, color=ui.Color.ACCENT)    # live token
ctx.heading("Reactor Console", level=2, color=(124, 92, 255))     # rgb tuple
ctx.heading("Reactor Console", level=2, size=44)                  # custom scale

# a background chip behind the title (pad/radius tune it)
ctx.heading("LIVE", level=4, color=ui.Color.ACCENT_FOREGROUND,
            bg=ui.Color.ACCENT_STRONG, pad=8, radius=10)

# …or a full-width banner instead of a hugging chip
ctx.heading("Section", level=3, color=ui.Color.ACCENT, bg=ui.Color.SURFACE_RAISED, width=ui.FILL)

# body copy: same color forms, plus translucent text
ctx.text("Body copy", size=14, color=ui.Color.TEXT_SECONDARY)
ctx.text("faded live value", size=14, color=ui.with_alpha(ui.Color.hex("#22c55e"), 0.45))

# a background for a paragraph: any container's bg= draws behind its children
with ctx.box(bg=ui.Color.SURFACE_RAISED, pad=10, radius=12):
    ctx.text("Text on its own surface", color=ui.Color.TEXT_SECONDARY)
```

> `ctx.heading(...)` with no `color`/`size`/`bg` is the plain CUI heading: theme heading size in `FOREGROUND`. The overrides above are resolved in Python from `ctx.theme.headings`, so they follow `ctx.theme.font_scale` and your own `ctx.theme.headings = (...)` edits.

#### One colour for a whole region: `fg=`

Instead of threading `color=` through every call, put it on the container. `fg=`
is pushed for the lifetime of the `with` block and used by `text()` and
`heading()` whenever they are not given an explicit `color=`:

```python
with ctx.column(pad=16, gap=8, fg="#7c5cff"):
    ctx.heading("Deploy log")            # purple
    ctx.text("14:02 build started")      # purple
    ctx.text("14:03 done", color=ui.Color.SUCCESS)   # explicit colour still wins

# scopes nest and restore: the inner block returns to the outer colour
with ctx.column(fg="#7c5cff"):
    ctx.text("purple")
    with ctx.box(fg=ui.Color.DANGER):
        ctx.text("red")
    ctx.text("purple again")             # stack unwound

# it works on cards and grids too, and unwinds even when the block raises
with ctx.card(fg=ui.Color.TEXT_SECONDARY, pad=18):
    ctx.text("muted body copy")
```

`fg=` reaches `text()`, `heading()`, `markdown()` and `expandable_text()` —
anything that takes `color=`. The shorthand micro-styles (`label`,
`secondary`, `muted`, `code`, `kbd`, `link`) and widgets that own their
colouring (buttons, inputs, tables, charts…) keep the palette they already use;
pass them their own colour argument, or wrap the region and use `text()` for the
copy you want tinted.

### Perceptual Color Math (`oklch`, `mix_colors`, `with_alpha`)

```python
brand = ui.oklch(0.68, 0.16, 172.0)              # Perceptually uniform Lightness, Chroma, Hue°
soft = ui.mix_colors(brand, ui.Color.hex("#ffffff"), 0.25)  # Mixed in OKLab space (no muddy grays!)
translucent = ui.with_alpha(brand, 0.20)         # Multiply alpha by 0.20
```

### Recoloring One Component (without touching the theme)

Theme tokens restyle everything; these arguments restyle a single widget and leave the rest of the app alone — same `ColorLike` forms as above.

| Component | Color arguments |
|---|---|
| `heading(...)` | `color=`, `bg=` (+ `pad`, `radius`, `width=ui.FILL` for a banner) |
| `text(...)`, `markdown(...)`, `expandable_text(...)` | `color=` |
| `input` / `textarea` / `search` / `number` | `bg=`, `color=` (alias `text_color=`), `placeholder_color=`, `border_color=`, `focus_color=` |
| `card(...)` | `bg=`, `border_color=` (with `muted=`, `selected=`) |
| `box(...)`, `row`, `column`, `grid`, `stack`, `card(...)` | `bg=`, `border_color=`, `border=`, `radius=`, and `fg=` — the text colour inherited by everything drawn inside |
| `button` / `icon_button` | `color=` (label + glyph tint) |
| `badge`, `progress`, `readout`, `status_bar_text`, `timeline_item` | `tone=` (semantic palette) |
| `image(...)` | `tint=` |
| `knob`, `dot_display`, `loader`, `voice_orb`, `dock_item`, `gradient_text`, `spotlight` | `color=` / `from_color=`, `to_color=` |
| `line_chart`, `bar_chart`, `donut_chart`, `area`, `sparkline`, … and every `Series` | per-series `color=` |
| everything else (selects, checkboxes, switches, sliders, tables, editors, docks…) | follows `ctx.theme[...]` — change a token, or wrap the region in `ctx.set_accent` |

> Color arguments cost nothing when you don't use them: the default path skips the conversion entirely, and every `ColorLike` value is memoised by its input (a hex string parses once, then costs ~0.1 µs) — so restyling 60 inputs every frame adds ~0.2 ms to the frame.

```python
# a dark hero input on an otherwise light page
ctx.input("email", value, bg="#101425", color="#e6e9ff",
          placeholder_color="#6b7390", border_color="#2b3350", focus_color="#7c5cff")

# a tinted panel that is not a card
with ctx.card(bg=ui.with_alpha("#7c5cff", 0.12), border_color="#7c5cff", pad=18):
    ctx.text("Notice", color="#c9b8ff")

# brand-tinted button, one colour argument
if ctx.button("Deploy", variant=ui.ButtonVariant.PRIMARY, color="#22d3ee"):
    deploy()
```

### All 34 `ui.Token` Slots
- **Surfaces**: `BACKGROUND`, `SURFACE`, `SURFACE_RAISED`, `SURFACE_MUTED`
- **Text**: `FOREGROUND`, `TEXT_SECONDARY`, `TEXT_MUTED`
- **Borders**: `BORDER`, `BORDER_SUBTLE`, `BORDER_STRONG`
- **Accent**: `ACCENT`, `ACCENT_STRONG`, `ACCENT_SUBTLE`, `ACCENT_FOREGROUND`
- **Semantic**: `SUCCESS`, `WARNING`, `DANGER`, `INFO`
- **Controls**: `CONTROL_ON`, `CONTROL_GLYPH`, `CONTROL_TRACK`, `CONTROL_TRACK_HOVER`, `CONTROL_THUMB`, `CONTROL_THUMB_ON`
- **States**: `HOVER`, `ACTIVE`, `SCRIM`, `FOCUS_RING`
- **Data Viz**: `SERIES_1`, `SERIES_2`, `SERIES_3`, `SERIES_4`, `SERIES_5`, `SERIES_6`

---

## 5. Typography, Custom `.ttf` Fonts & International Fallback

Out of the box, `nexa` embeds:
- **Inter** (`FontRole.BODY`, `FontRole.MEDIUM`, `FontRole.DISPLAY`)
- **Geist Mono** (`FontRole.MONO`)
- **Lucide** (`FontRole.ICONS` — `168` crisp vector icons)

### Make the whole UI use your font

`use_font()` loads a `.ttf`/`.otf` from a **file path**, from **raw bytes**, or by
**system family name**, installs it into every text role (`BODY`, `MEDIUM`,
`DISPLAY`) and returns its font id. Call it once, right after creating the UI:

```python
import nexa as ui
from nexa import fonts

with ui.SoftwareRenderer() as sw, ui.UI(width=900, height=600, renderer=sw) as ctx:
    # 1. a font that ships with your app
    ctx.use_font("assets/PlusJakartaSans-Regular.ttf")

    # 2. or a font installed on the machine, looked up by family name
    ctx.use_font(family="Segoe UI")          # Windows
    ctx.use_font(family="SF Pro Text")       # macOS
    ctx.use_font(family="DejaVu Sans")       # Linux
    ctx.use_system_font("Noto Sans")         # shorthand for the same thing

    # 3. or raw bytes (a font embedded in your package / downloaded at runtime)
    ctx.use_font(Path("assets/brand.ttf").read_bytes())
```

`nexa.fonts` finds the files for you: `find_system_font("DejaVu Sans")`,
`find_system_font("Inter", bold=True)`, `list_system_fonts()`, and
`system_font_dirs()` (honours `NEXA_FONT_DIRS`). On Linux it also asks
`fc-match`, so aliases and per-user installs resolve.

### Fallback chains (missing glyphs)

A font only covers the scripts it was designed for. `fallbacks=` attaches up to
four faces that are consulted for any glyph the primary font lacks — the usual
combination is a Latin UI font plus a Persian/Arabic or CJK one:

```python
ctx.use_font("assets/PlusJakartaSans-Regular.ttf",
             fallbacks=["assets/Vazirmatn-Regular.ttf", "assets/NotoSansCJK-Regular.ttf"])

# or reuse an id you already loaded (roles like ui.FontRole.MONO work as ids too)
latin = ctx.font_load_file("assets/Inter-Regular.ttf")
arabic = ctx.font_load_file("assets/Vazirmatn-Regular.ttf")
ctx.font_set_role(ui.FontRole.BODY, latin)
ctx.font_add_fallback(latin, arabic)
```

Low-level pieces, if you want them explicitly: `font_load_file(path)`,
`font_load_memory(bytes)`, `font_set_role(role, id)`,
`font_add_fallback(font_id, fallback_id)`.

### Persian / Arabic / Hebrew (RTL)

Right-to-left needs two things: a shaper (on by default since CUI 1.4) and a
font with Arabic-script coverage.

```bash
python -m nexa.build                      # shaping is on by default (+~24 KB)
python -m nexa.build --no-rtl             # drop it (Persian/Arabic letters stay unjoined)
```

A library built without shaping is detected on import and recompiled once, so an
old `_native/libnexa_cui.so` cannot silently render unjoined text.

Two things "on by default" does **not** mean: your layout does not become
right-to-left (containers stay LTR unless you pass `direction=`), and Latin text
is not routed through the shaper — `cui__text_needs_shaping()` only diverts a run
that contains Arabic/Hebrew/Arabic-presentation code points, ZWNJ/ZWJ or
directional controls, so a Latin-only frame rasterises to the same pixels and
costs the same per frame as a `--no-rtl` build. Only mixed or RTL text takes the
extra pass, and only that text benefits.

```python
import nexa as ui
from nexa import fonts

print(fonts.supports_text_shaping())      # True for a default build

with ui.SoftwareRenderer() as sw, ui.UI(width=800, height=600, renderer=sw) as ctx:
    ctx.use_rtl_font()                    # first installed of Vazirmatn, Vazir, Sahel,
                                          # Noto Naskh Arabic, Tahoma, DejaVu Sans, …
    # ctx.use_rtl_font("Vazirmatn")       # or name the family yourself
    # ctx.use_font("assets/Vazirmatn-Regular.ttf")

    with ctx.frame():
        with ctx.column(pad=16, gap=8, direction=ui.TextDirection.RTL):
            ctx.heading("سلام دنیا")
            ctx.text("متن راست‌به‌چپ با شکل‌دهی صحیح حروف.")
        ctx.text("Mixed LTR/RTL", direction=ui.TextDirection.AUTO)
```

What the engine implements (from CUI's `cui_bidi.c` / `cui_shape.c`): UAX #9
paragraph resolution (P2/P3, W1–W7, N0–N2 bracket pairs, I1/I2, L1/L2/L4) plus a
compact OpenType interpreter applying `rtla/rtlm`, `stch`, `ccmp`, `locl`,
`isol/fina/medi/init`, `rlig`, `calt`, `rclt`, `liga`, `clig`, `mset` (GSUB) and
`curs`, `kern`, `mark`, `mkmk`, `dist` (GPOS) with GDEF classes.

Two limits worth knowing: **explicit directional formatting is not applied** —
`LRE/RLE/PDF` and `LRI/RLI/FSI/PDI` are treated as boundary-neutral, so use
`direction=ui.TextDirection.RTL/AUTO` on containers instead of control
characters — and the shaper targets **Arabic-type joining**, not Indic-style
cluster reordering.

`direction=` works on `text`, `box`, `row`, `column`, `grid` and `stack`
(`ui.TextDirection.INHERIT / LTR / RTL / AUTO`); `AUTO` lets the shaper pick the
paragraph base from the first strong character. Calendar and picker names can be
localized at the same time with `ctx.set_strings(months=[...], weekdays=[...],
today="امروز")`.

> **Emoji** are separate from text fonts: `ctx.load_emoji_font()` (system) or
> `ctx.load_emoji_font("NotoColorEmoji.ttf")` enables `ui.emoji(...)` and
> `ui.emoji_picker(...)`.

---

## 6. Icons (`ui.Icon`)

All **168 bundled Lucide icons** are UTF-8 string constants on `ui.Icon` and can be passed to `icon=`, `ui.icon(...)`, `ui.icon_button(...)`, `ui.nav_item(...)`, or looked up dynamically by name:

```python
ui.icon(ui.Icon.SPARKLES, size=20, color=ui.Color.ACCENT)
ui.button("Deploy", icon=ui.Icon.ROCKET, icon_right=ui.Icon.ARROW_UP_RIGHT)

# Dynamic lookup (case-insensitive, supports kebab/snake case):
glyph = ui.Icon.get("arrow-right")  # -> ui.Icon.ARROW_RIGHT
```

Popular icons include:
- **Navigation & Arrows**: `ARROW_LEFT`, `ARROW_RIGHT`, `ARROW_UP`, `ARROW_DOWN`, `ARROW_UP_RIGHT`, `CHEVRON_LEFT`, `CHEVRON_RIGHT`, `CHEVRON_DOWN`, `CHEVRON_UP`, `HOUSE`, `MENU`, `PANEL_LEFT`, `EXTERNAL_LINK`
- **Actions & Editing**: `PLUS`, `MINUS`, `X`, `CHECK`, `SEARCH`, `EDIT` / `SQUARE_PEN`, `COPY`, `TRASH` / `TRASH_2`, `SAVE` / `DOWNLOAD`, `UPLOAD`, `SHARE_2`, `REFRESH_CW`, `FILTER`, `SLIDERS_HORIZONTAL`, `SETTINGS`
- **Files, Code & Dev**: `FILE`, `FILE_TEXT`, `FOLDER`, `CODE`, `TERMINAL`, `GIT_BRANCH`, `DATABASE`, `CPU`, `LAYERS`, `GRID_3X3`, `COMMAND`, `BUG`
- **Status, Security & Social**: `CIRCLE_CHECK`, `CIRCLE_ALERT`, `TRIANGLE_ALERT`, `INFO`, `SHIELD`, `LOCK`, `USER`, `USERS`, `MAIL`, `BELL`, `HEART`, `STAR`, `PIN` / `BOOKMARK`, `THUMBS_UP`, `THUMBS_DOWN`, `SEND`
- **Media, AI & Theme**: `SPARKLES`, `ZAP`, `PLAY`, `PAUSE`, `VOLUME_2`, `MIC`, `IMAGE`, `CALENDAR`, `CLOCK`, `GLOBE`, `WIFI`, `SUN`, `MOON`, `PALETTE`

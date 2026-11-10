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

### Perceptual Color Math (`oklch`, `mix_colors`, `with_alpha`)

```python
brand = ui.oklch(0.68, 0.16, 172.0)              # Perceptually uniform Lightness, Chroma, Hue°
soft = ui.mix_colors(brand, ui.Color.hex("#ffffff"), 0.25)  # Mixed in OKLab space (no muddy grays!)
translucent = ui.with_alpha(brand, 0.20)         # Multiply alpha by 0.20
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

To load your own `.ttf` / `.otf` typeface or add CJK / Arabic / Persian / Emoji fallback chains:

```python
# Load primary UI font from file or bytes:
regular_id = ctx.font_load_file("assets/PlusJakartaSans-Regular.ttf")
ctx.font_set_role(ui.FontRole.BODY, regular_id)

# Attach an international fallback font so missing glyphs fall through seamlessly:
rtl_or_cjk_id = ctx.font_load_file("assets/Vazirmatn-Regular.ttf")
ctx.font_add_fallback(regular_id, rtl_or_cjk_id)
```

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

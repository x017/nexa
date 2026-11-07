# Complete Component Reference (150+ Widgets Across 19 Domains)

Every widget method below is available **both** on `ctx: ui.UI` (`ctx.button(...)`) **and** as a top-level function when inside an active frame (`import nexa as ui; ui.button(...)`).

---

## 1. Layout & Containers (`nexa.widgets.layout`)

All layout scopes are **unconditional** (`with ui.row(...):` always enters).

- **`box(*, id=None, dir=Direction.COLUMN, width=None, height=None, min_width=0, max_width=0, min_height=0, max_height=0, pad=0, pad_x=0, pad_y=0, pad_top=0, pad_right=0, pad_bottom=0, pad_left=0, gap=0, columns=0, min_column_width=0, wrap=False, align=Align.STRETCH, justify=Justify.START, bg=None, border_color=None, border=0, radius=0, corners=None, elevation=Elevation.NONE, scroll_x=False, scroll_y=False, clip=False, opacity=0)`**
- **`row(**box_kwargs)`** — Horizontal flex container (`wrap=True` enables multi-line flex wrap).
- **`column(**box_kwargs)`** — Vertical flex container.
- **`stack(**box_kwargs)`** — Overlapping Z-stack container (`Direction.STACK`).
- **`grid(*, columns=0, min_column_width=0, gap=12, **box_kwargs)`** — Responsive CSS-Grid-like multi-column container.
- **`card(*, id=None, width=None, height=None, pad=0, pad_x=0, pad_y=0, gap=0, dir=Direction.COLUMN, align=Align.STRETCH, wrap=False, hoverable=False, selected=False, muted=False)`** -> `CardScope` (`card.clicked` is `True` when `hoverable=True` card is clicked).
- **`scroll(id, *, width=None, height=None, pad=0, pad_x=0, pad_y=0, gap=0, horizontal=False, sticky_bottom=False, fade_edges=False)`** + **`scroll_to(id, y)`**.
- **`split(id, ratio, *, vertical=False, min_first=120, min_second=120, width=None, height=None)`** -> `SplitScope` (call `sp.next()` between pane 1 and pane 2; read updated `sp.ratio`).
- **`spacer()`** | **`gap(px)`** | **`separator()`**
- **`id_scope(key: str | int)`** | **`disabled_scope(disabled: bool = True)`**
- Queries: **`make_id(s)`**, **`last_id`**, **`last_hovered`**, **`last_rect`**, **`get_rect(id)`**, **`is_disabled`**.

---

## 2. Text & Typography (`nexa.widgets.text`)

- **`text(content, *, font=FontRole.BODY, size=0, color=None, align=TextAlign.LEFT, max_lines=0, selectable=False, strikethrough=False, underline=False, nowrap=False, width=None)`**
- **`heading(content, level=2)`** (`level` in `1..4`)
- **`label(content)`** | **`secondary(content)`** | **`muted(content)`**
- **`code(content)`** — Inline monospace pill (`Geist Mono`).
- **`kbd(shortcut)`** — Styled keycap chord (`"Ctrl K"`, `"Shift Tab"`).
- **`link(label, **opts) -> bool`** — Clickable underlined link.
- **`icon(glyph, size=16.0, color=None)`** — Renders any `ui.Icon.*` glyph.

---

## 3. Buttons & Actions (`nexa.widgets.actions`)

- **`button(label, *, variant=ButtonVariant.DEFAULT, size=ControlSize.MD, icon=None, icon_right=None, disabled=False, loading=False, full_width=False, selected=False, tooltip=None, shortcut=None, width=None, color=None) -> bool`**
  - `ButtonVariant`: `DEFAULT`, `PRIMARY`, `SECONDARY`, `OUTLINE`, `GHOST`, `DANGER`, `LINK`.
- **`icon_button(icon, **button_opts) -> bool`**
- **`button_group()`** — Unconditional scope joining child buttons into a segmented bar.
- **`copy_button(id, text_to_copy, *, label=None, copied_label="Copied", size=ControlSize.MD, ghost=False) -> bool`**
- **`hold_button(label, *, duration=1.2, variant=ButtonVariant.DANGER, icon=None, size=ControlSize.MD, disabled=False) -> bool`** — Press-and-hold progress button for destructive/financial actions.
- **`confirm_button(label, *, confirm_label="Click to confirm", icon=None, variant=ButtonVariant.SECONDARY, size=ControlSize.MD, timeout=3.0, disabled=False) -> bool`** — Two-step morphing confirmation button.
- **`status_button(label, status: Status, *, busy_label=None, success_label="Done", error_label="Failed", variant=ButtonVariant.PRIMARY, size=ControlSize.MD, icon=None) -> bool`** (`Status`: `IDLE`, `BUSY`, `SUCCESS`, `ERROR`).
- **`split_button(label, menu_items, *, variant=ButtonVariant.PRIMARY, size=ControlSize.MD, icon=None, disabled=False) -> int`** (`0` = main click, `1..N` = dropdown item `0..N-1`, `-1` = none).
- **`segmented(id, labels, selected: int, *, icons=None, size=ControlSize.MD, full_width=False) -> int`**
- **`toggle_group(id, labels, values: Sequence[bool], *, icons=None, icon_only=False, exclusive=False, size=ControlSize.MD) -> list[bool]`**
- **`reactions(id, items: Sequence[Reaction]) -> tuple[list[Reaction], int]`**
- **`speed_dial(id, actions: Sequence[SpeedAction], *, icon=None, place=Placement.TOP) -> int`**
- **`swipe_item(id, *, left=(), right=())`** -> `SwipeItemScope` (`sw.action`: `0..99` left, `100+` right, `-1` none).
- **`command_palette(open: bool, commands: Sequence[Command], *, placeholder="Type a command...") -> tuple[bool, int]`**
- **`theme_switcher(mode: int) -> int`** | **`theme_toggle() -> bool`**

---

## 4. Selection Controls (`nexa.widgets.selection`)

- **`checkbox(label, checked: bool, *, description=None, indeterminate=False, disabled=False) -> bool`**
- **`switch(label, on: bool, *, description=None, disabled=False) -> bool`**
- **`radio(label, current: int, option_value: int) -> int`**
- **`radio_group(id, labels, selected: int, *, descriptions=None, disabled=False) -> int`**
- **`radio_cards(id, choices: Sequence[Choice], selected: int, *, columns=0, disabled=False) -> int`**
- **`slider(label, value: float, min_val=0.0, max_val=1.0, *, step=0.0, format=None, show_value=False, ticks=False, disabled=False, width=None) -> float`**
- **`range_slider(label, low: float, high: float, min_val=0.0, max_val=1.0, **opts) -> tuple[float, float]`**
- **`rating(id, value: int, max_stars=5, *, read_only=False, size=0) -> int`**
- **`chip(label, active: bool = False, *, icon=None, removable=False, tone=Tone.NEUTRAL, size=ControlSize.MD) -> bool | tuple[bool, bool]`**
- **`control_tile(label, on: bool, *, detail=None, icon=None, width=None, disabled=False) -> bool`**

---

## 5. Text & Specialized Inputs (`nexa.widgets.inputs`)

- **`input(id, value: str, *, max_bytes=512, label=None, placeholder=None, icon=None, hint=None, error=None, password=False, disabled=False, clearable=False, autofocus=False, read_only=False, size=ControlSize.MD, width=None, prefix=None, suffix=None) -> str`**
- **`search(id, value: str, *, placeholder="Search...", size=ControlSize.MD, width=None) -> str`**
- **`textarea(id, value: str, *, max_bytes=8192, height=120.0 | ui.FILL, **input_opts) -> str`**
- **`number(id, value: float, min_val=0.0, max_val=100.0, *, step=1.0, decimals=0, label=None, prefix=None, suffix=None, width=None) -> float`**
- **`scrub(label, value: float, min_val=-1e9, max_val=1e9, *, step=1.0, decimals=2, suffix=None, width=None) -> float`**
- **`money_input(id, cents_or_amount: float, *, symbol="$", code="USD", decimals=2, allow_negative=False, label=None, width=None) -> float`**
- **`inline_edit(id, value: str, *, font=FontRole.BODY, size=0, placeholder="Untitled", width=None) -> str`**
- **`tag_input(id, tags: list[str] | str, *, label=None, placeholder="Add tag...", max_tags=0, width=None) -> list[str] | str`**
- **`otp_input(id, code: str, digits=6, *, masked=False) -> tuple[str, bool]`** (`(code, completed)`)
- **`password_strength(password: str, *, show_rules=True) -> int`** (`0..4` score)
- **`shortcut_recorder(id, combo: KeyCombo, *, clearable=True, width=None) -> KeyCombo`**
- **`signature_pad(id, *, width=None, height=160.0, pen_color=None, stroke_width=2.2, label=None) -> bool`** (+ `signature_strokes(id)`, `signature_clear(id)`)
- **`dropzone(id, *, title=None, description=None, icon=None, accept=None, height=0, width=None, compact=False) -> tuple[list[str], bool]`** (`(accepted_paths, browse_clicked)`)

---

## 6. Pickers (`nexa.widgets.pickers`)

- **`select(id, options, selected: int, *, label=None, placeholder=None, width=None, size=ControlSize.MD) -> int`**
- **`combobox(id, options, selected: int, *, label=None, placeholder="Search...", width=None) -> int`**
- **`multi_select(id, options, selected: Sequence[bool], *, label=None, placeholder="Select...", width=None) -> list[bool]`**
- **`calendar(id, date: Date, *, min_date=None, max_date=None) -> Date`**
- **`date_picker(id, date: Date, *, label=None, width=None, min_date=None, max_date=None) -> Date`**
- **`range_calendar(id, date_range: DateRange, *, months=2) -> DateRange`**
- **`date_range_picker(id, date_range: DateRange, *, label=None, width=None, months=2) -> DateRange`**
- **`time_picker(id, hour: int, minute: int, *, use_24h=True, step_minutes=1, label=None, width=None) -> tuple[int, int]`**
- **`time_dial(id, hour: int, minute: int, *, use_24h=True, size=200.0) -> tuple[int, int]`**
- **`wheel_picker(id, items, selected: int, *, visible_rows=5, loop=False, width=None) -> int`**
- **`ruler_slider(label, value: float, min_val: float, max_val: float, *, step=1.0, major_every=10, unit=None, width=None) -> float`**
- **`histogram_slider(label, bins, low: float, high: float, min_val: float, max_val: float, *, height=56.0, width=None) -> tuple[float, float]`**
- **`color_picker(id, color: ColorLike, *, alpha=False, swatches=True, hex_input=True, popover=False, width=None) -> Color`**

---

## 7. Navigation (`nexa.widgets.navigation`)

- **`tabs(id, labels, selected: int, *, variant=TabsVariant.LINE, icons=None, badges=None) -> int`** (`TabsVariant`: `LINE`, `PILL`, `ENCLOSED`)
- **`nav_section(title)`** | **`nav_item(label, *, icon=None, badge=None, selected=False, disabled=False, group=None) -> bool`**
- **`breadcrumb(items, *, separator=None) -> int`** (returns clicked crumb index or `-1`)
- **`pagination(id, page: int, page_count: int, *, siblings=1) -> int`**
- **`stepper(steps, current: int, *, clickable=True) -> int`**
- **`tab_bar(id, items: Sequence[TabBarItem], selected: int, *, pill=False, icon_only=False, width=None) -> int`**
- **`dock(id, *, magnify=0.45, base_size=44.0)`** + **`dock_item(icon, label, *, running=False, attention=False, badge=0) -> bool`** + **`dock_separator()`**
- **`toc(id, scroll_id, headings, *, title="On this page", width=200.0) -> int`** + **`toc_anchor(scroll_id, index)`**

---

## 8. Overlays, Menus & Disclosure (`nexa.widgets.overlays`)

All popup/overlay scopes are **conditional**—always write `with ui.dialog(...) as d: if d: ...`!

- **`tooltip(text)`** — Attaches a hover tooltip to the immediately preceding widget.
- **`popover(id, *, place=Placement.BOTTOM_START, width=0)`** (`popover_open(id)`, `popover_is_open(id)`, `popover_close()`)
- **`hover_card(id, *, width=280.0, place=Placement.BOTTOM)`**
- **`confirm_popover(id, *, title="Are you sure?", description=None, confirm_label="Confirm", cancel_label="Cancel", danger=False) -> bool`** (`confirm_popover_open(id)` opens it on the anchor widget)
- **`menu(label, *, icon=None, variant=ButtonVariant.OUTLINE, size=ControlSize.MD)`** + **`context_menu(id)`** + **`user_menu(name, *, detail=None, avatar_tex=0, status=None, compact=False)`**
  - Inside menus: **`menu_item(label, *, icon=None, shortcut=None, disabled=False, danger=False, checked=False) -> bool`**, **`menu_separator()`**, **`menu_label(text)`**.
- **`dialog(title, open: bool, *, description=None, width=440.0, dismissible=True, close_button=True)`** -> `BoolStateScope` (`dlg.open`) + **`dialog_footer()`**.
- **`sheet(title, open: bool, *, description=None, side=Side.RIGHT, size=380.0, modal=True)`** -> `BoolStateScope` (`sh.open`).
- **`accordion(title, expanded: bool, *, subtitle=None, icon=None)`** -> `BoolStateScope` (`acc.open`).
- **`expandable_card(title, expanded: bool, *, subtitle=None, icon=None, badge=None, width=None)`** -> `BoolStateScope`.
- **`expandable_text(id, text, *, lines=3, more_label="Show more", less_label="Show less")`**

---

## 9. Feedback, Status & Badges (`nexa.widgets.feedback`)

- **`toast(title, *, description=None, tone=Tone.NEUTRAL, duration=4.0, action=None, dismissible=True) -> int`** (+ `toast_action_clicked(h)`, `toast_dismiss(h)`)
- **`alert(title, *, description=None, tone=Tone.INFO, icon=None, action=None, dismissible=False) -> tuple[bool, bool]`**
- **`banner(title, open: bool = True, *, action=None, tone=Tone.INFO, icon=None, dismissible=True) -> tuple[bool, bool]`**
- **`progress(value: float, *, indeterminate=False, label=None, show_value=False, tone=Tone.ACCENT, height=0, width=None)`**
- **`progress_ring(label, value: float, *, size=64.0, thickness=6.0, sublabel=None, color=None, indeterminate=False)`**
- **`spinner(size=18.0)`** | **`loader(*, style=LoaderStyle.SPINNER, size=24.0, label=None, color=None)`** | **`skeleton(width, height, *, circle=False)`**
- **`badge(text, *, tone=Tone.NEUTRAL, outline=False, dot=False, icon=None, size=ControlSize.MD)`**
- **`avatar(name, *, image=0, size=36.0, circle=True, status=None)`** | **`avatar_group(names, *, max_visible=4, size=32.0)`** | **`avatar_upload(id, name, image=0, *, size=72.0) -> tuple[int, bool]`**
- **`empty_state(title, *, description=None, icon=None, action=None) -> bool`**
- **`metric(label, value, *, delta=None, delta_text=None, hint=None, spark=None, lower_is_better=False, width=None)`**
- **`meter(label, used: float, total: float, unit="", *, warn_at=0.75, crit_at=0.90, width=None)`**
- **`countdown(id, remaining_seconds: float, *, label=None, show_days=False, compact=False) -> bool`**
- **`checklist(id, steps: Sequence[CheckStep], *, title=None, dismissible=False, width=None) -> tuple[int, bool]`**

---

## 10. Data, Virtual Lists, Tables, Grids & Code (`nexa.widgets.data`)

- **`tree(label, expanded=False, *, icon=None, badge=None, leaf=False, selected=False)`** -> `TreeScope` (`if tr:` for children; `tr.expanded`, `tr.clicked`).
- **`list_item(title, *, subtitle=None, trailing=None, icon=None, avatar=None, badge=None, badge_tone=Tone.NEUTRAL, chevron=False, selected=False, active=False) -> bool`**
- **`virtual_list(id, row_count: int, row_height: float, height: SizeLike = None)`** -> `VirtualListScope` (iterate `for i in vl.indices:`—renders 1,000,000+ rows in O(visible)!).
- **`reorder(id, order: Sequence[int], *, horizontal=False, gap=6.0, width=None)`** -> `ReorderScope` (`with ro.item(pos): ...`; read `ro.order`).
- **`timeline_item(title, *, description=None, time=None, icon=None, tone=Tone.ACCENT, last=False)`**
- **`table(id, columns: Sequence[TableColumn], *, sort=None, height=None, striped=False, compact=False, selectable=False)`** -> `TableScope` (`if tbl:`; `tbl.row(selected=...) -> bool`, `tbl.cell()`, `tbl.cell_text(s)`, `tbl.sort`).
- **`data_grid(id, columns: Sequence[GridColumn], row_count: int, *, width=None, height=None, row_height=0, selected=None, sort=None, striped=False, borderless=False, cursor=0)`** -> `DataGridScope` (`if dg:`; `for r in dg.rows:`, `dg.row(r)`, `dg.cell_text(s)`, `dg.edit(val)`, `dg.selected`, `dg.sort`, `dg.cursor`).
- **`filter_bar(id, fields: Sequence[FilterField], masks: Sequence[int], search: str = "", *, clearable=True, width=None) -> tuple[list[int], str]`**
- **`code_block(id, source, *, lang="python", line_numbers=True, copyable=True, wrap=False, highlight_line=0, max_height=0, filename=None)`**
- **`json_view(id, json_str, *, default_open_depth=2, max_height=0, copyable=True) -> bool`**

---

## 11. Charts & Data Visualization (`nexa.widgets.charts`)

- **`line_chart(id, series: Sequence[Series], *, labels=None, height=200.0, width=None, smooth=False, area=False, show_points=False, show_grid=True, show_legend=False, y_min=0, y_max=0, reference_y=None, reference_label=None, y_format=None)`**
- **`bar_chart(id, series: Sequence[Series], *, labels=None, stacked=False, horizontal=False, height=200.0, width=None, **opts)`**
- **`donut_chart(id, values, labels=None, *, colors=None, height=180.0, width=None, thickness=0.32, show_legend=True, center_label=None, format=None)`**
- **`sparkline(values, *, width=100.0, height=28.0, color=None, area=True)`**
- **`gauge(label, value: float, *, min_val=0.0, max_val=1.0, sublabel=None, size=120.0, color=None)`**
- **`heatmap(id, values, rows: int, cols: int, *, row_labels=None, col_labels=None, color=None, show_values=False, format=None, cell_size=0, width=None) -> tuple[int, int]`**
- **`calendar_heatmap(id, start_date: Date, daily_values, *, color=None, unit="contributions", cell_size=0) -> int`**
- **`treemap(id, items: Sequence[VizItem], *, width=None, height=240.0, format=None) -> int`**
- **`radar_chart(id, series: Sequence[Series], axes_labels, *, max_val=0, size=220.0, show_legend=False)`**
- **`funnel(id, stages: Sequence[VizItem], *, width=None, height=220.0, format=None) -> int`**
- **`sankey(id, nodes: Sequence[str], links: Sequence[SankeyLink], *, width=None, height=260.0, format=None, node_width=0) -> int`**
- **`waffle(id, parts: Sequence[VizItem], *, rows=10, cols=10, title=None, cell_size=0, legend=True)`**
- **`split_bar(id, parts: Sequence[VizItem], *, height=10.0, width=None, legend=True, format=None)`**
- **`bar_list(id, items: Sequence[VizItem], *, format=None, show_percent=False, color=None, width=None) -> int`**
- **`activity_rings(id, rings: Sequence[VizItem], *, size=120.0, legend=False, center_text=None, sublabel=None)`**
- **`scatter_chart(id, series: Sequence[ScatterSeries], *, width=None, height=220.0, x_label=None, y_label=None, x_format=None, y_format=None, no_legend=False) -> tuple[int, int]`**

---

## 12–19. Planning, AI, Social, Media, Motion, Chrome, Tools & Node/Canvas

- **Planning (`nexa.widgets.planning`)**:
  - `kanban(id)` -> `KanbanScope` (`board.column(title, count, dot=..., width=...)`, `board.card(id)`, `board.move`)
  - `week_calendar(id, week_start: Date, events: Sequence[CalEvent], **opts) -> tuple[list[CalEvent], int]`
  - `gantt(id, tasks: Sequence[GanttTask], origin: Date, days: int, **opts) -> tuple[list[GanttTask], int]`
- **AI & Agents (`nexa.widgets.ai`)**:
  - `reasoning(id, *, thinking=False, seconds=0, title=None, default_open=False)`
  - `tool_call(id, name, *, status=TaskStatus.DONE, detail=None, input_text=None, output_text=None, seconds=0)`
  - `agent_plan(id, steps: Sequence[PlanStep], *, title=None, width=None)` | `agent_status(label, *, detail=None, status=TaskStatus.RUNNING, seconds=0)`
  - `source_list(id, sources: Sequence[Source], *, compact=False) -> int` | `citation(number: int, source: Source) -> bool`
  - `context_meter(id, used: int, limit: int, *, unit="tokens", parts=None, cost_usd=-1)`
  - `response_actions(id, *, copy_text=None, vote=0, regenerate=True, edit=False, branch=False, more=False) -> tuple[ResponseFlags, int]`
  - `prompt_suggestions(id, items: Sequence[PromptSuggestion], *, columns=2, width=None) -> int`
  - `model_picker(id, models: Sequence[Model], selected: int, *, ghost=False, size=ControlSize.SM) -> int`
  - `chat_composer(id, text: str, *, placeholder=..., busy=False, attachments=None, models=None, model=0, **opts) -> ComposerResult`
  - `voice_orb(id, state=VoiceState.IDLE, level=0.0, *, size=72.0, color=None) -> bool`
- **Social (`nexa.widgets.social`)**: `chat_message`, `chat_divider`, `typing_indicator`, `comment`, `presence`.
- **Media (`nexa.widgets.media`)**: `image_load`, `image_load_bytes`, `image_create`, `image_destroy`, `image`, `carousel`, `image_compare`, `card_stack`, `waveform`, `now_playing`, `counter`, `ticker`.
- **Motion (`nexa.widgets.motion`)**: `shimmer_text`, `typewriter`, `text_reveal`, `word_rotate`, `number_roll`, `gradient_text`, `spotlight`, `animate`, `animate_spring`.
- **Desktop Chrome (`nexa.widgets.chrome`)**: `menu_bar` + `menu_bar_menu`, `toolbar` + `toolbar_button` / `toolbar_toggle` / `toolbar_separator` / `toolbar_spacer`, `status_bar` + `status_bar_item` / `status_bar_text` / `status_bar_progress` / `status_bar_spacer`, `doc_tabs` (`DocTabsResult.apply_to(tabs)`).
- **Developer Tools (`nexa.widgets.tools`)**: `inspector` + `inspector_group`, `prop_float`, `prop_int`, `prop_text`, `prop_bool`, `prop_enum`, `prop_color`, `prop_vec2/3/4`, `LogBuffer` + `log_view`.
- **Node Editor & Vector Canvas (`nexa.widgets.nodes_canvas`)**: `node_editor` (`ed.node`, `ed.input`, `ed.output`, `ed.content`, `ed.link`, `ed.created_links`, `ed.removed_links`), `canvas(id, w, h, paint_fn)`, `draw_rect`, `draw_rect_border`, `draw_rect_gradient`, `draw_line`, `draw_polyline`, `draw_polygon`, `draw_circle`, `draw_arc`, `draw_bezier`, `draw_text`, `draw_image`, `clip_scope`, `state_buffer`.

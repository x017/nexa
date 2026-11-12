# Complete Component Reference (190+ Widgets Across 22 Domains)

Every widget method below is available **both** on `ctx: ui.UI` (`ctx.button(...)`) **and** as a top-level function when inside an active frame (`import nexa as ui; ui.button(...)`).

---

## 1. Layout & Containers (`nexa.widgets.layout`)

All layout scopes are **unconditional** (`with ui.row(...):` always enters).

- **`box(*, id=None, dir=Direction.COLUMN, width=None, height=None, min_width=0, max_width=0, min_height=0, max_height=0, pad=0, pad_x=0, pad_y=0, pad_top=0, pad_right=0, pad_bottom=0, pad_left=0, gap=0, columns=0, min_column_width=0, wrap=False, align=Align.STRETCH, justify=Justify.START, bg=None, border_color=None, border=0, radius=0, corners=None, elevation=Elevation.NONE, scroll_x=False, scroll_y=False, clip=False, opacity=0)`** -> `BoxScope`
- **`row(**box_kwargs)`** — Horizontal flex container (`wrap=True` enables multi-line flex wrap).
- **`column(**box_kwargs)`** — Vertical flex container.
- **`stack(**box_kwargs)`** — Overlapping Z-stack container (`Direction.STACK`).
- **`grid(columns=0, *, min_column_width=0.0, **box_kwargs)`** — Responsive CSS-Grid-like multi-column container.
- **`card(*, id=None, width=None, height=None, min_width=0.0, max_width=0.0, pad=0.0, pad_x=0.0, pad_y=0.0, gap=0.0, dir=Direction.COLUMN, align=Align.DEFAULT, wrap=False, hoverable=False, muted=False, selected=False)`** -> `CardScope` (`card.clicked` is `True` when a `hoverable=True` card is clicked).
- **`scroll(id=None, *, width=None, height=None, horizontal=False, pad=0.0, gap=0.0, fade_edges=False, fade_color=None)`** -> `SimpleScope` + **`scroll_to(scroll_id, y)`**.
- **`split(id, ratio, *, vertical=False, min_first=0.0, min_second=0.0, width=None, height=None)`** -> `SplitScope` (call `sp.next()` between pane 1 and pane 2; read updated `sp.ratio`).
- **`spacer()`** | **`gap(size)`** | **`separator()`**
- **`id_scope(key: str | int)`** | **`disabled_scope(disabled: bool = True)`**
- Queries: **`make_id(key)`**, **`last_id`**, **`last_hovered`**, **`last_rect`**, **`get_rect(widget_id)`**, **`is_disabled`**.

---

## 2. Text & Typography (`nexa.widgets.text`)

- **`text(content, *, font=FontRole.BODY, size=0.0, color=None, align=TextAlign.LEFT, nowrap=False, tabular=False, selectable=False, width=None, line_height=0.0)`**
- **`heading(content, level=2)`** (`level` in `1..4`)
- **`label(content)`** | **`secondary(content)`** | **`muted(content)`**
- **`code(content)`** — Inline monospace pill (`Geist Mono`).
- **`kbd(keys)`** — Styled keycap chord (`"Ctrl K"`, `"Shift Tab"`).
- **`link(content) -> bool`** — Clickable underlined link.
- **`icon(glyph, size=16.0, color=Color.FOREGROUND)`** — Renders any `ui.Icon.*` glyph.
- Fonts & metrics: **`measure_text(content, *, font=FontRole.BODY, size=13.0) -> TextMetrics`**, **`font_load_file(path) -> int`**, **`font_load_memory(data) -> int`**, **`font_set_role(role, font_id)`**, **`font_add_fallback(font_id, fallback_font_id)`**.

---

## 3. Buttons & Actions (`nexa.widgets.actions`)

- **`button(label, *, variant=ButtonVariant.DEFAULT, size=ControlSize.MD, icon=None, icon_right=None, disabled=False, loading=False, full_width=False, selected=False, tooltip=None, shortcut=None, width=None, color=None) -> bool`**
  - `ButtonVariant`: `DEFAULT`, `PRIMARY`, `SECONDARY`, `OUTLINE`, `GHOST`, `DANGER`, `LINK`.
- **`icon_button(icon, **button_opts) -> bool`**
- **`button_group()`** -> `SimpleScope` — Unconditional scope joining child buttons into a segmented bar.
- **`copy_button(id, text_to_copy) -> bool`**
- **`hold_button(label, *, duration=0.0, icon=None, variant=ButtonVariant.DEFAULT) -> bool`** — Press-and-hold progress button for destructive/financial actions.
- **`confirm_button(label, *, confirm_label=None, icon=None, variant=ButtonVariant.DEFAULT, size=ControlSize.MD, timeout=0.0) -> bool`** — Two-step morphing confirmation button.
- **`status_button(label, status=Status.IDLE, *, busy_label=None, success_label=None, error_label=None, icon=None, variant=ButtonVariant.PRIMARY, size=ControlSize.MD) -> bool`** (`Status`: `IDLE`, `BUSY`, `SUCCESS`, `ERROR`).
- **`split_button(label, items, *, variant=ButtonVariant.PRIMARY, size=ControlSize.MD, icon=None, item_icons=None, disabled=False) -> int`** (`0` = main click, `1..N` = dropdown item `0..N-1`, `-1` = none).
- **`segmented(id, items, index: int, *, size=ControlSize.MD, full_width=False, icons=None) -> int`**
- **`toggle_group(id, labels, values: Sequence[bool], *, icons=None, exclusive=False, icon_only=False, size=ControlSize.MD) -> list[bool]`**
- **`reactions(id, items: Sequence[Reaction]) -> tuple[list[Reaction], int]`**
- **`speed_dial(id, actions: Sequence[SpeedAction], *, icon=None, placement=Placement.TOP, tooltip=None) -> int`**
- **`swipe_item(id, *, left=(), right=())`** -> `SwipeItemScope` (`SwipeScope`; `sw.action`: `0..99` left, `100+` right, `-1` none).
- **`command_palette(is_open: bool, commands: Sequence[Command]) -> tuple[bool, int]`**
- **`theme_switcher(mode: int, *, with_system=False) -> int`** | **`theme_toggle() -> bool`**

---

## 4. Selection Controls (`nexa.widgets.selection`)

- **`checkbox(label, value: bool, *, description=None, disabled=False, indeterminate=False) -> bool`**
- **`switch(label, value: bool, *, description=None, disabled=False) -> bool`**
- **`radio(label, value: int, option: int, *, description=None, disabled=False) -> int`**
- **`radio_group(id, items, index: int) -> int`**
- **`radio_cards(id, choices: Sequence[Choice], index: int, *, columns=0) -> int`**
- **`slider(label, value: float, min_value=0.0, max_value=1.0, *, step=0.0, show_value=False, format=None, disabled=False, width=None) -> float`**
- **`range_slider(label, lo: float, hi: float, min_value=0.0, max_value=1.0) -> tuple[float, float]`**
- **`rating(id, value: int, max_stars=5) -> int`**
- **`chip(label, selected: bool, *, icon=None, disabled=False) -> bool`**
- **`control_tile(label, on: bool, *, icon=None, detail=None, color=None, width=None, wide=False) -> bool`**

---

## 5. Text & Specialized Inputs (`nexa.widgets.inputs`)

- **`input(id, value: str, *, max_bytes=512, label=None, placeholder=None, icon=None, hint=None, error=None, password=False, disabled=False, clearable=False, autofocus=False, read_only=False, size=ControlSize.MD, width=None, height=0.0, prefix=None, suffix=None) -> str`**
- **`search(id, value: str, *, max_bytes=256, **input_opts) -> str`**
- **`textarea(id, value: str, *, max_bytes=4096, height=120.0, **input_opts) -> str`**
- **`number(id, value: float, min_value=-1e12, max_value=1e12, *, label=None, step=1.0, decimals=0, disabled=False, width=None, suffix=None) -> float`**
- **`scrub(label, value: float, min_value: float, max_value: float, *, step=0.0, format=None, suffix=None, icon=None, width=None) -> float`**
- **`money_input(id, value: float, *, label=None, symbol="$", code=None, decimals=2, width=None, hint=None) -> float`**
- **`inline_edit(id, value: str, *, max_bytes=256, font=FontRole.BODY, size=0.0, placeholder=None, width=None) -> str`**
- **`tag_input(id, tags: list[str] | str, *, label=None, placeholder=None, max_tags=0, width=None, max_bytes=1024) -> list[str] | str`**
- **`otp_input(id, code: str, length=6) -> tuple[str, bool]`** (`(code, submitted)`)
- **`password_strength(password: str) -> int`** (`0..4` score)
- **`shortcut_recorder(id, combo: KeyCombo, *, placeholder=None, width=None) -> KeyCombo`** (+ `shortcut_label(combo)`, `key_name(key)`)
- **`signature_pad(id, *, width=None, height=0.0, placeholder=None, ink=None) -> bool`** (+ `signature_strokes(id)`, `signature_clear(id)`)
- **`dropzone(id, *, title=None, description=None, icon=None, accept=None, height=0.0, width=None, compact=False) -> tuple[list[str], bool]`** (`(accepted_paths, browse_clicked)` + `path_has_extension(path, accept)`)

---

## 6. Pickers (`nexa.widgets.pickers`)

- **`select(id, items, index: int, *, label=None, placeholder=None, icons=None, searchable=False, disabled=False, width=None) -> int`**
- **`combobox(id, items, index: int, **select_opts) -> int`**
- **`multi_select(id, items, selected: Sequence[bool], *, label=None, placeholder=None, icons=None, searchable=True, max_chips=0, width=None) -> list[bool]`**
- **`calendar(id, value: Date) -> Date`**
- **`date_picker(id, value: Date, *, label=None, placeholder=None, width=None) -> Date`**
- **`range_calendar(id, value: DateRange, *, months=2) -> DateRange`**
- **`date_range_picker(id, value: DateRange, *, label=None, placeholder=None, width=None, no_presets=False) -> DateRange`**
- **`time_picker(id, hour: int, minute: int, *, label=None, twelve_hour=False, minute_step=1, width=None) -> tuple[int, int]`**
- **`time_dial(id, hour: int, minute: int, *, size=200.0) -> tuple[int, int]`**
- **`wheel_picker(id, items, index: int, *, rows=0, width=None, loop=False, join_left=False, join_right=False) -> int`**
- **`ruler_slider(label, value: float, min_value: float, max_value: float, *, step=0.0, major_every=0, spacing=0.0, format=None, unit=None, width=None) -> float`**
- **`histogram_slider(label, bins, lo: float, hi: float, min_value: float, max_value: float, *, height=0.0, format=None) -> tuple[float, float]`**
- **`color_picker(id, value: ColorLike) -> Color`**

---

## 7. Navigation (`nexa.widgets.navigation`)

- **`tabs(id, items, index: int, *, variant=TabsVariant.UNDERLINE, icons=None, full_width=False) -> int`** (`TabsVariant`: `UNDERLINE` / `LINE`, `PILL`)
- **`nav_section(title)`** | **`nav_item(label, *, icon=None, badge=None, selected=False, group=None) -> bool`**
- **`breadcrumb(items) -> int`** (returns clicked crumb index or `-1`)
- **`path_bar(id, segments: Sequence[str], *, icon=None, text=None, placeholder=None, size=ControlSize.MD, width=None, menus=False, no_edit=False) -> PathBarResult`** *(New in 1.1)* — Editable file-manager / IDE breadcrumb address bar (`clicked`, `submitted`, `editing`) + **`path_bar_menu(id)`** (`PathBarMenuScope` exposing `menu.segment`).
- **`pagination(id, page: int, page_count: int) -> int`**
- **`stepper(steps, current: int)`**
- **`tab_bar(id, items: Sequence[TabBarItem], selected: int, *, width=None, labels_on_selected_only=False) -> int`**
- **`dock(id, *, size=0.0, magnify=0.0)`** -> `SimpleScope` + **`dock_item(icon, label, *, color=None, running=False, badge=0) -> bool`** + **`dock_separator()`**
- **`toc(scroll_id, items: Sequence[TocItem]) -> int`** + **`toc_anchor(anchor)`**

---

## 8. Overlays, Menus & Disclosure (`nexa.widgets.overlays`)

All popup/overlay scopes are **conditional**—always write `with ui.dialog(...) as d: if d: ...`!

- **`tooltip(text)`** — Attaches a hover tooltip to the immediately preceding widget.
- **`popover(id, *, placement=Placement.BOTTOM_START, width=0.0, pad=0.0, gap=0.0)`** -> `ConditionalScope` (`popover_open(id)`, `popover_toggle(id)`, `popover_is_open(id)`, `popover_close(id)`)
- **`hover_card(id, *, placement=Placement.BOTTOM_START, width=0.0, delay=0.0)`** -> `ConditionalScope`
- **`confirm_popover(id, *, title=None, description=None, confirm_label=None, cancel_label=None, danger=False, placement=Placement.BOTTOM_START) -> bool`** (`confirm_popover_open(id)` or `popover_open(id)` opens it on the anchor widget)
- **`menu(label, *, icon=None, variant=ButtonVariant.DEFAULT, placement=Placement.BOTTOM_START, width=0.0, icon_only=False)`** + **`context_menu(id)`** + **`user_menu(name, *, detail=None, status=None, avatar=0, compact=False, placement=Placement.TOP_START, width=0.0)`**
  - Inside menus: **`menu_item(label, *, icon=None, shortcut=None, danger=False, disabled=False, checked=False) -> bool`**, **`menu_separator()`**, **`menu_label(text)`**.
- **`dialog(title, is_open: bool, *, description=None, width=0.0, no_close_button=False, persistent=False)`** -> `OpenStateScope` (`dlg.open`) + **`dialog_footer()`**.
- **`sheet(title, is_open: bool, *, side=Side.RIGHT, size=0.0, description=None)`** -> `OpenStateScope` (`sh.open`).
- **`accordion(title, is_open: bool)`** -> `OpenStateScope` (`acc.open`).
- **`expandable_card(title, is_open: bool, *, description=None, icon=None, badge=None, badge_tone=Tone.NEUTRAL)`** -> `OpenStateScope` (`card.open`).
- **`expandable_text(id, text, *, lines=3, size=0.0, color=None, fade_to=None) -> bool`**

---

## 9. Feedback, Status & Badges (`nexa.widgets.feedback`)

- **`toast(title, *, description=None, tone=Tone.NEUTRAL, duration=0.0, action=None, show_timer=False) -> int`** (+ `toast_action_clicked(handle)`, `toast_dismiss(handle)`)
- **`alert(title, *, description=None, tone=Tone.NEUTRAL, icon=None, dismissible=False) -> bool`**
- **`banner(text, is_open: bool, *, tone=Tone.INFO, icon=None, action=None, dismissible=True) -> tuple[bool, bool]`**
- **`progress(value=0.0, *, indeterminate=False, tone=Tone.ACCENT, height=0.0, label=None, show_value=False, width=None)`**
- **`progress_ring(label, value: float, *, size=80.0)`**
- **`spinner(size=18.0)`** | **`loader(*, style=LoaderStyle.DOTS, size=0.0, color=None)`** (`LoaderStyle`: `DOTS`, `BARS`, `PULSE`, `ORBIT`, `GRID`) | **`skeleton(width=None, height=16.0)`**
- **`badge(text, *, tone=Tone.NEUTRAL, dot=False, solid=False, icon=None, size=ControlSize.MD)`**
- **`avatar(name, *, size=0.0, image=0, status=None, square=False)`** | **`avatar_group(names, *, max_visible=4, size=32.0)`** | **`avatar_upload(id, name, image=0, *, size=72.0) -> tuple[int, bool]`**
- **`empty_state(title, *, icon=None, description=None, action=None) -> bool`**
- **`metric(label, value, *, delta=0.0, delta_label=None, spark=None, icon=None, width=None, lower_is_better=False)`**
- **`meter(label, used: float, total: float, unit="")`**
- **`countdown(id, seconds_left: float, *, hide_days=False, compact=False)`**
- **`checklist(id, steps: Sequence[CheckStep], *, title=None, description=None) -> tuple[list[CheckStep], int]`**

---

## 10. Data, Virtual Lists, Tables, Grids & Code (`nexa.widgets.data`)

- **`tree(label, is_open=False, *, icon=None, leaf=False, selected=False)`** -> `TreeScope` (`OpenStateScope`; `if tr:` for children; `tr.open` / `tr.expanded`, `tr.clicked`) + **`tree_cell(label, depth, has_children, is_open, *, icon=None) -> bool`**.
- **`list_item(title, *, icon=None, subtitle=None, trailing=None, selected=False, avatar=None) -> bool`**
- **`virtual_list(id, count: int, row_height: float, height: SizeLike = None)`** -> `VirtualListScope` (iterate `for i in vl.indices:`—renders 1,000,000+ rows in O(visible)!).
- **`reorder(id, order: Sequence[int])`** -> `ReorderScope` (`with ro.item(pos): ...`; read `ro.order`).
- **`timeline_item(title, *, time=None, description=None, icon=None, tone=Tone.NEUTRAL, last=False)`**
- **`table(id, columns: Sequence[TableColumn], *, sort=None, height=None, striped=False, compact=False, selectable=False)`** -> `TableScope` (`if tbl:`; `tbl.row(selected=...) -> bool`, `tbl.cell()`, `tbl.cell_text(s)`, `tbl.sort`).
- **`data_grid(id, columns: Sequence[GridColumn], row_count: int, *, width=None, height=None, row_height=0.0, selected=None, sort=None, striped=False, cursor=None, hide_checkboxes=False, anchor=None)`** -> `DataGridScope` (`if dg:`; `for r in dg.rows:`, `dg.row(r)`, `dg.cell_text(s)`, `dg.edit(val)`, `dg.selected`, `dg.sort`, `dg.cursor`, `dg.anchor`; `GridColumn(..., priority=0)` hides lower-priority columns gracefully).
- **`tree_table(id, columns: Sequence[GridColumn], nodes: Sequence[TreeNode], *, width=None, height=None, row_height=0.0, root=0, sort=None, cursor=None, guides=True, labels=None, label_fn=None)`** -> `TreeTableScope` *(New in 1.1)* — Virtualized hierarchical tree-grid (`for idx in tt.rows(): tt.name(label, icon=...); tt.cell_text(...)`; synchronizes `TreeNode.flags` and exposes `tt.events: TreeTableEvents`) + **`tree_sort(nodes, root=-1, *, key=None, reverse=False) -> int`**.
- **`filter_bar(id, fields: Sequence[FilterField], selected_masks: Sequence[int], search: str, *, max_search_bytes=256) -> tuple[list[int], str]`**
- **`code_block(id, code, *, lang=None, title=None, line_numbers=False, highlight_from=0, highlight_to=0, max_height=0.0, size=0.0, no_header=False)`**
- **`code_editor(id, text: str, *, lang=None, width=None, height=320.0, size=0.0, tab_size=4, use_tabs=False, read_only=False, no_line_numbers=False, autofocus=False, placeholder=None, max_bytes=0) -> CodeEditorResult`** *(New in 1.1)* — Multi-line source editor with syntax highlighting, undo/redo, bracket matching & find bar (`text, changed = ui.code_editor(...)`), plus **`code_editor_goto(id, line, column=1)`**, **`code_editor_select(id, anchor, cursor)`**, and **`code_editor_find(id, query=None)`**.
- **`diff_view(id, old_text, new_text, *, mode=DiffMode.SPLIT, language=None, old_title=None, new_title=None, current=None, context=3, no_fold=False, ignore_eol=False, split_min_width=0.0, width=None, height=340.0, size=0.0) -> DiffResult`** *(New in 1.1)* — Side-by-side or inline diff viewer with intraline word diffs & hunk folding, plus **`diff_view_rows(id, *, offset=0, max_rows=256)`** and context-free C99 **`diff_compute(old_text, new_text)`** / **`diff_words(old_line, new_line)`**.
- **`markdown(id, text: str, *, width=None, fit_content=False, size=0.0, color=None, streaming=False, compact=False) -> MarkdownResult`** *(New in 1.1)* — Rich CommonMark + GFM renderer (headings, tables, fenced code, GitHub alerts, interactive task lists via `res.apply_task(text)` or `markdown_apply_task(text, res)`).
- **`json_view(id, json_text, *, expand_depth=2, max_height=0.0) -> bool`**

---

## 11. Charts & Data Visualization (`nexa.widgets.charts`)

- **`line_chart(id, series: Sequence[Series], *, width=None, height=0.0, labels=None, area=False, no_grid=False, no_legend=False, stacked=False, smooth=False, format=None, min_y=0.0, max_y=0.0)`**
- **`bar_chart(id, series: Sequence[Series], *, width=None, height=0.0, labels=None, stacked=False, no_grid=False, no_legend=False, format=None, min_y=0.0, max_y=0.0)`**
- **`donut_chart(id, values, labels, *, width=None, height=0.0, no_legend=False, format=None)`**
- **`sparkline(values, *, width=96.0, height=28.0, color=Color.ACCENT)`**
- **`gauge(label, value: float, *, size=120.0)`**
- **`heatmap(id, values, rows: int, cols: int, *, row_labels=None, col_labels=None, cell=0.0, min_value=0.0, max_value=0.0, color=None, format=None, width=None) -> int`**
- **`calendar_heatmap(id, start: Date, values, *, cell=0.0, color=None, format=None, unit=None) -> int`**
- **`treemap(id, items: Sequence[VizItem], *, width=None, height=0.0, format=None) -> int`**
- **`radar_chart(id, series: Sequence[Series], axes, *, size=0.0, max_value=0.0, format=None, no_legend=False) -> int`**
- **`funnel(id, stages: Sequence[VizItem], *, width=None, height=0.0, format=None, color=None) -> int`**
- **`sankey(id, nodes: Sequence[str], links: Sequence[SankeyLink], *, width=None, height=0.0, format=None, node_width=0.0) -> int`**
- **`waffle(id, items: Sequence[VizItem], *, cell=0.0, columns=0, rows=0, format=None) -> int`**
- **`split_bar(id, items: Sequence[VizItem], *, width=None, height=0.0, format=None, no_legend=False) -> int`**
- **`bar_list(id, items: Sequence[VizItem], *, width=None, format=None, max_rows=0, keep_order=False, color=None) -> int`**
- **`activity_rings(id, rings: Sequence[VizItem], *, size=0.0, thickness=0.0, center=None, caption=None, legend=False) -> int`**
- **`scatter_chart(id, series: Sequence[ScatterSeries], *, width=None, height=0.0, x_label=None, y_label=None, x_format=None, y_format=None, no_legend=False) -> int`**

---

## 12–19. Planning, AI, Social, Media, Motion, Chrome, Tools & Node/Canvas

- **Planning (`nexa.widgets.planning`)**:
  - `kanban(id)` -> `KanbanScope` (`board.column(title, card_count, *, dot=None, limit=0, width=0.0)`, `board.card(card_id)`, `board.move`)
  - `week_calendar(id, week_start: Date, events: Sequence[CalEvent], *, start_hour=0.0, end_hour=0.0, hour_height=0.0, height=None, read_only=False) -> tuple[list[CalEvent], int]`
  - `gantt(id, tasks: Sequence[GanttTask], origin: Date, days: int, *, day_width=0.0, row_height=0.0, height=None, today=-1, read_only=False) -> tuple[list[GanttTask], int]`
- **AI & Agents (`nexa.widgets.ai`)**:
  - `reasoning(id, *, thinking=False, seconds=0.0, title=None)` -> `ConditionalScope`
  - `tool_call(id, name, *, status=TaskStatus.DONE, icon=None, detail=None, input_text=None, output_text=None, seconds=0.0)`
  - `agent_plan(id, steps: Sequence[PlanStep], *, title=None) -> int` | `agent_status(text, *, status=TaskStatus.RUNNING, seconds=0.0, icon=None)`
  - `source_list(id, sources: Sequence[Source]) -> int` | `citation(number: int, source: Source) -> bool`
  - `context_meter(id, used: float, limit: float, *, parts=None, unit=None)`
  - `response_actions(id, *, copy_text=None, vote=0, no_regenerate=False, no_share=False) -> tuple[ResponseActionFlags, int]`
  - `prompt_suggestions(id, items: Sequence[PromptSuggestion], *, columns=0) -> int`
  - `model_picker(id, models: Sequence[ModelInfo], selected: int, *, ghost=False, placement=Placement.BOTTOM_START) -> int`
  - `chat_composer(id, text: str, *, placeholder=None, busy=False, attachments=None, models=None, model=0, max_lines=0, width=None, max_bytes=8192) -> ComposerResult`
  - `voice_orb(id, state=VoiceState.IDLE, level=0.0, *, size=0.0, color=None) -> bool`
- **Social (`nexa.widgets.social`)**: `chat_message(text, *, mine=False, author=None, time=None, status=None, grouped=False, last_in_group=True, avatar=0, markdown=False) -> Optional[MarkdownResult]`, `chat_divider`, `typing_indicator`, `comment`, `presence`.
- **Media (`nexa.widgets.media`)**: `image_load`, `image_load_bytes`, `image_create`, `image_destroy`, `image`, `carousel`, `image_compare`, `card_stack`, `waveform`, `now_playing`, `counter`, `ticker` (`TickerItem`).
- **Motion (`nexa.widgets.motion`)**: `shimmer_text`, `typewriter`, `text_reveal`, `word_rotate`, `number_roll`, `gradient_text`, `spotlight`, `animate`, `animate_spring`.
- **Desktop Chrome & Docking (`nexa.widgets.chrome`)**: `menu_bar` + `menu_bar_menu`, `toolbar` + `toolbar_button` / `toolbar_toggle` / `toolbar_separator` / `toolbar_spacer`, `status_bar` + `status_bar_item` / `status_bar_text` / `status_bar_progress` / `status_bar_spacer`, `doc_tabs` (`DocTabsResult.apply_to(tabs)`), and *(New in 1.1)* **`dockspace(id="dockspace", *, layout=None, width=None, height=None, min_panel_width=0.0, min_panel_height=0.0, shortcuts=True)`** + **`dock_panel(title, is_open=None, *, icon=None, dirty=False)`** + **`dock_save(id="dockspace") -> str`** + **`dock_load(id, layout) -> bool`**.
- **Developer & Creative Studio Tools (`nexa.widgets.tools`)**: `inspector` + `inspector_group`, `prop_float`, `prop_int`, `prop_text`, `prop_bool`, `prop_enum`, `prop_color`, `prop_vec` / `prop_vec2` / `prop_vec3` / `prop_vec4`, `LogBuffer` + `log_view`, plus *(New in 1.1)*:
  - **`hex_view(id, data, selection=None, *, width=None, height=280.0, base=0, bytes_per_row=16, ranges=None, editable=False, no_ascii=False, no_header=False, size=0.0) -> HexResult`** + **`hex_view_goto(id, offset)`**
  - **`flame_graph(id, spans, *, view=None, selected=None, width=None, height=240.0, row_height=0.0, min_range=0.0) -> FlameResult`** + **`flame_sort(spans)`** + **`flame_span_rect(flame_id, span)`**
  - **`curve_editor(id, keys, *, capacity=64, x_min=0.0, x_max=1.0, y_min=0.0, y_max=1.0, width=None, height=200.0, x_format=None, y_format=None, x_label=None, y_label=None, selected=None, snap=False, show_playhead=False, playhead=0.0) -> CurveResult`** + **`curve_eval(keys, x) -> float`**
  - **`gradient_editor(id, stops, *, capacity=32, width=None, height=0.0, selected=None) -> GradientResult`** + **`gradient_eval(stops, t) -> Color`**
  - **`timeline_editor(id, tracks, time=0.0, *, start=0.0, end=10.0, fps=30.0, ruler=TimelineRuler.SECONDS, view=None, in_point=None, out_point=None, current_track=None, current_key=None, width=None, height=260.0, row_height=0.0, track_width=0.0, toggles=True, free_drag=False, key_headroom=16) -> TimelineEditorResult`**
- **Node Editor & Vector Canvas (`nexa.widgets.nodes_canvas`)**: `node_editor` (`ed.node`, `ed.input`, `ed.output`, `ed.content`, `ed.link`, `ed.created_links`, `ed.removed_links`, `ed.deleted_nodes`), `canvas(id, width, height, paint)`, `draw_rect`, `draw_rect_border`, `draw_rect_gradient`, `draw_shadow`, `draw_line`, `draw_polyline`, `draw_polygon`, `draw_circle`, `draw_arc`, `draw_bezier`, `draw_text`, `draw_icon`, `draw_image`, `push_clip`, `pop_clip`, `clip_scope`, `state_buffer`.

---

## 20. Instruments (`nexa.widgets.instruments`) *(New in 1.4)*

- **`knob(id, value, min=0.0, max=1.0, *, label=None, unit=None, format=None, size=0.0, step=0.0, reset=0.0, bipolar=False, log_scale=False, hide_value=False, disabled=False, color=None) -> float`**
- **`fader(id, value, min=0.0, max=1.0, *, label=None, unit=None, format=None, length=160.0, horizontal=False, step=0.0, reset=0.0, ticks=(), meter=None, meter_channels=1, hide_value=False, disabled=False) -> float`**
- **`level_meter(id, levels, min_db=-48.0, max_db=6.0, *, length=160.0, thickness=10.0, horizontal=False, scale=True, segmented=True, hold=1.6, decay=24.0) -> bool`**
- **`radial_gauge(id, value, min=0.0, max=100.0, *, label=None, unit=None, format=None, size=200.0, sweep=240.0, ticks=5, target=None, bands=(), no_needle=False)`**
- **`readout(label, value, unit=None, detail=None, *, size=ControlSize.MD, tone=Tone.NEUTRAL, accent=False, align=Align.START, width=None)`**
- **`dot_display(text, *, pitch=0.0, color=None, accent=False, no_dim=False, marquee=False, align=Align.START, width=None)`**
- **`dot_chart(id, series: Sequence[DotSeries], count=None, *, width=None, height=220.0, x_min=0.0, x_max=None, x_units="number", x_format=None, x_step=0.0, min=None, max=None, format=None, unit=None, pitch=0.0, no_grid=False, no_axis=False, no_readout=False, annotations=()) -> DotChartResult`**
- **`event_track(id, times: list[float], *, capacity=256, min=0.0, max=24.0, width=None, step=0.0, units="number", format=None, label_step=0.0, selected=-1, no_add=False, no_remove=False, no_axis=False) -> EventTrackResult`**

## 21. Developer Tools (`nexa.widgets.devtools`) *(New in 1.3/1.4)*

Every dev tool takes its rows as plain dicts (or any object with matching
attributes) named after the C struct fields, and returns a named tuple:

- **`problems(id, diagnostics, *, width=None, height=240.0, no_toolbar=False) -> ProblemsResult`** — rows: `{"message", "severity", "file", "line", "column", "source", "code"}`.
- **`pipeline(id, stages, jobs=(), *, width=None, selected=-1) -> PipelineResult`** — jobs: `{"name", "stage", "status", "duration", "allow_failure"}`.
- **`schedule_picker(id, cron="0 9 * * *", *, width=None, now=0, utc=False, next_count=3) -> ScheduleResult`** (`changed`, `valid`, `next`)
- **`keymap(id, bindings, *, width=None, categories=(), mods=(), no_function_row=False) -> KeymapResult`** — bindings: `{"combo": {"key": "S", "mods": "ctrl"}, "action": "Save", "category": 0}`.
- **`commit_graph(id, commits, *, width=None, height=280.0, selected=-1) -> CommitGraphResult`** — commits: `{"hash", "message", "author", "date", "refs", "parent": [a, b]}`.
- **`graph_view(id, nodes, edges=(), *, width=None, height=280.0, top_down=True, selected=-1) -> GraphResult`** — edges: `{"from", "to"}`.
- **`waterfall(id, requests, *, width=None, height=260.0, selected=-1, dom_loaded=-1.0, loaded=-1.0) -> WaterfallResult`** — requests: `{"name", "method", "status", "type", "size", "start", "timing": [6 floats]}`.
- **`trace_view(id, tracks, spans, view=None, selected=-1, *, width=None, height=260.0, row_height=20.0, markers=()) -> TraceResult`** (`view`, `selected`, `selection_changed`, `view_changed`, `hovered`)
- **`regex_tester(id, pattern="", text="", *, width=None, height=240.0, flags=0) -> RegexTesterResult`** (`pattern`, `text`, `valid`, `matches`, `error`)
- **`test_explorer(id, items, *, width=None, height=280.0) -> TestExplorerResult`** — items: `{"name", "depth", "status", "duration", "message"}`.
- **`stack_trace(id, frames, *, width=None, title="", message="", lang="") -> StackTraceResult`** — frames: `{"function", "file", "line", "column", "external", "source": [lines]}`.
- **`request_bar(id, method=0, url="", *, width=None, loading=False, placeholder="Enter a URL") -> RequestBarResult`**
- **`api_explorer(id, endpoints, *, width=None, height=300.0, selected=-1) -> ApiExplorerResult`** — endpoints: `{"method", "path", "summary", "tag", "deprecated", "params": [{"name", "in", "type", "required", "description"}]}`.
- **`feature_flags(id, flags, envs=(), *, width=None, height=260.0) -> FeatureFlagsResult`** — flags: `{"key", "description", "on": [8 bools], "rollout": [8 ints]}`.
- **`uptime_bars(id, services, *, width=None, last_day=None) -> UptimeResult`** — services: `{"name", "days": [floats]}`.
- **`time_histogram(id, start, bucket_seconds, series, selected=None, *, width=None, height=160.0, utc=False) -> TimeHistogramResult`** — series: `{"name", "counts": [floats], "tone"}`.
- **`coverage(id, files, *, width=None, height=260.0, low=0.5, high=0.8) -> CoverageResult`** — files: `{"path", "lines", "lines_hit", "branches", "branches_hit", "functions", "functions_hit"}`.
- **`blame(id, lines, line_commit, commits, *, width=None, height=300.0, lang="", now=0, first_line=1) -> BlameResult`**
- **`kv_editor(id, pairs=(), *, capacity=32, key_placeholder="Key", value_placeholder="Value", no_toggles=False, no_secrets=False, read_only=False, width=None) -> KvEditorResult`**
- **`query_builder(id, fields, nodes=(), *, capacity=32, width=None, max_depth=6, read_only=False) -> QueryBuilderResult`** — plus headless `devtools.query_text(fields, nodes)`, `devtools.query_match(fields, nodes, values)`, `devtools.query_op_name(type, op)`.

## 22. Text, Media, Files & Overlays *(New in 1.2–1.4)*

- **`terminal(id, buffer: TerminalBuffer, *, width=None, height=320.0, size=13.0, prompt=None, no_input=False) -> TerminalResult`** — `TerminalBuffer(text_capacity=…, line_capacity=…)` with `write`, `printf`, `clear`, `line_count`.
- **`emoji(text, size=16.0)`**, **`emoji_picker(id, *, width=None, height=280.0, size=26.0, recent="", tone=0, placeholder=None, empty_text=None, hint=None, group_names=(), no_search=False, no_preview=False, no_tone=False) -> Optional[str]`**, `load_emoji_font` / `emoji_supported`.
- **`image_viewer(id, texture, image_width, image_height, view: ImageView, width=None, height=None, max_zoom=8.0, no_toolbar=False, checkerboard=True) -> ImageView`** and **`cropper(id, texture, image_width, image_height, crop: Rect, width=None, height=None, aspect=0.0, round_=False, min_size=16.0) -> tuple[Rect, bool]`**.
- **`file_browser(id, path, *, width=None, height=380.0, filter=None, folders_only=False, hidden=False, places=(), no_places=False, max_entries=20000) -> FileBrowserResult`** (updated folder on `result.path`), **`file_picker(id, path, title=None, *, save=False, folders=False, start=None, name=None, filter=None, filter_label=None) -> FilePickerResult`**, and headless **`fs_list(path=".", hidden=False, max_entries=4096) -> list[FileEntry]`**.
- **`month_calendar(id, month: Date, events=(), selected=None, *, first_weekday=0, cell_height=104.0, month_names=(), day_names=(), hour12=False) -> MonthResult`** (`MonthEvent(title, start, end=None, time=0.0, all_day=False, tone=…)`).
- **`tour(id, steps: Sequence[TourStep], step, *, width=300.0, padding=6.0, block_target=False, next_label=None, back_label=None, done_label=None, count_format=None) -> tuple[int, str]`** — actions are `none`, `next`, `back`, `done`, `skipped`.
- **`candlestick(id, candles: Sequence[Candle], *, width=None, height=240.0, labels=None, format=None, overlays=(), no_volume=False, ohlc=False, up=None, down=None) -> int`** and `annotations=` on every chart (`ChartAnnotation`).
- **Right-to-left**: `direction=` on `text`, `row`, `column`, `box`, `grid`, `stack` (`ui.TextDirection.LTR/RTL/AUTO`), with `--rtl` shaping builds.
- **Typography**: `use_font(path | bytes, *, family=None, roles=(BODY, MEDIUM, DISPLAY), fallbacks=())`, `use_system_font(family)`, `use_rtl_font(family=None)`, `load_font(source, *, fallbacks=())`, plus `font_load_file` / `font_load_memory` / `font_set_role` / `font_add_fallback`; discovery helpers live in `nexa.fonts` (`find_system_font`, `find_rtl_font`, `list_system_fonts`, `supports_text_shaping`).
- **Context helpers**: `UI.request_wakeup(seconds)`, `UI.set_strings(...)` / `UI.get_strings()`, `UI.response_status(status, seconds=, size=)`, `UI.is_software()`, and the context-free `ui.regex_search`, `ui.cron_next`, `ui.cron_describe`, `ui.url_params`, `ui.url_set_params`, `ui.http_reason`, `ui.http_method_name`.

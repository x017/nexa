/* C99 ABI bridge for nexa Python bindings.
 * Exposes flat pointer/scalar entry points so ctypes never passes or returns
 * structs by value (avoiding libffi struct-by-value quirks on ARM64/Win64 and
 * eliminating temporary Python Structure allocations on hot paths). */
#include "cui/cui.h"
#include "cui/cui_app.h"
#include "cui/cui_render.h"

#include <stdlib.h>
#include <string.h>

enum {
    NEXA_FEAT_SW            = 1 << 0,
    NEXA_FEAT_GL            = 1 << 1,
    NEXA_FEAT_APP           = 1 << 2,
    NEXA_FEAT_DEFAULT_FONTS = 1 << 3,
    NEXA_FEAT_STB_IMAGE     = 1 << 4,
    NEXA_FEAT_IMAGE_ALL     = 1 << 5
};

static inline cui_color nexa__u2c(uint32_t u) {
    cui_color c = {
        (uint8_t)(u & 0xffu),
        (uint8_t)((u >> 8) & 0xffu),
        (uint8_t)((u >> 16) & 0xffu),
        (uint8_t)((u >> 24) & 0xffu)
    };
    return c;
}

static inline uint32_t nexa__c2u(cui_color c) {
    return (uint32_t)c.r | ((uint32_t)c.g << 8) | ((uint32_t)c.b << 16) | ((uint32_t)c.a << 24);
}

static inline cui_size nexa__sz(int kind, float value) {
    cui_size s = { (cui_size_kind)kind, value };
    return s;
}

static inline cui_rect nexa__rc(float x, float y, float w, float h) {
    cui_rect r = { x, y, w, h };
    return r;
}

static inline cui_corners nexa__cn(float tl, float tr, float br, float bl) {
    cui_corners c = { tl, tr, br, bl };
    return c;
}

CUI_API const char *nexa_version(void) {
    return CUI_VERSION_STRING;
}

CUI_API uint32_t nexa_features(void) {
    uint32_t f = 0;
#ifndef CUI_NO_SW
    f |= NEXA_FEAT_SW;
#endif
#ifndef CUI_NO_GL
    f |= NEXA_FEAT_GL;
#endif
#ifndef CUI_NO_APP
    f |= NEXA_FEAT_APP;
#endif
#ifndef CUI_NO_DEFAULT_FONTS
    f |= NEXA_FEAT_DEFAULT_FONTS;
#endif
#ifndef CUI_NO_STB_IMAGE
    f |= NEXA_FEAT_STB_IMAGE;
#endif
#ifdef CUI_IMAGE_ALL_FORMATS
    f |= NEXA_FEAT_IMAGE_ALL;
#endif
    return f;
}

/* ---- Context & Renderer wiring ---- */

CUI_API cui_ctx *nexa_ctx_create(int theme, int accent, bool no_default_fonts,
                                  cui_sw_renderer *sw, cui_gl_renderer *gl) {
    cui_ctx_desc desc;
    memset(&desc, 0, sizeof desc);
    desc.theme = (cui_theme_mode)theme;
    desc.accent = (cui_accent)accent;
    desc.no_default_fonts = no_default_fonts;
#ifndef CUI_NO_SW
    if (sw) desc.renderer = cui_sw_iface(sw);
#else
    (void)sw;
#endif
#ifndef CUI_NO_GL
    if (gl) desc.renderer = cui_gl_iface(gl);
#else
    (void)gl;
#endif
    return cui_create(&desc);
}

CUI_API void nexa_ctx_set_sw_renderer(cui_ctx *ui, cui_sw_renderer *sw) {
#ifndef CUI_NO_SW
    if (sw) {
        cui_renderer_iface iface = cui_sw_iface(sw);
        cui_set_renderer(ui, &iface);
    } else {
        cui_set_renderer(ui, NULL);
    }
#else
    (void)ui; (void)sw;
#endif
}

CUI_API void nexa_ctx_set_gl_renderer(cui_ctx *ui, cui_gl_renderer *gl) {
#ifndef CUI_NO_GL
    if (gl) {
        cui_renderer_iface iface = cui_gl_iface(gl);
        cui_set_renderer(ui, &iface);
    } else {
        cui_set_renderer(ui, NULL);
    }
#else
    (void)ui; (void)gl;
#endif
}

typedef cui_texture (*nexa_tex_create_fn)(void *user, int w, int h, int fmt, const void *pixels);
typedef void (*nexa_tex_update_fn)(void *user, cui_texture tex, int x, int y, int w, int h, const void *pixels, int stride);
typedef void (*nexa_tex_destroy_fn)(void *user, cui_texture tex);

CUI_API void nexa_ctx_set_custom_renderer(cui_ctx *ui, void *user,
                                           nexa_tex_create_fn create_fn,
                                           nexa_tex_update_fn update_fn,
                                           nexa_tex_destroy_fn destroy_fn) {
    if (!create_fn && !update_fn && !destroy_fn) {
        cui_set_renderer(ui, NULL);
        return;
    }
    cui_renderer_iface iface;
    memset(&iface, 0, sizeof iface);
    iface.user = user;
    iface.texture_create = (cui_texture (*)(void *, int, int, cui_texture_format, const void *))create_fn;
    iface.texture_update = update_fn;
    iface.texture_destroy = destroy_fn;
    cui_set_renderer(ui, &iface);
}

/* ---- Platform callbacks without by-value cui_rect ---- */

typedef void (*nexa_set_clip_fn)(void *user, const char *utf8);
typedef const char *(*nexa_get_clip_fn)(void *user);
typedef void (*nexa_set_cursor_fn)(void *user, int cursor);
typedef void (*nexa_set_ime_fn)(void *user, float x, float y, float w, float h);

typedef struct {
    void *py_user;
    nexa_set_clip_fn set_clip;
    nexa_get_clip_fn get_clip;
    nexa_set_cursor_fn set_cursor;
    nexa_set_ime_fn set_ime;
} nexa_plat_holder;

static void nexa__plat_set_clip(void *u, const char *s) {
    nexa_plat_holder *h = (nexa_plat_holder *)u;
    if (h && h->set_clip) h->set_clip(h->py_user, s);
}

static const char *nexa__plat_get_clip(void *u) {
    nexa_plat_holder *h = (nexa_plat_holder *)u;
    return (h && h->get_clip) ? h->get_clip(h->py_user) : NULL;
}

static void nexa__plat_set_cursor(void *u, cui_cursor c) {
    nexa_plat_holder *h = (nexa_plat_holder *)u;
    if (h && h->set_cursor) h->set_cursor(h->py_user, (int)c);
}

static void nexa__plat_set_ime(void *u, cui_rect r) {
    nexa_plat_holder *h = (nexa_plat_holder *)u;
    if (h && h->set_ime) h->set_ime(h->py_user, r.x, r.y, r.w, r.h);
}

CUI_API nexa_plat_holder *nexa_set_platform(cui_ctx *ui, void *py_user,
                                              nexa_set_clip_fn set_clip,
                                              nexa_get_clip_fn get_clip,
                                              nexa_set_cursor_fn set_cursor,
                                              nexa_set_ime_fn set_ime) {
    nexa_plat_holder *h = (nexa_plat_holder *)calloc(1, sizeof *h);
    if (!h) return NULL;
    h->py_user = py_user;
    h->set_clip = set_clip;
    h->get_clip = get_clip;
    h->set_cursor = set_cursor;
    h->set_ime = set_ime;
    cui_platform_iface pi;
    memset(&pi, 0, sizeof pi);
    pi.user = h;
    if (set_clip) pi.set_clipboard = nexa__plat_set_clip;
    if (get_clip) pi.get_clipboard = nexa__plat_get_clip;
    if (set_cursor) pi.set_cursor = nexa__plat_set_cursor;
    if (set_ime) pi.set_text_input_rect = nexa__plat_set_ime;
    cui_set_platform(ui, &pi);
    return h;
}

CUI_API void nexa_free_platform(cui_ctx *ui, nexa_plat_holder *h) {
    if (ui) {
        cui_platform_iface empty;
        memset(&empty, 0, sizeof empty);
        cui_set_platform(ui, &empty);
    }
    free(h);
}

/* ---- Flat geometry, metrics, colors, dates ---- */

CUI_API void nexa_viewport_size(cui_ctx *ui, float *w, float *h) {
    cui_vec2 v = cui_viewport_size(ui);
    if (w) *w = v.x;
    if (h) *h = v.y;
}

CUI_API void nexa_app_size(cui_app *app, float *w, float *h) {
#ifndef CUI_NO_APP
    cui_vec2 v = cui_app_size(app);
    if (w) *w = v.x;
    if (h) *h = v.y;
#else
    (void)app; if (w) *w = 0; if (h) *h = 0;
#endif
}

CUI_API void nexa_mouse_pos(cui_ctx *ui, float *x, float *y) {
    cui_vec2 v = cui_mouse_pos(ui);
    if (x) *x = v.x;
    if (y) *y = v.y;
}

CUI_API void nexa_last_rect(cui_ctx *ui, float *out4) {
    cui_rect r = cui_last_rect(ui);
    out4[0] = r.x; out4[1] = r.y; out4[2] = r.w; out4[3] = r.h;
}

CUI_API void nexa_get_rect(cui_ctx *ui, cui_id id, float *out4) {
    cui_rect r = cui_get_rect(ui, id);
    out4[0] = r.x; out4[1] = r.y; out4[2] = r.w; out4[3] = r.h;
}

CUI_API void nexa_measure_text(cui_ctx *ui, cui_font font, float size, const char *text, int len, float *out5) {
    cui_text_metrics m = cui_measure_text(ui, font, size, text, len);
    out5[0] = m.width;
    out5[1] = m.height;
    out5[2] = m.ascent;
    out5[3] = m.descent;
    out5[4] = m.line_height;
}

CUI_API uint32_t nexa_color_of(cui_ctx *ui, uint32_t rgba) {
    return nexa__c2u(cui_color_of(ui, nexa__u2c(rgba)));
}

CUI_API uint32_t nexa_token_color(cui_ctx *ui, int token) {
    return nexa__c2u(cui_token_color(ui, (cui_token)token));
}

CUI_API uint32_t nexa_oklch(float l, float ch, float h_deg, float alpha) {
    return nexa__c2u(cui_oklch(l, ch, h_deg, alpha));
}

CUI_API uint32_t nexa_mix(uint32_t a, uint32_t b, float t) {
    return nexa__c2u(cui_mix(nexa__u2c(a), nexa__u2c(b), t));
}

CUI_API uint32_t nexa_alpha(uint32_t c, float mult) {
    return nexa__c2u(cui_alpha(nexa__u2c(c), mult));
}

CUI_API bool nexa_color_picker(cui_ctx *ui, const char *id, uint32_t *rgba) {
    cui_color c = nexa__u2c(*rgba);
    bool changed = cui_color_picker(ui, id, &c);
    *rgba = nexa__c2u(c);
    return changed;
}

CUI_API void nexa_icon(cui_ctx *ui, const char *icon, float size, uint32_t rgba) {
    cui_icon(ui, icon, size, nexa__u2c(rgba));
}

CUI_API void nexa_skeleton(cui_ctx *ui, int w_kind, float w_val, float height) {
    cui_skeleton(ui, nexa__sz(w_kind, w_val), height);
}

CUI_API void nexa_virtual_list_begin(cui_ctx *ui, const char *id, int count, float row_height,
                                      int h_kind, float h_val, int *first, int *last) {
    cui_virtual_list_begin(ui, id, count, row_height, nexa__sz(h_kind, h_val), first, last);
}

CUI_API void nexa_sparkline(cui_ctx *ui, const float *values, int count,
                             int w_kind, float w_val, float height, uint32_t rgba) {
    cui_sparkline(ui, values, count, nexa__sz(w_kind, w_val), height, nexa__u2c(rgba));
}

CUI_API void nexa_date_today(int *out3) {
    cui_date d = cui_date_today();
    out3[0] = d.year; out3[1] = d.month; out3[2] = d.day;
}

CUI_API int nexa_date_to_days(int y, int m, int d) {
    cui_date dt = { y, m, d };
    return cui_date_to_days(dt);
}

CUI_API void nexa_date_from_days(int days, int *out3) {
    cui_date d = cui_date_from_days(days);
    out3[0] = d.year; out3[1] = d.month; out3[2] = d.day;
}

CUI_API int nexa_calendar_heatmap(cui_ctx *ui, const char *id, int y, int m, int d,
                                   const float *values, int days, const cui_calendar_heatmap_opts *opts) {
    cui_date start = { y, m, d };
    return cui_calendar_heatmap_ex(ui, id, start, values, days, opts);
}

CUI_API int nexa_week_calendar(cui_ctx *ui, const char *id, int y, int m, int d,
                                cui_cal_event *events, int count, const cui_week_opts *opts) {
    cui_date ws = { y, m, d };
    return cui_week_calendar_ex(ui, id, ws, events, count, opts);
}

CUI_API int nexa_gantt(cui_ctx *ui, const char *id, cui_gantt_task *tasks, int count,
                        int y, int m, int d, int days, const cui_gantt_opts *opts) {
    cui_date origin = { y, m, d };
    return cui_gantt_ex(ui, id, tasks, count, origin, days, opts);
}

CUI_API const char *nexa_shortcut_label(cui_ctx *ui, int mods, int key) {
    cui_key_combo kc = { mods, (cui_key)key };
    return cui_shortcut_label(ui, kc);
}

CUI_API void nexa_doc_tabs(cui_ctx *ui, const char *id, const cui_doc_tab *tabs, int count,
                            int *selected, const cui_doc_tabs_opts *opts, int *out4) {
    cui_doc_tabs_result r = cui_doc_tabs_ex(ui, id, tabs, count, selected, opts);
    out4[0] = r.changed ? 1 : 0;
    out4[1] = r.close;
    out4[2] = r.move_from;
    out4[3] = r.move_to;
}

CUI_API bool nexa_prop_color(cui_ctx *ui, const char *label, uint32_t *rgba, const cui_prop_opts *opts) {
    cui_color c = nexa__u2c(*rgba);
    bool changed = cui_prop_color_ex(ui, label, &c, opts);
    *rgba = nexa__c2u(c);
    return changed;
}

/* ---- Managed LogBuffer helper ---- */

typedef struct {
    cui_log_buffer buf;
    cui_log_line *lines_mem;
    char *text_mem;
} nexa_log_handle;

CUI_API cui_log_buffer *nexa_log_create(int line_cap, size_t text_cap) {
    if (line_cap <= 0) line_cap = 4096;
    if (text_cap == 0) text_cap = 256 * 1024;
    nexa_log_handle *h = (nexa_log_handle *)calloc(1, sizeof *h);
    if (!h) return NULL;
    h->lines_mem = (cui_log_line *)calloc((size_t)line_cap, sizeof(cui_log_line));
    h->text_mem = (char *)calloc(text_cap, 1);
    if (!h->lines_mem || !h->text_mem) {
        free(h->lines_mem);
        free(h->text_mem);
        free(h);
        return NULL;
    }
    cui_log_init(&h->buf, h->lines_mem, line_cap, h->text_mem, text_cap);
    return &h->buf;
}

CUI_API void nexa_log_destroy(cui_log_buffer *buf) {
    if (!buf) return;
    nexa_log_handle *h = (nexa_log_handle *)buf;
    free(h->lines_mem);
    free(h->text_mem);
    free(h);
}

CUI_API void nexa_log_set_now(cui_log_buffer *buf, double now) {
    if (buf) buf->now = now;
}

CUI_API int nexa_log_count(const cui_log_buffer *buf) {
    return buf ? buf->count : 0;
}

CUI_API uint64_t nexa_log_total(const cui_log_buffer *buf) {
    return buf ? buf->total : 0;
}

CUI_API bool nexa_log_line_at(const cui_log_buffer *buf, int index, double *time_out,
                               int *level_out, const char **text_out, int *len_out) {
    const char *txt = NULL;
    const cui_log_line *ln = cui_log_get(buf, index, &txt);
    if (!ln) return false;
    if (time_out) *time_out = ln->time;
    if (level_out) *level_out = (int)ln->level;
    if (text_out) *text_out = txt;
    if (len_out) *len_out = (int)ln->len;
    return true;
}

/* ---- Custom drawing & Canvas trampoline ---- */

CUI_API void nexa_draw_rect(cui_ctx *ui, float x, float y, float w, float h,
                             float tl, float tr, float br, float bl, uint32_t fill) {
    cui_draw_rect(ui, nexa__rc(x, y, w, h), nexa__cn(tl, tr, br, bl), nexa__u2c(fill));
}

CUI_API void nexa_draw_rect_border(cui_ctx *ui, float x, float y, float w, float h,
                                    float tl, float tr, float br, float bl,
                                    uint32_t fill, uint32_t border, float border_width) {
    cui_draw_rect_border(ui, nexa__rc(x, y, w, h), nexa__cn(tl, tr, br, bl),
                         nexa__u2c(fill), nexa__u2c(border), border_width);
}

CUI_API void nexa_draw_rect_gradient(cui_ctx *ui, float x, float y, float w, float h,
                                      float tl, float tr, float br, float bl,
                                      uint32_t top, uint32_t bottom) {
    cui_draw_rect_gradient(ui, nexa__rc(x, y, w, h), nexa__cn(tl, tr, br, bl),
                           nexa__u2c(top), nexa__u2c(bottom));
}

CUI_API void nexa_draw_shadow(cui_ctx *ui, float x, float y, float w, float h,
                               float tl, float tr, float br, float bl,
                               float blur, float spread, float ox, float oy, uint32_t color) {
    cui_vec2 off = { ox, oy };
    cui_draw_shadow(ui, nexa__rc(x, y, w, h), nexa__cn(tl, tr, br, bl),
                    blur, spread, off, nexa__u2c(color));
}

CUI_API void nexa_draw_line(cui_ctx *ui, float ax, float ay, float bx, float by,
                             float thickness, uint32_t color) {
    cui_vec2 a = { ax, ay }, b = { bx, by };
    cui_draw_line(ui, a, b, thickness, nexa__u2c(color));
}

CUI_API void nexa_draw_polyline(cui_ctx *ui, const float *xy, int count,
                                 float thickness, uint32_t color, bool closed) {
    cui_draw_polyline(ui, (const cui_vec2 *)xy, count, thickness, nexa__u2c(color), closed);
}

CUI_API void nexa_draw_polygon(cui_ctx *ui, const float *xy, int count, uint32_t color) {
    cui_draw_polygon(ui, (const cui_vec2 *)xy, count, nexa__u2c(color));
}

CUI_API void nexa_draw_circle(cui_ctx *ui, float cx, float cy, float radius, uint32_t color) {
    cui_vec2 c = { cx, cy };
    cui_draw_circle(ui, c, radius, nexa__u2c(color));
}

CUI_API void nexa_draw_arc(cui_ctx *ui, float cx, float cy, float radius,
                            float a0, float a1, float thickness, uint32_t color) {
    cui_vec2 c = { cx, cy };
    cui_draw_arc(ui, c, radius, a0, a1, thickness, nexa__u2c(color));
}

CUI_API void nexa_draw_text(cui_ctx *ui, cui_font font, float size, float x, float y,
                             uint32_t color, const char *text, int len) {
    cui_vec2 p = { x, y };
    cui_draw_text(ui, font, size, p, nexa__u2c(color), text, len);
}

CUI_API void nexa_draw_icon(cui_ctx *ui, const char *icon, float x, float y, float w, float h,
                             float size, uint32_t color) {
    cui_draw_icon(ui, icon, nexa__rc(x, y, w, h), size, nexa__u2c(color));
}

CUI_API void nexa_draw_image(cui_ctx *ui, cui_texture tex,
                              float x, float y, float w, float h,
                              float u0, float v0, float uw, float vh,
                              float tl, float tr, float br, float bl, uint32_t tint) {
    cui_draw_image(ui, tex, nexa__rc(x, y, w, h), nexa__rc(u0, v0, uw, vh),
                   nexa__cn(tl, tr, br, bl), nexa__u2c(tint));
}

CUI_API void nexa_push_clip(cui_ctx *ui, float x, float y, float w, float h) {
    cui_push_clip(ui, nexa__rc(x, y, w, h));
}

typedef void (*nexa_paint_tramp_fn)(cui_ctx *ui, float x, float y, float w, float h, uintptr_t slot);

typedef struct {
    nexa_paint_tramp_fn fn;
    uintptr_t slot;
} nexa_canvas_payload;

static void nexa__canvas_paint(cui_ctx *ui, cui_rect r, void *user) {
    nexa_canvas_payload *p = (nexa_canvas_payload *)user;
    if (p && p->fn) p->fn(ui, r.x, r.y, r.w, r.h, p->slot);
}

CUI_API void nexa_canvas(cui_ctx *ui, const char *id,
                          int w_kind, float w_val, int h_kind, float h_val,
                          nexa_paint_tramp_fn fn, uintptr_t slot,
                          float *out_rect4, int *out_flags3, float *out_mouse2) {
    nexa_canvas_payload payload = { fn, slot };
    cui_canvas_result r = cui_canvas(
        ui, id, nexa__sz(w_kind, w_val), nexa__sz(h_kind, h_val),
        fn ? nexa__canvas_paint : NULL,
        fn ? &payload : NULL,
        fn ? sizeof(payload) : 0
    );
    out_rect4[0] = r.rect.x; out_rect4[1] = r.rect.y;
    out_rect4[2] = r.rect.w; out_rect4[3] = r.rect.h;
    out_flags3[0] = r.hovered ? 1 : 0;
    out_flags3[1] = r.pressed ? 1 : 0;
    out_flags3[2] = r.clicked ? 1 : 0;
    out_mouse2[0] = r.mouse.x; out_mouse2[1] = r.mouse.y;
}

/* ---- Optional stubs when stripped via CUI_NO_SW / CUI_NO_GL / CUI_NO_APP ---- */

#ifdef CUI_NO_SW
CUI_API cui_sw_renderer *cui_sw_create(void) { return NULL; }
CUI_API void cui_sw_destroy(cui_sw_renderer *r) { (void)r; }
CUI_API void cui_sw_render(cui_sw_renderer *r, const cui_draw_data *dd, void *pixels,
                           int width, int height, int stride, cui_sw_format format) {
    (void)r; (void)dd; (void)pixels; (void)width; (void)height; (void)stride; (void)format;
}
CUI_API void cui_sw_set_threads(cui_sw_renderer *r, int threads) { (void)r; (void)threads; }
CUI_API bool cui_write_png(const char *path, const void *rgba, int width, int height, int stride) {
    (void)path; (void)rgba; (void)width; (void)height; (void)stride; return false;
}
#endif

#ifdef CUI_NO_GL
CUI_API cui_gl_renderer *cui_gl_create(cui_gl_loader loader) { (void)loader; return NULL; }
CUI_API void cui_gl_destroy(cui_gl_renderer *r) { (void)r; }
CUI_API void cui_gl_render(cui_gl_renderer *r, const cui_draw_data *dd, bool clear) {
    (void)r; (void)dd; (void)clear;
}
CUI_API void cui_gl_read_pixels(cui_gl_renderer *r, int width, int height, void *rgba) {
    (void)r; (void)width; (void)height; (void)rgba;
}
#endif

#ifdef CUI_NO_APP
CUI_API cui_app *cui_app_create(const cui_app_desc *desc) { (void)desc; return NULL; }
CUI_API void cui_app_destroy(cui_app *app) { (void)app; }
CUI_API bool cui_app_frame(cui_app *app) { (void)app; return false; }
CUI_API cui_ctx *cui_app_ui(cui_app *app) { (void)app; return NULL; }
CUI_API int cui_app_run(const cui_app_desc *desc, void (*frame)(cui_ctx *ui, void *user), void *user) {
    (void)desc; (void)frame; (void)user; return 1;
}
CUI_API void cui_app_quit(cui_app *app) { (void)app; }
CUI_API void cui_app_wake(cui_app *app) { (void)app; }
CUI_API void cui_app_set_title(cui_app *app, const char *title) { (void)app; (void)title; }
CUI_API void cui_app_set_size(cui_app *app, int width, int height) { (void)app; (void)width; (void)height; }
CUI_API bool cui_app_is_software(cui_app *app) { (void)app; return false; }
CUI_API void *cui_app_native_window(cui_app *app) { (void)app; return NULL; }
CUI_API const char *cui_app_backend(cui_app *app) { (void)app; return "none"; }
CUI_API bool cui_app_file_dialog(cui_app *app, const cui_file_dialog_opts *opts, char *out, size_t cap) {
    (void)app; (void)opts; (void)out; (void)cap; return false;
}
CUI_API bool cui_app_open_url(const char *url) { (void)url; return false; }
CUI_API bool cui_app_screenshot(cui_app *app, void *rgba, int width, int height) {
    (void)app; (void)rgba; (void)width; (void)height; return false;
}
#endif


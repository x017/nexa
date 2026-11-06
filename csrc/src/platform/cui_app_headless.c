/* Headless stub backend (used when YAPPS_WITH_APP=0 or YAPPS_PLATFORM=headless). */
#include "cui_platform.h"
#include <time.h>

double cui__plat_now(void) {
#if defined(_WIN32)
    return 0.0;
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
#endif
}

const char *cui__plat_name(void) { return "headless"; }
int cui__plat_system_dark(void) { return -1; }
bool cui__plat_init(cui_app *app) { (void)app; return false; }
void cui__plat_shutdown(cui_app *app) { (void)app; }
bool cui__plat_gl_create(cui_app *app, bool vsync) { (void)app; (void)vsync; return false; }
void *cui__plat_gl_proc(const char *name) { (void)name; return NULL; }
void cui__plat_gl_swap(cui_app *app) { (void)app; }
void cui__plat_present(cui_app *app, const void *bgra, int w, int h, int stride) {
    (void)app; (void)bgra; (void)w; (void)h; (void)stride;
}
void cui__plat_wait(cui_app *app, double timeout) { (void)app; (void)timeout; }
void cui__plat_wake(cui_app *app) { (void)app; }
void cui__plat_metrics(cui_app *app, float *w, float *h, float *scale, int *fb_w, int *fb_h) {
    (void)app; *w = 0; *h = 0; *scale = 1.0f; *fb_w = 0; *fb_h = 0;
}
void cui__plat_set_title(cui_app *app, const char *title) { (void)app; (void)title; }
void cui__plat_set_size(cui_app *app, int w, int h) { (void)app; (void)w; (void)h; }
void cui__plat_show(cui_app *app) { (void)app; }
void *cui__plat_native(cui_app *app) { (void)app; return NULL; }
bool cui__plat_file_dialog(cui_app *app, const cui_file_dialog_opts *o, char *out, size_t cap) {
    (void)app; (void)o; (void)out; (void)cap; return false;
}
bool cui__plat_open_url(const char *url) { (void)url; return false; }

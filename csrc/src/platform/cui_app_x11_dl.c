/* Dynamic X11 backend (Linux, BSD) via dlopen("libX11.so.6").
 * Requires zero X11 development headers at compile time and adds zero ELF
 * link dependencies, so the same binary runs headless in minimal containers
 * and opens native X11 + GLX/software windows on desktops. */
#include "cui_platform.h"

#include <dlfcn.h>
#include <fcntl.h>
#include <locale.h>
#include <sys/select.h>
#include <time.h>
#include <unistd.h>

/* ---- Frozen X11 ABI types & constants ---- */
typedef unsigned long XID;
typedef XID Window;
typedef XID Drawable;
typedef XID Pixmap;
typedef XID Colormap;
typedef XID Cursor;
typedef XID GContext;
typedef XID KeySym;
typedef unsigned long Atom;
typedef unsigned long VisualID;
typedef unsigned long Time;
typedef int Bool;
typedef int Status;
typedef char *XPointer;

typedef struct _XDisplay Display;
typedef struct _XGC *GC;
typedef struct _XIM *XIM;
typedef struct _XIC *XIC;
typedef struct _XrmHashBucketRec *XrmDatabase;
typedef void Visual;

#define None_                0L
#define False_               0
#define True_                1
#define Success_             0
#define CurrentTime_         0L
#define AnyPropertyType_     0L
#define PropModeReplace_     0
#define AllocNone_           0
#define InputOutput_         1
#define ZPixmap_             2
#define XA_ATOM_             ((Atom)4)
#define XA_STRING_           ((Atom)31)

#define CWBackPixel_         (1L << 1)
#define CWBorderPixel_       (1L << 3)
#define CWEventMask_         (1L << 11)
#define CWColormap_          (1L << 13)

#define NoEventMask_         0L
#define KeyPressMask_        (1L << 0)
#define KeyReleaseMask_      (1L << 1)
#define ButtonPressMask_     (1L << 2)
#define ButtonReleaseMask_   (1L << 3)
#define EnterWindowMask_     (1L << 4)
#define LeaveWindowMask_     (1L << 5)
#define PointerMotionMask_   (1L << 6)
#define ExposureMask_        (1L << 15)
#define StructureNotifyMask_ (1L << 17)
#define FocusChangeMask_     (1L << 21)

#define KeyPress_            2
#define KeyRelease_          3
#define ButtonPress_         4
#define ButtonRelease_       5
#define MotionNotify_        6
#define EnterNotify_         7
#define LeaveNotify_         8
#define FocusIn_             9
#define FocusOut_            10
#define Expose_              12
#define ConfigureNotify_     22
#define SelectionClear_      29
#define SelectionRequest_    30
#define SelectionNotify_     31
#define ClientMessage_       33

#define ShiftMask_           (1 << 0)
#define ControlMask_         (1 << 2)
#define Mod1Mask_            (1 << 3)
#define Mod4Mask_            (1 << 6)

#define Button1_             1
#define Button2_             2
#define Button3_             3
#define Button4_             4
#define Button5_             5

#define PMinSize_            (1L << 4)
#define PMaxSize_            (1L << 5)

#define XIMPreeditNothing_   0x0008L
#define XIMStatusNothing_    0x0400L
#define XNInputStyle_        "inputStyle"
#define XNClientWindow_      "clientWindow"
#define XNFocusWindow_       "focusWindow"
#define XLookupChars_        2
#define XLookupBoth_         4

#define XC_X_cursor_         0
#define XC_fleur_            52
#define XC_hand2_            60
#define XC_left_ptr_         68
#define XC_sb_h_double_arrow_ 108
#define XC_sb_v_double_arrow_ 116
#define XC_xterm_            152

/* KeySyms */
#define XK_BackSpace_        0xff08
#define XK_Tab_              0xff09
#define XK_Return_           0xff0d
#define XK_Escape_           0xff1b
#define XK_Home_             0xff50
#define XK_Left_             0xff51
#define XK_Up_               0xff52
#define XK_Right_            0xff53
#define XK_Down_             0xff54
#define XK_Page_Up_          0xff55
#define XK_Page_Down_        0xff56
#define XK_End_              0xff57
#define XK_KP_Enter_         0xff8d
#define XK_KP_Home_          0xff95
#define XK_KP_Left_          0xff96
#define XK_KP_Up_            0xff97
#define XK_KP_Right_         0xff98
#define XK_KP_Down_          0xff99
#define XK_KP_Page_Up_       0xff9a
#define XK_KP_Page_Down_     0xff9b
#define XK_KP_End_           0xff9c
#define XK_KP_Delete_        0xff9f
#define XK_F1_               0xffbe
#define XK_F12_              0xffc9
#define XK_Shift_L_          0xffe1
#define XK_Shift_R_          0xffe2
#define XK_Control_L_        0xffe3
#define XK_Control_R_        0xffe4
#define XK_Meta_L_           0xffe7
#define XK_Meta_R_           0xffe8
#define XK_Alt_L_            0xffe9
#define XK_Alt_R_            0xffea
#define XK_Super_L_          0xffeb
#define XK_Super_R_          0xffec
#define XK_ISO_Left_Tab_     0xfe20
#define XK_Delete_           0xffff
#define XK_space_            0x0020
#define XK_comma_            0x002c
#define XK_minus_            0x002d
#define XK_period_           0x002e
#define XK_slash_            0x002f
#define XK_0_                0x0030
#define XK_9_                0x0039
#define XK_equal_            0x003d
#define XK_A_                0x0041
#define XK_Z_                0x005a
#define XK_a_                0x0061
#define XK_z_                0x007a

typedef struct {
    Visual *visual;
    VisualID visualid;
    int screen;
    int depth;
    int c_class;
    unsigned long red_mask, green_mask, blue_mask;
    int colormap_size;
    int bits_per_rgb;
} XVisualInfo;

typedef struct {
    Pixmap background_pixmap;
    unsigned long background_pixel;
    Pixmap border_pixmap;
    unsigned long border_pixel;
    int bit_gravity;
    int win_gravity;
    int backing_store;
    unsigned long backing_planes;
    unsigned long backing_pixel;
    Bool save_under;
    long event_mask;
    long do_not_propagate_mask;
    Bool override_redirect;
    Colormap colormap;
    Cursor cursor;
} XSetWindowAttributes;

typedef struct {
    long flags;
    int x, y;
    int width, height;
    int min_width, min_height;
    int max_width, max_height;
    int width_inc, height_inc;
    struct { int x, y; } min_aspect, max_aspect;
    int base_width, base_height;
    int win_gravity;
} XSizeHints;

typedef struct {
    char *res_name;
    char *res_class;
} XClassHint;

typedef struct {
    unsigned int size;
    XPointer addr;
} XrmValue;

typedef struct _XImage {
    int width, height;
    int xoffset;
    int format;
    char *data;
    int byte_order;
    int bitmap_unit;
    int bitmap_bit_order;
    int bitmap_pad;
    int depth;
    int bytes_per_line;
    int bits_per_pixel;
    unsigned long red_mask, green_mask, blue_mask;
    XPointer obdata;
    struct {
        struct _XImage *(*create_image)(void *, void *, unsigned int, int, int, char *, unsigned int, unsigned int, int, int);
        int (*destroy_image)(struct _XImage *);
        unsigned long (*get_pixel)(struct _XImage *, int, int);
        int (*put_pixel)(struct _XImage *, int, int, unsigned long);
        struct _XImage *(*sub_image)(struct _XImage *, int, int, unsigned int, unsigned int);
        int (*add_pixel)(struct _XImage *, long);
    } f;
} XImage;

typedef struct {
    int type;
    Display *display;
    XID resourceid;
    unsigned long serial;
    unsigned char error_code;
    unsigned char request_code;
    unsigned char minor_code;
} XErrorEvent;

typedef struct {
    int type;
    unsigned long serial;
    Bool send_event;
    Display *display;
    Window window;
    Window root;
    Window subwindow;
    Time time;
    int x, y;
    int x_root, y_root;
    unsigned int state;
    unsigned int keycode;
    Bool same_screen;
} XKeyEvent;

typedef struct {
    int type;
    unsigned long serial;
    Bool send_event;
    Display *display;
    Window window;
    Window root;
    Window subwindow;
    Time time;
    int x, y;
    int x_root, y_root;
    unsigned int state;
    unsigned int button;
    Bool same_screen;
} XButtonEvent;

typedef struct {
    int type;
    unsigned long serial;
    Bool send_event;
    Display *display;
    Window window;
    Window root;
    Window subwindow;
    Time time;
    int x, y;
    int x_root, y_root;
    unsigned int state;
    char is_hint;
    Bool same_screen;
} XMotionEvent;

typedef struct {
    int type;
    unsigned long serial;
    Bool send_event;
    Display *display;
    Window window;
    Window root;
    Window subwindow;
    Time time;
    int x, y;
    int x_root, y_root;
    int mode;
    int detail;
    Bool same_screen;
    Bool focus;
    unsigned int state;
} XCrossingEvent;

typedef struct {
    int type;
    unsigned long serial;
    Bool send_event;
    Display *display;
    Window event;
    Window window;
    int x, y;
    int width, height;
    int border_width;
    Window above;
    Bool override_redirect;
} XConfigureEvent;

typedef struct {
    int type;
    unsigned long serial;
    Bool send_event;
    Display *display;
    Window owner;
    Window requestor;
    Atom selection;
    Atom target;
    Atom property;
    Time time;
} XSelectionRequestEvent;

typedef struct {
    int type;
    unsigned long serial;
    Bool send_event;
    Display *display;
    Window requestor;
    Atom selection;
    Atom target;
    Atom property;
    Time time;
} XSelectionEvent;

typedef struct {
    int type;
    unsigned long serial;
    Bool send_event;
    Display *display;
    Window window;
    Atom message_type;
    int format;
    union {
        char b[20];
        short s[10];
        long l[5];
    } data;
} XClientMessageEvent;

typedef union _XEvent {
    int type;
    XKeyEvent xkey;
    XButtonEvent xbutton;
    XMotionEvent xmotion;
    XCrossingEvent xcrossing;
    XConfigureEvent xconfigure;
    XSelectionRequestEvent xselectionrequest;
    XSelectionEvent xselection;
    XClientMessageEvent xclient;
    long pad[24];
} XEvent;

typedef int (*XErrorHandler)(Display *, XErrorEvent *);

/* ---- Dynamically loaded X11 function table ---- */
typedef struct {
    void *handle;
    Status (*XInitThreads)(void);
    Display *(*XOpenDisplay)(const char *);
    int (*XCloseDisplay)(Display *);
    int (*XDefaultScreen)(Display *);
    Window (*XRootWindow)(Display *, int);
    Visual *(*XDefaultVisual)(Display *, int);
    int (*XDefaultDepth)(Display *, int);
    int (*XConnectionNumber)(Display *);
    Colormap (*XCreateColormap)(Display *, Window, Visual *, int);
    int (*XFreeColormap)(Display *, Colormap);
    Window (*XCreateWindow)(Display *, Window, int, int, unsigned int, unsigned int, unsigned int, int, unsigned int, Visual *, unsigned long, XSetWindowAttributes *);
    int (*XDestroyWindow)(Display *, Window);
    int (*XMapWindow)(Display *, Window);
    int (*XFlush)(Display *);
    int (*XSync)(Display *, Bool);
    int (*XPending)(Display *);
    int (*XNextEvent)(Display *, XEvent *);
    Atom (*XInternAtom)(Display *, const char *, Bool);
    Status (*XSetWMProtocols)(Display *, Window, Atom *, int);
    int (*XChangeProperty)(Display *, Window, Atom, Atom, int, int, const unsigned char *, int);
    XSizeHints *(*XAllocSizeHints)(void);
    void (*XSetWMNormalHints)(Display *, Window, XSizeHints *);
    XClassHint *(*XAllocClassHint)(void);
    int (*XSetClassHint)(Display *, Window, XClassHint *);
    int (*XStoreName)(Display *, Window, const char *);
    int (*XResizeWindow)(Display *, Window, unsigned int, unsigned int);
    int (*XFree)(void *);
    char *(*XSetLocaleModifiers)(const char *);
    XIM (*XOpenIM)(Display *, XrmDatabase, char *, char *);
    Status (*XCloseIM)(XIM);
    XIC (*XCreateIC)(XIM, ...);
    void (*XDestroyIC)(XIC);
    void (*XSetICFocus)(XIC);
    void (*XUnsetICFocus)(XIC);
    Cursor (*XCreateFontCursor)(Display *, unsigned int);
    int (*XDefineCursor)(Display *, Window, Cursor);
    int (*XFreeCursor)(Display *, Cursor);
    GC (*XCreateGC)(Display *, Drawable, unsigned long, void *);
    int (*XFreeGC)(Display *, GC);
    XImage *(*XCreateImage)(Display *, Visual *, unsigned int, int, int, char *, unsigned int, unsigned int, int, int);
    int (*XDestroyImage)(XImage *);
    int (*XPutImage)(Display *, Drawable, GC, XImage *, int, int, int, int, unsigned int, unsigned int);
    XErrorHandler (*XSetErrorHandler)(XErrorHandler);
    int (*XSetSelectionOwner)(Display *, Atom, Window, Time);
    Window (*XGetSelectionOwner)(Display *, Atom);
    int (*XConvertSelection)(Display *, Atom, Atom, Atom, Window, Time);
    Status (*XSendEvent)(Display *, Window, Bool, long, XEvent *);
    Bool (*XCheckTypedWindowEvent)(Display *, Window, int, XEvent *);
    int (*XGetWindowProperty)(Display *, Window, Atom, long, long, Bool, Atom, Atom *, int *, unsigned long *, unsigned long *, unsigned char **);
    Bool (*XTranslateCoordinates)(Display *, Window, Window, int, int, int *, int *, Window *);
    Bool (*XFilterEvent)(XEvent *, Window);
    KeySym (*XLookupKeysym)(XKeyEvent *, int);
    int (*XLookupString)(XKeyEvent *, char *, int, KeySym *, void *);
    int (*Xutf8LookupString)(XIC, XKeyEvent *, char *, int, KeySym *, Status *);
    char *(*XResourceManagerString)(Display *);
    void (*XrmInitialize)(void);
    XrmDatabase (*XrmGetStringDatabase)(const char *);
    Bool (*XrmGetResource)(XrmDatabase, const char *, const char *, char **, XrmValue *);
    void (*XrmDestroyDatabase)(XrmDatabase);
} cui__xlib_syms;

static cui__xlib_syms g_x11;

static bool cui__load_x11(void) {
    if (g_x11.handle) return true;
    void *h = dlopen("libX11.so.6", RTLD_LAZY | RTLD_LOCAL);
    if (!h) h = dlopen("libX11.so", RTLD_LAZY | RTLD_LOCAL);
    if (!h) return false;
#define LOAD_SYM(name) do { \
    *(void **)(&g_x11.name) = dlsym(h, #name); \
    if (!g_x11.name) { dlclose(h); memset(&g_x11, 0, sizeof g_x11); return false; } \
} while (0)
    LOAD_SYM(XInitThreads);
    LOAD_SYM(XOpenDisplay);
    LOAD_SYM(XCloseDisplay);
    LOAD_SYM(XDefaultScreen);
    LOAD_SYM(XRootWindow);
    LOAD_SYM(XDefaultVisual);
    LOAD_SYM(XDefaultDepth);
    LOAD_SYM(XConnectionNumber);
    LOAD_SYM(XCreateColormap);
    LOAD_SYM(XFreeColormap);
    LOAD_SYM(XCreateWindow);
    LOAD_SYM(XDestroyWindow);
    LOAD_SYM(XMapWindow);
    LOAD_SYM(XFlush);
    LOAD_SYM(XSync);
    LOAD_SYM(XPending);
    LOAD_SYM(XNextEvent);
    LOAD_SYM(XInternAtom);
    LOAD_SYM(XSetWMProtocols);
    LOAD_SYM(XChangeProperty);
    LOAD_SYM(XAllocSizeHints);
    LOAD_SYM(XSetWMNormalHints);
    LOAD_SYM(XAllocClassHint);
    LOAD_SYM(XSetClassHint);
    LOAD_SYM(XStoreName);
    LOAD_SYM(XResizeWindow);
    LOAD_SYM(XFree);
    LOAD_SYM(XSetLocaleModifiers);
    LOAD_SYM(XOpenIM);
    LOAD_SYM(XCloseIM);
    LOAD_SYM(XCreateIC);
    LOAD_SYM(XDestroyIC);
    LOAD_SYM(XSetICFocus);
    LOAD_SYM(XUnsetICFocus);
    LOAD_SYM(XCreateFontCursor);
    LOAD_SYM(XDefineCursor);
    LOAD_SYM(XFreeCursor);
    LOAD_SYM(XCreateGC);
    LOAD_SYM(XFreeGC);
    LOAD_SYM(XCreateImage);
    LOAD_SYM(XDestroyImage);
    LOAD_SYM(XPutImage);
    LOAD_SYM(XSetErrorHandler);
    LOAD_SYM(XSetSelectionOwner);
    LOAD_SYM(XGetSelectionOwner);
    LOAD_SYM(XConvertSelection);
    LOAD_SYM(XSendEvent);
    LOAD_SYM(XCheckTypedWindowEvent);
    LOAD_SYM(XGetWindowProperty);
    LOAD_SYM(XTranslateCoordinates);
    LOAD_SYM(XFilterEvent);
    LOAD_SYM(XLookupKeysym);
    LOAD_SYM(XLookupString);
    LOAD_SYM(Xutf8LookupString);
    LOAD_SYM(XResourceManagerString);
    LOAD_SYM(XrmInitialize);
    LOAD_SYM(XrmGetStringDatabase);
    LOAD_SYM(XrmGetResource);
    LOAD_SYM(XrmDestroyDatabase);
#undef LOAD_SYM
    g_x11.handle = h;
    return true;
}

/* ---- GLX ---- */
typedef struct __GLXFBConfigRec *GLXFBConfig_;
typedef struct __GLXcontextRec *GLXContext_;
typedef XID GLXDrawable_;

typedef GLXFBConfig_ *(*PFN_glXChooseFBConfig)(Display *, int, const int *, int *);
typedef XVisualInfo *(*PFN_glXGetVisualFromFBConfig)(Display *, GLXFBConfig_);
typedef void *(*PFN_glXGetProcAddress)(const unsigned char *);
typedef int (*PFN_glXMakeCurrent)(Display *, GLXDrawable_, GLXContext_);
typedef void (*PFN_glXSwapBuffers)(Display *, GLXDrawable_);
typedef void (*PFN_glXDestroyContext)(Display *, GLXContext_);
typedef GLXContext_ (*PFN_glXCreateContextAttribsARB)(Display *, GLXFBConfig_, GLXContext_, int, const int *);
typedef void (*PFN_glXSwapIntervalEXT)(Display *, GLXDrawable_, int);
typedef int (*PFN_glXSwapIntervalMESA)(unsigned int);
typedef Bool (*PFN_glXGetMscRateOML)(Display *, GLXDrawable_, int32_t *, int32_t *);
typedef const char *(*PFN_glXQueryExtensionsString)(Display *, int);

#define GLX_X_RENDERABLE_ 0x8012
#define GLX_DRAWABLE_TYPE_ 0x8010
#define GLX_WINDOW_BIT_ 0x0001
#define GLX_RENDER_TYPE_ 0x8011
#define GLX_RGBA_BIT_ 0x0001
#define GLX_X_VISUAL_TYPE_ 0x22
#define GLX_TRUE_COLOR_ 0x8002
#define GLX_RED_SIZE_ 8
#define GLX_GREEN_SIZE_ 9
#define GLX_BLUE_SIZE_ 10
#define GLX_ALPHA_SIZE_ 11
#define GLX_DOUBLEBUFFER_ 5
#define GLX_CONTEXT_MAJOR_VERSION_ARB_ 0x2091
#define GLX_CONTEXT_MINOR_VERSION_ARB_ 0x2092
#define GLX_CONTEXT_PROFILE_MASK_ARB_ 0x9126
#define GLX_CONTEXT_CORE_PROFILE_BIT_ARB_ 0x0001
#define GLX_CONTEXT_FLAGS_ARB_ 0x2094
#define GLX_CONTEXT_FORWARD_COMPATIBLE_BIT_ARB_ 0x0002

typedef struct {
    Display *dpy;
    int screen;
    Window win;
    Colormap cmap;
    Visual *visual;
    int depth;
    XIM im;
    XIC ic;
    Atom wm_delete, wm_protocols, net_wm_name, utf8_string, clipboard, targets, cui_sel, net_wm_icon_name;
    Cursor cursors[CUI_CURSOR_COUNT];
    cui_cursor current_cursor;
    int width, height;
    float scale;
    GC gc;
    XImage *image;
    void *libgl;
    GLXContext_ ctx;
    GLXFBConfig_ fbc;
    PFN_glXGetProcAddress GetProcAddress;
    PFN_glXMakeCurrent MakeCurrent;
    PFN_glXSwapBuffers SwapBuffers;
    PFN_glXDestroyContext DestroyContext;
    PFN_glXGetMscRateOML GetMscRate;   /* refresh rate, when GLX_OML_sync_control is there */
    char *clip_owned;
    char *clip_read;
    bool mapped;
    Atom xdnd_aware, xdnd_enter, xdnd_position, xdnd_status, xdnd_leave, xdnd_drop, xdnd_finished,
         xdnd_selection, xdnd_action_copy, uri_list, cui_xdnd;
    Window xdnd_source;
    int xdnd_version;
    float xdnd_x, xdnd_y;
    int wake_pipe[2];
} cui__x11;

static cui__x11 *cui__x(cui_app *app) { return app->plat; }
static void *cui__x11_libgl;
static PFN_glXGetProcAddress cui__x11_getproc;

double cui__plat_now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

const char *cui__plat_name(void) { return "x11"; }

int cui__plat_system_dark(void) {
    const char *gtk = getenv("GTK_THEME");
    if (gtk && strstr(gtk, "dark")) return 1;
    return -1;
}

static float cui__x11_dpi_scale(Display *dpy) {
    const char *env = getenv("CUI_SCALE");
    if (env) { float s = (float)atof(env); if (s > 0.25f && s < 8) return s; }
    char *rms = g_x11.XResourceManagerString(dpy);
    float scale = 1.0f;
    if (rms) {
        g_x11.XrmInitialize();
        XrmDatabase db = g_x11.XrmGetStringDatabase(rms);
        if (db) {
            char *type = NULL;
            XrmValue val;
            if (g_x11.XrmGetResource(db, "Xft.dpi", "Xft.Dpi", &type, &val) && val.addr) {
                float dpi = (float)atof(val.addr);
                if (dpi > 0) scale = dpi / 96.0f;
            }
            g_x11.XrmDestroyDatabase(db);
        }
    }
    if (scale < 1.0f) scale = 1.0f;
    return roundf(scale * 4) / 4;
}

static const char *cui__x11_get_clip(void *user);
static void cui__x11_set_clip(void *user, const char *utf8);
static void cui__x11_set_cursor(void *user, cui_cursor c);

static bool cui__x11_load_glx(cui__x11 *x) {
    if (!cui__x11_libgl) cui__x11_libgl = dlopen("libGL.so.1", RTLD_NOW | RTLD_GLOBAL);
    if (!cui__x11_libgl) cui__x11_libgl = dlopen("libGL.so", RTLD_NOW | RTLD_GLOBAL);
    if (!cui__x11_libgl) return false;
    x->libgl = cui__x11_libgl;
    cui__x11_getproc = (PFN_glXGetProcAddress)dlsym(x->libgl, "glXGetProcAddressARB");
    x->GetProcAddress = cui__x11_getproc;
    x->MakeCurrent = (PFN_glXMakeCurrent)dlsym(x->libgl, "glXMakeCurrent");
    x->SwapBuffers = (PFN_glXSwapBuffers)dlsym(x->libgl, "glXSwapBuffers");
    x->DestroyContext = (PFN_glXDestroyContext)dlsym(x->libgl, "glXDestroyContext");
    return x->GetProcAddress && x->MakeCurrent && x->SwapBuffers && x->DestroyContext;
}

bool cui__plat_init(cui_app *app) {
    if (!cui__load_x11()) return false;
    cui__x11 *x = calloc(1, sizeof *x);
    if (!x) return false;
    app->plat = x;
    x->wake_pipe[0] = x->wake_pipe[1] = -1;
    if (pipe(x->wake_pipe) == 0) {
        fcntl(x->wake_pipe[0], F_SETFL, O_NONBLOCK);
        fcntl(x->wake_pipe[1], F_SETFL, O_NONBLOCK);
    }
    setlocale(LC_CTYPE, "");
    g_x11.XInitThreads();
    x->dpy = g_x11.XOpenDisplay(NULL);
    if (!x->dpy) {
        if (x->wake_pipe[0] >= 0) { close(x->wake_pipe[0]); close(x->wake_pipe[1]); }
        free(x); app->plat = NULL; return false;
    }
    x->screen = g_x11.XDefaultScreen(x->dpy);
    x->scale = cui__x11_dpi_scale(x->dpy);
    Window root = g_x11.XRootWindow(x->dpy, x->screen);
    x->visual = g_x11.XDefaultVisual(x->dpy, x->screen);
    x->depth = g_x11.XDefaultDepth(x->dpy, x->screen);
    bool want_gl = app->desc.renderer != CUI_RENDERER_SOFTWARE && !(getenv("CUI_RENDERER") && strcmp(getenv("CUI_RENDERER"), "software") == 0);
    if (want_gl && cui__x11_load_glx(x)) {
        PFN_glXChooseFBConfig choose = (PFN_glXChooseFBConfig)dlsym(x->libgl, "glXChooseFBConfig");
        PFN_glXGetVisualFromFBConfig getvis = (PFN_glXGetVisualFromFBConfig)dlsym(x->libgl, "glXGetVisualFromFBConfig");
        if (choose && getvis) {
            int attrs[] = { GLX_X_RENDERABLE_, True_, GLX_DRAWABLE_TYPE_, GLX_WINDOW_BIT_, GLX_RENDER_TYPE_, GLX_RGBA_BIT_,
                            GLX_X_VISUAL_TYPE_, GLX_TRUE_COLOR_, GLX_RED_SIZE_, 8, GLX_GREEN_SIZE_, 8, GLX_BLUE_SIZE_, 8,
                            GLX_ALPHA_SIZE_, 8, GLX_DOUBLEBUFFER_, True_, (int)None_ };
            int n = 0;
            GLXFBConfig_ *cfgs = choose(x->dpy, x->screen, attrs, &n);
            if (cfgs && n > 0) {
                XVisualInfo *vi = getvis(x->dpy, cfgs[0]);
                if (vi) {
                    x->fbc = cfgs[0];
                    x->visual = vi->visual;
                    x->depth = vi->depth;
                    g_x11.XFree(vi);
                }
            }
            if (cfgs) g_x11.XFree(cfgs);
        }
    }
    x->cmap = g_x11.XCreateColormap(x->dpy, root, x->visual, AllocNone_);
    XSetWindowAttributes swa;
    memset(&swa, 0, sizeof swa);
    swa.colormap = x->cmap;
    cui_color bg = app->ui->theme.colors[CUI_TOKEN_BACKGROUND];
    swa.background_pixel = ((unsigned long)bg.r << 16) | ((unsigned long)bg.g << 8) | bg.b;
    swa.event_mask = ExposureMask_ | KeyPressMask_ | KeyReleaseMask_ | ButtonPressMask_ | ButtonReleaseMask_ |
                     PointerMotionMask_ | EnterWindowMask_ | LeaveWindowMask_ | StructureNotifyMask_ | FocusChangeMask_;
    x->width = (int)(app->desc.width * x->scale);
    x->height = (int)(app->desc.height * x->scale);
    x->win = g_x11.XCreateWindow(x->dpy, root, 0, 0, (unsigned)x->width, (unsigned)x->height, 0, x->depth, InputOutput_, x->visual,
                                 CWColormap_ | CWBorderPixel_ | CWBackPixel_ | CWEventMask_, &swa);
    if (!x->win) {
        if (x->wake_pipe[0] >= 0) { close(x->wake_pipe[0]); close(x->wake_pipe[1]); }
        g_x11.XCloseDisplay(x->dpy); free(x); app->plat = NULL; return false;
    }
    x->wm_protocols = g_x11.XInternAtom(x->dpy, "WM_PROTOCOLS", False_);
    x->wm_delete = g_x11.XInternAtom(x->dpy, "WM_DELETE_WINDOW", False_);
    x->net_wm_name = g_x11.XInternAtom(x->dpy, "_NET_WM_NAME", False_);
    x->net_wm_icon_name = g_x11.XInternAtom(x->dpy, "_NET_WM_ICON_NAME", False_);
    x->utf8_string = g_x11.XInternAtom(x->dpy, "UTF8_STRING", False_);
    x->clipboard = g_x11.XInternAtom(x->dpy, "CLIPBOARD", False_);
    x->targets = g_x11.XInternAtom(x->dpy, "TARGETS", False_);
    x->cui_sel = g_x11.XInternAtom(x->dpy, "CUI_SELECTION", False_);
    g_x11.XSetWMProtocols(x->dpy, x->win, &x->wm_delete, 1);

    x->xdnd_aware = g_x11.XInternAtom(x->dpy, "XdndAware", False_);
    x->xdnd_enter = g_x11.XInternAtom(x->dpy, "XdndEnter", False_);
    x->xdnd_position = g_x11.XInternAtom(x->dpy, "XdndPosition", False_);
    x->xdnd_status = g_x11.XInternAtom(x->dpy, "XdndStatus", False_);
    x->xdnd_leave = g_x11.XInternAtom(x->dpy, "XdndLeave", False_);
    x->xdnd_drop = g_x11.XInternAtom(x->dpy, "XdndDrop", False_);
    x->xdnd_finished = g_x11.XInternAtom(x->dpy, "XdndFinished", False_);
    x->xdnd_selection = g_x11.XInternAtom(x->dpy, "XdndSelection", False_);
    x->xdnd_action_copy = g_x11.XInternAtom(x->dpy, "XdndActionCopy", False_);
    x->uri_list = g_x11.XInternAtom(x->dpy, "text/uri-list", False_);
    x->cui_xdnd = g_x11.XInternAtom(x->dpy, "CUI_XDND", False_);
    {
        Atom version = 5;
        g_x11.XChangeProperty(x->dpy, x->win, x->xdnd_aware, XA_ATOM_, 32, PropModeReplace_, (unsigned char *)&version, 1);
    }
    XSizeHints *hints = g_x11.XAllocSizeHints();
    if (hints) {
        hints->flags = PMinSize_;
        hints->min_width = (int)(app->desc.min_width * x->scale);
        hints->min_height = (int)(app->desc.min_height * x->scale);
        if (app->desc.fixed_size) {
            hints->flags |= PMaxSize_;
            hints->min_width = hints->max_width = x->width;
            hints->min_height = hints->max_height = x->height;
        }
        g_x11.XSetWMNormalHints(x->dpy, x->win, hints);
        g_x11.XFree(hints);
    }
    /* Desktops find the window's .desktop file (name, icon, dock entry) by
     * matching WM_CLASS against its file name, so both parts carry the app ID */
    XClassHint *ch = g_x11.XAllocClassHint();
    if (ch) {
        ch->res_name = (char *)(app->desc.app_id ? app->desc.app_id : app->title);
        ch->res_class = (char *)(app->desc.app_id ? app->desc.app_id : "Nexa");
        g_x11.XSetClassHint(x->dpy, x->win, ch);
        g_x11.XFree(ch);
    }
    cui__plat_set_title(app, app->title);
    g_x11.XSetLocaleModifiers("");
    x->im = g_x11.XOpenIM(x->dpy, NULL, NULL, NULL);
    if (!x->im) { g_x11.XSetLocaleModifiers("@im=none"); x->im = g_x11.XOpenIM(x->dpy, NULL, NULL, NULL); }
    if (x->im) x->ic = g_x11.XCreateIC(x->im, XNInputStyle_, XIMPreeditNothing_ | XIMStatusNothing_, XNClientWindow_, x->win, XNFocusWindow_, x->win, NULL);
    unsigned int shapes[CUI_CURSOR_COUNT] = { XC_left_ptr_, XC_hand2_, XC_xterm_, XC_sb_h_double_arrow_, XC_sb_v_double_arrow_, XC_fleur_, XC_X_cursor_ };
    for (int i = 0; i < CUI_CURSOR_COUNT; i++) x->cursors[i] = g_x11.XCreateFontCursor(x->dpy, shapes[i]);
    x->gc = g_x11.XCreateGC(x->dpy, x->win, 0, NULL);
    cui_platform_iface pi;
    memset(&pi, 0, sizeof pi);
    pi.user = app;
    pi.get_clipboard = cui__x11_get_clip;
    pi.set_clipboard = cui__x11_set_clip;
    pi.set_cursor = cui__x11_set_cursor;
    cui_set_platform(app->ui, &pi);
    return true;
}

void cui__plat_show(cui_app *app) {
    cui__x11 *x = cui__x(app);
    g_x11.XMapWindow(x->dpy, x->win);
    g_x11.XFlush(x->dpy);
    x->mapped = true;
}

void cui__plat_shutdown(cui_app *app) {
    cui__x11 *x = cui__x(app);
    if (!x) return;
    if (x->ctx) { x->MakeCurrent(x->dpy, None_, NULL); x->DestroyContext(x->dpy, x->ctx); }
    if (x->image) { x->image->data = NULL; g_x11.XDestroyImage(x->image); }
    if (x->ic) g_x11.XDestroyIC(x->ic);
    if (x->im) g_x11.XCloseIM(x->im);
    for (int i = 0; i < CUI_CURSOR_COUNT; i++) if (x->cursors[i]) g_x11.XFreeCursor(x->dpy, x->cursors[i]);
    if (x->gc) g_x11.XFreeGC(x->dpy, x->gc);
    g_x11.XDestroyWindow(x->dpy, x->win);
    g_x11.XFreeColormap(x->dpy, x->cmap);
    g_x11.XCloseDisplay(x->dpy);
    if (x->wake_pipe[0] >= 0) { close(x->wake_pipe[0]); close(x->wake_pipe[1]); }
    free(x->clip_owned);
    free(x->clip_read);
    free(x);
    app->plat = NULL;
}

static int cui__x11_err_flag;
static int cui__x11_error_handler(Display *d, XErrorEvent *e) { (void)d; (void)e; cui__x11_err_flag = 1; return 0; }

bool cui__plat_gl_create(cui_app *app, bool vsync) {
    cui__x11 *x = cui__x(app);
    if (!x->libgl || !x->fbc) return false;
    PFN_glXCreateContextAttribsARB create = (PFN_glXCreateContextAttribsARB)x->GetProcAddress((const unsigned char *)"glXCreateContextAttribsARB");
    if (!create) return false;
    int attrs[] = { GLX_CONTEXT_MAJOR_VERSION_ARB_, 3, GLX_CONTEXT_MINOR_VERSION_ARB_, 3,
                    GLX_CONTEXT_PROFILE_MASK_ARB_, GLX_CONTEXT_CORE_PROFILE_BIT_ARB_,
                    GLX_CONTEXT_FLAGS_ARB_, GLX_CONTEXT_FORWARD_COMPATIBLE_BIT_ARB_, (int)None_ };
    XErrorHandler old = g_x11.XSetErrorHandler(cui__x11_error_handler);
    cui__x11_err_flag = 0;
    x->ctx = create(x->dpy, x->fbc, NULL, True_, attrs);
    g_x11.XSync(x->dpy, False_);
    g_x11.XSetErrorHandler(old);
    if (!x->ctx || cui__x11_err_flag) { x->ctx = NULL; return false; }
    if (!x->MakeCurrent(x->dpy, x->win, x->ctx)) { x->DestroyContext(x->dpy, x->ctx); x->ctx = NULL; return false; }
    PFN_glXSwapIntervalEXT sie = (PFN_glXSwapIntervalEXT)x->GetProcAddress((const unsigned char *)"glXSwapIntervalEXT");
    PFN_glXSwapIntervalMESA sim = (PFN_glXSwapIntervalMESA)x->GetProcAddress((const unsigned char *)"glXSwapIntervalMESA");
    if (sie) sie(x->dpy, x->win, vsync ? 1 : 0);
    else if (sim) sim(vsync ? 1 : 0);
    PFN_glXQueryExtensionsString qes = (PFN_glXQueryExtensionsString)dlsym(x->libgl, "glXQueryExtensionsString");
    const char *ext = qes ? qes(x->dpy, g_x11.XDefaultScreen(x->dpy)) : NULL;
    if (ext && strstr(ext, "GLX_OML_sync_control"))
        x->GetMscRate = (PFN_glXGetMscRateOML)x->GetProcAddress((const unsigned char *)"glXGetMscRateOML");
    return true;
}

void *cui__plat_gl_proc(const char *name) {
    void *p = NULL;
    if (cui__x11_getproc) p = cui__x11_getproc((const unsigned char *)name);
    if (!p && cui__x11_libgl) p = dlsym(cui__x11_libgl, name);
    return p;
}

double cui__plat_refresh_hz(cui_app *app) {
    cui__x11 *x = cui__x(app);
    int32_t num = 0, den = 0;
    if (x->ctx && x->GetMscRate && x->GetMscRate(x->dpy, x->win, &num, &den) && den > 0) return (double)num / den;
    return 0;
}

void cui__plat_gl_release(cui_app *app) {
    cui__x11 *x = cui__x(app);
    x->GetMscRate = NULL;
    if (x->ctx) { x->MakeCurrent(x->dpy, None_, NULL); x->DestroyContext(x->dpy, x->ctx); x->ctx = NULL; }
}

void cui__plat_gl_swap(cui_app *app) {
    cui__x11 *x = cui__x(app);
    if (x->ctx) x->SwapBuffers(x->dpy, x->win);
}

void cui__plat_present(cui_app *app, const void *bgra, int w, int h, int stride) {
    cui__x11 *x = cui__x(app);
    if (!x->image || x->image->width != w || x->image->height != h) {
        if (x->image) { x->image->data = NULL; g_x11.XDestroyImage(x->image); }
        x->image = g_x11.XCreateImage(x->dpy, x->visual, (unsigned)x->depth, ZPixmap_, 0, NULL, (unsigned)w, (unsigned)h, 32, stride);
    }
    if (!x->image) return;
    x->image->data = (char *)bgra;
    g_x11.XPutImage(x->dpy, x->win, x->gc, x->image, 0, 0, 0, 0, (unsigned)w, (unsigned)h);
    g_x11.XFlush(x->dpy);
}

bool cui__plat_present_part(cui_app *app, const void *bgra, int w, int h, int stride, int px, int py, int pw, int ph) {
    cui__x11 *x = cui__x(app);
    if (!x->image || x->image->width != w || x->image->height != h) return false;
    x->image->data = (char *)bgra;
    (void)stride;
    g_x11.XPutImage(x->dpy, x->win, x->gc, x->image, px, py, px, py, (unsigned)pw, (unsigned)ph);
    g_x11.XFlush(x->dpy);
    return true;
}

void cui__plat_metrics(cui_app *app, float *w, float *h, float *scale, int *fb_w, int *fb_h) {
    cui__x11 *x = cui__x(app);
    *scale = x->scale;
    *fb_w = x->width; *fb_h = x->height;
    *w = (float)x->width / x->scale;
    *h = (float)x->height / x->scale;
}

void cui__plat_set_title(cui_app *app, const char *title) {
    cui__x11 *x = cui__x(app);
    g_x11.XStoreName(x->dpy, x->win, title);
    g_x11.XChangeProperty(x->dpy, x->win, x->net_wm_name, x->utf8_string, 8, PropModeReplace_, (const unsigned char *)title, (int)strlen(title));
    g_x11.XChangeProperty(x->dpy, x->win, x->net_wm_icon_name, x->utf8_string, 8, PropModeReplace_, (const unsigned char *)title, (int)strlen(title));
    g_x11.XFlush(x->dpy);
}

void cui__plat_set_size(cui_app *app, int w, int h) {
    cui__x11 *x = cui__x(app);
    g_x11.XResizeWindow(x->dpy, x->win, (unsigned)(w * x->scale), (unsigned)(h * x->scale));
    g_x11.XFlush(x->dpy);
}

void *cui__plat_native(cui_app *app) { return (void *)(uintptr_t)cui__x(app)->win; }

static void cui__x11_set_cursor(void *user, cui_cursor c) {
    cui_app *app = user;
    cui__x11 *x = cui__x(app);
    if (c == x->current_cursor || (int)c < 0 || c >= CUI_CURSOR_COUNT) return;
    x->current_cursor = c;
    g_x11.XDefineCursor(x->dpy, x->win, x->cursors[c]);
    g_x11.XFlush(x->dpy);
}

static void cui__x11_set_clip(void *user, const char *utf8) {
    cui_app *app = user;
    cui__x11 *x = cui__x(app);
    free(x->clip_owned);
    size_t n = strlen(utf8);
    x->clip_owned = malloc(n + 1);
    if (x->clip_owned) memcpy(x->clip_owned, utf8, n + 1);
    g_x11.XSetSelectionOwner(x->dpy, x->clipboard, x->win, CurrentTime_);
    g_x11.XFlush(x->dpy);
}

static void cui__x11_handle_selection_request(cui__x11 *x, XSelectionRequestEvent *req) {
    XSelectionEvent ev;
    memset(&ev, 0, sizeof ev);
    ev.type = SelectionNotify_;
    ev.requestor = req->requestor;
    ev.selection = req->selection;
    ev.target = req->target;
    ev.time = req->time;
    ev.property = None_;
    if (x->clip_owned) {
        if (req->target == x->targets) {
            Atom list[3] = { x->targets, x->utf8_string, XA_STRING_ };
            g_x11.XChangeProperty(x->dpy, req->requestor, req->property, XA_ATOM_, 32, PropModeReplace_, (unsigned char *)list, 3);
            ev.property = req->property;
        } else if (req->target == x->utf8_string || req->target == XA_STRING_) {
            g_x11.XChangeProperty(x->dpy, req->requestor, req->property, req->target, 8, PropModeReplace_,
                                  (unsigned char *)x->clip_owned, (int)strlen(x->clip_owned));
            ev.property = req->property;
        }
    }
    g_x11.XSendEvent(x->dpy, req->requestor, False_, 0, (XEvent *)&ev);
    g_x11.XFlush(x->dpy);
}

static const char *cui__x11_get_clip(void *user) {
    cui_app *app = user;
    cui__x11 *x = cui__x(app);
    Window owner = g_x11.XGetSelectionOwner(x->dpy, x->clipboard);
    if (owner == x->win) return x->clip_owned;
    if (owner == None_) return NULL;
    g_x11.XConvertSelection(x->dpy, x->clipboard, x->utf8_string, x->cui_sel, x->win, CurrentTime_);
    g_x11.XFlush(x->dpy);
    double start = cui__plat_now();
    while (cui__plat_now() - start < 0.5) {
        XEvent ev;
        if (g_x11.XCheckTypedWindowEvent(x->dpy, x->win, SelectionNotify_, &ev)) {
            if (ev.xselection.property == None_) return NULL;
            Atom type;
            int fmt;
            unsigned long n, rest;
            unsigned char *data = NULL;
            g_x11.XGetWindowProperty(x->dpy, x->win, x->cui_sel, 0, 1 << 24, True_, AnyPropertyType_, &type, &fmt, &n, &rest, &data);
            free(x->clip_read);
            x->clip_read = NULL;
            if (data) {
                x->clip_read = malloc(n + 1);
                if (x->clip_read) { memcpy(x->clip_read, data, n); x->clip_read[n] = 0; }
                g_x11.XFree(data);
            }
            return x->clip_read;
        }
        if (g_x11.XCheckTypedWindowEvent(x->dpy, x->win, SelectionRequest_, &ev)) cui__x11_handle_selection_request(x, &ev.xselectionrequest);
        { struct timespec ts = { 0, 1000000 }; nanosleep(&ts, NULL); }
    }
    return NULL;
}

static cui_key cui__x11_key(KeySym ks) {
    if (ks >= XK_a_ && ks <= XK_z_) return (cui_key)(CUI_KEY_A + (int)(ks - XK_a_));
    if (ks >= XK_A_ && ks <= XK_Z_) return (cui_key)(CUI_KEY_A + (int)(ks - XK_A_));
    if (ks >= XK_0_ && ks <= XK_9_) return (cui_key)(CUI_KEY_0 + (int)(ks - XK_0_));
    if (ks >= XK_F1_ && ks <= XK_F12_) return (cui_key)(CUI_KEY_F1 + (int)(ks - XK_F1_));
    switch (ks) {
    case XK_Tab_: case XK_ISO_Left_Tab_: return CUI_KEY_TAB;
    case XK_Return_: case XK_KP_Enter_: return CUI_KEY_ENTER;
    case XK_Escape_: return CUI_KEY_ESCAPE;
    case XK_BackSpace_: return CUI_KEY_BACKSPACE;
    case XK_Delete_: case XK_KP_Delete_: return CUI_KEY_DELETE;
    case XK_space_: return CUI_KEY_SPACE;
    case XK_Left_: case XK_KP_Left_: return CUI_KEY_LEFT;
    case XK_Right_: case XK_KP_Right_: return CUI_KEY_RIGHT;
    case XK_Up_: case XK_KP_Up_: return CUI_KEY_UP;
    case XK_Down_: case XK_KP_Down_: return CUI_KEY_DOWN;
    case XK_Home_: case XK_KP_Home_: return CUI_KEY_HOME;
    case XK_End_: case XK_KP_End_: return CUI_KEY_END;
    case XK_Page_Up_: case XK_KP_Page_Up_: return CUI_KEY_PAGE_UP;
    case XK_Page_Down_: case XK_KP_Page_Down_: return CUI_KEY_PAGE_DOWN;
    case XK_minus_: return CUI_KEY_MINUS;
    case XK_equal_: return CUI_KEY_EQUAL;
    case XK_comma_: return CUI_KEY_COMMA;
    case XK_period_: return CUI_KEY_PERIOD;
    case XK_slash_: return CUI_KEY_SLASH;
    default: return CUI_KEY_NONE;
    }
}

static int cui__x11_mods(unsigned int state) {
    int m = 0;
    if (state & ShiftMask_) m |= CUI_MOD_SHIFT;
    if (state & ControlMask_) m |= CUI_MOD_CTRL;
    if (state & Mod1Mask_) m |= CUI_MOD_ALT;
    if (state & Mod4Mask_) m |= CUI_MOD_SUPER;
    return m;
}

static void cui__x11_xdnd_send(cui__x11 *x, Window to, Atom type, long l1, long l2, long l3, long l4) {
    XEvent e;
    memset(&e, 0, sizeof e);
    e.xclient.type = ClientMessage_;
    e.xclient.display = x->dpy;
    e.xclient.window = to;
    e.xclient.message_type = type;
    e.xclient.format = 32;
    e.xclient.data.l[0] = (long)x->win;
    e.xclient.data.l[1] = l1;
    e.xclient.data.l[2] = l2;
    e.xclient.data.l[3] = l3;
    e.xclient.data.l[4] = l4;
    g_x11.XSendEvent(x->dpy, to, False_, NoEventMask_, &e);
    g_x11.XFlush(x->dpy);
}

static int cui__hexv(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

static void cui__x11_xdnd_deliver(cui_app *app, const char *data, size_t len) {
    cui__x11 *x = cui__x(app);
    char *paths[64];
    int n = 0;
    size_t i = 0;
    while (i < len && n < 64) {
        size_t e = i;
        while (e < len && data[e] != '\n' && data[e] != '\r') e++;
        if (e > i && data[i] != '#' && e - i > 7 && strncmp(data + i, "file://", 7) == 0) {
            size_t p = i + 7;
            while (p < e && data[p] != '/') p++;
            char *out = malloc(e - p + 1);
            if (out) {
                size_t o = 0;
                for (size_t k = p; k < e; k++) {
                    if (data[k] == '%' && k + 2 < e && cui__hexv(data[k + 1]) >= 0 && cui__hexv(data[k + 2]) >= 0) {
                        out[o++] = (char)(cui__hexv(data[k + 1]) * 16 + cui__hexv(data[k + 2]));
                        k += 2;
                    } else out[o++] = data[k];
                }
                out[o] = 0;
                paths[n++] = out;
            }
        }
        i = e;
        while (i < len && (data[i] == '\n' || data[i] == '\r')) i++;
    }
    cui_input_file_drop(app->ui, (const char *const *)paths, n, x->xdnd_x, x->xdnd_y);
    for (int k = 0; k < n; k++) free(paths[k]);
}

static bool cui__x11_xdnd_message(cui_app *app, XClientMessageEvent *m) {
    cui__x11 *x = cui__x(app);
    Atom t = m->message_type;
    if (t == x->xdnd_enter) {
        x->xdnd_source = (Window)m->data.l[0];
        x->xdnd_version = (int)((unsigned long)m->data.l[1] >> 24);
        return true;
    }
    if (t == x->xdnd_position) {
        x->xdnd_source = (Window)m->data.l[0];
        int rx = (int)(((unsigned long)m->data.l[2] >> 16) & 0xFFFF), ry = (int)((unsigned long)m->data.l[2] & 0xFFFF);
        int wx = 0, wy = 0;
        Window child;
        g_x11.XTranslateCoordinates(x->dpy, g_x11.XRootWindow(x->dpy, x->screen), x->win, rx, ry, &wx, &wy, &child);
        x->xdnd_x = wx / x->scale;
        x->xdnd_y = wy / x->scale;
        cui_input_file_hover(app->ui, true, x->xdnd_x, x->xdnd_y);
        cui__x11_xdnd_send(x, x->xdnd_source, x->xdnd_status, 1 | 2, 0, 0, (long)x->xdnd_action_copy);
        return true;
    }
    if (t == x->xdnd_leave) {
        cui_input_file_hover(app->ui, false, 0, 0);
        return true;
    }
    if (t == x->xdnd_drop) {
        x->xdnd_source = (Window)m->data.l[0];
        Time when = x->xdnd_version >= 1 ? (Time)m->data.l[2] : CurrentTime_;
        g_x11.XConvertSelection(x->dpy, x->xdnd_selection, x->uri_list, x->cui_xdnd, x->win, when);
        return true;
    }
    return false;
}

static void cui__x11_xdnd_selection(cui_app *app, XSelectionEvent *se) {
    cui__x11 *x = cui__x(app);
    if (se->property == None_) {
        cui_input_file_hover(app->ui, false, 0, 0);
    } else {
        Atom type;
        int format;
        unsigned long count = 0, after = 0;
        unsigned char *data = NULL;
        if (g_x11.XGetWindowProperty(x->dpy, x->win, x->cui_xdnd, 0, 1 << 22, True_, AnyPropertyType_, &type, &format, &count, &after, &data) == Success_ && data) {
            cui__x11_xdnd_deliver(app, (const char *)data, count);
            g_x11.XFree(data);
        }
    }
    if (x->xdnd_source && x->xdnd_version >= 2)
        cui__x11_xdnd_send(x, x->xdnd_source, x->xdnd_finished, se->property != None_ ? 1 : 0, (long)x->xdnd_action_copy, 0, 0);
    x->xdnd_source = 0;
}

static void cui__x11_event(cui_app *app, XEvent *ev) {
    cui__x11 *x = cui__x(app);
    cui_ctx *ui = app->ui;
    if (g_x11.XFilterEvent(ev, None_)) return;
    float s = x->scale;
    switch (ev->type) {
    case ClientMessage_:
        if (cui__x11_xdnd_message(app, &ev->xclient)) break;
        if ((Atom)ev->xclient.data.l[0] == x->wm_delete) app->running = false;
        break;
    case SelectionNotify_:
        if (ev->xselection.property == x->cui_xdnd || (ev->xselection.selection == x->xdnd_selection)) cui__x11_xdnd_selection(app, &ev->xselection);
        break;
    case ConfigureNotify_:
        if (ev->xconfigure.width != x->width || ev->xconfigure.height != x->height) {
            x->width = ev->xconfigure.width;
            x->height = ev->xconfigure.height;
            cui_request_redraw(ui);
        }
        break;
    case Expose_:
        app->force_present = true;
        cui_request_redraw(ui);
        break;
    case MotionNotify_:
        cui_input_mouse_move(ui, ev->xmotion.x / s, ev->xmotion.y / s);
        break;
    case EnterNotify_:
        cui_input_mouse_move(ui, ev->xcrossing.x / s, ev->xcrossing.y / s);
        break;
    case LeaveNotify_:
        if (!cui_mouse_down(ui, CUI_MOUSE_LEFT)) cui_input_mouse_leave(ui);
        break;
    case ButtonPress_:
    case ButtonRelease_: {
        bool down = ev->type == ButtonPress_;
        unsigned int b = ev->xbutton.button;
        cui_input_mouse_move(ui, ev->xbutton.x / s, ev->xbutton.y / s);
        if (b == Button1_) cui_input_mouse_button(ui, CUI_MOUSE_LEFT, down);
        else if (b == Button2_) cui_input_mouse_button(ui, CUI_MOUSE_MIDDLE, down);
        else if (b == Button3_) cui_input_mouse_button(ui, CUI_MOUSE_RIGHT, down);
        else if (down && b == Button4_) cui_input_scroll(ui, 0, 1);
        else if (down && b == Button5_) cui_input_scroll(ui, 0, -1);
        else if (down && b == 6) cui_input_scroll(ui, 1, 0);
        else if (down && b == 7) cui_input_scroll(ui, -1, 0);
        break;
    }
    case KeyPress_:
    case KeyRelease_: {
        bool down = ev->type == KeyPress_;
        KeySym ks = g_x11.XLookupKeysym(&ev->xkey, 0);
        int mods = cui__x11_mods(ev->xkey.state);
        cui_key k = cui__x11_key(ks);
        if (k) cui_input_key(ui, k, down, mods);
        else {
            int bit = (ks == XK_Shift_L_ || ks == XK_Shift_R_) ? CUI_MOD_SHIFT : (ks == XK_Control_L_ || ks == XK_Control_R_) ? CUI_MOD_CTRL
                    : (ks == XK_Alt_L_ || ks == XK_Alt_R_ || ks == XK_Meta_L_ || ks == XK_Meta_R_) ? CUI_MOD_ALT : (ks == XK_Super_L_ || ks == XK_Super_R_) ? CUI_MOD_SUPER : 0;
            if (bit) cui_input_key(ui, CUI_KEY_NONE, down, down ? (mods | bit) : (mods & ~bit));
        }
        if (down) {
            char buf[64];
            KeySym sym = 0;
            int n;
            if (x->ic) {
                Status st;
                n = g_x11.Xutf8LookupString(x->ic, &ev->xkey, buf, (int)sizeof buf - 1, &sym, &st);
                if (st != XLookupChars_ && st != XLookupBoth_) n = 0;
            } else {
                n = g_x11.XLookupString(&ev->xkey, buf, (int)sizeof buf - 1, &sym, NULL);
            }
            if (n > 0 && !(mods & CUI_MOD_CTRL)) {
                buf[n] = 0;
                cui_input_text(ui, buf);
            }
        }
        break;
    }
    case FocusIn_:
        if (x->ic) g_x11.XSetICFocus(x->ic);
        cui_input_focus(ui, true);
        break;
    case FocusOut_:
        if (x->ic) g_x11.XUnsetICFocus(x->ic);
        cui_input_focus(ui, false);
        break;
    case SelectionRequest_:
        cui__x11_handle_selection_request(x, &ev->xselectionrequest);
        break;
    case SelectionClear_:
        break;
    default:
        break;
    }
}

void cui__plat_wait(cui_app *app, double timeout) {
    cui__x11 *x = cui__x(app);
    g_x11.XFlush(x->dpy);
    if (timeout != 0 && !g_x11.XPending(x->dpy)) {
        int fd = g_x11.XConnectionNumber(x->dpy);
        int max_fd = fd;
        fd_set set;
        FD_ZERO(&set);
        FD_SET(fd, &set);
        if (x->wake_pipe[0] >= 0) {
            FD_SET(x->wake_pipe[0], &set);
            if (x->wake_pipe[0] > max_fd) max_fd = x->wake_pipe[0];
        }
        struct timeval tv, *ptv = NULL;
        if (timeout > 0) {
            tv.tv_sec = (long)timeout;
            tv.tv_usec = (long)((timeout - (double)tv.tv_sec) * 1e6);
            ptv = &tv;
        }
        select(max_fd + 1, &set, NULL, NULL, ptv);
    }
    if (x->wake_pipe[0] >= 0) {
        char drain[64];
        bool woke = false;
        while (read(x->wake_pipe[0], drain, sizeof drain) > 0) woke = true;
        if (woke) cui_request_redraw(app->ui);
    }
    while (g_x11.XPending(x->dpy)) {
        XEvent ev;
        g_x11.XNextEvent(x->dpy, &ev);
        cui__x11_event(app, &ev);
    }
}

void cui__plat_wake(cui_app *app) {
    cui__x11 *x = cui__x(app);
    if (x && x->wake_pipe[1] >= 0) {
        char b = 1;
        ssize_t r = write(x->wake_pipe[1], &b, 1);
        (void)r;
    }
}

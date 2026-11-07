/* ==========================================================================
   yapps Interactive Theme, Accent, Ordered-Bayer Dither & Docs Controller
   ========================================================================== */

(function () {
  "use strict";

  // Exact 8 built-in CUI OKLCH Accent palettes (0..7)
  const ACCENTS = [
    { key: "NEUTRAL", id: 0, label: "Neutral", dark: "#e8e8e8", darkFg: "#111215", light: "#1d1d1d", lightFg: "#ffffff" },
    { key: "VIOLET",  id: 1, label: "Violet",  dark: "#a78bff", darkFg: "#13092b", light: "#7747ff", lightFg: "#ffffff" },
    { key: "BLUE",    id: 2, label: "Blue",    dark: "#6ba3ff", darkFg: "#071428", light: "#0562ef", lightFg: "#ffffff" },
    { key: "GREEN",   id: 3, label: "Green",   dark: "#53dca6", darkFg: "#052216", light: "#00864b", lightFg: "#ffffff" },
    { key: "AMBER",   id: 4, label: "Amber",   dark: "#ffcb62", darkFg: "#261800", light: "#f3ad20", lightFg: "#1c1200" },
    { key: "ORANGE",  id: 5, label: "Orange",  dark: "#ffad5e", darkFg: "#261000", light: "#c25300", lightFg: "#ffffff" },
    { key: "CORAL",   id: 6, label: "Coral",   dark: "#ff9386", darkFg: "#280906", light: "#d1403a", lightFg: "#ffffff" },
    { key: "ROSE",    id: 7, label: "Rose",    dark: "#ff8bc5", darkFg: "#280718", light: "#d23286", lightFg: "#ffffff" },
  ];

  const ICON_SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>';
  const ICON_MOON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>';

  const SHOWCASES = [
    {
      id: "gallery",
      label: "Editor & Nodes",
      title: "Gallery & Studio — yapps (1200×780)",
      img: "assets/screenshots/gallery.png",
      caption: "Desktop menu bar, toolbar, dirty document tabs, Bezier node graph, typed property inspector & C-backed log console.",
      file: "examples/gallery.py",
    },
    {
      id: "dashboard",
      label: "Data & Analytics",
      title: "Larkspur Analytics — yapps (1140×740)",
      img: "assets/screenshots/dashboard.png",
      caption: "Animated rolling KPIs, sparklines, smooth cubic area chart, donut breakdown, filter bar & 250-row virtualized data grid.",
      file: "examples/dashboard.py",
    },
    {
      id: "tracker",
      label: "Planning",
      title: "Tracker — yapps (1100×700)",
      img: "assets/screenshots/tracker.png",
      caption: "Light-mode drag-and-drop Kanban board, interactive Gantt timeline, 7-day week schedule & live team presence rings.",
      file: "examples/tracker.py",
    },
    {
      id: "assistant",
      label: "Assistant",
      title: "Muse AI — yapps (1160×740)",
      img: "assets/screenshots/assistant.png",
      caption: "Non-blocking BackgroundRunner token streaming, model picker, context ring meter, execution plan & procedural voice orb.",
      file: "examples/assistant.py",
    },
    {
      id: "finance",
      label: "Charts & Finance",
      title: "Finance — yapps (1080×720)",
      img: "assets/screenshots/finance.png",
      caption: "Live scrolling market ticker, rolling odometer counter, proportional Treemap, split bar, Sankey diagram & trading heatmap.",
      file: "examples/finance.py",
    },
    {
      id: "settings",
      label: "OOP & 8 Accents",
      title: "Settings — yapps OOP (980×680)",
      img: "assets/screenshots/settings.png",
      caption: "Object-oriented Application + Router + View + Component architecture showcasing all 8 built-in OKLCH Accent presets.",
      file: "examples/settings.py",
    },
  ];

  const PARADIGMS = {
    functional: {
      file: "hello_functional.py",
      guideLink: "guide.html#tutorial-functional",
      guideLabel: "Read Functional Tutorial →",
      code: `<span class="tok-kw">import</span> <span class="tok-cls">yapps</span> <span class="tok-kw">as</span> ui

<span class="tok-kw">def</span> main() -> <span class="tok-kw">None</span>:
    count = <span class="tok-num">0</span>
    name = <span class="tok-str">"world"</span>

    <span class="tok-kw">def</span> draw() -> <span class="tok-kw">None</span>:
        <span class="tok-kw">nonlocal</span> count, name
        <span class="tok-kw">with</span> ui.column(width=ui.<span class="tok-cls">FILL</span>, height=ui.<span class="tok-cls">FILL</span>, pad=<span class="tok-num">24</span>, gap=<span class="tok-num">14</span>, bg=ui.<span class="tok-cls">Color</span>.<span class="tok-cls">BACKGROUND</span>):
            ui.heading(<span class="tok-str">f"Hello, {name or 'stranger'}!"</span>, level=<span class="tok-num">1</span>)
            name = ui.input(<span class="tok-str">"name"</span>, name, label=<span class="tok-str">"Your name"</span>, clearable=<span class="tok-kw">True</span>)

            <span class="tok-kw">with</span> ui.row(gap=<span class="tok-num">10</span>, align=ui.<span class="tok-cls">Align</span>.<span class="tok-cls">CENTER</span>):
                <span class="tok-kw">if</span> ui.button(<span class="tok-str">"Increment"</span>, variant=ui.<span class="tok-cls">ButtonVariant</span>.<span class="tok-cls">PRIMARY</span>, icon=ui.<span class="tok-cls">Icon</span>.<span class="tok-cls">PLUS</span>):
                    count += <span class="tok-num">1</span>
                ui.badge(<span class="tok-str">f"Count: {count}"</span>, tone=ui.<span class="tok-cls">Tone</span>.<span class="tok-cls">ACCENT</span>)

    ui.run(draw, title=<span class="tok-str">"Functional Quickstart"</span>, width=<span class="tok-num">540</span>, height=<span class="tok-num">320</span>, accent=ui.<span class="tok-cls">Accent</span>.<span class="tok-cls">BLUE</span>)

<span class="tok-kw">if</span> __name__ == <span class="tok-str">"__main__"</span>:
    main()`,
    },
    procedural: {
      file: "ledger_procedural.py",
      guideLink: "guide.html#tutorial-functional",
      guideLabel: "Read Procedural Guide →",
      code: `<span class="tok-kw">import</span> <span class="tok-cls">yapps</span> <span class="tok-kw">as</span> ui

<span class="tok-kw">def</span> render_sidebar(ctx: ui.<span class="tok-cls">UI</span>, st: dict) -> <span class="tok-kw">None</span>:
    <span class="tok-kw">with</span> ctx.column(width=<span class="tok-num">210</span>, height=ui.<span class="tok-cls">FILL</span>, bg=ui.<span class="tok-cls">Color</span>.<span class="tok-cls">SURFACE_MUTED</span>, pad=<span class="tok-num">12</span>, gap=<span class="tok-num">4</span>):
        <span class="tok-kw">for</span> i, label <span class="tok-kw">in</span> enumerate([<span class="tok-str">"Overview"</span>, <span class="tok-str">"Metrics"</span>, <span class="tok-str">"Logs"</span>]):
            <span class="tok-kw">if</span> ctx.nav_item(label, selected=(st[<span class="tok-str">"tab"</span>] == i), group=<span class="tok-str">"nav"</span>):
                st[<span class="tok-str">"tab"</span>] = i

<span class="tok-kw">def</span> render_main(ctx: ui.<span class="tok-cls">UI</span>, st: dict) -> <span class="tok-kw">None</span>:
    <span class="tok-kw">with</span> ctx.column(width=ui.<span class="tok-cls">FILL</span>, height=ui.<span class="tok-cls">FILL</span>, pad=<span class="tok-num">24</span>, gap=<span class="tok-num">14</span>):
        st[<span class="tok-str">"query"</span>] = ctx.search(<span class="tok-str">"q"</span>, st[<span class="tok-str">"query"</span>], placeholder=<span class="tok-str">"Filter metrics..."</span>)
        ctx.metric(<span class="tok-str">"Throughput"</span>, <span class="tok-str">"124,800 req/s"</span>, delta=<span class="tok-num">14.2</span>, spark=[<span class="tok-num">82</span>, <span class="tok-num">95</span>, <span class="tok-num">108</span>, <span class="tok-num">124</span>])

<span class="tok-kw">def</span> main() -> <span class="tok-kw">None</span>:
    state = {<span class="tok-str">"tab"</span>: <span class="tok-num">0</span>, <span class="tok-str">"query"</span>: <span class="tok-str">""</span>}
    <span class="tok-kw">with</span> ui.<span class="tok-cls">App</span>(<span class="tok-str">"Procedural App"</span>, width=<span class="tok-num">820</span>, height=<span class="tok-num">480</span>, theme=ui.<span class="tok-cls">ThemeMode</span>.<span class="tok-cls">DARK</span>) <span class="tok-kw">as</span> app:
        <span class="tok-kw">while</span> app.frame(wait=<span class="tok-kw">True</span>):
            <span class="tok-kw">with</span> app.ui.row(width=ui.<span class="tok-cls">FILL</span>, height=ui.<span class="tok-cls">FILL</span>, bg=ui.<span class="tok-cls">Color</span>.<span class="tok-cls">BACKGROUND</span>):
                render_sidebar(app.ui, state)
                render_main(app.ui, state)`,
    },
    oop: {
      file: "studio_oop.py",
      guideLink: "guide.html#tutorial-oop",
      guideLabel: "Read OOP Architecture Tutorial →",
      code: `<span class="tok-kw">import</span> <span class="tok-cls">yapps</span> <span class="tok-kw">as</span> ui

<span class="tok-kw">class</span> <span class="tok-cls">PipelineCard</span>(ui.<span class="tok-cls">Component</span>):
    <span class="tok-kw">def</span> __init__(self, key: str, title: str) -> <span class="tok-kw">None</span>:
        super().__init__(key)  <span class="tok-com"># Auto-pushes ID scope — zero collisions!</span>
        self.title = title
        self.count = <span class="tok-num">0</span>

    <span class="tok-kw">def</span> build(self, ctx: ui.<span class="tok-cls">UI</span>) -> <span class="tok-kw">None</span>:
        <span class="tok-kw">with</span> ctx.card(pad=<span class="tok-num">18</span>, gap=<span class="tok-num">10</span>, width=ui.<span class="tok-cls">GROW</span>(<span class="tok-num">1</span>)):
            ctx.heading(self.title, level=<span class="tok-num">4</span>)
            <span class="tok-kw">if</span> ctx.button(<span class="tok-str">"Increment"</span>, icon=ui.<span class="tok-cls">Icon</span>.<span class="tok-cls">PLUS</span>, variant=ui.<span class="tok-cls">ButtonVariant</span>.<span class="tok-cls">PRIMARY</span>):
                self.count += <span class="tok-num">1</span>
            ctx.secondary(<span class="tok-str">f"Completed jobs: {self.count}"</span>)

<span class="tok-kw">class</span> <span class="tok-cls">StudioApp</span>(ui.<span class="tok-cls">Application</span>):
    <span class="tok-kw">def</span> __init__(self) -> <span class="tok-kw">None</span>:
        super().__init__(<span class="tok-str">"OOP Studio"</span>, width=<span class="tok-num">760</span>, height=<span class="tok-num">380</span>, theme=ui.<span class="tok-cls">ThemeMode</span>.<span class="tok-cls">DARK</span>, accent=ui.<span class="tok-cls">Accent</span>.<span class="tok-cls">GREEN</span>)

    <span class="tok-kw">def</span> setup(self) -> <span class="tok-kw">None</span>:
        self.left = <span class="tok-cls">PipelineCard</span>(<span class="tok-str">"pipe_a"</span>, <span class="tok-str">"Ingestion Cluster"</span>)
        self.right = <span class="tok-cls">PipelineCard</span>(<span class="tok-str">"pipe_b"</span>, <span class="tok-str">"Inference Workers"</span>)

    <span class="tok-kw">def</span> build(self, ctx: ui.<span class="tok-cls">UI</span>) -> <span class="tok-kw">None</span>:
        <span class="tok-kw">with</span> ctx.row(width=ui.<span class="tok-cls">FILL</span>, height=ui.<span class="tok-cls">FILL</span>, pad=<span class="tok-num">24</span>, gap=<span class="tok-num">16</span>, bg=ui.<span class="tok-cls">Color</span>.<span class="tok-cls">BACKGROUND</span>):
            self.left(ctx)
            self.right(ctx)

<span class="tok-kw">if</span> __name__ == <span class="tok-str">"__main__"</span>:
    <span class="tok-cls">StudioApp</span>().run()`,
    },
  };

  function hexToRgba(hex, alpha) {
    const h = hex.replace("#", "");
    const r = parseInt(h.slice(0, 2), 16);
    const g = parseInt(h.slice(2, 4), 16);
    const b = parseInt(h.slice(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  const savedTheme = localStorage.getItem("yapps_theme");
  let currentTheme =
    savedTheme === "dark" || savedTheme === "light"
      ? savedTheme
      : matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  let currentAccent = localStorage.getItem("yapps_accent") || "BLUE";
  if (!ACCENTS.some((a) => a.key === currentAccent)) currentAccent = "BLUE";

  function applyThemeAndAccent() {
    document.documentElement.setAttribute("data-theme", currentTheme);
    document.documentElement.setAttribute("data-accent", currentAccent);
    const acc = ACCENTS.find((a) => a.key === currentAccent) || ACCENTS[2];
    const hex = currentTheme === "dark" ? acc.dark : acc.light;
    const fg = currentTheme === "dark" ? acc.darkFg : acc.lightFg;
    const root = document.documentElement.style;
    root.setProperty("--accent", hex);
    root.setProperty("--accent-fg", fg);
    root.setProperty("--accent-subtle", hexToRgba(hex, currentTheme === "dark" ? 0.15 : 0.10));
    root.setProperty("--accent-ring", hexToRgba(hex, currentTheme === "dark" ? 0.35 : 0.26));

    const themeBtn = document.getElementById("theme-toggle-btn");
    if (themeBtn) {
      themeBtn.innerHTML = currentTheme === "dark" ? ICON_SUN : ICON_MOON;
      themeBtn.title = currentTheme === "dark" ? "Switch to light mode" : "Switch to dark mode";
    }

    document.querySelectorAll(".accent-dot").forEach((el) => {
      const a = ACCENTS.find((x) => x.key === el.dataset.accent);
      if (a) {
        el.style.backgroundColor = currentTheme === "dark" ? a.dark : a.light;
        el.classList.toggle("active", a.key === currentAccent);
      }
    });

    document.querySelectorAll(".accent-card").forEach((el) => {
      const a = ACCENTS.find((x) => x.key === el.dataset.accent);
      if (a) {
        const curHex = currentTheme === "dark" ? a.dark : a.light;
        el.classList.toggle("active", a.key === currentAccent);
        const sw = el.querySelector(".swatch-pill");
        const hexEl = el.querySelector(".accent-hex");
        if (sw) sw.style.backgroundColor = curHex;
        if (hexEl) hexEl.textContent = `ui.Accent.${a.key} · ${curHex}`;
      }
    });

    const liveCodeEl = document.getElementById("active-accent-code");
    if (liveCodeEl) {
      liveCodeEl.textContent = `accent=ui.Accent.${acc.key}  # ${hex} (${currentTheme} mode)`;
    }
  }

  function initHeaderAndScrollChrome() {
    const strip = document.getElementById("header-accent-strip");
    if (strip) {
      strip.innerHTML = ACCENTS.map(
        (a) =>
          `<button class="accent-dot" type="button" data-accent="${a.key}" title="ui.Accent.${a.key} (${a.label})" aria-label="${a.label}"></button>`
      ).join("");
      strip.addEventListener("click", (ev) => {
        const btn = ev.target.closest(".accent-dot");
        if (!btn) return;
        currentAccent = btn.dataset.accent;
        localStorage.setItem("yapps_accent", currentAccent);
        applyThemeAndAccent();
      });
    }

    const themeBtn = document.getElementById("theme-toggle-btn");
    if (themeBtn) {
      themeBtn.addEventListener("click", () => {
        currentTheme = currentTheme === "dark" ? "light" : "dark";
        localStorage.setItem("yapps_theme", currentTheme);
        applyThemeAndAccent();
      });
    }

    const progressEl = document.getElementById("read-progress");
    const updateScroll = () => {
      document.body.classList.toggle("scrolled", window.scrollY > 6);
      if (progressEl) {
        const max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
        const ratio = Math.min(1, Math.max(0, window.scrollY / max));
        progressEl.style.transform = `scaleX(${ratio.toFixed(4)})`;
      }
    };
    window.addEventListener("scroll", updateScroll, { passive: true });
    updateScroll();
  }

  // Pointer spotlight tracking on bento & guide cards (matches CUI's spotlight)
  function initCardSpotlights() {
    document.querySelectorAll(".bento-card, .guide-card").forEach((card) => {
      card.addEventListener("pointermove", (ev) => {
        const r = card.getBoundingClientRect();
        card.style.setProperty("--mx", `${(ev.clientX - r.left).toFixed(1)}px`);
        card.style.setProperty("--my", `${(ev.clientY - r.top).toFixed(1)}px`);
      });
    });
  }

  // Mount Procedural 3D Topographic Woodcut & Stipple Engraving on Landing & Guide pages
  function initDitherBackgrounds() {
    if (typeof window.ditherArt !== "function") return;

    const homeHeroArt = document.getElementById("home-hero-art");
    if (homeHeroArt) {
      const heroDither = window.ditherArt({
        scene: "horizon",
        loop: true,
      });
      homeHeroArt.appendChild(heroDither);

      // Gentle 0.35x scroll drift + fade
      if (!matchMedia("(prefers-reduced-motion: reduce)").matches) {
        let ticking = false;
        window.addEventListener(
          "scroll",
          () => {
            if (ticking) return;
            ticking = true;
            requestAnimationFrame(() => {
              ticking = false;
              const y = Math.min(window.scrollY, 900);
              heroDither.style.transform = `translate3d(0, ${(y * 0.35).toFixed(1)}px, 0)`;
              heroDither.style.opacity = String(Math.max(0, 1 - y / 760).toFixed(3));
            });
          },
          { passive: true }
        );
      }
    }

    const homeCtaBand = document.getElementById("home-cta-band");
    if (homeCtaBand) {
      homeCtaBand.prepend(
        window.ditherArt({
          scene: "basin",
          reveal: "view",
          loop: true,
        })
      );
    }

    const docsHeroArt = document.getElementById("docs-hero-art");
    if (docsHeroArt) {
      docsHeroArt.appendChild(
        window.ditherArt({
          scene: "horizon",
          loop: true,
        })
      );
    }

    const docsCtaBand = document.getElementById("docs-cta-band");
    if (docsCtaBand) {
      docsCtaBand.prepend(
        window.ditherArt({
          scene: "basin",
          reveal: "view",
          loop: true,
        })
      );
    }
  }

  function bindCopyButtons(scope) {
    (scope || document).querySelectorAll("[data-copy-text], [data-copy-code]").forEach((btn) => {
      if (btn.dataset.boundCopy) return;
      btn.dataset.boundCopy = "1";
      btn.addEventListener("click", () => {
        let text = btn.dataset.copyText || "";
        if (!text && btn.dataset.copyCode) {
          const panel = btn.closest(".code-panel");
          const codeEl = panel && panel.querySelector("pre code");
          text = codeEl ? codeEl.textContent : "";
        }
        if (!text) return;
        navigator.clipboard.writeText(text).then(() => {
          const prev = btn.textContent;
          btn.textContent = "Copied";
          setTimeout(() => {
            btn.textContent = prev;
          }, 1400);
        });
      });
    });
  }

  // ---- Landing Page Initializer ----
  function initLandingPage() {
    const tabsRoot = document.getElementById("showcase-tabs");
    const imgEl = document.getElementById("showcase-img");
    const winTitle = document.getElementById("showcase-win-title");
    const capText = document.getElementById("showcase-caption-text");
    const capLink = document.getElementById("showcase-source-link");

    if (tabsRoot && imgEl) {
      function selectShowcase(id) {
        const item = SHOWCASES.find((s) => s.id === id) || SHOWCASES[0];
        imgEl.src = item.img;
        imgEl.alt = item.label;
        if (winTitle) winTitle.textContent = item.title;
        if (capText) capText.textContent = item.caption;
        if (capLink) {
          capLink.textContent = `Source: ${item.file} →`;
          capLink.href = `https://github.com/x017/yapps/blob/main/${item.file}`;
        }
        tabsRoot.querySelectorAll(".tab-pill").forEach((b) => {
          b.classList.toggle("active", b.dataset.showcase === item.id);
        });
      }

      tabsRoot.innerHTML = SHOWCASES.map(
        (s) => `<button class="tab-pill" type="button" data-showcase="${s.id}">${s.label}</button>`
      ).join("");
      tabsRoot.addEventListener("click", (ev) => {
        const b = ev.target.closest(".tab-pill");
        if (b) selectShowcase(b.dataset.showcase);
      });
      selectShowcase("gallery");
    }

    const pSelector = document.getElementById("paradigm-selector");
    const pCode = document.getElementById("paradigm-code");
    const pFile = document.getElementById("paradigm-filename");
    const pGuideLink = document.getElementById("paradigm-guide-link");

    if (pSelector && pCode) {
      function setParadigm(key) {
        const p = PARADIGMS[key] || PARADIGMS.functional;
        pCode.innerHTML = p.code;
        if (pFile) pFile.textContent = p.file;
        if (pGuideLink) {
          pGuideLink.href = p.guideLink;
          pGuideLink.textContent = p.guideLabel;
        }
        pSelector.querySelectorAll(".paradigm-card").forEach((c) => {
          c.classList.toggle("active", c.dataset.paradigm === key);
        });
      }
      pSelector.addEventListener("click", (ev) => {
        const card = ev.target.closest(".paradigm-card");
        if (card) setParadigm(card.dataset.paradigm);
      });
      setParadigm("functional");
    }

    const accGrid = document.getElementById("accents-interactive-grid");
    if (accGrid) {
      accGrid.innerHTML = ACCENTS.map(
        (a) => `<button class="accent-card" type="button" data-accent="${a.key}">
          <span class="swatch-pill"></span>
          <span class="accent-meta">
            <strong>${a.label}</strong>
            <code class="accent-hex">ui.Accent.${a.key}</code>
          </span>
        </button>`
      ).join("");
      accGrid.addEventListener("click", (ev) => {
        const card = ev.target.closest(".accent-card");
        if (!card) return;
        currentAccent = card.dataset.accent;
        localStorage.setItem("yapps_accent", currentAccent);
        applyThemeAndAccent();
      });
    }
  }

  // ---- Documentation Portal (`guide.html`) Initializer ----
  function initDocsPortal() {
    const docsData = window.YAPPS_DOCS;
    const navRoot = document.getElementById("docs-sidebar-nav");
    const articleRoot = document.getElementById("docs-article");
    const tocRoot = document.getElementById("docs-toc-links");
    const searchInput = document.getElementById("docs-search-input");
    const searchResults = document.getElementById("docs-search-results");
    if (!docsData || !navRoot || !articleRoot) return;

    document.body.classList.add("guide-mode");
    const chapters = docsData.chapters;

    const groups = [];
    chapters.forEach((ch) => {
      let g = groups.find((x) => x.name === ch.group);
      if (!g) {
        g = { name: ch.group, items: [] };
        groups.push(g);
      }
      g.items.push(ch);
    });

    navRoot.innerHTML = groups
      .map(
        (g) =>
          `<div class="sidebar-group-title">${g.name}</div>` +
          g.items
            .map(
              (ch) =>
                `<a class="sidebar-link" href="#${ch.slug}" data-chapter="${ch.slug}">${ch.title}</a>`
            )
            .join("")
      )
      .join("");

    let activeSlug = "";

    function renderChapter(slug, anchorId) {
      const idx = chapters.findIndex((c) => c.slug === slug);
      const ch = idx >= 0 ? chapters[idx] : chapters[0];
      const realIdx = idx >= 0 ? idx : 0;

      if (activeSlug !== ch.slug) {
        activeSlug = ch.slug;
        const prev = realIdx > 0 ? chapters[realIdx - 1] : null;
        const next = realIdx < chapters.length - 1 ? chapters[realIdx + 1] : null;

        const pagerHtml = `<div class="pager-nav">
          ${
            prev
              ? `<a class="pager-card prev" href="#${prev.slug}" data-doc-link="${prev.slug}">
                   <span>← Previous</span><strong>${prev.title}</strong>
                 </a>`
              : `<div></div>`
          }
          ${
            next
              ? `<a class="pager-card next" href="#${next.slug}" data-doc-link="${next.slug}">
                   <span>Next →</span><strong>${next.title}</strong>
                 </a>`
              : `<div></div>`
          }
        </div>`;

        articleRoot.innerHTML = ch.html + pagerHtml;
        document.title = `${ch.title} — yapps Documentation`;

        navRoot.querySelectorAll(".sidebar-link").forEach((el) => {
          el.classList.toggle("active", el.dataset.chapter === ch.slug);
        });

        if (tocRoot) {
          tocRoot.innerHTML = ch.toc
            .map(
              (t) =>
                `<a class="toc-link" href="#${ch.slug}--${t.id}" data-anchor="${t.id}">${t.title}</a>`
            )
            .join("");
        }

        bindCopyButtons(articleRoot);
      }

      if (anchorId) {
        const target = document.getElementById(anchorId);
        if (target) {
          target.scrollIntoView({ behavior: "smooth", block: "start" });
          return;
        }
      }
      window.scrollTo({ top: 0, behavior: "instant" in window ? "instant" : "auto" });
    }

    function syncFromHash() {
      const raw = (window.location.hash || "").replace(/^#/, "");
      if (!raw) {
        renderChapter(chapters[0].slug, "");
        return;
      }
      const parts = raw.split("--");
      renderChapter(parts[0], parts[1] || "");
    }

    window.addEventListener("hashchange", syncFromHash);

    document.addEventListener("click", (ev) => {
      const docLink = ev.target.closest("[data-doc-link]");
      if (docLink) {
        ev.preventDefault();
        const slug = docLink.dataset.docLink;
        window.location.hash = `#${slug}`;
        return;
      }
      const tocLink = ev.target.closest(".toc-link[data-anchor]");
      if (tocLink) {
        ev.preventDefault();
        const aid = tocLink.dataset.anchor;
        history.replaceState(null, "", `#${activeSlug}--${aid}`);
        const el = document.getElementById(aid);
        if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });

    if (searchInput && searchResults) {
      searchInput.addEventListener("input", () => {
        const q = searchInput.value.trim().toLowerCase();
        if (q.length < 2) {
          searchResults.classList.remove("open");
          searchResults.innerHTML = "";
          return;
        }
        const hits = docsData.search
          .filter(
            (item) =>
              item.heading.toLowerCase().includes(q) ||
              item.text.toLowerCase().includes(q) ||
              item.chapter.toLowerCase().includes(q)
          )
          .slice(0, 10);

        if (!hits.length) {
          searchResults.innerHTML = `<div class="search-hit"><span>No matches for "${q}"</span></div>`;
        } else {
          searchResults.innerHTML = hits
            .map((h) => {
              const hash = h.anchor ? `#${h.slug}--${h.anchor}` : `#${h.slug}`;
              return `<a class="search-hit" href="${hash}">
                <strong>${h.chapter} · ${h.heading}</strong>
                <span>${h.text.slice(0, 95)}…</span>
              </a>`;
            })
            .join("");
        }
        searchResults.classList.add("open");
      });

      searchResults.addEventListener("click", () => {
        searchResults.classList.remove("open");
        searchInput.value = "";
      });

      window.addEventListener("keydown", (ev) => {
        if (
          (ev.key === "/" || ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === "k")) &&
          document.activeElement !== searchInput
        ) {
          ev.preventDefault();
          searchInput.focus();
        } else if (ev.key === "Escape" && document.activeElement === searchInput) {
          searchInput.blur();
          searchResults.classList.remove("open");
        }
      });
    }

    syncFromHash();
  }

  document.addEventListener("DOMContentLoaded", () => {
    initHeaderAndScrollChrome();
    applyThemeAndAccent();
    initDitherBackgrounds();
    bindCopyButtons(document);
    initLandingPage();
    initDocsPortal();
    initCardSpotlights();
  });
})();

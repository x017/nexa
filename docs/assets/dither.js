/* ==========================================================================
   nexa Procedural 3D Topographic Woodcut & Stipple Engraving Engine
   100% original generative printmaking (zero external images):
   - Projects a 3D ridged-multifractal alpine amphitheater & winding S-curve
     river via smooth floating-horizon occlusion.
   - Renders crisp device-pixel-snapped topographic isolines, slope-aligned
     woodcut engraving hatches, drifting cirrus bands, and a concentric
     celestial halo.
   - Live-harmonizes its 4-ink printmaker palette with all 8 `ui.Accent`
     presets in both Light and Dark themes, plus subtle pointer sun-angle tilt.
   ========================================================================== */

(function () {
  "use strict";

  // Hybrid 8x8 Bayer + Interleaved Gradient Noise threshold table
  const BAYER = (() => {
    let m = [[0]];
    while (m.length < 8) {
      const n = m.length;
      const next = [];
      for (let y = 0; y < n * 2; y++) {
        next.push([]);
        for (let x = 0; x < n * 2; x++) {
          next[y].push(4 * m[y % n][x % n] + [0, 2, 3, 1][(y >= n) * 2 + (x >= n)]);
        }
      }
      m = next;
    }
    return Float32Array.from(m.flat(), (v) => (v + 0.5) / 64);
  })();

  // Bespoke 4-ink museum printmaker harmonies for all 8 `ui.Accent` presets
  const ACCENT_PRINTS = {
    BLUE: {
      light: { sky: [26, 92, 170], cloud: [66, 118, 164], valley: [72, 106, 34], warm: [154, 112, 32] },
      dark:  { sky: [78, 148, 228], cloud: [188, 214, 242], valley: [130, 172, 96], warm: [226, 198, 126] },
    },
    VIOLET: {
      light: { sky: [84, 52, 178], cloud: [112, 92, 168], valley: [68, 96, 86], warm: [158, 108, 54] },
      dark:  { sky: [152, 124, 248], cloud: [212, 198, 252], valley: [132, 176, 158], warm: [232, 196, 138] },
    },
    GREEN: {
      light: { sky: [14, 112, 78], cloud: [58, 126, 108], valley: [64, 104, 36], warm: [152, 114, 34] },
      dark:  { sky: [72, 204, 152], cloud: [182, 232, 210], valley: [142, 188, 104], warm: [228, 202, 128] },
    },
    AMBER: {
      light: { sky: [146, 96, 18], cloud: [132, 104, 58], valley: [78, 98, 38], warm: [176, 118, 22] },
      dark:  { sky: [236, 186, 84], cloud: [244, 222, 168], valley: [154, 176, 98], warm: [250, 208, 112] },
    },
    ORANGE: {
      light: { sky: [168, 76, 18], cloud: [142, 96, 62], valley: [76, 98, 44], warm: [172, 112, 28] },
      dark:  { sky: [244, 156, 82], cloud: [246, 208, 172], valley: [148, 176, 108], warm: [248, 204, 124] },
    },
    CORAL: {
      light: { sky: [172, 58, 52], cloud: [144, 88, 86], valley: [68, 102, 68], warm: [162, 108, 42] },
      dark:  { sky: [246, 134, 122], cloud: [246, 202, 196], valley: [136, 178, 132], warm: [238, 198, 132] },
    },
    ROSE: {
      light: { sky: [168, 46, 112], cloud: [138, 84, 118], valley: [72, 96, 88], warm: [158, 108, 58] },
      dark:  { sky: [244, 132, 190], cloud: [244, 202, 224], valley: [138, 174, 164], warm: [236, 198, 144] },
    },
    NEUTRAL: {
      light: { sky: [38, 40, 44], cloud: [88, 92, 98], valley: [68, 72, 66], warm: [116, 104, 84] },
      dark:  { sky: [168, 172, 178], cloud: [224, 226, 230], valley: [148, 154, 146], warm: [208, 198, 178] },
    },
  };

  const clamp01 = (v) => (v < 0 ? 0 : v > 1 ? 1 : v);
  const lerp = (a, b, t) => a + (b - a) * t;
  const smoothstep = (a, b, x) => {
    const t = clamp01((x - a) / (b - a));
    return t * t * (3 - 2 * t);
  };
  const easeOut = (t) => 1 - Math.pow(1 - t, 3);

  function hash2(ix, iy) {
    let n = (Math.imul(ix, 374761393) + Math.imul(iy, 668265263)) | 0;
    n = Math.imul(n ^ (n >>> 13), 1274126177);
    return ((n ^ (n >>> 16)) >>> 8) / 16777216;
  }

  function vnoise(x, y) {
    const ix = Math.floor(x);
    const iy = Math.floor(y);
    const fx = x - ix;
    const fy = y - iy;
    const ux = fx * fx * (3 - 2 * fx);
    const uy = fy * fy * (3 - 2 * fy);
    const a = hash2(ix, iy);
    const b = hash2(ix + 1, iy);
    const c = hash2(ix, iy + 1);
    const d = hash2(ix + 1, iy + 1);
    return a + (b - a) * ux + (c - a) * uy + (a - b - c + d) * ux * uy;
  }

  function fbm(x, y, octaves) {
    let v = 0;
    let amp = 0.5;
    for (let i = 0; i < octaves; i++) {
      v += amp * vnoise(x, y);
      x = x * 2.02 + 11.3;
      y = y * 2.02 + 6.7;
      amp *= 0.5;
    }
    return v;
  }

  function ridged(x, y, octaves) {
    let v = 0;
    let amp = 0.55;
    let w = 1;
    for (let i = 0; i < octaves; i++) {
      let n = 1 - Math.abs(vnoise(x, y) * 2 - 1);
      n = n * n * w;
      w = clamp01(n * 1.8);
      v += n * amp;
      x = x * 2.04 + 4.7;
      y = y * 2.04 + 9.3;
      amp *= 0.48;
    }
    return v;
  }

  function screenThreshold(x, y) {
    const b = BAYER[(y & 7) * 8 + (x & 7)];
    const f = 0.06711056 * x + 0.00583715 * y;
    const ig = (52.9829189 * (f - Math.floor(f))) % 1;
    return b * 0.55 + (ig < 0 ? ig + 1 : ig) * 0.45;
  }

  // 3D world heightfield for "horizon" (alpine amphitheater + S-curve river)
  // and "basin" (converging contour river terraces for closing CTA band)
  function evalWorld(wx, wz, isBasin) {
    if (isBasin) {
      const riverX = 0.34 * Math.sin(wz * 4.2 + 1.1) - 0.14 * Math.cos(wz * 2.5);
      const distR = Math.abs(wx - riverX);
      const riverW = lerp(0.22, 0.06, Math.pow(wz, 0.85));
      const carve = smoothstep(riverW * 0.8, riverW * 3.2, distR);
      const warp = (fbm(wx * 1.3 + 4.2, wz * 1.9 + 2.7, 3) - 0.5) * 0.3;
      const terrace = ridged((wx + warp) * 1.55 + 3.1, wz * 2.5 + 5.4, 3);
      const bowl = 0.25 + 0.75 * Math.pow(Math.min(1.3, Math.abs(wx)), 1.15);
      const h = terrace * 0.46 * bowl * carve;
      return [h, distR < riverW ? 1 : 0];
    }

    const riverX = -0.06 + 0.28 * Math.sin(wz * 3.8 + 0.35) - 0.12 * Math.cos(wz * 6.2);
    const distR = Math.abs(wx - riverX);
    const riverW = lerp(0.18, 0.032, Math.pow(wz, 0.85));
    const carve = smoothstep(riverW * 0.82, riverW * 3.6, distR);
    const flank = 0.14 + 0.86 * Math.pow(Math.min(1.3, Math.abs(wx)), 1.3);

    const warp = (fbm(wx * 1.1 + 2.1, wz * 1.7 + 1.3, 3) - 0.5) * 0.32;
    const broad = ridged((wx + warp) * 1.35 + 5.4, wz * 2.3 + 2.2, 3);
    const fine = ridged((wx + warp) * 2.8 + 9.1, wz * 4.2 + 4.7, 3) * 0.22;
    const farRise = smoothstep(0.42, 0.96, wz) * 0.36;
    let h = (broad * 0.82 + fine) * (0.36 * flank + farRise) * carve;

    if (wz > 0.70) {
      const back = smoothstep(0.70, 0.96, wz) * (1 - smoothstep(0.96, 1.0, wz) * 0.15);
      const massif = ridged(wx * 1.75 + 14.2, wz * 2.6 + 8.1, 4);
      const passDip = 0.42 + 0.58 * smoothstep(0.05, 0.92, Math.abs(wx + 0.05));
      const mh = back * massif * 0.62 * passDip;
      if (mh > h) h = mh;
    }
    return [h, distR < riverW ? 1 : 0];
  }

  function mixRgb(out, idx, a, b, t) {
    out[idx] = (a[0] + (b[0] - a[0]) * t) | 0;
    out[idx + 1] = (a[1] + (b[1] - a[1]) * t) | 0;
    out[idx + 2] = (a[2] + (b[2] - a[2]) * t) | 0;
    out[idx + 3] = 255;
  }

  function ditherArt(opts) {
    const o = {
      cell: 2,
      scene: "horizon",
      reveal: true,
      loop: true,
      reduced: () => matchMedia("(prefers-reduced-motion: reduce)").matches,
      ...opts,
    };
    const isBasin = o.scene === "basin";
    const PERIOD = 16;

    const el = document.createElement("div");
    el.className = "dither";
    el.setAttribute("aria-hidden", "true");
    const canvas = document.createElement("canvas");
    el.append(canvas);

    let gw = 0;
    let gh = 0;
    let k = 1;
    let aspect = 2;
    let small = null;
    let sctx = null;
    let data = null;

    // Precomputed static 3D geometry buffers (rebuilt only on resize)
    let pKind = null;
    let pWz = null;
    let pH = null;
    let pDhDx = null;
    let pDhDz = null;
    let pHatch = null;
    let pThresh = null;
    let pRippleNoise = null;

    let raf = 0;
    let revealed = !o.reveal;
    let visible = o.reveal !== "view";
    let sunBias = 0; // -0.35 .. +0.35 from subtle pointer tilt
    const ctx = canvas.getContext("2d");

    function buildGeometry() {
      const r = el.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) return false;
      const dpr = window.devicePixelRatio || 1;
      k = Math.max(1, Math.round(o.cell * dpr));
      gw = Math.ceil((r.width * dpr) / k);
      gh = Math.ceil((r.height * dpr) / k);
      aspect = gw / Math.max(1, gh);

      const total = gw * gh;
      pKind = new Uint8Array(total);
      pWz = new Float32Array(total);
      pH = new Float32Array(total);
      pDhDx = new Float32Array(total);
      pDhDz = new Float32Array(total);
      pHatch = new Float32Array(total);
      pThresh = new Float32Array(total);
      pRippleNoise = new Float32Array(total);

      pWz.fill(1);
      for (let y = 0; y < gh; y++) {
        const v = y / gh;
        for (let x = 0; x < gw; x++) {
          const idx = y * gw + x;
          pThresh[idx] = screenThreshold(x, y);
          pRippleNoise[idx] = fbm((x / gw) * 15, v * 11, 2) * 4.8;
        }
      }

      const SLICES = isBasin ? 120 : 165;
      const minY = new Int32Array(gw).fill(gh);
      const prevH = new Float32Array(gw);
      const prevWz = new Float32Array(gw);
      const prevDx = new Float32Array(gw);
      const prevDz = new Float32Array(gw);

      for (let s = 0; s < SLICES; s++) {
        const t = s / (SLICES - 1);
        const wz = Math.pow(t, 1.18);
        const zCam = 0.55 + wz * 3.1;
        const baseV = isBasin ? 1.02 - wz * 0.88 : 0.99 - wz * 0.51;
        const hScale = (isBasin ? 0.52 : 0.46) / (0.58 + wz * 0.72);
        const epsX = 0.016 * zCam;

        for (let x = 0; x < gw; x++) {
          const u = x / gw;
          const wx = (u - 0.5) * 2.25 * (0.56 + wz * 0.74);
          const hw = evalWorld(wx, wz, isBasin);
          const h = hw[0];
          const isW = hw[1];
          const sy = Math.max(0, Math.min(gh, Math.round((baseV - h * hScale) * gh)));

          const hx = evalWorld(wx + epsX, wz, isBasin)[0];
          const hz = evalWorld(wx, Math.min(1, wz + 0.012), isBasin)[0];
          const dhDx = (hx - h) / epsX;
          const dhDz = (hz - h) / 0.012;

          const pTop = minY[x];
          if (sy < pTop) {
            const span = Math.max(1, pTop - sy);
            const occluded = s > 2 && wz - prevWz[x] > 0.035 && h > 0.05;
            for (let y = sy; y < pTop; y++) {
              const frac = occluded ? 0 : (y - sy) / span;
              const ih = lerp(h, prevH[x], frac);
              const iwz = lerp(wz, prevWz[x], frac);
              const idxSlope = lerp(dhDx, prevDx[x], frac);
              const idzSlope = lerp(dhDz, prevDz[x], frac);

              const idx = y * gw + x;
              const isRim = y === sy && (occluded || s >= SLICES - 3) && h > 0.04;
              pKind[idx] = isRim ? 3 : isW > 0.5 ? 1 : 2;
              pWz[idx] = iwz;
              pH[idx] = ih;
              pDhDx[idx] = idxSlope;
              pDhDz[idx] = idzSlope;

              const ang = Math.atan2(idxSlope, 1) * 0.6;
              pHatch[idx] = 0.5 + 0.5 * Math.sin((x * Math.cos(ang) + y * Math.sin(ang)) * 1.45);
            }
            minY[x] = sy;
          }
          if (sy <= pTop) {
            prevH[x] = h;
            prevWz[x] = wz;
            prevDx[x] = dhDx;
            prevDz[x] = dhDz;
          }
        }
      }

      small = document.createElement("canvas");
      small.width = gw;
      small.height = gh;
      sctx = small.getContext("2d");
      data = sctx.createImageData(gw, gh);
      canvas.width = gw * k;
      canvas.height = gh * k;
      canvas.style.width = `${(gw * k) / dpr}px`;
      canvas.style.height = `${(gh * k) / dpr}px`;
      return true;
    }

    let loopReady = false;
    let loopDelay = 0;
    let loopRaf = 0;
    let loopLast = 0;
    let inView = false;
    const t0 = performance.now();

    function loopTime() {
      return o.loop && !o.reduced() && loopReady ? (performance.now() - t0) / 1000 : 0;
    }

    function paint(progress, explicitTime) {
      if (!pKind || !data) return;
      const time = explicitTime === undefined ? loopTime() : explicitTime;
      const dark = document.documentElement.dataset.theme === "dark";
      const accentKey = document.documentElement.dataset.accent || "BLUE";
      const preset = ACCENT_PRINTS[accentKey] || ACCENT_PRINTS.BLUE;
      const pal = dark ? preset.dark : preset.light;

      const sunDx = 0.78 + sunBias;
      const sunDz = -0.42;
      const sweepPhase = (time / PERIOD) * Math.PI * 2;
      const cloudDrift = time * 0.016;
      const rippleShift = time * 1.5;
      const sunU = 0.80 + sunBias * 0.03;

      const d = data.data;
      for (let y = 0; y < gh; y++) {
        const v = y / gh;
        const revealT =
          progress >= 1
            ? 1
            : easeOut(clamp01(progress * 1.5 - v * 0.5));

        for (let x = 0; x < gw; x++) {
          const idx = y * gw + x;
          const j = idx * 4;
          const u = x / gw;
          const th = pThresh[idx];
          const kind = pKind[idx];

          // Gentle diagonal cloud-shadow band across the valley
          const sw = 0.5 + 0.5 * Math.cos((u * 0.85 + v * 0.35) * Math.PI * 2 - sweepPhase);
          const bandBoost = sw * sw * sw * sw;

          if (kind === 0) {
            // Engraved celestial sun/moon halo + drifting woodcut cirrus
            const sdx = (u - sunU) * aspect;
            const sdy = v - 0.17;
            const sdist = Math.hypot(sdx, sdy);

            const cirrus = fbm(u * 4.5 + v * 1.4 - cloudDrift, v * 9.2 + 3.1, 3);
            const band = smoothstep(0.48, 0.80, cirrus) * (1 - smoothstep(0, 0.46, v) * 0.35);
            const skyLine = 0.5 + 0.5 * Math.sin(y * 1.45 + cirrus * 3.8);

            let halo = 0;
            if (!isBasin && sdist < 0.19) {
              const rings = 0.5 + 0.5 * Math.cos(sdist * 165 - time * 0.7);
              halo = (1 - sdist / 0.19) * (sdist < 0.028 ? 0.68 : rings * 0.48);
            }

            const dens = Math.max(band * 0.50 * (0.45 + 0.55 * skyLine), halo) * revealT;
            if (dens > th) {
              const tw = clamp01(halo * 1.4) * 0.7;
              mixRgb(d, j, pal.sky, dark ? pal.cloud : pal.warm, tw);
            } else {
              d[j + 3] = 0;
            }
          } else if (kind === 1) {
            // Winding alpine river with horizontal woodcut water shimmer
            const wz = pWz[idx];
            const ripple = 0.5 + 0.5 * Math.sin(y * 2.1 - rippleShift + pRippleNoise[idx]);
            const glint = smoothstep(0.45, 0, Math.abs(u - 0.62)) * 0.28;
            const dens = (0.36 + glint) * (0.35 + 0.65 * ripple) * (1 - wz * 0.3) * revealT;
            if (dens > th) {
              const c = dark ? pal.cloud : pal.sky;
              d[j] = c[0];
              d[j + 1] = c[1];
              d[j + 2] = c[2];
              d[j + 3] = 255;
            } else {
              d[j + 3] = 0;
            }
          } else if (kind === 3) {
            // Crisp mountain occlusion silhouette rim
            const wz = pWz[idx];
            if (th < lerp(0.92, 0.68, wz) * revealT) {
              const c = dark ? pal.cloud : pal.sky;
              d[j] = c[0];
              d[j + 1] = c[1];
              d[j + 2] = c[2];
              d[j + 3] = 255;
            } else {
              d[j + 3] = 0;
            }
          } else {
            // 3D sculpted terrain: topographic isolines + slope-aligned woodcut relief
            const wz = pWz[idx];
            const h = pH[idx];
            const aerial = smoothstep(0.38, 0.94, wz);
            let shade = clamp01(0.48 + pDhDx[idx] * sunDx * 0.52 + pDhDz[idx] * sunDz * 0.22);
            shade = clamp01(shade + (dark ? 0.14 : -0.10) * bandBoost);

            const cPhase = (h * 18) % 1;
            const isContour = Math.min(cPhase, 1 - cPhase) < lerp(0.095, 0.055, wz);

            if (isContour && th < lerp(0.84, 0.45, aerial) * revealT) {
              const tHigh = Math.max(smoothstep(0.10, 0.34, h), aerial * 0.8);
              const lr = lerp(pal.valley[0], pal.warm[0], shade);
              const lg = lerp(pal.valley[1], pal.warm[1], shade);
              const lb = lerp(pal.valley[2], pal.warm[2], shade);
              const hc = dark ? pal.cloud : pal.sky;
              d[j] = lerp(lr, hc[0], tHigh) | 0;
              d[j + 1] = lerp(lg, hc[1], tHigh) | 0;
              d[j + 2] = lerp(lb, hc[2], tHigh) | 0;
              d[j + 3] = 255;
            } else {
              const lumVal = dark ? shade : 1 - shade * 0.80;
              const dens =
                lumVal *
                lerp(0.58, 0.28, aerial) *
                (0.42 + 0.58 * pHatch[idx]) *
                revealT;
              if (dens > th) {
                const swWarm = smoothstep(0.32, 0.82, shade);
                const vr = lerp(pal.valley[0], pal.warm[0], swWarm);
                const vg = lerp(pal.valley[1], pal.warm[1], swWarm);
                const vb = lerp(pal.valley[2], pal.warm[2], swWarm);
                const pr = lerp(pal.sky[0], pal.cloud[0], shade);
                const pg = lerp(pal.sky[1], pal.cloud[1], shade);
                const pb = lerp(pal.sky[2], pal.cloud[2], shade);
                const mixT = Math.max(smoothstep(0.12, 0.36, h), aerial * 0.85);
                d[j] = lerp(vr, pr, mixT) | 0;
                d[j + 1] = lerp(vg, pg, mixT) | 0;
                d[j + 2] = lerp(vb, pb, mixT) | 0;
                d[j + 3] = 255;
              } else {
                d[j + 3] = 0;
              }
            }
          }
        }
      }

      sctx.putImageData(data, 0, 0);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(small, 0, 0, gw * k, gh * k);
    }

    function loopTick(now) {
      loopRaf = 0;
      if (!el.isConnected || !o.loop || o.reduced() || !loopReady || !inView || document.hidden) {
        return;
      }
      if (now - loopLast >= 55 && pKind) {
        loopLast = now;
        paint(1);
      }
      loopRaf = requestAnimationFrame(loopTick);
    }

    function loopStart() {
      if (o.loop && loopReady && !loopRaf) {
        loopRaf = requestAnimationFrame(loopTick);
      }
    }

    function draw() {
      cancelAnimationFrame(raf);
      if (!buildGeometry()) return;
      if (!visible) {
        paint(1, 0);
        return;
      }
      paint(1, 0);
      if (!revealed) {
        revealed = true;
        if (!o.reveal || o.reduced()) el.classList.add("shown", "instant");
        else raf = requestAnimationFrame(() => el.classList.add("shown"));
        clearTimeout(loopDelay);
        loopDelay = setTimeout(
          () => {
            loopReady = true;
            loopStart();
          },
          o.reduced() ? 0 : 1200
        );
      } else {
        loopStart();
      }
    }

    const vio = new IntersectionObserver(
      (es) => {
        inView = es.some((e) => e.isIntersecting);
        if (inView) loopStart();
      },
      { threshold: 0 }
    );

    const onVis = () => {
      if (!document.hidden) loopStart();
    };
    document.addEventListener("visibilitychange", onVis);

    const onPointer = (ev) => {
      if (!inView || o.reduced()) return;
      const nx = ev.clientX / Math.max(1, window.innerWidth) - 0.5;
      sunBias = nx * 0.42;
    };
    window.addEventListener("pointermove", onPointer, { passive: true });

    let lastW = 0;
    let lastH = 0;
    let pending = 0;
    let settle = 0;
    let seen = false;

    const ro = new ResizeObserver(([e]) => {
      const { width, height } = e.contentRect;
      if (el.isConnected) seen = true;
      else {
        if (seen) stop();
        return;
      }
      if (Math.abs(width - lastW) < 1 && Math.abs(height - lastH) < 1) return;
      lastW = width;
      lastH = height;
      cancelAnimationFrame(pending);
      clearTimeout(settle);
      if (!pKind) pending = requestAnimationFrame(draw);
      else settle = setTimeout(draw, 140);
    });

    let themeRaf = 0;
    const mo = new MutationObserver(() => {
      if (!el.isConnected) {
        if (seen) stop();
        return;
      }
      if (pKind && !themeRaf) {
        themeRaf = requestAnimationFrame(() => {
          themeRaf = 0;
          paint(1);
        });
      }
    });

    const io = new IntersectionObserver(
      (es) => {
        if (!es.some((e) => e.isIntersecting)) return;
        io.disconnect();
        if (!visible) {
          visible = true;
          if (pKind) draw();
        }
      },
      { threshold: 0.25 }
    );

    function stop() {
      ro.disconnect();
      mo.disconnect();
      io.disconnect();
      vio.disconnect();
      document.removeEventListener("visibilitychange", onVis);
      window.removeEventListener("pointermove", onPointer);
      cancelAnimationFrame(raf);
      cancelAnimationFrame(pending);
      cancelAnimationFrame(loopRaf);
      cancelAnimationFrame(themeRaf);
      clearTimeout(settle);
      clearTimeout(loopDelay);
    }

    requestAnimationFrame(() => {
      ro.observe(el);
      if (!visible) io.observe(el);
      if (o.loop) vio.observe(el);
      mo.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["data-theme", "data-accent"],
      });
    });

    return el;
  }

  window.ditherArt = ditherArt;
})();

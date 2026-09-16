"use client";

import * as React from "react";

export type GridPulseProps = Omit<React.ComponentPropsWithoutRef<"div">, "children"> & {
  /** Cell size in px. The hairlines and the lit cells share it. */
  cell?: number;
  /** How far from the pointer a cell can still catch light, in cells. */
  reach?: number;
  /** How many cells light on their own each beat, so the grid is never dead. */
  ambient?: number;
  /** A lid, so a fast sweep cannot light the whole field at once. */
  maxLit?: number;
  /**
   * Elements whose lines of text the light holds back from, looked up
   * inside the grid's parent.
   */
  avoid?: string;
};

/** Hue at the top of the field and how far it turns by the bottom: yellow,
 *  through orange, red, magenta and blue, to green. */
const HUE_TOP = 60;
const HUE_SPAN = 270;
/**
 * Each cell takes one of these lightnesses, so a sweep reads as a field of
 * tints rather than one flat colour. On a dark ground the pale end of the
 * ladder would fade through grey, so it starts deeper there.
 */
const TINTS = [88, 80, 72, 64, 56];
const TINTS_DARK = [72, 65, 58, 51, 44];
/** How faint a cell goes right behind a line of text. */
const FAINT = 0.13;
/** How many cells it takes to come back up to full strength. */
const FADE = 2.2;
/** Clearing kept around each line of text, in px. */
const PAD = 5;
/**
 * A cell arrives almost at once, so the trail sits under the cursor instead
 * of trailing behind it, and leaves slowly — the linger is what reads as
 * smooth, not a slow arrival.
 */
const FADE_IN = 90;
const FADE_OUT = 1150;
/** How long a cell stays at full strength once caught. */
const HOLD = 620;

type Cell = {
  col: number;
  row: number;
  colour: string;
  /** How much of its colour the cell is allowed, 0 to 1. */
  dim: number;
  born: number;
  /** When it starts to fade out. */
  until: number;
};

/** Smoothstep: eases at both ends, so a fade has no visible corner. */
const smooth = (t: number) => t * t * (3 - 2 * t);
/** How faint the outer edge of the brush gets. */
const EDGE = 0.35;

/**
 * A fine grid that takes colour where the pointer passes and lets it go a
 * moment later, with a few cells lighting on their own. The spectrum runs
 * down the field like a printed colour chart, so a sweep reveals one
 * coherent band of colour rather than confetti.
 *
 * Place it inside a positioned container, under the content. It is
 * decoration only: hidden from assistive tech, transparent to the pointer,
 * drawn on one canvas that sleeps whenever nothing is lit, paused off screen,
 * and still for readers who ask for reduced motion.
 */
export function GridPulse({
  cell = 24,
  reach = 3,
  ambient = 1,
  maxLit = 900,
  avoid = "[data-grid-avoid]",
  className,
  style,
  ...props
}: GridPulseProps) {
  const box = React.useRef<HTMLDivElement>(null);
  const canvas = React.useRef<HTMLCanvasElement>(null);

  React.useEffect(() => {
    const el = box.current;
    const paper = canvas.current;
    const ctx = paper?.getContext("2d");
    if (!el || !paper || !ctx) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    let cols = 1;
    let rows = 1;
    let width = 0;
    let height = 0;
    let clear: DOMRect[] = [];
    let tints = TINTS;
    // Read once here and refreshed on scroll/resize, so a pointer event never
    // forces a layout read on the hot path.
    let bounds = el.getBoundingClientRect();
    const cells = new Map<string, Cell>();

    // Light or dark ground, read from the text colour the grid inherits,
    // so it follows any theme switch: a class, an attribute or the system.
    // Resolved through a pixel, since computed colours may be oklch.
    const probe = document.createElement("canvas").getContext("2d", {
      willReadFrequently: true,
    });
    const readTheme = () => {
      if (!probe) return;
      probe.clearRect(0, 0, 1, 1);
      probe.fillStyle = getComputedStyle(el).color;
      probe.fillRect(0, 0, 1, 1);
      const [r, g, b] = probe.getImageData(0, 0, 1, 1).data;
      const light = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 > 0.5;
      tints = light ? TINTS_DARK : TINTS;
    };

    // Protect the lines of text, not the boxes that hold them: a paragraph
    // set to a measure keeps that width on its short last line too, and the
    // box would hold a band of cells dark where there is nothing to read.
    const measureText = () => {
      bounds = el.getBoundingClientRect();
      const scope = el.parentElement ?? document;
      clear = [...scope.querySelectorAll(avoid)].flatMap((node) => {
        const range = document.createRange();
        range.selectNodeContents(node);
        const lines = [...range.getClientRects()].filter(
          (r) => r.width > 0 && r.height > 0,
        );
        const boxes = lines.length > 0 ? lines : [node.getBoundingClientRect()];
        return boxes.map(
          (r) =>
            new DOMRect(
              r.left - bounds.left - PAD,
              r.top - bounds.top - PAD,
              r.width + PAD * 2,
              r.height + PAD * 2,
            ),
        );
      });
    };

    const measure = () => {
      width = el.clientWidth;
      height = el.clientHeight;
      cols = Math.max(1, Math.ceil(width / cell));
      rows = Math.max(1, Math.ceil(height / cell));
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      paper.width = Math.round(width * dpr);
      paper.height = Math.round(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      readTheme();
      measureText();
      wake();
    };

    /**
     * How bright a cell may be, by its distance from the nearest line of
     * text. Cells behind the words go faint rather than dark: a hole cut in
     * the grid reads as a fault, a dip in brightness reads as depth.
     */
    const brightness = (col: number, row: number) => {
      const x = col * cell + cell / 2;
      const y = row * cell + cell / 2;
      let nearest = Number.POSITIVE_INFINITY;
      for (const r of clear) {
        const dx = Math.max(r.left - x, 0, x - r.right);
        const dy = Math.max(r.top - y, 0, y - r.bottom);
        nearest = Math.min(nearest, Math.hypot(dx, dy));
        if (nearest === 0) break;
      }
      if (nearest === Number.POSITIVE_INFINITY) return 1;
      return FAINT + (1 - FAINT) * Math.min(1, nearest / (FADE * cell));
    };

    const ink = (row: number) => {
      const t = rows > 1 ? Math.min(1, row / (rows - 1)) : 0;
      const hue = (((HUE_TOP - t * HUE_SPAN) % 360) + 360) % 360;
      // Step down the ladder with the row instead of picking at random, so a
      // sweep reads as one band of colour rather than confetti.
      const tint = tints[Math.round(t * (tints.length - 1))];
      return `hsl(${Math.round(hue)} 94% ${tint}%)`;
    };

    // One loop draws every cell; it runs only while something is lit.
    let frame = 0;
    const draw = (now: number) => {
      frame = 0;
      ctx.clearRect(0, 0, width, height);
      for (const [key, c] of cells) {
        let alpha: number;
        if (now < c.until) {
          alpha = smooth(Math.min(1, (now - c.born) / FADE_IN));
        } else {
          const t = (now - c.until) / FADE_OUT;
          if (t >= 1) {
            cells.delete(key);
            continue;
          }
          alpha = 1 - smooth(t);
        }
        ctx.globalAlpha = alpha * c.dim;
        ctx.fillStyle = c.colour;
        // Inset by the hairline, so the grid still shows between lit cells.
        ctx.fillRect(c.col * cell + 1, c.row * cell + 1, cell - 1, cell - 1);
      }
      ctx.globalAlpha = 1;
      if (cells.size > 0) frame = requestAnimationFrame(draw);
    };
    const wake = () => {
      if (!frame) frame = requestAnimationFrame(draw);
    };

    /** Lights one cell, unless it is off the grid or already lit. */
    const light = (col: number, row: number, hold: number, falloff = 1) => {
      if (col < 0 || row < 0 || col >= cols || row >= rows) return;
      const key = `${col},${row}`;
      const now = performance.now();
      const lit = cells.get(key);
      if (lit && now < lit.until) return;
      // At the ceiling, drop the oldest cell rather than refuse this one.
      // The pointer walks a path oldest-to-newest, so refusing would starve
      // exactly the cells under the cursor and the trail would fall behind.
      if (!lit && cells.size >= maxLit) {
        const oldest = cells.keys().next().value;
        if (oldest !== undefined) cells.delete(oldest);
      }
      // A cell caught again while fading picks up from where it had got to,
      // instead of blinking out and back in.
      let born = now;
      if (lit) {
        const faded = 1 - smooth(Math.min(1, (now - lit.until) / FADE_OUT));
        born = now - (1 - Math.sqrt(1 - faded)) * FADE_IN;
      }
      cells.set(key, {
        col,
        row,
        colour: lit?.colour ?? ink(row),
        dim: brightness(col, row) * falloff,
        born,
        until: now + hold,
      });
      wake();
    };

    /** One brush impression: a smooth pool of light, densest at its centre. */
    const stamp = (x: number, y: number) => {
      const cx = Math.floor(x / cell);
      const cy = Math.floor(y / cell);
      const span = Math.ceil(reach);
      for (let dy = -span; dy <= span; dy++) {
        for (let dx = -span; dx <= span; dx++) {
          const away = Math.hypot(dx, dy);
          if (away > reach) continue;
          const falloff = 1 - (away / reach) ** 1.7 * (1 - EDGE);
          light(cx + dx, cy + dy, HOLD, falloff);
        }
      }
    };

    // The pointer paints. A fast sweep can travel a long way between two
    // frames, so the path is walked rather than stamped once at the end of
    // it, which is what keeps the trail unbroken.
    let pending = 0;
    let last: { x: number; y: number } | null = null;
    let next: { x: number; y: number } | null = null;
    const flush = () => {
      pending = 0;
      if (!next) return;
      if (!last || Math.hypot(next.x - last.x, next.y - last.y) > cell * 24) {
        // No previous point, or a jump too far to be a real move — don't
        // draw a streak between two unrelated places.
        stamp(next.x, next.y);
      } else {
        const travel = Math.hypot(next.x - last.x, next.y - last.y);
        const steps = Math.max(1, Math.ceil(travel / (cell * 0.5)));
        for (let s = 1; s <= steps; s++) {
          const t = s / steps;
          stamp(last.x + (next.x - last.x) * t, last.y + (next.y - last.y) * t);
        }
      }
      last = next;
      next = null;
    };
    // Listened for on the window, because the grid sits under the content
    // and never receives the pointer itself.
    const onMove = (event: PointerEvent) => {
      next = { x: event.clientX - bounds.left, y: event.clientY - bounds.top };
      if (!pending) pending = requestAnimationFrame(flush);
    };
    // Losing the pointer breaks the path, so it doesn't resume with a streak.
    const onLeave = () => {
      last = null;
    };
    window.addEventListener("pointerleave", onLeave);
    window.addEventListener("blur", onLeave);

    // A few cells find their own way on, so the grid is alive on arrival and
    // on a screen with no pointer at all. Paused while out of sight.
    let visible = true;
    let beat = 0;
    const drift = () => {
      beat = window.setTimeout(drift, 1400 + Math.random() * 1800);
      if (!visible || document.hidden) return;
      for (let i = 0; i < ambient; i++) {
        light(
          Math.floor(Math.random() * cols),
          Math.floor(Math.random() * rows),
          HOLD * 2 + Math.random() * 900,
        );
      }
    };
    beat = window.setTimeout(drift, 500);

    const sight = new IntersectionObserver(([entry]) => {
      visible = entry?.isIntersecting ?? true;
    });
    sight.observe(el);
    const resize = new ResizeObserver(measure);
    resize.observe(el);
    // Text added, removed or rewritten moves the lines to hold back from.
    let recheck = 0;
    const copy = new MutationObserver(() => {
      if (!recheck) {
        recheck = requestAnimationFrame(() => {
          recheck = 0;
          measureText();
        });
      }
    });
    copy.observe(el.parentElement ?? document.body, {
      childList: true,
      subtree: true,
      characterData: true,
    });
    // On this intro the wordmark is scaled by a scroll-driven timeline, so
    // its lines move without any DOM mutation to catch. Re-measure as the
    // page scrolls, throttled to a frame and only while the grid is on screen.
    let rescanned = 0;
    const onScroll = () => {
      if (rescanned || !visible) return;
      rescanned = requestAnimationFrame(() => {
        rescanned = 0;
        measureText();
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    const theme = new MutationObserver(readTheme);
    theme.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class", "style", "data-theme"],
    });
    const scheme = window.matchMedia("(prefers-color-scheme: dark)");
    scheme.addEventListener("change", readTheme);
    measure();
    // Lines of text move once the web fonts arrive.
    document.fonts?.ready.then(measureText).catch(() => {});
    window.addEventListener("pointermove", onMove, { passive: true });

    return () => {
      sight.disconnect();
      resize.disconnect();
      copy.disconnect();
      cancelAnimationFrame(recheck);
      cancelAnimationFrame(rescanned);
      window.removeEventListener("scroll", onScroll);
      theme.disconnect();
      scheme.removeEventListener("change", readTheme);
      cancelAnimationFrame(frame);
      cancelAnimationFrame(pending);
      clearTimeout(beat);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerleave", onLeave);
      window.removeEventListener("blur", onLeave);
    };
  }, [cell, reach, ambient, maxLit, avoid]);

  return (
    <div
      ref={box}
      aria-hidden
      data-slot="grid-pulse"
      className={className}
      style={
        {
          "--grid-pulse-cell": `${cell}px`,
          ...style,
        } as React.CSSProperties
      }
      {...props}
    >
      <canvas ref={canvas} />
    </div>
  );
}

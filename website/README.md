# AegisOS V8 — System UI refresh

This build fixes the stale `02 / THE AEGISOS SYSTEM` implementation that could keep showing the older V3 diagrams.

## What changed

- The system section now loads from a brand-new module: `components/v3/platform-system-v8.tsx`.
- `components/v3/platform-horizontal.tsx` is now only a compatibility re-export, so the old V3 visual implementation no longer exists in this build.
- The new system surfaces are:
  - Understand → intent compiler + compiled execution plan
  - Orchestrate → workforce topology + shared memory + human owner
  - Execute → swimlane execution timeline + state + dependencies
  - Govern → policy envelope + human gate + blocked/approved paths
  - Observe → operations console + trace waterfall + telemetry
- The Execute playhead is split into a background line and foreground marker, so it cannot cut through event cards.
- The previous page-level service-worker cache is removed. This was capable of preserving an older UI bundle after redesigns.
- Next.js hashed static assets remain immutable-cached and important routes are still prefetched for smooth navigation.

## Start cleanly

```bash
npm install
npm run dev:clean
```

`dev:clean` removes `.next` before starting Next.js so the UI is compiled from the V8 sources.

For a production build:

```bash
npm run build:clean
npm start
```

## V8 verification marker

The system section renders with:

```html
data-system-ui="v8"
```

This is intentionally non-visible and can be inspected in DevTools if needed.

## V8.1 Execute timeline visual fix

The global blue playhead line in **03 / Execute** has been removed entirely. Current execution is now communicated locally on the running event cards with compact `CURRENT` / `AUTHORIZED` state chips, so no vertical line crosses the timeline or extends into empty space.

## V11 — Lenis + AegisOS scroll entry

The homepage now starts with a pinned AegisOS brand sequence. As the user scrolls, `AegisOS` scales through the viewport and releases into the existing hero. Global smooth scrolling is powered by Lenis and synchronized to GSAP ScrollTrigger through GSAP's ticker.

Key files:
- `components/v3/smooth-scroll-runtime-v11.tsx`
- `components/v3/brand-zoom-intro-v11.tsx`
- `app/intro-v11.css`

Lenis is intentionally not combined with CSS `scroll-behavior: smooth`; Lenis owns wheel smoothing and ScrollTrigger updates from the same RAF loop.

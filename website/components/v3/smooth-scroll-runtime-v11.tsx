"use client";

import Lenis from "lenis";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useEffect } from "react";

export function SmoothScrollRuntimeV11() {
  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);

    const lenis = new Lenis({
      lerp: 0.09,
      smoothWheel: true,
      wheelMultiplier: 0.92,
      touchMultiplier: 1,
      syncTouch: false,
      anchors: true,
      stopInertiaOnNavigate: true,
      respectReducedMotion: true,
      prevent: (node) => {
        if (!(node instanceof HTMLElement)) return false;
        return Boolean(node.closest("[data-lenis-prevent], .react-flow, [role='dialog']"));
      },
    });

    const updateScrollTrigger = () => ScrollTrigger.update();
    lenis.on("scroll", updateScrollTrigger);

    const tick = (time: number) => {
      lenis.raf(time * 1000);
    };

    // Run Lenis from GSAP's clock so Lenis, ScrollTrigger and the pinned
    // system sections are rendered from one animation loop.
    gsap.ticker.add(tick, false, true);
    gsap.ticker.lagSmoothing(0);

    const refresh = () => {
      lenis.resize();
      ScrollTrigger.refresh();
    };

    const onPageShow = () => refresh();
    window.addEventListener("pageshow", onPageShow);
    window.addEventListener("load", refresh, { once: true });

    // Expose the instance only for internal UI helpers / debugging.
    (window as Window & { __aegisLenis?: Lenis }).__aegisLenis = lenis;

    requestAnimationFrame(refresh);

    return () => {
      window.removeEventListener("pageshow", onPageShow);
      window.removeEventListener("load", refresh);
      lenis.off("scroll", updateScrollTrigger);
      gsap.ticker.remove(tick);
      lenis.destroy();
      delete (window as Window & { __aegisLenis?: Lenis }).__aegisLenis;
    };
  }, []);

  return null;
}

"use client";

import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { ArrowDown } from "lucide-react";
import { useEffect, useLayoutEffect, useRef } from "react";
import { GridPulse } from "./grid-pulse";
import { Wordmark } from "./wordmark";

/* GSAP pinning wraps the section in a `pin-spacer`, moving it out of the parent
   React believes it owns. Layout-effect cleanup runs BEFORE React removes nodes,
   so ctx.revert() restores the DOM first and removeChild() stays valid. */
const useIsomorphicLayoutEffect = typeof window !== "undefined" ? useLayoutEffect : useEffect;

export function BrandZoomIntroV11() {
  const sectionRef = useRef<HTMLElement>(null);
  const wordRef = useRef<HTMLDivElement>(null);
  const shellRef = useRef<HTMLDivElement>(null);
  const progressRef = useRef<HTMLSpanElement>(null);
  const bloomRef = useRef<HTMLDivElement>(null);

  useIsomorphicLayoutEffect(() => {
    const section = sectionRef.current;
    const word = wordRef.current;
    const shell = shellRef.current;
    const progress = progressRef.current;
    const bloom = bloomRef.current;
    if (!section || !word || !shell || !progress || !bloom) return;

    gsap.registerPlugin(ScrollTrigger);

    const header = document.querySelector<HTMLElement>(".v3-header");
    const scrollProgress = document.querySelector<HTMLElement>(".v4-scroll-progress");
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion) {
      gsap.set(word, { scale: 1, opacity: 1 });
      if (header) gsap.set(header, { autoAlpha: 1, y: 0 });
      if (scrollProgress) gsap.set(scrollProgress, { autoAlpha: 1 });
      return;
    }

    const ctx = gsap.context(() => {
      if (header) gsap.set(header, { autoAlpha: 0, y: -12 });
      if (scrollProgress) gsap.set(scrollProgress, { autoAlpha: 0 });

      // The zoom peaks near 200000px wide (35x viewport fill). Past a certain
      // size Chromium keeps serving stale compositor tiles on the way back:
      // the timeline state returns to a perfect identity matrix, yet the word
      // paints as fragments. Dropping the box for one synchronous reflow
      // forces a fresh raster at the current transform — verified to restore
      // pixel-perfect rendering (a filter toggle was tried: it does NOT bust
      // the stale tiles). No paint happens mid-task, so there is no flash.
      const healWordLayer = () => {
        word.style.display = "none";
        void word.offsetHeight;
        word.style.display = "";
      };
      let healedAtZero = false;
      let lastReverseHeal = 0;

      const zoomScale = () => {
        // Derive from font-size, never the live rect: the rect includes the
        // tween's own transform, so on invalidateOnRefresh (resize or
        // orientation change mid-zoom) the end value would be recomputed from
        // an already-scaled box and the zoom would jump to a wrong value.
        // Ink box is 12137x1920 units on a 2048 upem, i.e. 5.926em wide.
        const fs = parseFloat(getComputedStyle(word).fontSize) || 16;
        const w = 5.926 * fs;
        const h = (w * 1920) / 12137;
        const byWidth = window.innerWidth / Math.max(w, 1);
        const byHeight = window.innerHeight / Math.max(h, 1);
        return Math.max(byWidth, byHeight) * 35;
      };

      const tl = gsap.timeline({
        defaults: { ease: "none" },
        scrollTrigger: {
          trigger: section,
          start: "top top",
          end: "bottom top",
          pin: section,
          pinSpacing: false,
          scrub: 1,
          anticipatePin: 1,
          invalidateOnRefresh: true,
          fastScrollEnd: true,
          snap: {
            snapTo: (val) => (val > 0.18 ? 1 : 0),
            duration: { min: 0.25, max: 0.5 },
            ease: "power2.out",
          },
          // Note: onLeaveBack can never fire here — the pin start IS scroll 0,
          // so there is no "above the start" to cross. Both paths below are
          // the revisit handling (scrub settles near ~1e-9, never exactly 0).
          //
          // The throttled heal while direction === -1 is the one that keeps
          // the reverse SMOOTH: without it only the rest state is repaired
          // and every mid-reverse frame paints stale giant-scale tiles
          // (fragments), snapping clean only at the end. Each heal is one
          // synchronous reflow — no paint happens mid-task, so no flash.
          onUpdate: (self) => {
            if (self.progress < 0.002) {
              if (!healedAtZero) {
                healedAtZero = true;
                healWordLayer();
              }
            } else {
              healedAtZero = false;
              if (self.direction === -1) {
                const now = performance.now();
                if (now - lastReverseHeal > 120) {
                  lastReverseHeal = now;
                  healWordLayer();
                }
              }
            }
          },
        },
      });

      tl.to(".aegis-intro-v11__eyebrow, .aegis-intro-v11__hint, .aegis-intro-v11__index", {
        opacity: 0,
        y: -12,
        duration: 0.12,
      }, 0.04)
        .to(word, {
          scale: zoomScale,
          duration: 0.76,
          // Gentle start: a linear 1→153x reads as an instant explosion
          // (17x after ~100px of scroll). power1.in keeps the same endpoint
          // and dive character but eases out of rest smoothly.
          ease: "power1.in",
          force3D: true,
          transformOrigin: "50% 50%",
        }, 0.04)
        .to(bloom, {
          scale: 3,
          opacity: 0.95,
          duration: 0.44,
        }, 0.22)
        .to(word, {
          opacity: 0,
          duration: 0.2,
        }, 0.65)
        .to(shell, {
          backgroundColor: "rgba(247,249,252,0)",
          duration: 0.22,
        }, 0.65)
        .to(progress, {
          scaleX: 1,
          duration: 0.85,
        }, 0)
        .to(section, {
          autoAlpha: 0,
          pointerEvents: "none",
          duration: 0.12,
        }, 0.88);

      if (header) {
        tl.to(header, {
          autoAlpha: 1,
          y: 0,
          duration: 0.18,
        }, 0.80);
      }
      if (scrollProgress) {
        tl.to(scrollProgress, {
          autoAlpha: 1,
          duration: 0.14,
        }, 0.82);
      }
    }, section);

    return () => {
      ctx.revert();
      if (header) gsap.set(header, { clearProps: "opacity,visibility,transform" });
      if (scrollProgress) gsap.set(scrollProgress, { clearProps: "opacity,visibility" });
    };
  }, []);

  const handleEnterClick = (e: React.MouseEvent) => {
    e.preventDefault();
    const hero = document.getElementById("main-hero");
    if (hero) {
      const lenis = (window as unknown as { __aegisLenis?: { scrollTo: (target: HTMLElement, opts?: unknown) => void } }).__aegisLenis;
      if (lenis) {
        lenis.scrollTo(hero, { offset: 0, duration: 1.1 });
      } else {
        hero.scrollIntoView({ behavior: "smooth" });
      }
    }
  };

  return (
    <section ref={sectionRef} className="aegis-intro-v11" aria-label="Worksimplified introduction">
      <div ref={shellRef} className="aegis-intro-v11__shell">
        <GridPulse className="aegis-intro-v11__pulse" cell={24} />
        <div ref={bloomRef} className="aegis-intro-v11__bloom" aria-hidden="true" />

        <div className="aegis-intro-v11__eyebrow" data-grid-avoid>
          <span><i /> Enterprise AI Operating System</span>
          <b>Business intent → governed execution</b>
        </div>

        <div ref={wordRef} className="aegis-intro-v11__word" data-grid-avoid>
          <Wordmark className="aegis-intro-v11__wordmark" />
        </div>

        <div className="aegis-intro-v11__index" aria-hidden="true">
          <span>01</span><i /><span>ENTER</span>
        </div>

        <a className="aegis-intro-v11__hint" href="#main-hero" onClick={handleEnterClick}>
          <span>Scroll to enter</span><ArrowDown size={15} />
        </a>

        <div className="aegis-intro-v11__progress" aria-hidden="true">
          <span ref={progressRef} />
        </div>
      </div>
    </section>
  );
}

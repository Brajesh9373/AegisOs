"use client";

import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { ArrowDown } from "lucide-react";
import { useEffect, useLayoutEffect, useRef } from "react";

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

      const zoomScale = () => {
        const rect = word.getBoundingClientRect();
        const byWidth = window.innerWidth / Math.max(rect.width, 1);
        const byHeight = window.innerHeight / Math.max(rect.height, 1);
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
          scrub: 0.45,
          anticipatePin: 1,
          invalidateOnRefresh: true,
          fastScrollEnd: true,
          snap: {
            snapTo: (val) => (val > 0.18 ? 1 : 0),
            duration: { min: 0.25, max: 0.5 },
            ease: "power2.out",
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
          letterSpacing: "-0.08em",
          duration: 0.76,
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
        <div className="aegis-intro-v11__grid" aria-hidden="true" />
        <div ref={bloomRef} className="aegis-intro-v11__bloom" aria-hidden="true" />

        <div className="aegis-intro-v11__eyebrow">
          <span><i /> Enterprise AI Operating System</span>
          <b>Business intent → governed execution</b>
        </div>

        <div ref={wordRef} className="aegis-intro-v11__word" aria-label="Worksimplified">
          <span>Worksimplified</span>
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

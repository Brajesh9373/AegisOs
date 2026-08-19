"use client";

import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { ArrowDown } from "lucide-react";
import { useEffect, useRef } from "react";

export function BrandZoomIntroV11() {
  const sectionRef = useRef<HTMLElement>(null);
  const wordRef = useRef<HTMLDivElement>(null);
  const shellRef = useRef<HTMLDivElement>(null);
  const progressRef = useRef<HTMLSpanElement>(null);
  const bloomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
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
        return Math.max(byWidth, byHeight) * 12.5;
      };

      const tl = gsap.timeline({
        defaults: { ease: "none" },
        scrollTrigger: {
          trigger: section,
          start: "top top",
          end: () => `+=${Math.max(window.innerHeight * 1.55, 980)}`,
          pin: shell,
          pinSpacing: true,
          scrub: 0.58,
          anticipatePin: 1,
          invalidateOnRefresh: true,
          fastScrollEnd: false,
        },
      });

      tl.to(".aegis-intro-v11__eyebrow, .aegis-intro-v11__hint, .aegis-intro-v11__index", {
        opacity: 0,
        y: -10,
        duration: 0.16,
      }, 0.06)
        .to(word, {
          scale: zoomScale,
          yPercent: -4,
          letterSpacing: "-0.075em",
          duration: 0.72,
          force3D: true,
          transformOrigin: "50% 50%",
        }, 0.08)
        .to(bloom, {
          scale: 2.5,
          opacity: 0.95,
          duration: 0.46,
        }, 0.34)
        .to(word, {
          opacity: 0,
          duration: 0.18,
        }, 0.75)
        .to(shell, {
          backgroundColor: "rgba(247,249,252,0)",
          duration: 0.2,
        }, 0.78)
        .to(progress, {
          scaleX: 1,
          duration: 0.9,
        }, 0);

      if (header) {
        tl.to(header, {
          autoAlpha: 1,
          y: 0,
          duration: 0.16,
        }, 0.84);
      }
      if (scrollProgress) {
        tl.to(scrollProgress, {
          autoAlpha: 1,
          duration: 0.12,
        }, 0.88);
      }
    }, section);

    return () => {
      ctx.revert();
      if (header) gsap.set(header, { clearProps: "opacity,visibility,transform" });
      if (scrollProgress) gsap.set(scrollProgress, { clearProps: "opacity,visibility" });
    };
  }, []);

  return (
    <section ref={sectionRef} className="aegis-intro-v11" aria-label="AegisOS introduction">
      <div ref={shellRef} className="aegis-intro-v11__shell">
        <div className="aegis-intro-v11__grid" aria-hidden="true" />
        <div ref={bloomRef} className="aegis-intro-v11__bloom" aria-hidden="true" />

        <div className="aegis-intro-v11__eyebrow">
          <span><i /> Enterprise AI Operating System</span>
          <b>Business intent → governed execution</b>
        </div>

        <div ref={wordRef} className="aegis-intro-v11__word" aria-label="AegisOS">
          <span>Aegis</span><strong>OS</strong>
        </div>

        <div className="aegis-intro-v11__index" aria-hidden="true">
          <span>01</span><i /><span>ENTER</span>
        </div>

        <a className="aegis-intro-v11__hint" href="#main-hero">
          <span>Scroll to enter</span><ArrowDown size={15} />
        </a>

        <div className="aegis-intro-v11__progress" aria-hidden="true">
          <span ref={progressRef} />
        </div>
      </div>
    </section>
  );
}

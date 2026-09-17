"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { ArrowDown, ArrowUpRight, BrainCircuit, Code2, FileCheck2, Key, RefreshCcw, Target, Wrench } from "lucide-react";
import { useEffect, useRef, useState, type MouseEvent } from "react";

const HeroCoreCanvas = dynamic(() => import("./hero-core-canvas").then(m => m.HeroCoreCanvas), { ssr: false });

const satellites = [
  { label: "BA Agent", meta: "Requirements", icon: BrainCircuit, cls: "satellite-a", detail: "Discuss your project and generate the system flow diagram through interactive conversation." },
  { label: "Refinement", meta: "Iterate", icon: RefreshCcw, cls: "satellite-b", detail: "Continuous feedback loop that refines code and logic until it's exactly right." },
  { label: "Frappe", meta: "Connect", icon: Key, cls: "satellite-c", detail: "Securely link your Frappe backend and provision the live project." },
  { label: "Project", meta: "Manage", icon: Target, cls: "satellite-d", detail: "End-to-end oversight of requirements, milestones, and deliverables." },
  { label: "Functional", meta: "Build", icon: Wrench, cls: "satellite-e", detail: "Design functionalities and generate the comprehensive functional diagram." },
  { label: "Technical", meta: "Architect", icon: Code2, cls: "satellite-f", detail: "Create the technical diagram — database, APIs, and system architecture." },
];

export function HeroV3() {
  const [activeSatellite, setActiveSatellite] = useState(0);
  const sectionRef = useRef<HTMLElement>(null);
  const [coreReady, setCoreReady] = useState(false);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const sx = useSpring(x, { stiffness: 55, damping: 22, mass: 0.55 });
  const sy = useSpring(y, { stiffness: 55, damping: 22, mass: 0.55 });
  const moveX = useTransform(sx, [-.5, .5], [-10, 10]);
  const moveY = useTransform(sy, [-.5, .5], [-7, 7]);

  // three.js + R3F + drei are ~850KB — over half the home page's JS — for the
  // decorative core behind this hero. The brand intro fills the first screen,
  // so none of it is visible on arrival and none of it needs to be there.
  //
  // Wait for the first scroll instead of an IntersectionObserver: the intro is
  // pinned, so the hero sits at exactly one viewport height while the whole
  // intro plays — it only comes into view once the pin is done, which is far
  // too late to start an 850KB download. Any observer margin large enough to
  // fire early would also fire at page load. A scroll check is both earlier
  // and immune to the jump case, where a single large scroll can carry an
  // element past the viewport without the observer ever seeing it intersect.
  useEffect(() => {
    if (coreReady) return;
    const el = sectionRef.current;
    if (!el) return;

    let frame = 0;
    const check = () => {
      frame = 0;
      // A restored scroll position lands here on mount; otherwise the first
      // scroll event is the cue.
      if (window.scrollY > 0 || el.getBoundingClientRect().top < window.innerHeight) {
        setCoreReady(true);
      }
    };
    const schedule = () => {
      if (!frame) frame = requestAnimationFrame(check);
    };

    check();
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    return () => {
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
      cancelAnimationFrame(frame);
    };
  }, [coreReady]);

  function onMove(event: MouseEvent<HTMLDivElement>) {
    const r = event.currentTarget.getBoundingClientRect();
    x.set((event.clientX - r.left) / r.width - .5);
    y.set((event.clientY - r.top) / r.height - .5);
  }

  return (
    <section id="main-hero" className="v3-hero" ref={sectionRef} onMouseMove={onMove} onMouseLeave={() => { x.set(0); y.set(0); }}>
      <div className="v3-hero-noise" />
      <div className="v3-hero-radial" />
      <div className="v4-hero-aurora" aria-hidden="true">
        <i className="v4-ambient-orb v4-orb-a" />
        <i className="v4-ambient-orb v4-orb-b" />
        <i className="v4-ambient-orb v4-orb-c" />
      </div>
      <div className="v3-hero-copy">
        <motion.div className="v3-hero-kicker" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .6 }}>
          <i /> Agent-Driven Development Platform
        </motion.div>
        <motion.h1 initial={{ opacity: 0, y: 34 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .8, delay: .04, ease: [0.16, 1, 0.3, 1] }}>
          From idea to code,<br /><span>through specialist agents.</span>
        </motion.h1>
        <motion.div className="v3-hero-subrow" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .75, delay: .15 }}>
          <p>Discuss your project with the BA Agent, iterate through the refinement loop, connect Frappe, and get production code — all through six coordinated agents.</p>
          <div><a href="/login" className="v3-hero-primary">Get started <ArrowUpRight size={16} /></a><Link href="/platform" className="v3-hero-secondary">Explore agents</Link></div>
        </motion.div>
      </div>

      <motion.div className="v3-hero-stage" style={{ x: moveX, y: moveY }} transition={{ type: "spring", stiffness: 55, damping: 24 }}>
        <div className="v3-stage-grid" />
        <div className="v4-scanline" aria-hidden="true" />
        <div className="v4-stage-badge"><i /> 6 agents · pipeline ready</div>
        <div className="v3-stage-topline"><span>WORKSIMPLIFIED / AGENT PIPELINE</span><span><i /> READY</span></div>
        <div className="v3-core-canvas">{coreReady ? <HeroCoreCanvas /> : null}</div>
        <div className="v3-core-caption"><span>AGENT SYSTEM</span><span>Six specialist agents</span><small>BA → Refine → Frappe → Project → Functional → Technical</small></div>
        <svg className="v3-stage-wires" viewBox="0 0 1440 720" preserveAspectRatio="none" aria-hidden="true">
          <path d="M180 168 C330 165 432 250 596 318" />
          <path d="M1260 160 C1110 165 1010 250 844 318" />
          <path d="M162 544 C328 516 440 446 592 383" />
          <path d="M1278 548 C1102 515 998 446 846 383" />
          <path d="M720 90 C720 175 720 225 720 265" />
          <path d="M720 625 C720 547 720 490 720 445" />
        </svg>
        {satellites.map(({ label, meta, icon: Icon, cls }, i) => (
          <motion.button type="button" className={`v3-satellite ${cls} ${activeSatellite === i ? "is-active" : ""}`} key={label} animate={{ y: [0, i % 2 ? -6 : 6, 0] }} transition={{ repeat: Infinity, duration: 6.2 + i * .45, ease: [0.45, 0, 0.55, 1] }} onClick={() => setActiveSatellite(i)} aria-pressed={activeSatellite === i}>
            <span><Icon size={15} /></span><div><b>{label}</b><small>{meta}</small></div>
          </motion.button>
        ))}
        <motion.div className="v4-stage-insight" key={activeSatellite} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .28, ease: [0.16,1,0.3,1] }}>
          <span>AGENT · 0{activeSatellite + 1}</span><b>{satellites[activeSatellite].label}</b><p>{satellites[activeSatellite].detail}</p>
        </motion.div>
        <div className="v3-live-strip">
          <span><b>01</b> BA Agent ready</span><i />
          <span><b>02</b> Refinement loop</span><i />
          <span className="active"><b>03</b> Pipeline connected</span><i />
          <span><b>04</b> Output delivery</span></div>
      </motion.div>

      <a className="v3-scroll-cue" href="#architecture"><span>SEE THE AGENTS</span><ArrowDown size={15} /></a>
    </section>
  );
}

"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { ArrowDown, ArrowUpRight, Database, FileCheck2, Network, ShieldCheck, Sparkles, UsersRound } from "lucide-react";
import { useState, type MouseEvent } from "react";

const HeroCoreCanvas = dynamic(() => import("./hero-core-canvas").then(m => m.HeroCoreCanvas), { ssr: false });

const satellites = [
  { label: "Business brief", meta: "Natural language", icon: Sparkles, cls: "satellite-a", detail: "Intent normalized into objectives, constraints and success criteria." },
  { label: "Workforce", meta: "3 roles assigned", icon: UsersRound, cls: "satellite-b", detail: "Specialists are assigned with scoped tools, memory and autonomy." },
  { label: "Execution graph", meta: "8 live steps", icon: Network, cls: "satellite-c", detail: "State, branches and dependencies stay coordinated inside one run." },
  { label: "ERP write", meta: "Approval required", icon: Database, cls: "satellite-d", detail: "High-impact system actions pause at the exact control boundary." },
  { label: "Policy engine", meta: "12 rules active", icon: ShieldCheck, cls: "satellite-e", detail: "Permissions and policy are evaluated continuously during execution." },
  { label: "Outcome", meta: "Auditable", icon: FileCheck2, cls: "satellite-f", detail: "The completed outcome, decisions and trace become reusable context." },
];

export function HeroV3() {
  const [activeSatellite, setActiveSatellite] = useState(2);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const sx = useSpring(x, { stiffness: 55, damping: 22, mass: 0.55 });
  const sy = useSpring(y, { stiffness: 55, damping: 22, mass: 0.55 });
  const moveX = useTransform(sx, [-.5, .5], [-10, 10]);
  const moveY = useTransform(sy, [-.5, .5], [-7, 7]);

  function onMove(event: MouseEvent<HTMLDivElement>) {
    const r = event.currentTarget.getBoundingClientRect();
    x.set((event.clientX - r.left) / r.width - .5);
    y.set((event.clientY - r.top) / r.height - .5);
  }

  return (
    <section id="main-hero" className="v3-hero" onMouseMove={onMove} onMouseLeave={() => { x.set(0); y.set(0); }}>
      <div className="v3-hero-noise" />
      <div className="v3-hero-radial" />
      <div className="v4-hero-aurora" aria-hidden="true">
        <i className="v4-ambient-orb v4-orb-a" />
        <i className="v4-ambient-orb v4-orb-b" />
        <i className="v4-ambient-orb v4-orb-c" />
      </div>
      <div className="v3-hero-copy">
        <motion.div className="v3-hero-kicker" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .6 }}>
          <i /> Enterprise AI Operating System
        </motion.div>
        <motion.h1 initial={{ opacity: 0, y: 34 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .8, delay: .04, ease: [0.16, 1, 0.3, 1] }}>
          Business intent,<br /><span>executed.</span>
        </motion.h1>
        <motion.div className="v3-hero-subrow" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .75, delay: .15 }}>
          <p>AegisOS turns a business requirement into coordinated, governed work across AI workers, humans, and enterprise systems.</p>
          <div><a href="/login" className="v3-hero-primary">Get started <ArrowUpRight size={16} /></a><Link href="/platform" className="v3-hero-secondary">Explore platform</Link></div>
        </motion.div>
      </div>

      <motion.div className="v3-hero-stage" style={{ x: moveX, y: moveY }} transition={{ type: "spring", stiffness: 55, damping: 24 }}>
        <div className="v3-stage-grid" />
        <div className="v4-scanline" aria-hidden="true" />
        <div className="v4-stage-badge"><i /> latency 184ms · policy checks 12/12</div>
        <div className="v3-stage-topline"><span>AEGIS / LIVE EXECUTION FABRIC</span><span><i /> RUNNING</span></div>
        <div className="v3-core-canvas"><HeroCoreCanvas /></div>
        <div className="v3-core-caption"><span>AEGIS CORE</span><strong>Policy-aware orchestration</strong><small>Run #2841 · Vendor onboarding</small></div>
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
          <span>LIVE LAYER · 0{activeSatellite + 1}</span><b>{satellites[activeSatellite].label}</b><p>{satellites[activeSatellite].detail}</p>
        </motion.div>
        <div className="v3-live-strip">
          <span><b>01</b> Requirement understood</span><i />
          <span><b>02</b> Specialists assigned</span><i />
          <span className="active"><b>03</b> Executing systems</span><i />
          <span><b>04</b> Awaiting approval</span>
        </div>
      </motion.div>

      <a className="v3-scroll-cue" href="#architecture"><span>SEE THE SYSTEM</span><ArrowDown size={15} /></a>
    </section>
  );
}

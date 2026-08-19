"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, ArrowUpRight, BrainCircuit, Check, DatabaseZap, Eye, Network, ShieldCheck, UsersRound, Workflow } from "lucide-react";
import type { ProductPageData } from "@/lib/products";

const iconMap: Record<string, typeof BrainCircuit> = {
  "business-analyst": BrainCircuit,
  memory: Network,
  workforce: UsersRound,
  workflows: Workflow,
  governance: ShieldCheck,
  integrations: DatabaseZap,
  observability: Eye,
};

function ProductVisual({ slug }: { slug: string }) {
  if (slug === "business-analyst") return <div className="pv pv-brief"><span>BUSINESS REQUIREMENT</span><p>“Reduce vendor onboarding time while keeping finance and compliance approvals intact.”</p><div className="pv-status"><i/><b>Requirement mapped</b><small>3 roles · 4 systems · 2 gates</small></div></div>;
  if (slug === "workforce") return <div className="pv pv-workforce"><div className="pv-person lead"><span>BA</span><b>Business Analyst</b><small>Supervisor</small></div><i/><div className="pv-people"><div><span>CO</span><b>Compliance</b></div><div><span>FI</span><b>Finance</b></div><div><span>OP</span><b>Operations</b></div></div></div>;
  if (slug === "workflows") return <div className="pv pv-flow">{["Intent","Plan","Check","Approve","Execute"].map((x,i)=><div key={x}><span>0{i+1}</span><b>{x}</b>{i<4&&<i/>}</div>)}</div>;
  if (slug === "governance") return <div className="pv pv-policy"><div><span>POLICY</span><b>ERP_VENDOR_CREATE</b><em>Approval required</em></div>{[["Role","Finance Ops"],["Risk","High impact"],["Audit","Enabled"]].map(x=><p key={x[0]}><span>{x[0]}</span><b>{x[1]}</b></p>)}<button>Approve execution</button></div>;
  if (slug === "integrations") return <div className="pv pv-connect"><div className="pv-hub">AEGIS</div>{["CRM","ERP","DB","DRIVE","EMAIL","API"].map((x,i)=><span className={`pvc c${i}`} key={x}>{x}</span>)}</div>;
  if (slug === "observability") return <div className="pv pv-observe"><div className="pv-observe-kpis"><div><span>RUNS</span><b>846</b></div><div><span>SUCCESS</span><b>97.8%</b></div><div><span>SPEND</span><b>$1.2K</b></div></div><div className="pv-observe-chart">{[36,52,44,66,61,82,70,91,76,88,95].map((h,i)=><i style={{height:`${h}%`}} key={i}/>)}</div></div>;
  return <div className="pv pv-memory"><div className="memory-core">ORG<br/>MEMORY</div>{["Policy","Terms","Decisions","Runs","Roles","Data"].map((x,i)=><span className={`mem m${i}`} key={x}>{x}</span>)}</div>;
}

export function ProductPageV3({ product }: { product: ProductPageData }) {
  const Icon = iconMap[product.slug] || BrainCircuit;
  return (
    <>
      <section className={`v3-product-hero product-${product.slug}`}>
        <div className="v3-product-hero-copy">
          <div className="v3-product-eyebrow"><Icon size={15}/><span>{product.eyebrow.toUpperCase()}</span></div>
          <motion.h1 initial={{opacity:0,y:24}} animate={{opacity:1,y:0}} transition={{duration:.75}}>{product.title}</motion.h1>
          <p>{product.description}</p>
          <div className="v3-product-actions"><a href="#contact" className="v3-solid-button">Book a demo <ArrowUpRight size={14}/></a><Link href="/platform">Platform overview <ArrowRight size={14}/></Link></div>
        </div>
        <motion.div className="v3-product-hero-visual" initial={{opacity:0,scale:.96,y:24}} animate={{opacity:1,scale:1,y:0}} transition={{duration:.8,delay:.1}}><div className="pv-toolbar"><span>AEGIS / {product.slug.toUpperCase()}</span><em><i/> LIVE</em></div><ProductVisual slug={product.slug}/></motion.div>
        <div className="v3-product-flowline"><span>{product.primary}</span><i/><b>AegisOS</b><i/><span>{product.secondary}</span></div>
      </section>

      <section className="v3-product-metrics">
        {product.metrics.map((m,i)=><div key={m.label}><span>0{i+1}</span><b>{m.value}</b><p>{m.label}</p></div>)}
      </section>

      <section className="v3-product-capabilities">
        <div className="v3-section-label"><span>CAPABILITIES</span><p>Purpose-built around the operating model, not a collection of agent features.</p></div>
        <div className="v3-product-cap-grid">
          <div className="v3-product-cap-title"><h2>Built for work that has to <span>actually happen.</span></h2><p>Each capability is designed to remain connected to the execution runtime, governance model, and organizational context.</p></div>
          {product.capabilities.map((c,i)=><motion.article key={c.title} initial={{opacity:0,y:22}} whileInView={{opacity:1,y:0}} viewport={{once:true,amount:.25}} transition={{delay:i*.04}}><span>0{i+1}</span><h3>{c.title}</h3><p>{c.text}</p><Check size={16}/></motion.article>)}
        </div>
      </section>

      <section className="v3-product-process">
        <div className="v3-product-process-head"><span>HOW IT MOVES</span><h2>From input to operating outcome.</h2></div>
        <div className="v3-process-track">
          {product.steps.map((s,i)=><div key={s.number}><span>{s.number}</span><i/><h3>{s.title}</h3><p>{s.text}</p>{i<product.steps.length-1&&<ArrowRight className="process-arrow"/>}</div>)}
        </div>
      </section>

      <section className="v3-product-end" id="contact"><span>AEGISOS / {product.eyebrow.toUpperCase()}</span><h2>Put {product.eyebrow.toLowerCase()} inside the same system that executes the work.</h2><a href="mailto:hello@aegisos.ai">Book a demo <ArrowUpRight size={15}/></a></section>
    </>
  );
}

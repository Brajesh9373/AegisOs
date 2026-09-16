"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, ArrowUpRight, BrainCircuit, Check, CircleDollarSign, Code2, Database, FileText, Key, Network, PanelsTopLeft, ShieldCheck, Target, Wrench } from "lucide-react";
import type { ProductPageData } from "@/lib/products";

const iconMap: Record<string, typeof BrainCircuit> = {
  "ba-agent": BrainCircuit,
  "frappe-agent": Key,
  "project-agent": Target,
  "functional-agent": Wrench,
  "technical-agent": Code2,
};

function ProductVisual({ slug }: { slug: string }) {
  if (slug === "ba-agent") {
    return (
      <div className="pv pv-ba-agent">
        <div className="pv-ba-chat">
          <div className="pv-ba-message user"><span>USER</span><p>I need a vendor onboarding system that handles compliance checks and finance approvals.</p></div>
          <div className="pv-ba-message agent"><span>BA</span><p>Understood. I'll map out the stakeholders, systems, and flow. Generating your diagram now…</p></div>
        </div>

        <div className="pv-diagram">
          <div className="pv-diagram-head">
            <div><small>GENERATED</small><b>System Flow Diagram</b></div>
            <em className="pv-diagram-chip"><i />4 systems mapped</em>
          </div>
          <div className="pv-diagram-body">
            <svg className="pv-wires" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
              <path d="M20 50 H32" />
              <path d="M32 50 V26 H44" />
              <path d="M32 50 V74 H44" />
              <path d="M60 26 H70 V50 H80" />
              <path d="M60 74 H70 V50" />
            </svg>
            <span className="pv-node is-start" style={{ left: "12%", top: "50%" }}><FileText size={11} />Brief</span>
            <span className="pv-node is-done" style={{ left: "52%", top: "26%" }}><ShieldCheck size={11} />Compliance</span>
            <span className="pv-node is-live" style={{ left: "52%", top: "74%" }}><CircleDollarSign size={11} />Finance risk</span>
            <span className="pv-node is-end" style={{ left: "88%", top: "50%" }}><Database size={11} />Create in ERP</span>
          </div>
        </div>
      </div>
    );
  }
  if (slug === "frappe-agent") {
    return (
      <div className="pv pv-frappe">
        <div className="pv-frappe-creds">
          <Key size={14}/><small>CREDENTIALS</small><b>Connected</b><em>Secure</em>
        </div>
        <div className="pv-frappe-steps">
          <div className="pv-frappe-step done"><small>01</small><b>Get credentials</b><em>Done</em></div>
          <div className="pv-frappe-step done"><small>02</small><b>Create project</b><em>Done</em></div>
          <div className="pv-frappe-step live"><small>03</small><b>Interactive mode</b><em>Ready</em></div>
        </div>
        <div className="pv-frappe-portal"><Database size={12}/><b>Frappe Portal</b><small>Live · Accessible</small></div>
      </div>
    );
  }
  if (slug === "project-agent") {
    return (
      <div className="pv pv-project">
        <div className="pv-project-head"><Target size={14}/><b>Project Overview</b><em>On track</em></div>
        <div className="pv-project-milestones">
          <div className="pv-milestone done"><span>01</span><b>Requirements</b><small>Complete</small></div>
          <div className="pv-milestone done"><span>02</span><b>Flow diagram</b><small>Complete</small></div>
          <div className="pv-milestone live"><span>03</span><b>Functionals</b><small>In progress</small></div>
          <div className="pv-milestone"><span>04</span><b>Technical</b><small>Queued</small></div>
        </div>
      </div>
    );
  }
  if (slug === "functional-agent") {
    const leaves = [
      ["Intake form", "6 fields", "14%"],
      ["Compliance", "4 rules", "38%"],
      ["Approval", "2 gates", "62%"],
      ["ERP sync", "3 calls", "86%"],
    ] as const;
    return (
      <div className="pv pv-functional">
        <div className="pv-diagram">
          <div className="pv-diagram-head">
            <div><small>GENERATED</small><b>Functional Diagram</b></div>
            <em className="pv-diagram-chip"><i />4 modules mapped</em>
          </div>
          <div className="pv-diagram-body">
            <svg className="pv-wires" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
              <path d="M50 18 V34" />
              <path d="M14 34 H86" />
              <path d="M14 34 V54" />
              <path d="M38 34 V54" />
              <path d="M62 34 V54" />
              <path d="M86 34 V54" />
            </svg>
            <span className="pv-node is-start" style={{ left: "50%", top: "11%" }}><Wrench size={11} />Vendor onboarding</span>
            {leaves.map(([label, meta, left]) => (
              <span className="pv-fnode" key={label} style={{ left, top: "65%" }}>
                <b>{label}</b><small>{meta}</small>
              </span>
            ))}
          </div>
        </div>
      </div>
    );
  }
  if (slug === "technical-agent") {
    const stack = [
      { t: "Client", s: "Next.js UI", icon: PanelsTopLeft, top: "9%" },
      { t: "API", s: "24 routes", icon: Network, top: "37%" },
      { t: "Services", s: "business logic", icon: Code2, top: "65%" },
      { t: "Database", s: "12 tables", icon: Database, top: "93%", end: true },
    ];
    return (
      <div className="pv pv-technical">
        <div className="pv-diagram">
          <div className="pv-diagram-head">
            <div><small>GENERATED</small><b>Technical Architecture</b></div>
            <em className="pv-diagram-chip"><i />4 layers resolved</em>
          </div>
          <div className="pv-diagram-body">
            <svg className="pv-wires" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
              <path d="M50 20 V30" />
              <path d="M50 48 V58" />
              <path d="M50 76 V86" />
            </svg>
            {stack.map(({ t, s, icon: Icon, top, end }) => (
              <span className={`pv-lnode${end ? " is-end" : ""}`} key={t} style={{ top }}>
                <span className="pv-lnode-icon"><Icon size={13} /></span>
                <b>{t}</b>
                <small>{s}</small>
              </span>
            ))}
          </div>
        </div>
      </div>
    );
  }
  return <div className="pv pv-default"><BrainCircuit size={24}/></div>;
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
        <motion.div className="v3-product-hero-visual" initial={{opacity:0,scale:.96,y:24}} animate={{opacity:1,scale:1,y:0}} transition={{duration:.8,delay:.1}}><div className="pv-toolbar"><span>WORKSIMPLIFIED / {product.slug.toUpperCase()}</span><em><i/> LIVE</em></div><ProductVisual slug={product.slug}/></motion.div>
        <div className="v3-product-flowline"><span>{product.primary}</span><i/><b>Agent System</b><i/><span>{product.secondary}</span></div>
      </section>

      <section className="v3-product-metrics">
        {product.metrics.map((m,i)=><div key={m.label}><span>0{i+1}</span><b>{m.value}</b><p>{m.label}</p></div>)}
      </section>

      <section className="pv-caps">
        <div className="pv-caps-head">
          <span>CAPABILITIES</span>
          <p>Specialized agent capabilities for this stage of the workflow.</p>
        </div>

        <div className="pv-caps-body">
          <div className="pv-caps-intro">
            <h2>Built for this stage<br /><span>of the agent pipeline.</span></h2>
            <p>Each capability is purpose-built to advance the project to the next agent in the flow.</p>
            <div className="pv-caps-stats">
              <div>
                <small>CAPABILITIES</small>
                <b>{String(product.capabilities.length).padStart(2, "0")}</b>
              </div>
              <div>
                <small>PIPELINE STAGE</small>
                <b>{product.eyebrow.toUpperCase()}</b>
              </div>
            </div>
          </div>

          <div className="pv-caps-list">
            {product.capabilities.map((c, i) => (
              <motion.article
                className="pv-cap"
                key={c.title}
                initial={{ opacity: 0, y: 18 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.3 }}
                transition={{ duration: 0.55, delay: i * 0.06, ease: [0.16, 1, 0.3, 1] }}
              >
                <span className="pv-cap-n">{String(i + 1).padStart(2, "0")}</span>
                <div className="pv-cap-copy">
                  <h3>{c.title}</h3>
                  <p>{c.text}</p>
                </div>
                <span className="pv-cap-mark"><Check size={12} /></span>
              </motion.article>
            ))}
          </div>
        </div>
      </section>

      <section className="pv-steps">
        <div className="pv-steps-head">
          <span>HOW IT WORKS</span>
          <h2>The agent workflow for this stage.</h2>
        </div>

        <div className="pv-steps-track">
          <span className="pv-steps-rail" aria-hidden="true" />
          {product.steps.map((s, i) => (
            <motion.article
              className="pv-step"
              key={s.number}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.6, delay: i * 0.09, ease: [0.16, 1, 0.3, 1] }}
            >
              <div className="pv-step-top">
                <span className="pv-step-n">{s.number}</span>
                <span className="pv-step-node" />
              </div>
              <h3>{s.title}</h3>
              <p>{s.text}</p>
              <div className="pv-step-progress" aria-hidden="true">
                {product.steps.map((_, k) => (
                  <i key={k} className={k <= i ? "is-on" : ""} />
                ))}
              </div>
            </motion.article>
          ))}
        </div>
      </section>

      <section className="v3-product-end" id="contact"><span>WORKSIMPLIFIED / {product.eyebrow.toUpperCase()}</span><h2>Put this agent to work in your pipeline.</h2><a href="mailto:hello@aegisos.ai">Book a demo <ArrowUpRight size={15}/></a></section>
    </>
  );
}

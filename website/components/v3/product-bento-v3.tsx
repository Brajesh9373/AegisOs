"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, ArrowUpRight, BrainCircuit, CheckCircle2, DatabaseZap, Eye, FileText, GitBranch, Network, ShieldCheck, UserCheck, UsersRound, Workflow } from "lucide-react";

function AnalystVisual() {
  return <div className="v9-mini-analyst">
    <div className="v9-mini-brief-head"><span><FileText size={12}/> BUSINESS BRIEF</span><em>01</em></div>
    <div className="v9-analyst-brief">
      <p>Automate vendor onboarding across finance, compliance and ERP.</p>
      <span>Natural language</span>
    </div>
    <div className="v9-analyst-workspace">
      <div className="v9-analyst-structure">
        <small>STRUCTURED REQUIREMENT</small>
        <div className="v9-mini-parse"><span>Objective <b>Onboard</b></span><span>Systems <b>CRM · ERP</b></span><span>Control <b>Finance approval</b></span></div>
      </div>
      <div className="v9-analyst-plan">
        <small>EXECUTION PLAN</small>
        <div><span>01</span><b>Verify vendor</b><em>Compliance</em></div>
        <div><span>02</span><b>Score risk</b><em>Finance</em></div>
        <div><span>03</span><b>Create supplier</b><em>ERP</em></div>
      </div>
    </div>
    <div className="v9-mini-ready"><i/><b>Execution plan ready</b><small>8 steps · 3 roles · 2 controls</small></div>
  </div>;
}

function WorkforceVisual() {
  return <div className="v9-mini-workforce">
    <div className="v9-workforce-core"><GitBranch size={14}/><b>Runtime</b><small>Supervisor</small></div>
    <svg viewBox="0 0 300 170" preserveAspectRatio="none" aria-hidden="true"><path d="M150 83 L48 38M150 83 L252 38M150 83 L55 142M150 83 L245 142"/></svg>
    <div className="v9-worker w1"><span>CO</span><div><b>Compliance</b><small>Policy</small></div></div>
    <div className="v9-worker w2"><span>FI</span><div><b>Finance</b><small>Risk</small></div></div>
    <div className="v9-worker w3"><span>OP</span><div><b>Operations</b><small>ERP</small></div></div>
    <div className="v9-worker w4 human"><UserCheck size={12}/><div><b>Human</b><small>Escalation</small></div></div>
  </div>;
}

function WorkflowVisual() {
  return <div className="v9-mini-workflow">
    <div className="v9-run-state"><i/> RUN #2841 <span>LIVE</span></div>
    <div className="v9-flow-nodes">
      <div className="done"><small>01</small><b>Read CRM</b><em>done</em></div><ArrowRight/>
      <div className="done"><small>02</small><b>Policy</b><em>done</em></div><ArrowRight/>
      <div className="live"><small>03</small><b>ERP write</b><em>running</em></div><ArrowRight/>
      <div><small>04</small><b>Notify</b><em>queued</em></div>
    </div>
    <div className="v9-run-progress"><span/><b>67%</b></div>
  </div>;
}

function GovernanceVisual() {
  return <div className="v9-mini-governance">
    <div className="v9-policy-title"><ShieldCheck size={13}/><span><small>POLICY PACK</small><b>ERP_VENDOR_CREATE</b></span><em>3 checks</em></div>
    <div className="v9-policy-row"><span>Role permission</span><b>Passed</b></div>
    <div className="v9-policy-row"><span>Data classification</span><b>Passed</b></div>
    <div className="v9-policy-row warn"><span>Amount &gt; $25K</span><b>Review</b></div>
    <div className="v9-policy-gate"><UserCheck size={12}/><span><small>HUMAN GATE</small><b>Finance Ops</b></span><em>Required</em></div>
  </div>;
}

function IntegrationsVisual() {
  return <div className="v9-mini-integrations">
    <svg viewBox="0 0 300 180" preserveAspectRatio="none" aria-hidden="true"><path d="M150 90 L42 38M150 90 L258 38M150 90 L42 145M150 90 L258 145"/></svg>
    <div className="v9-integration-core"><DatabaseZap size={14}/><b>AegisOS</b></div>
    <span className="i1">CRM<small>Read</small></span><span className="i2">ERP<small>Write</small></span><span className="i3">DB<small>Scoped</small></span><span className="i4">API<small>Action</small></span>
  </div>;
}

function MemoryVisual() {
  return <div className="v9-mini-memory">
    <div className="v9-memory-sources">
      <span><small>POLICY</small><b>AP-04</b></span>
      <span><small>GLOSSARY</small><b>186 terms</b></span>
      <span><small>DECISIONS</small><b>42 linked</b></span>
      <span><small>RUN HISTORY</small><b>1.8K traces</b></span>
    </div>
    <div className="v9-memory-runtime">
      <div className="v9-memory-core"><Network size={15}/><b>ORG MEMORY</b><small>24 sources</small></div>
      <div className="v9-memory-context"><span>Vendor onboarding</span><i/><span>Finance approval rule</span><i/><span>ERP write pattern</span></div>
    </div>
    <div className="v9-memory-foot"><i/><b>Relevant context attached to the next run</b><small>12ms retrieval</small></div>
  </div>;
}

function ObserveVisual() {
  const bars=[32,55,45,78,63,90,72,84];
  return <div className="v9-mini-observe">
    <div className="v9-observe-kpis"><span><small>RUNS</small><b>846</b></span><span><small>SUCCESS</small><b>97.8%</b></span><span><small>COST/RUN</small><b>$0.43</b></span></div>
    <div className="v9-observe-chart">{bars.map((h,i)=><i key={i} style={{height:`${h}%`}} />)}<span className="v9-chart-line"/></div>
    <div className="v9-observe-foot"><span><CheckCircle2 size={11}/> Healthy</span><b>Live telemetry</b></div>
  </div>;
}

const products = [
  { href: "/product/business-analyst", label: "Business Analyst", eyebrow: "UNDERSTAND", icon: BrainCircuit, className: "feature-large", body: "Turn natural-language requirements into structured, executable plans.", visual: <AnalystVisual/> },
  { href: "/product/workforce", label: "AI Workforce", eyebrow: "ORCHESTRATE", icon: UsersRound, className: "", body: "Role-based digital employees with memory, skills, tools, and boundaries.", visual: <WorkforceVisual/> },
  { href: "/product/workflows", label: "Workflow Engine", eyebrow: "EXECUTE", icon: Workflow, className: "", body: "Stateful execution across AI workers, humans, systems, branches, and time.", visual: <WorkflowVisual/> },
  { href: "/product/governance", label: "Governance", eyebrow: "CONTROL", icon: ShieldCheck, className: "", body: "Make autonomy conditional on policy, permissions, risk, and human judgment.", visual: <GovernanceVisual/> },
  { href: "/product/integrations", label: "Integrations", eyebrow: "CONNECT", icon: DatabaseZap, className: "", body: "Expose enterprise data and actions as governed capabilities.", visual: <IntegrationsVisual/> },
  { href: "/product/memory", label: "Organizational Memory", eyebrow: "REMEMBER", icon: Network, className: "feature-wide", body: "Carry policies, terminology, decisions, run history, and role context into the next piece of work.", visual: <MemoryVisual/> },
  { href: "/product/observability", label: "Observability & Cost", eyebrow: "OBSERVE", icon: Eye, className: "feature-wide", body: "See every run, approval, failure, latency signal, and dollar spent.", visual: <ObserveVisual/> },
];

export function ProductBentoV3() {
  return (
    <section className="v3-product-bento">
      <div className="v3-section-label dark"><span>04 / PLATFORM MODULES</span><p>Each module is useful alone. Together they form the operating system.</p></div>
      <div className="v3-bento-title"><h2>One platform.<br/><span>No loose ends.</span></h2><Link href="/platform">Explore the platform <ArrowUpRight size={15}/></Link></div>
      <div className="v3-bento-grid v9-bento-grid">
        {products.map(({href,label,eyebrow,icon:Icon,className,body,visual}, index) => (
          <motion.article key={href} className={`v3-bento-card v9-bento-card ${className}`} initial={{opacity:0,y:24}} whileInView={{opacity:1,y:0}} viewport={{once:true,amount:.2}} transition={{duration:.7,delay:(index%3)*.06,ease:[.16,1,.3,1]}} whileHover={{y:-4}} onMouseMove={(event) => { const r = event.currentTarget.getBoundingClientRect(); event.currentTarget.style.setProperty("--mx", `${event.clientX-r.left}px`); event.currentTarget.style.setProperty("--my", `${event.clientY-r.top}px`); }}>
            <Link href={href} aria-label={label} />
            <div className="v3-bento-card-head"><span><Icon size={15}/>{eyebrow}</span><span className="v9-card-open"><ArrowUpRight size={14}/></span></div>
            <div className="v3-bento-visual">{visual}</div>
            <div className="v3-bento-copy"><h3>{label}</h3><p>{body}</p><span className="v9-card-link">Explore module <ArrowRight size={12}/></span></div>
          </motion.article>
        ))}
      </div>
    </section>
  );
}

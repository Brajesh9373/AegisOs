import Link from "next/link";
import { ArrowRight, ArrowUpRight, BrainCircuit, DatabaseZap, Eye, Network, ShieldCheck, UsersRound, Workflow } from "lucide-react";

const modules = [
  ["Business Analyst","/product/business-analyst","Understand business intent before choosing technology.",BrainCircuit],
  ["Organizational Memory","/product/memory","Carry policies, terminology, decisions and run history forward.",Network],
  ["AI Workforce","/product/workforce","Deploy role-based digital employees with bounded autonomy.",UsersRound],
  ["Workflow Engine","/product/workflows","Coordinate stateful execution across people, agents and systems.",Workflow],
  ["Integrations","/product/integrations","Expose enterprise data and actions as governed capabilities.",DatabaseZap],
  ["Governance","/product/governance","Enforce RBAC, approvals, policy and human intervention.",ShieldCheck],
  ["Observability & Cost","/product/observability","Operate AI with traces, reliability, economics and outcomes.",Eye],
] as const;

export default function PlatformPage() {
  return (
    <>
      <section className="v3-platform-page-hero">
        <span>AEGISOS PLATFORM</span>
        <h1>One operating system between<br/><em>business intent and execution.</em></h1>
        <p>Instead of stitching together an assistant, agent framework, workflow engine, tool layer, approval system, and observability stack, AegisOS connects the full operating loop.</p>
        <div><a href="#contact" className="v3-solid-button">Book a demo <ArrowUpRight size={14}/></a><Link href="/product/workflows">Explore workflow runtime <ArrowRight size={14}/></Link></div>
      </section>

      <section className="v3-platform-map">
        <div className="platform-map-head"><span>THE SYSTEM</span><h2>Every layer stays connected to the work.</h2></div>
        <div className="platform-map-stack">
          <div className="map-row input"><span>BUSINESS LAYER</span><b>Requirements</b><b>People</b><b>Policies</b><b>Systems</b></div>
          <i className="map-arrow">↓</i>
          <div className="map-core"><span>AEGISOS CORE</span><div><b>Understand</b><i/> <b>Orchestrate</b><i/> <b>Execute</b><i/> <b>Govern</b><i/> <b>Observe</b></div></div>
          <i className="map-arrow">↓</i>
          <div className="map-row output"><span>OUTCOME LAYER</span><b>Completed work</b><b>Audit trail</b><b>Human decisions</b><b>Business metrics</b></div>
        </div>
      </section>

      <section className="v3-platform-modules">
        <div className="v3-section-label"><span>PLATFORM MODULES</span><p>Explore the parts of the system in depth.</p></div>
        <div className="platform-module-grid">
          {modules.map(([name,href,text,Icon],i)=><article key={href}><Link href={href}/><div><span>0{i+1}</span><Icon size={18}/></div><h3>{name}</h3><p>{text}</p><b>Explore <ArrowUpRight size={13}/></b></article>)}
        </div>
      </section>

      <section className="v3-platform-loop">
        <span>THE OPERATING LOOP</span>
        <h2>AegisOS does not end when a model returns text.</h2>
        <div className="platform-loop-track">{["Intent","Context","Plan","Workforce","Actions","Approvals","Outcome","Trace"].map((x,i)=><div key={x}><span>{String(i+1).padStart(2,"0")}</span><b>{x}</b>{i<7&&<ArrowRight/>}</div>)}</div>
      </section>

      <section className="v3-page-cta" id="contact"><span>BUILD THE OPERATING LAYER</span><h2>Move from AI features to an AI operating model.</h2><a href="mailto:hello@aegisos.ai">Book a demo <ArrowUpRight size={15}/></a></section>
    </>
  );
}

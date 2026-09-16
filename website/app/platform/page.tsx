import Link from "next/link";
import { ArrowRight, ArrowUpRight, BrainCircuit, Code2, Key, Target, Wrench } from "lucide-react";

const modules = [
  ["BA Agent","/product/ba-agent","Discuss the project and generate the system flow diagram.",BrainCircuit],
  ["Frappe Agent","/product/frappe-agent","Connect the backend and go live in Frappe.",Key],
  ["Project Agent","/product/project-agent","Track scope, milestones, and deliverables end to end.",Target],
  ["Functional Agent","/product/functional-agent","Map functionalities, user actions, and edge cases.",Wrench],
  ["Technical Agent","/product/technical-agent","Design the database schema, APIs, and architecture.",Code2],
] as const;

export default function PlatformPage() {
  return (
    <>
      <section className="v3-platform-page-hero">
        <span>WORKSIMPLIFIED PLATFORM</span>
        <h1>Six specialist agents between<br/><em>a business idea and running code.</em></h1>
        <p>Instead of stitching together an assistant, an agent framework, a workflow engine, and a tool layer, Worksimplified runs one connected pipeline — from requirement to deployed system.</p>
        <div><a href="#contact" className="v3-solid-button">Book a demo <ArrowUpRight size={14}/></a><Link href="/product/ba-agent">Explore the agent pipeline <ArrowRight size={14}/></Link></div>
      </section>

      <section className="v3-platform-map">
        <div className="platform-map-head"><span>THE SYSTEM</span><h2>Every layer stays connected to the work.</h2></div>
        <div className="platform-map-stack">
          <div className="map-row input"><span>BUSINESS LAYER</span><b>Requirements</b><b>People</b><b>Policies</b><b>Systems</b></div>
          <i className="map-arrow">↓</i>
          <div className="map-core"><span>THE AGENT PIPELINE</span><div><b>Discover</b><i/> <b>Refine</b><i/> <b>Connect</b><i/> <b>Build</b><i/> <b>Architect</b></div></div>
          <i className="map-arrow">↓</i>
          <div className="map-row output"><span>OUTCOME LAYER</span><b>Running system</b><b>Flow diagram</b><b>Decision trail</b><b>Technical design</b></div>
        </div>
      </section>

      <section className="v3-platform-modules">
        <div className="v3-section-label"><span>THE AGENT PIPELINE</span><p>Explore each agent in depth.</p></div>
        <div className="platform-module-grid">
          {modules.map(([name,href,text,Icon],i)=><article key={href}><Link href={href}/><div><span>0{i+1}</span><Icon size={18}/></div><h3>{name}</h3><p>{text}</p><b>Explore <ArrowUpRight size={13}/></b></article>)}
        </div>
      </section>

      <section className="v3-platform-loop">
        <span>THE OPERATING LOOP</span>
        <h2>Worksimplified does not end when a model returns text.</h2>
        <div className="platform-loop-track">{["Intent","BA Agent","Flow diagram","Refinement","Frappe connect","Functional","Technical","Running system"].map((x,i)=><div key={x}><span>{String(i+1).padStart(2,"0")}</span><b>{x}</b>{i<7&&<ArrowRight/>}</div>)}</div>
      </section>

      <section className="v3-page-cta" id="contact"><span>BUILD THE AGENT PIPELINE</span><h2>Move from disconnected AI tools to one pipeline that ships.</h2><a href="mailto:hello@aegisos.ai">Book a demo <ArrowUpRight size={15}/></a></section>
    </>
  );
}

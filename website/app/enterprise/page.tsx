import { ArrowUpRight, Check, Eye, KeyRound, LockKeyhole, ScanSearch, ShieldCheck, UserCheck } from "lucide-react";

const controls = [
  ["Role-based access", "Scope workers, users, teams, and capabilities to the access they actually need.", KeyRound],
  ["Human approvals", "Place human judgment before high-impact actions without breaking the workflow.", UserCheck],
  ["Policy enforcement", "Apply workflow, action, value, data, and risk policies at runtime.", ShieldCheck],
  ["Data boundaries", "Keep organizational memory and enterprise data scoped to the right context.", LockKeyhole],
  ["Complete trace", "Inspect every worker action, system call, approval, exception, and outcome.", ScanSearch],
  ["Operational visibility", "Monitor reliability, human load, spend, latency, and business results.", Eye],
] as const;

export default function EnterprisePage(){
  return <>
    <section className="v3-enterprise-hero">
      <div><span>AEGISOS FOR ENTERPRISE</span><h1>More autonomy.<br/><em>Without giving up control.</em></h1><p>Enterprise AI needs more than intelligence. AegisOS puts identity, permissions, policy, human judgment, observability, and audit directly into the execution layer.</p><a href="#contact">Talk to us <ArrowUpRight size={15}/></a></div>
      <div className="enterprise-policy-card"><div className="epc-head"><ShieldCheck/><div><span>POLICY ENGINE</span><b>Production controls</b></div><em><i/> ENFORCED</em></div>{[["Worker identity","Verified"],["Tool permissions","Scoped"],["Human approval","Conditional"],["Audit trail","Always on"],["Data access","Policy-bound"]].map(([a,b])=><div className="epc-row" key={a}><span>{a}</span><b><Check size={12}/>{b}</b></div>)}</div>
    </section>

    <section className="v3-enterprise-principle"><span>CONTROL IS PART OF EXECUTION</span><h2>Governance should not be a dashboard you look at after the AI has already acted.</h2><p>AegisOS evaluates identity, policy, risk, system access, and human checkpoints while work is moving through the runtime.</p></section>

    <section className="v3-enterprise-controls">
      <div className="v3-section-label"><span>ENTERPRISE CONTROLS</span><p>Bound autonomy without reducing the system to manual automation.</p></div>
      <div className="enterprise-control-grid">{controls.map(([title,text,Icon],i)=><article key={title}><span>0{i+1}</span><Icon size={20}/><h3>{title}</h3><p>{text}</p></article>)}</div>
    </section>

    <section className="v3-autonomy-matrix"><div className="matrix-copy"><span>AUTONOMY MODEL</span><h2>Different work deserves different control.</h2><p>Low-risk actions can run automatically. Material work can require review. High-impact actions can stop for explicit approval.</p></div><div className="matrix-ui"><div className="matrix-axis y"><span>HIGH RISK</span><span>LOW RISK</span></div><div className="matrix-grid"><div className="approve"><b>APPROVE</b><small>Prepare → Human authorizes → Execute</small></div><div className="review"><b>REVIEW</b><small>Execute → Human oversight</small></div><div className="auto"><b>AUTO</b><small>Execute inside policy boundaries</small></div><i className="matrix-dot d1"/><i className="matrix-dot d2"/><i className="matrix-dot d3"/></div><div className="matrix-axis x"><span>LOW IMPACT</span><span>HIGH IMPACT</span></div></div></section>

    <section className="v3-page-cta" id="contact"><span>ENTERPRISE AEGISOS</span><h2>Build an AI operating model your organization can actually govern.</h2><a href="mailto:hello@aegisos.ai">Book an enterprise demo <ArrowUpRight size={15}/></a></section>
  </>;
}

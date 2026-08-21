"use client";

import { motion } from "framer-motion";
import { Braces, Database, FileText, Mail, MessageSquare, PanelsTopLeft, PlugZap, ShieldCheck } from "lucide-react";

const systems = [
  { label: "CRM", icon: PanelsTopLeft, cls: "sys-a", meta: "Read / Write" },
  { label: "Slack", icon: MessageSquare, cls: "sys-b", meta: "Messages" },
  { label: "PostgreSQL", icon: Database, cls: "sys-c", meta: "Scoped data" },
  { label: "Drive", icon: FileText, cls: "sys-d", meta: "Documents" },
  { label: "Email", icon: Mail, cls: "sys-e", meta: "Send / Read" },
  { label: "Internal API", icon: Braces, cls: "sys-f", meta: "Custom actions" },
];

export function IntegrationFieldV3() {
  return (
    <section className="v3-integration-field">
      <div className="v3-integration-copy">
        <span>05 / ENTERPRISE CONNECTIONS</span>
        <h2>AI becomes useful when it can safely <em>touch the business.</em></h2>
        <p>Connect the systems you already run. AegisOS exposes only approved data and actions, then applies role, workflow, and policy boundaries at execution time.</p>
        <div className="v3-connection-stats"><div><b>Scoped</b><small>data access</small></div><div><b>Governed</b><small>system actions</small></div><div><b>Audited</b><small>every run</small></div></div>
      </div>
      <div className="v3-system-field">
        <div className="v3-system-grid" />
        <svg viewBox="0 0 900 680" preserveAspectRatio="none" aria-hidden="true">
          <ellipse cx="450" cy="340" rx="260" ry="190" />
          <ellipse cx="450" cy="340" rx="355" ry="270" />
          <line x1="450" y1="340" x2="152" y2="150" /><line x1="450" y1="340" x2="735" y2="130" />
          <line x1="450" y1="340" x2="780" y2="370" /><line x1="450" y1="340" x2="690" y2="580" />
          <line x1="450" y1="340" x2="205" y2="585" /><line x1="450" y1="340" x2="115" y2="370" />
        </svg>
        <div className="v3-aegis-hub"><span className="v3-brand-glyph"><i/><i/><i/></span><strong>AegisOS</strong><small>Execution layer</small><em><ShieldCheck size={12}/> Policy enforced</em></div>
        {systems.map(({label,icon:Icon,cls,meta},i)=><motion.div className={`v3-system-node ${cls}`} key={label} animate={{y:[0,i%2?-5:5,0]}} transition={{duration:6+i*.42,repeat:Infinity,ease:[.45,0,.55,1]}} whileHover={{scale:1.05}}><span><Icon size={17}/></span><div><b>{label}</b><small>{meta}</small></div></motion.div>)}
      </div>
    </section>
  );
}

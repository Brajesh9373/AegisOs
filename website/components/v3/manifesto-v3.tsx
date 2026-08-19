"use client";

import { motion } from "framer-motion";
import { CheckCircle2, FileText, MessageSquareText, Network, ShieldCheck, Sparkles, UserCheck, Workflow } from "lucide-react";

const aegisSteps = [
  { label: "Intent", meta: "Business brief", icon: FileText },
  { label: "Plan", meta: "8 steps", icon: Sparkles },
  { label: "Workforce", meta: "3 roles", icon: Network },
  { label: "Execution", meta: "Systems + humans", icon: Workflow },
  { label: "Outcome", meta: "Auditable", icon: CheckCircle2 },
];

export function ManifestoV3() {
  return (
    <section className="v3-manifesto">
      <div className="v3-manifesto-grid">
        <div className="v3-manifesto-index">01 / CATEGORY</div>
        <motion.h2 initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: .3 }} transition={{ duration: .7 }}>
          AI assistants stop at an answer.<br /><span>AegisOS continues until the work is done.</span>
        </motion.h2>
        <div className="v3-manifesto-copy">AegisOS is the execution layer between a business request and the systems, AI workers, approvals, and people required to complete it.</div>
      </div>

      <div className="v9-compare-shell">
        <div className="v9-compare-row assistant-row">
          <div className="v9-compare-label"><span><MessageSquareText size={17} /></span><div><b>AI ASSISTANT</b><small>Response system</small></div></div>
          <div className="v9-assistant-flow">
            <div className="v9-simple-node"><small>INPUT</small><b>Prompt</b></div>
            <span className="v9-flow-arrow">→</span>
            <div className="v9-simple-node answer"><small>MODEL</small><b>Answer</b></div>
            <div className="v9-stop-chip">Stops here</div>
          </div>
          <p>Useful for knowledge and generation. The system has no persistent ownership of the work that follows.</p>
        </div>

        <div className="v9-compare-row aegis-row">
          <div className="v9-compare-label"><span><Workflow size={17} /></span><div><b>AEGISOS</b><small>Execution runtime</small></div></div>
          <div className="v9-aegis-flow">
            <div className="v9-aegis-track" aria-hidden="true"><motion.i animate={{ x: [0, 520] }} transition={{ repeat: Infinity, duration: 6.5, ease: "linear" }} /></div>
            {aegisSteps.map(({ label, meta, icon: Icon }, index) => (
              <div className={`v9-runtime-node ${index === 3 ? "is-live" : ""}`} key={label}>
                <span><Icon size={13} /></span><div><small>0{index + 1}</small><b>{label}</b><em>{meta}</em></div>
              </div>
            ))}
          </div>
          <p>One governed runtime carries context, state and responsibility from request to completed business outcome.</p>
        </div>

        <div className="v9-runtime-band">
          <span><ShieldCheck size={13} /> Policies evaluated during execution</span>
          <span><UserCheck size={13} /> Human gates at high-impact actions</span>
          <span><Network size={13} /> Memory and trace persist across the run</span>
        </div>
      </div>
    </section>
  );
}

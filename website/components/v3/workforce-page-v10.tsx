"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight,
  ArrowUpRight,
  BadgeCheck,
  BrainCircuit,
  CheckCircle2,
  ChevronRight,
  CircleDollarSign,
  Database,
  FileText,
  Fingerprint,
  GitBranch,
  KeyRound,
  Network,
  Play,
  ShieldCheck,
  Sparkles,
  UserCheck,
  UsersRound,
  Workflow,
  Wrench,
} from "lucide-react";

type WorkerKey = "analyst" | "compliance" | "finance" | "operations" | "human";
type AnatomyKey = "role" | "skills" | "memory" | "tools" | "permissions" | "policies" | "supervisor";

const workers: Record<WorkerKey, {
  name: string;
  role: string;
  short: string;
  state: string;
  stateClass: string;
  tools: string[];
  memory: string;
  autonomy: string;
}> = {
  analyst: {
    name: "Avery",
    role: "Business Analyst",
    short: "BA",
    state: "Supervising",
    stateClass: "live",
    tools: ["Requirements", "Org memory", "Planner"],
    memory: "Business rules + workflow patterns",
    autonomy: "Plan + delegate",
  },
  compliance: {
    name: "Mira",
    role: "Compliance Specialist",
    short: "CO",
    state: "Active",
    stateClass: "live",
    tools: ["Policy DB", "Vendor docs", "Risk rules"],
    memory: "Compliance policy + evidence history",
    autonomy: "Review independently",
  },
  finance: {
    name: "Atlas",
    role: "Finance Specialist",
    short: "FI",
    state: "Working",
    stateClass: "working",
    tools: ["Risk API", "Ledger", "ERP"],
    memory: "Approval thresholds + vendor risk",
    autonomy: "Score + recommend",
  },
  operations: {
    name: "Nova",
    role: "Operations Specialist",
    short: "OP",
    state: "Ready",
    stateClass: "ready",
    tools: ["ERP", "CRM", "Email"],
    memory: "Execution patterns + system mappings",
    autonomy: "Execute approved actions",
  },
  human: {
    name: "Finance Ops",
    role: "Human Owner",
    short: "HO",
    state: "On call",
    stateClass: "human",
    tools: ["Approval", "Override", "Escalation"],
    memory: "Decision context + audit trail",
    autonomy: "Final authority",
  },
};

const anatomy: Record<AnatomyKey, { title: string; eyebrow: string; copy: string; detail: string; items: string[]; icon: typeof UsersRound }> = {
  role: {
    title: "A job, not a prompt.",
    eyebrow: "ROLE",
    copy: "Every digital employee starts with a clear operating responsibility, success criteria, and boundary of work.",
    detail: "Compliance Specialist",
    items: ["Verify vendor evidence", "Apply policy pack AP-04", "Escalate ambiguous cases"],
    icon: UsersRound,
  },
  skills: {
    title: "Capabilities attached to responsibility.",
    eyebrow: "SKILLS",
    copy: "Skills define what the worker knows how to do without turning the role into unrestricted general-purpose autonomy.",
    detail: "Policy reasoning + evidence review",
    items: ["Document verification", "Risk classification", "Exception explanation"],
    icon: Sparkles,
  },
  memory: {
    title: "Context that persists between runs.",
    eyebrow: "MEMORY",
    copy: "Role-scoped organizational memory keeps language, policy, decisions, and previous run context available when it matters.",
    detail: "24 approved sources",
    items: ["Vendor policy history", "Decision precedents", "Organization terminology"],
    icon: BrainCircuit,
  },
  tools: {
    title: "Only the systems the role needs.",
    eyebrow: "TOOLS",
    copy: "Workers receive explicit capabilities instead of broad access to enterprise applications and data.",
    detail: "3 governed capabilities",
    items: ["Read vendor documents", "Query policy service", "Create review record"],
    icon: Wrench,
  },
  permissions: {
    title: "Access is part of the role design.",
    eyebrow: "PERMISSIONS",
    copy: "Data scopes, action scopes, and environment boundaries are defined before execution begins.",
    detail: "Scoped to Vendor Ops",
    items: ["Internal data only", "No direct ERP write", "Read-only finance context"],
    icon: KeyRound,
  },
  policies: {
    title: "Autonomy lives inside policy.",
    eyebrow: "POLICIES",
    copy: "Rules decide when a worker may act, when it must request review, and when execution is blocked entirely.",
    detail: "AP-04 · Vendor onboarding",
    items: ["<$25K may proceed", ">$25K requires Finance", "Missing evidence blocks run"],
    icon: ShieldCheck,
  },
  supervisor: {
    title: "Every worker has an escalation path.",
    eyebrow: "SUPERVISOR",
    copy: "Supervisors coordinate assignments, resolve ambiguity, and route high-impact decisions to the right human owner.",
    detail: "Aegis Runtime → Finance Ops",
    items: ["Task delegation", "Exception routing", "Human escalation"],
    icon: GitBranch,
  },
};

const flowSteps = [
  { id: "01", label: "Requirement", owner: "Business Analyst", status: "done" },
  { id: "02", label: "Evidence review", owner: "Compliance", status: "done" },
  { id: "03", label: "Risk score", owner: "Finance", status: "live" },
  { id: "04", label: "Approval", owner: "Human owner", status: "review" },
  { id: "05", label: "ERP create", owner: "Operations", status: "queued" },
];

function WorkerNode({ id, active, onClick, className = "" }: { id: WorkerKey; active: boolean; onClick: (id: WorkerKey) => void; className?: string }) {
  const w = workers[id];
  return (
    <motion.button
      type="button"
      className={`wf10-worker-node ${className} ${active ? "is-active" : ""}`}
      onClick={() => onClick(id)}
      whileHover={{ y: -3 }}
      transition={{ duration: .35, ease: [0.16, 1, 0.3, 1] }}
    >
      <span className={`wf10-avatar ${id === "human" ? "human" : ""}`}>{id === "human" ? <UserCheck size={16}/> : w.short}</span>
      <span className="wf10-worker-copy"><small>{w.name}</small><b>{w.role}</b></span>
      <em className={w.stateClass}><i />{w.state}</em>
    </motion.button>
  );
}

function WorkforceHeroVisual() {
  const [active, setActive] = useState<WorkerKey>("finance");
  const current = workers[active];

  return (
    <div className="wf10-hero-console">
      <div className="wf10-console-head">
        <span><i /> AEGIS / WORKFORCE RUNTIME</span>
        <em>5 MEMBERS · LIVE</em>
      </div>
      <div className="wf10-topology">
        <svg className="wf10-topology-lines" viewBox="0 0 760 510" preserveAspectRatio="none" aria-hidden="true">
          <path d="M380 248 L150 120"/><path d="M380 248 L610 120"/><path d="M380 248 L150 390"/><path d="M380 248 L610 390"/>
          <path className="soft" d="M150 120 Q380 40 610 120"/><path className="soft" d="M150 390 Q380 470 610 390"/>
        </svg>

        <div className="wf10-topology-memory"><BrainCircuit size={13}/><span>Shared organization memory</span><b>24 sources</b></div>
        <div className="wf10-supervisor">
          <span className="ring r1"/><span className="ring r2"/>
          <span className="icon"><GitBranch size={20}/></span>
          <small>SUPERVISOR</small><b>Aegis Runtime</b><em>team fit 94%</em>
        </div>

        <WorkerNode id="compliance" active={active === "compliance"} onClick={setActive} className="n1"/>
        <WorkerNode id="finance" active={active === "finance"} onClick={setActive} className="n2"/>
        <WorkerNode id="operations" active={active === "operations"} onClick={setActive} className="n3"/>
        <WorkerNode id="human" active={active === "human"} onClick={setActive} className="n4"/>

        <AnimatePresence mode="wait">
          <motion.div key={active} className="wf10-worker-inspector" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: .28 }}>
            <div className="wf10-inspector-title"><span className={`wf10-avatar ${active === "human" ? "human" : ""}`}>{active === "human" ? <UserCheck size={15}/> : current.short}</span><div><small>SELECTED MEMBER</small><b>{current.role}</b></div><em className={current.stateClass}><i/>{current.state}</em></div>
            <div className="wf10-inspector-grid"><span><small>MEMORY</small><b>{current.memory}</b></span><span><small>AUTONOMY</small><b>{current.autonomy}</b></span></div>
            <div className="wf10-tool-row">{current.tools.map(tool => <span key={tool}>{tool}</span>)}</div>
          </motion.div>
        </AnimatePresence>
      </div>
      <div className="wf10-console-foot"><span><i/> Supervisor coordinating</span><span>3 specialists</span><span>1 human checkpoint</span><span>6 scoped tools</span></div>
    </div>
  );
}

function AnatomyStudio() {
  const [active, setActive] = useState<AnatomyKey>("role");
  const current = anatomy[active];
  const Icon = current.icon;

  return (
    <div className="wf10-anatomy-shell">
      <div className="wf10-anatomy-tabs">
        {(Object.keys(anatomy) as AnatomyKey[]).map(key => {
          const item = anatomy[key];
          const ItemIcon = item.icon;
          return <button key={key} className={active === key ? "active" : ""} onClick={() => setActive(key)}><ItemIcon size={14}/><span>{item.eyebrow}</span><ChevronRight size={13}/></button>;
        })}
      </div>
      <AnimatePresence mode="wait">
        <motion.div key={active} className="wf10-anatomy-main" initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -8 }} transition={{ duration: .32, ease: [0.16, 1, 0.3, 1] }}>
          <div className="wf10-anatomy-copy"><span><Icon size={15}/>{current.eyebrow}</span><h3>{current.title}</h3><p>{current.copy}</p></div>
          <div className="wf10-profile-card">
            <div className="wf10-profile-head"><span className="wf10-avatar">CO</span><div><small>DIGITAL EMPLOYEE</small><b>Compliance Specialist</b></div><em><i/> ACTIVE</em></div>
            <div className="wf10-profile-highlight"><small>{current.eyebrow}</small><b>{current.detail}</b></div>
            <div className="wf10-profile-list">{current.items.map((item, idx) => <div key={item}><span>0{idx + 1}</span><b>{item}</b><CheckCircle2 size={14}/></div>)}</div>
            <div className="wf10-profile-context"><span><small>MEMORY</small><b>Vendor policy + precedents</b></span><span><small>TOOLS</small><b>Policy DB · Docs · Risk API</b></span><span><small>SUPERVISOR</small><b>Aegis Runtime</b></span></div>
            <div className="wf10-profile-foot"><span>Role ID · WORKER-CO-04</span><b>Bounded by policy</b></div>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

function TeamComposer() {
  const [running, setRunning] = useState(false);
  const [selected, setSelected] = useState(0);
  const team = useMemo(() => [
    ["Compliance", "Evidence + policy", "3 tools"],
    ["Finance", "Risk + approval", "2 tools"],
    ["Operations", "ERP execution", "3 tools"],
    ["Human owner", "Escalation", "1 gate"],
  ], []);

  return (
    <div className="wf10-composer">
      <div className="wf10-composer-head"><span><i/> TEAM COMPOSER</span><em>{running ? "COMPOSING..." : "PLAN READY"}</em></div>
      <div className="wf10-composer-grid">
        <div className="wf10-brief-column">
          <small>BUSINESS REQUIREMENT</small>
          <h3>“Onboard vendors, score financial risk, route exceptions, and create approved suppliers in ERP.”</h3>
          <div className="wf10-brief-tags"><span>ERP</span><span>Compliance</span><span>Finance</span><span>Human approval</span></div>
          <button onClick={() => { setRunning(true); window.setTimeout(() => setRunning(false), 1200); }}><Sparkles size={14}/>{running ? "Composing workforce" : "Compose workforce"}<ArrowRight size={14}/></button>
        </div>
        <div className="wf10-team-column">
          <div className="wf10-team-title"><span>RECOMMENDED TEAM</span><b>4 members</b></div>
          <div className="wf10-team-list">
            {team.map((member, idx) => <motion.button key={member[0]} className={selected === idx ? "active" : ""} onClick={() => setSelected(idx)} animate={running ? { y: [0, -3, 0] } : {}} transition={{ delay: idx * .08, duration: .5 }}><span>0{idx + 1}</span><div><b>{member[0]}</b><small>{member[1]}</small></div><em>{member[2]}</em><ChevronRight size={13}/></motion.button>)}
          </div>
          <div className="wf10-team-insight"><Fingerprint size={14}/><div><small>WHY THIS TEAM</small><b>{selected === 0 ? "Vendor policy requires evidence verification before any system write." : selected === 1 ? "Risk scoring controls the approval path and spending threshold." : selected === 2 ? "Only the Operations role receives the approved ERP write capability." : "High-value exceptions must retain a human decision owner."}</b></div></div>
        </div>
      </div>
      <div className="wf10-composer-foot"><span><i/> Skills matched</span><span>Memory attached</span><span>Permissions scoped</span><span>Supervisor assigned</span></div>
    </div>
  );
}

function RuntimeChoreography() {
  return (
    <div className="wf10-runtime-card">
      <div className="wf10-runtime-head"><span><i/> RUN #2841 · VENDOR ONBOARDING</span><em>67% COMPLETE</em></div>
      <div className="wf10-runtime-progress"><i style={{ width: "67%" }}/></div>
      <div className="wf10-runtime-steps">
        {flowSteps.map((step, index) => <div key={step.id} className={`wf10-runtime-step ${step.status}`}><span className="num">{step.id}</span><div><small>{step.owner}</small><b>{step.label}</b></div><em>{step.status === "done" ? "DONE" : step.status === "live" ? "RUNNING" : step.status === "review" ? "HUMAN REVIEW" : "QUEUED"}</em>{index < flowSteps.length - 1 && <i className="connector"/>}</div>)}
      </div>
      <div className="wf10-runtime-trace"><span><CheckCircle2 size={13}/> State preserved</span><span><ShieldCheck size={13}/> Policy evaluated</span><span><UserCheck size={13}/> 1 human checkpoint</span><span><Database size={13}/> 2 systems touched</span></div>
    </div>
  );
}

function ControlMatrix() {
  const [mode, setMode] = useState<"auto" | "review" | "approve">("approve");
  const info = {
    auto: ["AUTO", "Low-risk work executes independently inside pre-approved policy boundaries.", "No human wait", "Customer email"],
    review: ["REVIEW", "The worker completes the action, then surfaces the result for human oversight.", "Post-action review", "Contract summary"],
    approve: ["APPROVE", "The worker prepares the action and waits for a human decision before execution.", "Pre-execution gate", "ERP vendor create"],
  }[mode];
  return (
    <div className="wf10-control-shell">
      <div className="wf10-control-modes">{(["auto", "review", "approve"] as const).map(value => <button key={value} className={mode === value ? "active" : ""} onClick={() => setMode(value)}><span>{value.toUpperCase()}</span><small>{value === "auto" ? "Independent" : value === "review" ? "Visible" : "Authorized"}</small></button>)}</div>
      <AnimatePresence mode="wait"><motion.div key={mode} className="wf10-control-main" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: .3 }}>
        <div className="wf10-control-copy"><span><ShieldCheck size={15}/> AUTONOMY MODE</span><h3>{info[0]}</h3><p>{info[1]}</p><div><small>CONTROL</small><b>{info[2]}</b></div></div>
        <div className="wf10-policy-card"><div className="wf10-policy-head"><span><ShieldCheck size={14}/><div><small>POLICY PACK</small><b>WORKFORCE_AUTONOMY</b></div></span><em>{mode === "approve" ? "GATE ACTIVE" : "POLICY ACTIVE"}</em></div><div className="wf10-policy-row"><span>Action</span><b>{info[3]}</b></div><div className="wf10-policy-row"><span>Worker</span><b>{mode === "auto" ? "Communication Specialist" : mode === "review" ? "Contract Analyst" : "Operations Specialist"}</b></div><div className="wf10-policy-row"><span>Boundary</span><b>{mode === "approve" ? "Finance approval required" : "Within assigned role"}</b></div><div className={`wf10-policy-result ${mode}`}><span>{mode === "approve" ? <UserCheck size={14}/> : <BadgeCheck size={14}/>}</span><div><small>{mode === "approve" ? "HUMAN OWNER" : "DECISION"}</small><b>{mode === "approve" ? "Finance Ops" : "Execution permitted"}</b></div><em>{mode === "approve" ? "WAITING" : "READY"}</em></div></div>
      </motion.div></AnimatePresence>
    </div>
  );
}

const roleCards = [
  { icon: ShieldCheck, title: "Compliance Specialist", text: "Reusable across onboarding, procurement, audits, and vendor reviews.", workflows: ["Vendor onboarding", "Policy review", "Audit prep"] },
  { icon: CircleDollarSign, title: "Finance Specialist", text: "One governed role can score risk and support approval decisions across many workflows.", workflows: ["Vendor onboarding", "Expense review", "Credit checks"] },
  { icon: Database, title: "Operations Specialist", text: "A single system-action role can execute approved updates across operational workflows.", workflows: ["ERP updates", "Account setup", "Case resolution"] },
];

export function WorkforcePageV10() {
  return (
    <div className="wf10-page">
      <section className="wf10-hero">
        <div className="wf10-hero-copy">
          <div className="wf10-eyebrow"><UsersRound size={15}/><span>ORCHESTRATE / AI WORKFORCE</span></div>
          <motion.h1 initial={{ opacity: 0, y: 28 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .8, ease: [0.16, 1, 0.3, 1] }}>Build a workforce.<br/><span>Not a pile of agents.</span></motion.h1>
          <motion.p initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .7, delay: .12 }}>AegisOS turns specialist AI workers into an operating team — each with a job, context, tools, permissions, policies, a supervisor, and a clear path to human judgment.</motion.p>
          <motion.div className="wf10-actions" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: .25 }}><a href="#workforce-demo" className="v3-solid-button">Book a workforce demo <ArrowUpRight size={14}/></a><Link href="#anatomy">Explore the system <ArrowRight size={14}/></Link></motion.div>
          <div className="wf10-hero-proof"><span><i/> Role-based</span><span><i/> Policy-bounded</span><span><i/> Reusable</span></div>
        </div>
        <motion.div className="wf10-hero-visual" initial={{ opacity: 0, scale: .97, y: 22 }} animate={{ opacity: 1, scale: 1, y: 0 }} transition={{ duration: .9, delay: .08, ease: [0.16, 1, 0.3, 1] }}><WorkforceHeroVisual/></motion.div>
      </section>

      <section className="wf10-positioning">
        <div className="wf10-section-kicker"><span>01 / THE SHIFT</span><p>Move from disposable agents to durable operating roles.</p></div>
        <div className="wf10-position-grid">
          <div className="wf10-position-copy"><h2>Agents complete tasks.<br/><span>A workforce owns work.</span></h2><p>AegisOS gives AI workers the operating structure normally missing from agent deployments: role clarity, supervision, permissions, memory, and repeatable responsibility.</p></div>
          <div className="wf10-compare-card"><div className="assistant"><span>GENERIC AGENT</span><div><small>Prompt</small><ArrowRight/><small>Tool call</small><ArrowRight/><small>Response</small></div><p>Context and responsibility end with the task.</p></div><div className="workforce"><span>AEGISOS WORKER</span><div><small>Role</small><ArrowRight/><small>Context</small><ArrowRight/><small>Execution</small><ArrowRight/><small>Outcome</small></div><p><i/> Persistent role · governed capabilities · supervised execution</p></div></div>
        </div>
      </section>

      <section className="wf10-anatomy" id="anatomy">
        <div className="wf10-section-head"><span>02 / DIGITAL EMPLOYEE ANATOMY</span><h2>Everything a real role needs to operate.</h2><p>A worker is more than a model and a system prompt. Select each layer to inspect how AegisOS defines the role.</p></div>
        <AnatomyStudio/>
      </section>

      <section className="wf10-compose-section">
        <div className="wf10-section-kicker"><span>03 / COMPOSE A TEAM</span><p>Start with the work. AegisOS determines the workforce around it.</p></div>
        <div className="wf10-compose-title"><h2>The team forms around the requirement.</h2><p>Business context determines which specialists are needed, what each role can access, and where human authority belongs.</p></div>
        <TeamComposer/>
      </section>

      <section className="wf10-runtime-section">
        <div className="wf10-runtime-copy"><span>04 / COORDINATED EXECUTION</span><h2>Specialists become one continuous run.</h2><p>Workers do not operate as isolated chatbots. AegisOS coordinates state, dependencies, system actions, policy checks, and human decisions as one execution runtime.</p><Link href="/product/workflows">Explore Workflow Engine <ArrowRight size={14}/></Link></div>
        <RuntimeChoreography/>
      </section>

      <section className="wf10-control-section">
        <div className="wf10-section-head"><span>05 / SUPERVISION + CONTROL</span><h2>Autonomy is assigned.<br/><span>Authority stays explicit.</span></h2><p>Every role can operate with a different autonomy model based on business impact, policy, and human accountability.</p></div>
        <ControlMatrix/>
      </section>

      <section className="wf10-reuse-section">
        <div className="wf10-section-kicker"><span>06 / REUSABLE WORKFORCE</span><p>Build the role once. Deploy it wherever the organization needs that responsibility.</p></div>
        <div className="wf10-reuse-head"><h2>Your workforce compounds.</h2><p>Roles keep their approved skills, tools, memory scopes, and policies while participating in many different workflows.</p></div>
        <div className="wf10-role-grid">{roleCards.map(({ icon: Icon, title, text, workflows }, idx) => <motion.article key={title} initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: .25 }} transition={{ delay: idx * .06, duration: .65, ease: [0.16, 1, 0.3, 1] }}><div className="wf10-role-head"><span><Icon size={16}/></span><em>ROLE 0{idx + 1}</em></div><h3>{title}</h3><p>{text}</p><div className="wf10-role-workflows">{workflows.map((workflow, i) => <span key={workflow}><i>{i + 1}</i>{workflow}<CheckCircle2 size={12}/></span>)}</div><Link href="/platform">View in platform <ArrowUpRight size={13}/></Link></motion.article>)}</div>
      </section>

      <section className="wf10-metrics">
        <div><span>ROLE</span><b>Clear responsibility</b><p>Define ownership before autonomy.</p></div><div><span>TOOLS</span><b>Approved capabilities</b><p>Expose only what the role needs.</p></div><div><span>MEMORY</span><b>Persistent context</b><p>Carry organizational knowledge into every run.</p></div><div><span>POLICY</span><b>Bounded autonomy</b><p>Make review and authority part of execution.</p></div>
      </section>

      <section className="wf10-final" id="workforce-demo">
        <div><span>AEGISOS / AI WORKFORCE</span><h2>Build the operating team behind your AI workflows.</h2><p>Bring the business role. AegisOS handles the context, capabilities, supervision, control, and runtime around it.</p></div>
        <div className="wf10-final-actions"><a href="mailto:hello@aegisos.ai">Book a demo <ArrowUpRight size={15}/></a><Link href="/platform">Explore AegisOS <ArrowRight size={15}/></Link></div>
        <div className="wf10-final-orbit" aria-hidden="true"><span className="o1"/><span className="o2"/><span className="core"><UsersRound size={23}/></span></div>
      </section>
    </div>
  );
}

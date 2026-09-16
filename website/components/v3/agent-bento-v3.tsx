"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowUpRight,
  BrainCircuit,
  Check,
  CircleDollarSign,
  Code2,
  Database,
  FileText,
  GitBranch,
  Key,
  LockKeyhole,
  Network,
  RefreshCcw,
  ShieldCheck,
  Target,
  Wrench,
} from "lucide-react";

const STAGES = [
  { n: "01", label: "BA Agent" },
  { n: "02", label: "Refinement" },
  { n: "03", label: "Frappe" },
  { n: "04", label: "Project" },
  { n: "05", label: "Functional" },
  { n: "06", label: "Technical" },
];

function ArtHeader({ label, state, tone = "blue" }: { label: string; state: string; tone?: "blue" | "teal" }) {
  return (
    <div className={`ap-ar-head ap-tone-${tone}`}>
      <span className="ap-ar-live"><i /></span>
      <b>{label}</b>
      <em>{state}</em>
    </div>
  );
}

function BAAgentArtifact() {
  return (
    <div className="ap-ar">
      <ArtHeader label="BUSINESS ANALYST AGENT" state="DISCOVERY" />
      <div className="ap-ar-body ap-ba">
        <div className="ap-ba-chat">
          <div className="ap-bubble ap-bubble-user">
            <small>USER</small>
            <p>Onboard vendors, score risk, approve, then create suppliers in ERP.</p>
          </div>
          <div className="ap-bubble ap-bubble-agent">
            <small>BA AGENT</small>
            <p>Mapped 3 roles, 4 systems and 2 control points. Generating the flow…</p>
          </div>
        </div>
        <div className="ap-ba-flow">
          <div className="ap-node is-start"><FileText size={11} /><b>Brief</b></div>
          <span className="ap-wire" />
          <div className="ap-node"><ShieldCheck size={11} /><b>Compliance</b></div>
          <span className="ap-wire" />
          <div className="ap-node"><CircleDollarSign size={11} /><b>Finance</b></div>
          <span className="ap-wire" />
          <div className="ap-node is-end"><Database size={11} /><b>ERP</b></div>
        </div>
      </div>
      <div className="ap-ar-foot">
        <span>Requirements captured</span>
        <span>3 roles · 4 systems</span>
        <span className="ok">Flow diagram ready</span>
      </div>
    </div>
  );
}

function RefinementArtifact() {
  return (
    <div className="ap-ar">
      <ArtHeader label="REFINEMENT LOOP" state="ITERATING" tone="teal" />
      <div className="ap-ar-body ap-loop">
        <div className="ap-ring">
          <svg viewBox="0 0 120 120" aria-hidden="true">
            <circle className="ap-ring-track" cx="60" cy="60" r="52" />
            <circle className="ap-ring-arc" cx="60" cy="60" r="52" />
          </svg>
          <div className="ap-ring-core">
            <RefreshCcw size={15} />
            <b>Iter 03</b>
            <small>refining</small>
          </div>
        </div>
        <div className="ap-versions">
          <span className="is-done">v1<Check size={9} /></span>
          <span className="is-done">v2<Check size={9} /></span>
          <span className="is-live">v3<i /></span>
        </div>
        <div className="ap-diff">
          <span className="ap-diff-add">+2 refinements</span>
          <span className="ap-diff-note">awaiting your review</span>
        </div>
      </div>
      <div className="ap-ar-foot">
        <span>Feedback applied</span>
        <span>Code + logic</span>
        <span className="ok">User in control</span>
      </div>
    </div>
  );
}

function FrappeArtifact() {
  return (
    <div className="ap-ar">
      <ArtHeader label="FRAPPE AGENT" state="CONNECTING" tone="teal" />
      <div className="ap-ar-body ap-frappe">
        <div className="ap-cred">
          <span className="ap-cred-icon"><Key size={12} /></span>
          <div className="ap-cred-copy">
            <small>FRAPPE CREDENTIALS</small>
            <b>•••••••••••••••</b>
          </div>
          <em className="ap-cred-chip"><LockKeyhole size={9} />SECURE</em>
        </div>
        <div className="ap-link">
          <span className="ap-link-line"><i /></span>
          <em>backend linked</em>
        </div>
        <div className="ap-portal">
          <div className="ap-portal-bar">
            <span className="ap-portal-dots"><i /><i /><i /></span>
            <b>frappe / project</b>
            <em><i />LIVE</em>
          </div>
          <div className="ap-portal-rows">
            <span><i /><b>Vendor onboarding</b><em>active</em></span>
            <span><i /><b>Compliance pack</b><em>ready</em></span>
            <span><i /><b>Supplier form</b><em>live</em></span>
          </div>
        </div>
      </div>
      <div className="ap-ar-foot">
        <span>Credentials secured</span>
        <span>Project provisioned</span>
        <span className="ok">Portal interactive</span>
      </div>
    </div>
  );
}

const MILESTONES = [
  { t: "Requirements", s: "Done", p: 100, state: "done" },
  { t: "Flow diagram", s: "Done", p: 100, state: "done" },
  { t: "Functionals", s: "Building", p: 64, state: "live" },
  { t: "Technical design", s: "Queued", p: 0, state: "idle" },
];

function ProjectArtifact() {
  return (
    <div className="ap-ar">
      <ArtHeader label="PROJECT AGENT" state="ON TRACK" />
      <div className="ap-ar-body ap-project">
        <div className="ap-project-top">
          <div>
            <small>SCOPE COVERAGE</small>
            <b>18 of 24 requirements</b>
          </div>
          <span className="ap-gauge"><b>75</b><small>%</small></span>
        </div>
        <div className="ap-milestones">
          {MILESTONES.map((m, i) => (
            <div className={`ap-mile is-${m.state}`} key={m.t}>
              <span className="ap-mile-mark">
                {m.state === "done" ? <Check size={9} /> : <i style={{ animationDelay: `${i * 0.18}s` }} />}
              </span>
              <div className="ap-mile-copy">
                <b>{m.t}</b>
                <span className="ap-mile-bar"><i style={{ width: `${m.p}%` }} /></span>
              </div>
              <em>{m.s}</em>
            </div>
          ))}
        </div>
      </div>
      <div className="ap-ar-foot">
        <span>Scope managed</span>
        <span>Milestones tracked</span>
        <span className="ok">Quality verified</span>
      </div>
    </div>
  );
}

const FEATURES = [
  { t: "Core logic", p: 92 },
  { t: "User actions", p: 78 },
  { t: "Edge cases", p: 86 },
];

function FunctionalArtifact() {
  return (
    <div className="ap-ar">
      <ArtHeader label="FUNCTIONAL AGENT" state="MAPPING" />
      <div className="ap-ar-body ap-functional">
        <div className="ap-tree">
          <div className="ap-tree-root"><Wrench size={11} /><b>Feature set</b></div>
          <svg className="ap-tree-links" viewBox="0 0 260 46" preserveAspectRatio="none" aria-hidden="true">
            <path d="M130 0 V14" />
            <path d="M130 14 H34 V46" />
            <path d="M130 14 H130 V46" />
            <path d="M130 14 H226 V46" />
          </svg>
          <div className="ap-tree-leaves">
            <span><i />Inputs</span>
            <span><i />Actions</span>
            <span><i />Outputs</span>
          </div>
        </div>
        <div className="ap-bars">
          {FEATURES.map((f, i) => (
            <div className="ap-bar-row" key={f.t}>
              <span>{f.t}</span>
              <span className="ap-bar"><i style={{ width: `${f.p}%`, animationDelay: `${i * 0.16}s` }} /></span>
              <em>{f.p}%</em>
            </div>
          ))}
        </div>
      </div>
      <div className="ap-ar-foot">
        <span>Features defined</span>
        <span>Logic mapped</span>
        <span className="ok">Functional diagram ready</span>
      </div>
    </div>
  );
}

const STACK = [
  { t: "API", s: "Endpoints", icon: Network, meta: "24 routes" },
  { t: "Database", s: "Schema", icon: Database, meta: "12 tables" },
  { t: "Codebase", s: "Implementation", icon: Code2, meta: "deployed" },
];

function TechnicalArtifact() {
  return (
    <div className="ap-ar">
      <ArtHeader label="TECHNICAL AGENT" state="ARCHITECTING" />
      <div className="ap-ar-body ap-technical">
        <div className="ap-stack">
          {STACK.map(({ t, s, icon: Icon, meta }, i) => (
            <div className="ap-layer" key={t} style={{ animationDelay: `${i * 0.14}s` }}>
              <span className="ap-layer-icon"><Icon size={12} /></span>
              <div className="ap-layer-copy">
                <small>{s.toUpperCase()}</small>
                <b>{t}</b>
              </div>
              <em>{meta}</em>
            </div>
          ))}
        </div>
        <div className="ap-tech-foot">
          <span><GitBranch size={10} />dependency graph resolved</span>
          <span className="ok"><Check size={10} />implementation ready</span>
        </div>
      </div>
      <div className="ap-ar-foot">
        <span>Schema designed</span>
        <span>Endpoints mapped</span>
        <span className="ok">Technical diagram ready</span>
      </div>
    </div>
  );
}

const AGENTS = [
  { n: "01", label: "BA Agent", eyebrow: "DISCOVER", icon: BrainCircuit, body: "Discuss your project, gather requirements, and generate the system flow diagram.", artifact: <BAAgentArtifact /> },
  { n: "02", label: "Refinement Loop", eyebrow: "REFINE", icon: RefreshCcw, body: "Continuous iteration loop that updates code and logic until it matches your vision.", artifact: <RefinementArtifact /> },
  { n: "03", label: "Frappe Agent", eyebrow: "CONNECT", icon: Key, body: "Securely connect Frappe, provision your project, and enable the interactive portal.", artifact: <FrappeArtifact /> },
  { n: "04", label: "Project Agent", eyebrow: "MANAGE", icon: Target, body: "End-to-end oversight of requirements, milestones, and deliverables.", artifact: <ProjectArtifact /> },
  { n: "05", label: "Functional Agent", eyebrow: "BUILD", icon: Wrench, body: "Design functionalities, map logic, and generate the functional diagram.", artifact: <FunctionalArtifact /> },
  { n: "06", label: "Technical Agent", eyebrow: "ARCHITECT", icon: Code2, body: "Create the technical diagram — database schemas, APIs, and system architecture.", artifact: <TechnicalArtifact /> },
];

export function AgentBentoV3() {
  return (
    <section className="ap-section">
      <div className="ap-head">
        <div className="ap-kicker">
          <span>03 / THE AGENT PIPELINE</span>
          <p>Six specialized agents that take your project from idea to implementation.</p>
        </div>
        <div className="ap-title">
          <h2>One pipeline.<br /><span>Six specialist agents.</span></h2>
          <div className="ap-title-meta">
            <p>Every stage hands a finished artifact to the next — requirement to running system.</p>
            <Link href="/platform">Explore the system <ArrowUpRight size={14} /></Link>
          </div>
        </div>
      </div>

      <div className="ap-spine" aria-hidden="true">
        <span className="ap-spine-rail" />
        {STAGES.map((s, i) => (
          <div className="ap-spine-node" key={s.n}>
            <span className="ap-spine-dot" style={{ animationDelay: `${i * 0.12}s` }} />
            <b>{s.n}</b>
            <small>{s.label}</small>
          </div>
        ))}
      </div>

      <div className="ap-grid">
        {AGENTS.map(({ n, label, eyebrow, icon: Icon, body, artifact }, index) => (
          <motion.article
            className="ap-card"
            key={label}
            initial={{ opacity: 0, y: 26 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.15 }}
            transition={{ duration: 0.68, delay: (index % 3) * 0.07, ease: [0.16, 1, 0.3, 1] }}
            onMouseMove={(event) => {
              const r = event.currentTarget.getBoundingClientRect();
              event.currentTarget.style.setProperty("--mx", `${event.clientX - r.left}px`);
              event.currentTarget.style.setProperty("--my", `${event.clientY - r.top}px`);
            }}
          >
            <div className="ap-card-top">
              <span className="ap-card-n">{n}</span>
              <span className="ap-card-eyebrow"><Icon size={13} />{eyebrow}</span>
            </div>
            {artifact}
            <div className="ap-card-copy">
              <h3>{label}</h3>
              <p>{body}</p>
            </div>
          </motion.article>
        ))}
      </div>
    </section>
  );
}

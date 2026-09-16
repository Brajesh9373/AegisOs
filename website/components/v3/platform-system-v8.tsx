"use client";

import { useEffect, useLayoutEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  BrainCircuit,
  Check,
  Code2,
  Database,
  FileText,
  GitBranch,
  Key,
  LockKeyhole,
  Network,
  RefreshCcw,
  ScanSearch,
  ShieldCheck,
  Target,
  UserCheck,
  Wrench,
} from "lucide-react";

function SurfaceHeader({ label, status = "LIVE" }: { label: string; status?: string }) {
  return (
    <div className="sys7-surface-head">
      <div>
        <span className="sys7-live-dot" />
        <b>{label}</b>
      </div>
      <em>{status}</em>
    </div>
  );
}

function MetaStrip({ left, middle, right }: { left: string; middle: string; right: string }) {
  return (
    <div className="sys7-meta-strip">
      <span><i />{left}</span>
      <span>{middle}</span>
      <span>{right}</span>
    </div>
  );
}

/* ---------------- 01 · BA AGENT ---------------- */
function BAAgentDiagram() {
  return (
    <div className="sys7-diagram sys7-understand">
      <SurfaceHeader label="BUSINESS ANALYST AGENT" status="REQUIREMENTS GATHERING" />
      <div className="sys7-canvas pp-ba">
        <div className="pp-brief">
          <div className="pp-kicker"><FileText size={13} />PROJECT DISCOVERY</div>
          <p>
            “Discuss the <mark>project scope</mark>, identify key <mark>stakeholders</mark>,
            and generate a detailed <mark>Flow Diagram</mark> for the entire system lifecycle.”
          </p>
          <div className="pp-thread">
            <span className="is-user"><b>User</b>Six approval steps, two systems.</span>
            <span className="is-agent"><b>BA Agent</b>Mapped to 3 roles and 2 control gates.</span>
          </div>
          <div className="pp-panel-foot"><span>Interactive chat</span><b>01</b></div>
        </div>

        <div className="pp-rail">
          <span className="pp-rail-node is-active">CHAT</span>
          <span className="pp-rail-node">ANALYZE</span>
          <span className="pp-rail-node">FLOW DIAGRAM</span>
          <i className="pp-rail-scan" />
        </div>

        <div className="pp-graph">
          <div className="pp-graph-head">
            <div>
              <small>GENERATED ASSET</small>
              <b>System Flow Diagram</b>
            </div>
            <span className="pp-conf"><b>100</b><small>%</small></span>
          </div>
          <div className="pp-graph-body">
            <svg className="pp-graph-wires" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
              <path d="M50 12 V30" />
              <path d="M25 30 H75" />
              <path d="M25 30 V46" />
              <path d="M75 30 V46" />
              <path d="M25 58 V74" />
              <path d="M75 58 V74" />
              <path d="M25 74 H75" />
              <path d="M50 74 V88" />
            </svg>
            <span className="pp-gnode is-start" style={{ left: "50%", top: "8%" }}><FileText size={11} />Brief</span>
            <span className="pp-gnode" style={{ left: "25%", top: "52%" }}><ShieldCheck size={11} />Compliance</span>
            <span className="pp-gnode" style={{ left: "75%", top: "52%" }}><Target size={11} />Finance</span>
            <span className="pp-gnode is-end" style={{ left: "50%", top: "92%" }}><Database size={11} />ERP</span>
          </div>
        </div>
      </div>
      <MetaStrip left="Requirements captured" middle="3 roles · 4 systems" right="Flow diagram created" />
    </div>
  );
}

/* ---------------- 02 · REFINEMENT LOOP ---------------- */
function LoopDiagram() {
  return (
    <div className="sys7-diagram sys7-orchestrate">
      <SurfaceHeader label="ITERATION LOOP" status="AWAITING USER APPROVAL" />
      <div className="sys7-canvas pp-loop">
        <svg className="pp-loop-wires" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          <path d="M45 44 C 38 52, 26 60, 19 68" />
          <path className="solid" d="M28 74 H 72" />
          <path d="M81 68 C 74 60, 62 52, 55 44" />
        </svg>

        <div className="pp-loop-core">
          <span className="pp-loop-ring r1" />
          <span className="pp-loop-ring r2" />
          <span className="pp-loop-icon"><RefreshCcw size={19} /></span>
          <small>FEEDBACK LOOP</small>
          <b>Continuous Refinement</b>
          <em>User in control</em>
        </div>

        <div className="pp-loop-node is-a" style={{ left: "19%", top: "74%" }}>
          <span className="pp-loop-node-icon"><FileText size={13} /></span>
          <div><small>INPUT</small><b>User Feedback</b></div>
          <em className="is-live">ACTIVE</em>
        </div>

        <div className="pp-loop-node is-b" style={{ left: "81%", top: "74%" }}>
          <span className="pp-loop-node-icon"><Code2 size={13} /></span>
          <div><small>OUTPUT</small><b>Code &amp; Logic</b></div>
          <em>REFINING</em>
        </div>

        <div className="pp-loop-tag"><RefreshCcw size={11} />iteration 03 · refinements applied in place</div>
      </div>
      <MetaStrip left="Continuous updates" middle="Until perfect match" right="User gets exact code" />
    </div>
  );
}

/* ---------------- 03 · FRAPPE AGENT ---------------- */
function FrappeAgentDiagram() {
  return (
    <div className="sys7-diagram sys7-execute">
      <SurfaceHeader label="FRAPPE AGENT" status="CONNECTING BACKEND" />
      <div className="sys7-canvas pp-frappe">
        <div className="pp-frappe-head">
          <div>
            <small>INTEGRATION</small>
            <b>Frappe Framework Setup</b>
          </div>
          <span className="pp-online"><i />online</span>
        </div>

        <div className="pp-lanes">
          <div className="pp-lane">
            <div className="pp-lane-label"><span><Key size={13} /></span><div><b>CREDENTIALS</b><small>secure</small></div></div>
            <div className="pp-lane-track">
              <div className="pp-event is-done" style={{ left: "3%", width: "26%" }}>
                <small>INPUT</small><b>Get user credentials</b><em>SECURE</em>
              </div>
              <div className="pp-event is-done" style={{ left: "35%", width: "24%" }}>
                <small>VERIFY</small><b>Authenticate instance</b><em>VERIFIED</em>
              </div>
            </div>
          </div>

          <div className="pp-lane">
            <div className="pp-lane-label"><span><Network size={13} /></span><div><b>PROVISION</b><small>frappe</small></div></div>
            <div className="pp-lane-track">
              <div className="pp-event is-done" style={{ left: "3%", width: "26%" }}>
                <small>SETUP</small><b>Create project</b><em>DONE</em>
              </div>
              <div className="pp-event is-running" style={{ left: "35%", width: "26%" }}>
                <small>CONNECT</small><b>Link backend</b><em>LIVE</em>
              </div>
            </div>
          </div>

          <div className="pp-lane">
            <div className="pp-lane-label"><span><UserCheck size={13} /></span><div><b>INTERACT</b><small>portal</small></div></div>
            <div className="pp-lane-track">
              <div className="pp-event is-live" style={{ left: "35%", width: "28%" }}>
                <small>USER</small><b>Interactive mode</b><em>READY</em>
              </div>
            </div>
          </div>
        </div>

        <div className="pp-frappe-foot">
          <span><LockKeyhole size={11} />credentials never logged</span>
          <span><Check size={11} />portal reachable</span>
        </div>
      </div>
      <MetaStrip left="Frappe connected" middle="Project created" right="Interactive portal live" />
    </div>
  );
}

/* ---------------- 04 · PROJECT AGENT ---------------- */
function ProjectAgentDiagram() {
  return (
    <div className="sys7-diagram sys7-govern">
      <SurfaceHeader label="PROJECT AGENT" status="MANAGING SCOPE" />
      <div className="sys7-canvas pp-project">
        <div className="pp-req">
          <span className="pp-req-icon"><Target size={15} /></span>
          <small>OVERVIEW</small>
          <b>Project Management</b>
          <p>End-to-end requirement tracking</p>
          <div className="pp-req-stats">
            <span><b>24</b><small>requirements</small></span>
            <span><b>18</b><small>fulfilled</small></span>
          </div>
        </div>

        <div className="pp-arrow"><i /><span>›</span></div>

        <div className="pp-scope">
          <div className="pp-scope-head">
            <span><ShieldCheck size={14} /></span>
            <div><small>SCOPE CONTROL</small><b>Requirements Tracker</b></div>
            <em>TRACKING</em>
          </div>
          <div className="pp-scope-rows">
            {[
              ["MILESTONES", "Tracking", "ON TIME", "done"],
              ["DELIVERABLES", "Quality", "VERIFIED", "done"],
              ["CHANGE REQUESTS", "Review", "1 OPEN", "warn"],
              ["SIGNOFF", "Pending", "QUEUED", "idle"],
            ].map(([k, v, s, st], i) => (
              <div className={`pp-scope-row is-${st}`} key={k}>
                <span>0{i + 1}</span>
                <div><small>{k}</small><b>{v}</b></div>
                <em>{s}</em>
              </div>
            ))}
          </div>
        </div>

        <div className="pp-arrow"><i /><span>›</span></div>

        <div className="pp-progress">
          <div className="pp-progress-head"><small>DELIVERY PROGRESS</small><b>75%</b></div>
          <div className="pp-progress-ring">
            <span className="pp-progress-core"><b>18</b><small>of 24</small></span>
          </div>
          <div className="pp-progress-legend">
            <span><i className="is-done" />Complete</span>
            <span><i className="is-live" />In progress</span>
            <span><i />Queued</span>
          </div>
        </div>
      </div>
      <MetaStrip left="Project scope managed" middle="Milestones tracked" right="Quality verified" />
    </div>
  );
}

/* ---------------- 05 · FUNCTIONAL AGENT ---------------- */
function FunctionalAgentDiagram() {
  return (
    <div className="sys7-diagram sys7-observe">
      <SurfaceHeader label="FUNCTIONAL AGENT" status="FEATURE DESIGN" />
      <div className="sys7-canvas pp-functional">
        <div className="pp-kpi-row">
          <div><span><Wrench size={12} /></span><p><small>FEATURES</small><b>Defined</b></p><em>ALL</em></div>
          <div><span><GitBranch size={12} /></span><p><small>DIAGRAM</small><b>Generated</b></p><em>READY</em></div>
          <div><span><ScanSearch size={12} /></span><p><small>EDGE CASES</small><b>Covered</b></p><em>86%</em></div>
          <div><span><Check size={12} /></span><p><small>REVIEW</small><b>Approved</b></p><em>V1.0</em></div>
        </div>

        <div className="pp-tree-panel">
          <div className="pp-panel-title">
            <div><small>ASSET</small><b>Functional Diagram</b></div>
            <span>V1.0</span>
          </div>
          <div className="pp-feature-tree">
            <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
              <path d="M50 6 V26" />
              <path d="M50 26 H16 V46" />
              <path d="M50 26 H50 V46" />
              <path d="M50 26 H84 V46" />
              <path d="M50 64 V84" />
            </svg>
            <span className="pp-fnode is-root" style={{ left: "50%", top: "4%" }}><Wrench size={10} />Feature set</span>
            <span className="pp-fnode" style={{ left: "16%", top: "50%" }}>Inputs</span>
            <span className="pp-fnode" style={{ left: "50%", top: "50%" }}>Actions</span>
            <span className="pp-fnode" style={{ left: "84%", top: "50%" }}>Outputs</span>
            <span className="pp-fnode is-end" style={{ left: "50%", top: "90%" }}>Validated flow</span>
          </div>
        </div>

        <div className="pp-trace-panel">
          <div className="pp-panel-title">
            <div><small>COVERAGE</small><b>Logic mapped</b></div>
            <span>3 branches</span>
          </div>
          <div className="pp-trace-rows">
            {[["CORE LOGIC", 92, "10%"], ["USER ACTIONS", 78, "24%"], ["EDGE CASES", 86, "16%"]].map(([k, p, l]) => (
              <div className="pp-trace-row" key={k as string}>
                <span>{k}</span>
                <span className="pp-trace-bar"><i style={{ width: `${p}%`, marginLeft: `${l}` }} /></span>
                <em>{p}%</em>
              </div>
            ))}
          </div>
        </div>
      </div>
      <MetaStrip left="Functionalities built" middle="Logic mapped" right="Functional diagram ready" />
    </div>
  );
}

/* ---------------- 06 · TECHNICAL AGENT ---------------- */
function TechnicalAgentDiagram() {
  return (
    <div className="sys7-diagram sys7-understand">
      <SurfaceHeader label="TECHNICAL AGENT" status="ARCHITECTURE & CODE" />
      <div className="sys7-canvas pp-technical">
        <div className="pp-tech-left">
          <div className="pp-panel-title">
            <div><small>ARCHITECTURE</small><b>System layers</b></div>
            <span className="pp-conf small"><b>100</b><small>%</small></span>
          </div>
          <div className="pp-layers">
            {[
              { t: "Application", s: "UI + workflows", icon: BrainCircuit, meta: "12 modules" },
              { t: "API", s: "Endpoints mapped", icon: Network, meta: "24 routes" },
              { t: "Database", s: "Schema designed", icon: Database, meta: "12 tables" },
              { t: "Codebase", s: "Implementation", icon: Code2, meta: "deployed" },
            ].map(({ t, s, icon: Icon, meta }, i) => (
              <div className="pp-layer" key={t} style={{ animationDelay: `${i * 0.13}s` }}>
                <span className="pp-layer-icon"><Icon size={14} /></span>
                <div className="pp-layer-copy"><small>{s.toUpperCase()}</small><b>{t}</b></div>
                <em>{meta}</em>
              </div>
            ))}
          </div>
        </div>

        <div className="pp-tech-right">
          <div className="pp-panel-title">
            <div><small>DELIVERABLE</small><b>Technical Diagram</b></div>
            <span>ready</span>
          </div>
          <div className="pp-schema">
            <div className="pp-schema-table">
              <b>vendor</b>
              {["id · uuid", "name · text", "risk_score · int", "status · enum"].map((f) => (
                <span key={f}>{f}</span>
              ))}
            </div>
            <div className="pp-schema-table">
              <b>approval</b>
              {["id · uuid", "vendor_id · fk", "approver · user", "decision · enum"].map((f) => (
                <span key={f}>{f}</span>
              ))}
            </div>
          </div>
          <div className="pp-tech-foot">
            <span><GitBranch size={11} />dependencies resolved</span>
            <span className="ok"><Check size={11} />implementation ready</span>
          </div>
        </div>
      </div>
      <MetaStrip left="Technical architecture" middle="Database schema" right="Technical diagram ready" />
    </div>
  );
}

const layers = [
  {
    n: "01", name: "BA AGENT", title: "Begin with the business intent.", text: "The BA Agent discusses the project with you, gathers requirements, and builds the foundational Flow Diagram for the system.", icon: BrainCircuit,
    visual: <BAAgentDiagram />,
  },
  {
    n: "02", name: "REFINEMENT LOOP", title: "Iterate until it's perfect.", text: "Everything goes into a continuous feedback loop. The system updates code and logic until you get exactly the project you envisioned.", icon: RefreshCcw,
    visual: <LoopDiagram />,
  },
  {
    n: "03", name: "FRAPPE AGENT", title: "Connect the backend operations.", text: "This agent securely gets your Frappe credentials, provisions the project, and links it so you can interact with your new system directly.", icon: Key,
    visual: <FrappeAgentDiagram />,
  },
  {
    n: "04", name: "PROJECT AGENT", title: "End-to-end requirement tracking.", text: "The Project Agent looks entirely after the project's overall requirements, ensuring scope and milestones are strictly managed.", icon: Target,
    visual: <ProjectAgentDiagram />,
  },
  {
    n: "05", name: "FUNCTIONAL AGENT", title: "Define the core functionalities.", text: "Works purely on the functional logic of the project, mapping out user actions and creating the comprehensive Functional Diagram.", icon: Wrench,
    visual: <FunctionalAgentDiagram />,
  },
  {
    n: "06", name: "TECHNICAL AGENT", title: "Build the robust architecture.", text: "Translates functional requirements into the Technical Diagram, designing the database schemas, APIs, and looking after all technical aspects.", icon: Code2,
    visual: <TechnicalAgentDiagram />,
  },
];

/* GSAP pinning wraps the section in a `pin-spacer`, moving it out of the parent
   React believes it owns. Layout-effect cleanup runs BEFORE React removes nodes,
   so ctx.revert() restores the DOM first and removeChild() stays valid. */
const useIsomorphicLayoutEffect = typeof window !== "undefined" ? useLayoutEffect : useEffect;

export function PlatformSystemV8() {
  const section = useRef<HTMLElement>(null);
  const track = useRef<HTMLDivElement>(null);

  useIsomorphicLayoutEffect(() => {
    gsap.registerPlugin(ScrollTrigger);
    const ctx = gsap.context(() => {
      const panels = gsap.utils.toArray<HTMLElement>(".v3-platform-panel");
      const mm = gsap.matchMedia();
      mm.add("(min-width: 900px)", () => {
        gsap.set(panels, { force3D: true, willChange: "transform" });
        const tween = gsap.to(panels, {
          xPercent: -100 * (panels.length - 1),
          ease: "none",
          force3D: true,
          scrollTrigger: {
            trigger: section.current,
            pin: true,
            scrub: 0.72,
            anticipatePin: 1,
            invalidateOnRefresh: true,
            fastScrollEnd: true,
            end: () => `+=${window.innerWidth * (panels.length - 1) * 1.08}`,
            snap: {
              snapTo: 1 / (panels.length - 1),
              duration: { min: 0.22, max: 0.48 },
              delay: 0.03,
              ease: "power3.out",
            },
            onUpdate: (self) => section.current?.style.setProperty("--system-progress", `${self.progress * 100}%`),
          },
        });
        return () => tween.kill();
      });
      return () => mm.revert();
    }, section);
    return () => ctx.revert();
  }, []);

  return (
    <section className="v3-platform-horizontal" id="architecture" data-system-ui="v8" ref={section}>
      <div className="v3-platform-topbar v9-platform-topbar">
        <span>02 / THE WORKSIMPLIFIED SYSTEM</span>
        <div className="v9-system-nav" aria-hidden="true" style={{ gridTemplateColumns: "repeat(6, 1fr)" }}>
          <b>BA Agent</b><i /><b>Refinement</b><i /><b>Frappe</b><i /><b>Project</b><i /><b>Functional</b><i /><b>Technical</b>
        </div>
        <small>SCROLL TO EXPLORE</small>
        <div className="v9-system-progress"><i /></div>
      </div>
      <div className="v3-platform-track" ref={track}>
        {layers.map(({ n, name, title, text, icon: Icon, visual }) => (
          <article className="v3-platform-panel" key={name}>
            <div className="v3-panel-number">{n}</div>
            <div className="v3-panel-copy">
              <span><Icon size={16} /> {name}</span>
              <h3>{title}</h3>
              <p>{text}</p>
            </div>
            <div className="v3-panel-visual">{visual}</div>
          </article>
        ))}
      </div>
    </section>
  );
}

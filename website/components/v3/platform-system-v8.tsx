"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  Activity,
  BadgeDollarSign,
  BrainCircuit,
  CheckCircle2,
  Clock3,
  Database,
  Eye,
  FileText,
  GitBranch,
  Mail,
  Network,
  Play,
  ShieldCheck,
  Sparkles,
  Target,
  UserCheck,
  UsersRound,
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

function MetaStrip({ left, middle, right, warn = false }: { left: string; middle: string; right: string; warn?: boolean }) {
  return (
    <div className="sys7-meta-strip">
      <span><i className={warn ? "warn" : ""} />{left}</span>
      <span>{middle}</span>
      <span>{right}</span>
    </div>
  );
}

function UnderstandDiagram() {
  return (
    <div className="sys7-diagram sys7-understand">
      <SurfaceHeader label="INTENT COMPILER" status="PLAN READY" />
      <div className="sys7-canvas sys7-understand-canvas">
        <div className="sys7-brief-panel">
          <div className="sys7-panel-kicker"><FileText size={13} /> BUSINESS BRIEF</div>
          <p>
            “When a new vendor applies, <mark>verify documents</mark>, assess risk, and create the
            vendor in <mark>ERP</mark>. Anything above <mark>$25K</mark> needs Finance approval.”
          </p>
          <div className="sys7-brief-foot"><span>Natural language</span><b>01</b></div>
        </div>

        <div className="sys7-parser-rail" aria-hidden="true">
          <span className="sys7-parser-node is-active">INTENT</span>
          <span className="sys7-parser-node">ENTITIES</span>
          <span className="sys7-parser-node">CONTROLS</span>
          <i className="sys7-parser-scan" />
        </div>

        <div className="sys7-plan-panel">
          <div className="sys7-plan-top">
            <div>
              <small>COMPILED EXECUTION PLAN</small>
              <b>Vendor onboarding</b>
            </div>
            <div className="sys7-confidence"><span>96</span><small>%</small></div>
          </div>

          <div className="sys7-plan-map">
            <div><span><Target size={12} /></span><p><small>OBJECTIVE</small><b>Verify + onboard</b></p><em>resolved</em></div>
            <div><span><Database size={12} /></span><p><small>SYSTEMS</small><b>CRM · ERP · Email</b></p><em>3 mapped</em></div>
            <div><span><UsersRound size={12} /></span><p><small>WORKFORCE</small><b>Compliance · Finance · Ops</b></p><em>3 roles</em></div>
            <div><span><UserCheck size={12} /></span><p><small>CONTROL</small><b>Finance approval</b></p><em>1 gate</em></div>
          </div>

          <div className="sys7-plan-route">
            <span>Brief</span><i /><span>Plan</span><i /><span>Workforce</span><i /><span>Run</span>
          </div>
        </div>
      </div>
      <MetaStrip left="Requirement structured" middle="8 execution steps" right="4 constraints resolved" />
    </div>
  );
}

function OrchestrateDiagram() {
  return (
    <div className="sys7-diagram sys7-orchestrate">
      <SurfaceHeader label="WORKFORCE TOPOLOGY" status="TEAM READY" />
      <div className="sys7-canvas sys7-topology-canvas">
        <svg className="sys7-topology-links" viewBox="0 0 1000 560" preserveAspectRatio="none" aria-hidden="true">
          <path d="M500 280 L220 145" />
          <path d="M500 280 L785 145" />
          <path d="M500 280 L235 430" />
          <path d="M500 280 L770 430" />
          <path className="soft" d="M220 145 Q500 40 785 145" />
          <path className="soft" d="M235 430 Q500 535 770 430" />
        </svg>

        <div className="sys7-shared-memory"><BrainCircuit size={12} /><span>Shared organizational memory</span><b>24 sources</b></div>

        <div className="sys7-supervisor-core">
          <span className="sys7-core-ring r1" />
          <span className="sys7-core-ring r2" />
          <span className="sys7-core-icon"><GitBranch size={19} /></span>
          <small>SUPERVISOR</small>
          <b>Aegis Runtime</b>
          <em>team fit 94%</em>
        </div>

        <div className="sys7-agent-node a1">
          <span><ShieldCheck size={14} /></span><div><small>SPECIALIST 01</small><b>Compliance</b><p>Policy + evidence</p></div><em>ACTIVE</em>
          <div className="sys7-agent-tools"><i>Policy DB</i><i>Docs</i></div>
        </div>
        <div className="sys7-agent-node a2">
          <span><Activity size={14} /></span><div><small>SPECIALIST 02</small><b>Finance</b><p>Risk + approval</p></div><em>ACTIVE</em>
          <div className="sys7-agent-tools"><i>Risk API</i><i>Ledger</i></div>
        </div>
        <div className="sys7-agent-node a3">
          <span><Database size={14} /></span><div><small>SPECIALIST 03</small><b>Operations</b><p>System actions</p></div><em>READY</em>
          <div className="sys7-agent-tools"><i>ERP</i><i>CRM</i></div>
        </div>
        <div className="sys7-agent-node a4 human">
          <span><UserCheck size={14} /></span><div><small>HUMAN OWNER</small><b>Finance Ops</b><p>Escalation point</p></div><em>ON CALL</em>
          <div className="sys7-agent-tools"><i>Approval</i><i>Override</i></div>
        </div>
      </div>
      <MetaStrip left="Supervisor coordinating" middle="3 specialists · 1 human" right="6 scoped tools" />
    </div>
  );
}

function ExecuteDiagram() {
  return (
    <div className="sys7-diagram sys7-execute">
      <SurfaceHeader label="EXECUTION TIMELINE" status="RUN #2841 · LIVE" />
      <div className="sys7-canvas sys7-timeline-canvas">
        <div className="sys7-run-header">
          <div><small>RUN</small><b>Vendor onboarding / ACME-482</b></div>
          <span><i /> running · 67%</span>
        </div>

        <div className="sys7-time-axis"><span>00:00</span><span>00:12</span><span>00:24</span><span>00:36</span><span>00:48</span></div>

        <div className="sys7-swimlanes">
          <div className="sys7-lane-label"><span><BrainCircuit size={12} /></span><b>AEGIS</b><small>runtime</small></div>
          <div className="sys7-lane-track">
            <div className="sys7-event e1 done"><small>00:04</small><b>Plan compiled</b><em>DONE</em></div>
            <div className="sys7-event e2 done"><small>00:11</small><b>Policy verified</b><em>DONE</em></div>
            <div className="sys7-event e3 running"><small>00:31</small><b>Write transaction</b><em>RUNNING</em></div>
          </div>

          <div className="sys7-lane-label"><span><Database size={12} /></span><b>SYSTEMS</b><small>tools</small></div>
          <div className="sys7-lane-track">
            <div className="sys7-event s1 done"><small>CRM</small><b>Read vendor</b><em>184ms</em></div>
            <div className="sys7-event s2 running"><small>ERP</small><b>Create vendor</b><em>writing</em></div>
            <div className="sys7-event s3 queued"><small>EMAIL</small><b>Send notice</b><em>queued</em></div>
          </div>

          <div className="sys7-lane-label"><span><UserCheck size={12} /></span><b>HUMAN</b><small>control</small></div>
          <div className="sys7-lane-track">
            <div className="sys7-event h1 done"><small>FIN OPS</small><b>Approval granted</b><em>+18s</em></div>
          </div>
        </div>

        <div className="sys7-run-footer"><span>State checkpoint saved</span><span>Retries 0 / 1</span><span>Latency 184ms</span></div>
      </div>
      <MetaStrip left="State preserved" middle="5 events complete" right="1 action in progress" />
    </div>
  );
}

function GovernDiagram() {
  return (
    <div className="sys7-diagram sys7-govern">
      <SurfaceHeader label="POLICY ENVELOPE" status="HUMAN REVIEW" />
      <div className="sys7-canvas sys7-govern-canvas">
        <div className="sys7-request-card">
          <span><FileText size={14} /></span><small>REQUEST</small><b>Create ERP vendor</b><p>ACME-482 · $31,400</p>
        </div>

        <div className="sys7-arrow-link l1"><i /><span>›</span></div>

        <div className="sys7-policy-envelope">
          <div className="sys7-envelope-head"><span><ShieldCheck size={14} /></span><div><small>POLICY PACK</small><b>Vendor write / AP-04</b></div><em>3 CHECKS</em></div>
          <div className="sys7-policy-checks">
            <div><span>01</span><p><small>ROLE PERMISSION</small><b>Finance Ops</b></p><em className="pass">PASSED</em></div>
            <div><span>02</span><p><small>DATA CLASSIFICATION</small><b>Internal</b></p><em className="pass">PASSED</em></div>
            <div><span>03</span><p><small>AMOUNT THRESHOLD</small><b>&gt; $25K</b></p><em className="review">REVIEW</em></div>
          </div>
          <div className="sys7-boundary-label">execution boundary</div>
        </div>

        <div className="sys7-arrow-link l2"><i /><span>›</span></div>

        <div className="sys7-decision-stack">
          <div className="sys7-approval-card"><span><UserCheck size={14} /></span><div><small>HUMAN GATE</small><b>Finance Ops</b><p>Awaiting approval</p></div><em>REQUIRED</em></div>
          <div className="sys7-action-card"><span><Play size={14} /></span><div><small>APPROVED PATH</small><b>Execute ERP write</b></div><em>LOCKED</em></div>
          <div className="sys7-blocked-card"><span>×</span><div><small>BLOCKED PATH</small><b>No system action</b></div></div>
        </div>
      </div>
      <MetaStrip left="Human checkpoint active" middle="Audit trace immutable" right="RBAC enforced" warn />
    </div>
  );
}

function ObserveDiagram() {
  return (
    <div className="sys7-diagram sys7-observe">
      <SurfaceHeader label="OPERATIONS CONSOLE" status="HEALTHY · 99.9%" />
      <div className="sys7-canvas sys7-observe-canvas">
        <div className="sys7-kpi-row">
          <div><span><Activity size={12} /></span><p><small>RUNS TODAY</small><b>846</b></p><em>+18%</em></div>
          <div><span><CheckCircle2 size={12} /></span><p><small>SUCCESS</small><b>97.8%</b></p><em>+1.4%</em></div>
          <div><span><BadgeDollarSign size={12} /></span><p><small>COST / RUN</small><b>$0.43</b></p><em>-8%</em></div>
          <div><span><Clock3 size={12} /></span><p><small>P95 LATENCY</small><b>2.4s</b></p><em>-11%</em></div>
        </div>

        <div className="sys7-observe-grid">
          <div className="sys7-reliability-panel">
            <div className="sys7-panel-title"><div><small>RELIABILITY</small><b>Execution success</b></div><span>12H</span></div>
            <svg viewBox="0 0 700 235" preserveAspectRatio="none" aria-hidden="true">
              <defs>
                <linearGradient id="sys7Area" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3157d5" stopOpacity=".20" />
                  <stop offset="100%" stopColor="#3157d5" stopOpacity="0" />
                </linearGradient>
              </defs>
              <path className="sys7-grid-line" d="M0 45 H700 M0 105 H700 M0 165 H700 M0 225 H700" />
              <path className="sys7-area" d="M0 188 C58 178 84 151 127 160 S199 117 246 129 S326 91 372 105 S451 62 505 78 S596 41 640 51 S678 37 700 31 L700 235 L0 235 Z" />
              <path className="sys7-line" d="M0 188 C58 178 84 151 127 160 S199 117 246 129 S326 91 372 105 S451 62 505 78 S596 41 640 51 S678 37 700 31" />
              <circle cx="700" cy="31" r="5" className="sys7-point" />
            </svg>
            <div className="sys7-chart-axis"><span>08:00</span><span>12:00</span><span>16:00</span><span>20:00</span></div>
          </div>

          <div className="sys7-trace-waterfall">
            <div className="sys7-panel-title"><div><small>TRACE</small><b>Run #2841</b></div><span>42.8s</span></div>
            <div className="sys7-trace-row"><span>PLAN</span><i style={{ left: "4%", width: "18%" }} /><em>4.1s</em></div>
            <div className="sys7-trace-row"><span>COMPLIANCE</span><i style={{ left: "18%", width: "29%" }} /><em>11.2s</em></div>
            <div className="sys7-trace-row"><span>FINANCE</span><i style={{ left: "39%", width: "34%" }} /><em>14.5s</em></div>
            <div className="sys7-trace-row"><span>ERP WRITE</span><i className="running" style={{ left: "68%", width: "22%" }} /><em>9.4s</em></div>
            <div className="sys7-trace-row"><span>NOTICE</span><i className="queued" style={{ left: "88%", width: "8%" }} /><em>3.6s</em></div>
            <div className="sys7-trace-scale"><span>0s</span><span>20s</span><span>40s</span></div>
          </div>
        </div>

        <div className="sys7-live-runs">
          <div><span className="ok"><CheckCircle2 size={11} /></span><p><b>Vendor onboarding</b><small>completed · 42s</small></p><em>$0.82</em></div>
          <div><span className="review"><Clock3 size={11} /></span><p><b>Contract review</b><small>human review · 3m</small></p><em>$0.46</em></div>
          <div><span className="ok"><CheckCircle2 size={11} /></span><p><b>Invoice triage</b><small>completed · 18s</small></p><em>$0.19</em></div>
        </div>
      </div>
      <MetaStrip left="97.8% reliability" middle="13 human reviews" right="Complete trace retained" />
    </div>
  );
}

const layers = [
  {
    n: "01", name: "UNDERSTAND", title: "Begin with the business problem.", text: "The AI Business Analyst turns natural-language intent into a structured objective, systems map, dependencies, workforce plan, and risk-aware checkpoints.", icon: BrainCircuit,
    visual: <UnderstandDiagram />,
  },
  {
    n: "02", name: "ORCHESTRATE", title: "Compose the workforce around the work.", text: "AegisOS assigns specialist digital employees with role-specific memory, tools, permissions, supervisors, and escalation rules.", icon: GitBranch,
    visual: <OrchestrateDiagram />,
  },
  {
    n: "03", name: "EXECUTE", title: "Move through systems, not just prompts.", text: "The workflow runtime coordinates long-running state, branches, retries, tools, enterprise actions, and humans as one continuous run.", icon: Play,
    visual: <ExecuteDiagram />,
  },
  {
    n: "04", name: "GOVERN", title: "Put autonomy inside real boundaries.", text: "Policies, RBAC, human approvals, execution limits, scoped data, and audit trails sit inside the runtime rather than around it as an afterthought.", icon: ShieldCheck,
    visual: <GovernDiagram />,
  },
  {
    n: "05", name: "OBSERVE", title: "Operate AI like a real business system.", text: "Every run exposes reliability, cost, approvals, latency, worker activity, outcomes, and the complete execution trace.", icon: Eye,
    visual: <ObserveDiagram />,
  },
];

export function PlatformSystemV8() {
  const section = useRef<HTMLElement>(null);
  const track = useRef<HTMLDivElement>(null);

  useEffect(() => {
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
        <span>02 / THE AEGISOS SYSTEM</span>
        <div className="v9-system-nav" aria-hidden="true"><b>Understand</b><i/><b>Orchestrate</b><i/><b>Execute</b><i/><b>Govern</b><i/><b>Observe</b></div>
        <small>SCROLL TO EXPLORE</small>
        <div className="v9-system-progress"><i /></div>
      </div>
      <div className="v3-platform-track" ref={track}>
        {layers.map(({ n, name, title, text, icon: Icon, visual }) => (
          <article className="v3-platform-panel" key={name}>
            <div className="v3-panel-number">{n}</div>
            <div className="v3-panel-copy"><span><Icon size={16}/> {name}</span><h3>{title}</h3><p>{text}</p><a href={`/product/${name === "UNDERSTAND" ? "business-analyst" : name === "ORCHESTRATE" ? "workforce" : name === "EXECUTE" ? "workflows" : name === "GOVERN" ? "governance" : "observability"}`}>Explore {name.toLowerCase()} ↗</a></div>
            <div className="v3-panel-visual">{visual}</div>
          </article>
        ))}
      </div>
    </section>
  );
}

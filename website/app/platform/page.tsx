import Link from "next/link";
import type { ReactNode } from "react";
import { ArrowRight, ArrowUpRight, BrainCircuit, Check, Code2, Key, RefreshCcw, Target, Wrench } from "lucide-react";

/* ---------- per-stage artifact visuals ---------- */

function VizBA() {
  return (
    <div className="pf-viz">
      <span className="pf-viz-label">System flow diagram</span>
      <div className="pf-viz-split">
        <span className="pf-viz-node is-start">Business brief</span>
        <span className="pf-viz-brace" />
        <span className="pf-viz-stack">
          <em>Compliance review</em>
          <em>Finance risk</em>
        </span>
        <span className="pf-viz-brace" />
        <span className="pf-viz-node is-end">Create in ERP</span>
      </div>
      <span className="pf-viz-foot">3 roles · 4 systems · 2 gates</span>
    </div>
  );
}

function VizRefine() {
  return (
    <div className="pf-viz">
      <span className="pf-viz-label">Revision 2</span>
      <div className="pf-viz-diff">
        <span className="is-removed">require tax_id at submit</span>
        <span className="is-added">collect tax_id, verify before approval</span>
      </div>
      <span className="pf-viz-foot">flow updated · schema unchanged</span>
    </div>
  );
}

function VizFrappe() {
  return (
    <div className="pf-viz">
      <span className="pf-viz-label">vendor_onboarding</span>
      <div className="pf-viz-checks">
        <span><Check size={11} />site provisioned</span>
        <span><Check size={11} />3 DocTypes created</span>
        <span><Check size={11} />endpoints live</span>
      </div>
      <span className="pf-viz-foot">portal reachable</span>
    </div>
  );
}

function VizProject() {
  return (
    <div className="pf-viz">
      <span className="pf-viz-label">Scope coverage</span>
      <div className="pf-viz-bars">
        {[["Requirements", 100], ["Functionals", 64], ["Technical", 0]].map(([t, p]) => (
          <div className="pf-viz-bar" key={t as string}>
            <span>{t}</span>
            <span className="pf-viz-track"><i style={{ width: `${p}%` }} /></span>
            <em>{p}%</em>
          </div>
        ))}
      </div>
      <span className="pf-viz-foot">18 of 24 requirements met</span>
    </div>
  );
}

function VizFunctional() {
  return (
    <div className="pf-viz">
      <span className="pf-viz-label">Functional map</span>
      <div className="pf-viz-tree">
        <b>Vendor onboarding</b>
        <span>Intake form</span>
        <span>Compliance check</span>
        <span>Approval</span>
        <span>ERP sync</span>
      </div>
      <span className="pf-viz-foot">4 modules · 86% edge coverage</span>
    </div>
  );
}

function VizTechnical() {
  return (
    <div className="pf-viz">
      <span className="pf-viz-label">Vendor</span>
      <div className="pf-viz-schema">
        <span><i>tax_id</i><em>Data · unique</em></span>
        <span><i>risk_score</i><em>Int</em></span>
        <span><i>status</i><em>Select</em></span>
      </div>
      <span className="pf-viz-foot">12 tables · 24 endpoints</span>
    </div>
  );
}

const gaps = [
  {
    label: "AN ASSISTANT",
    gives: "An answer.",
    left: "You still decompose the requirement, design the data model, write the application and deploy it yourself.",
  },
  {
    label: "AN AGENT FRAMEWORK",
    gives: "A loop and a toolbox.",
    left: "You still define the roles, the handoffs, the state between them, and where any of it ends up running.",
  },
  {
    label: "WORKSIMPLIFIED",
    gives: "The pipeline itself.",
    left: "Roles, handoffs, artifacts and the deployment target are the product. You bring the requirement.",
  },
];

const stages: {
  n: string; agent: string; eyebrow: string; icon: typeof BrainCircuit;
  receives: string; does: string; decides: string; produces: string; you: string;
  viz: ReactNode;
}[] = [
  {
    n: "01", agent: "BA Agent", eyebrow: "DISCOVER", icon: BrainCircuit,
    receives: "A business requirement, written the way you would say it out loud.",
    does: "Asks the questions the brief leaves open — who is involved, which systems get touched, where approval is required, what “done” means. It keeps asking until the flow has no unexplained branches, then draws it.",
    decides: "Which roles take part, which systems are in scope, where a human has to approve, and what the project is explicitly not doing.",
    produces: "System flow diagram",
    you: "Answer the questions once. Every later stage reads from this diagram, so this is the only time the project gets explained.",
    viz: <VizBA />,
  },
  {
    n: "02", agent: "Refinement Loop", eyebrow: "REFINE", icon: RefreshCcw,
    receives: "Any artifact already produced — the flow, the schema, the code.",
    does: "Takes your feedback and revises that artifact in place rather than regenerating from a prompt, so the rest of the project stays consistent with the change instead of drifting away from it.",
    decides: "What the change actually touches, and which downstream artifacts have to move with it.",
    produces: "A revised artifact, still in sync with the rest",
    you: "Open an artifact, say what is wrong or missing, and get a revised version of that same artifact back.",
    viz: <VizRefine />,
  },
  {
    n: "03", agent: "Frappe Agent", eyebrow: "CONNECT", icon: Key,
    receives: "Your Frappe credentials and the project definition.",
    does: "Provisions the site, creates the DocTypes, wires the endpoints and links the backend — so the project exists somewhere you can open and use, not merely read about.",
    decides: "How the project maps onto your instance: which site, which app, which DocTypes, which permissions.",
    produces: "A live project in your Frappe instance",
    you: "Supply credentials once. The project appears inside your own instance, not a hosted sandbox.",
    viz: <VizFrappe />,
  },
  {
    n: "04", agent: "Project Agent", eyebrow: "MANAGE", icon: Target,
    receives: "The requirement set and the scope you agreed to.",
    does: "Watches the build against the plan — which requirements are met, which milestones are drifting, what changed along the way. It raises drift instead of quietly absorbing it into the estimate.",
    decides: "Whether the current state still matches the agreed scope, and what needs escalating to a human.",
    produces: "Verified scope with milestones tracked",
    you: "See what is done, what is slipping and what changed — without asking for a status update.",
    viz: <VizProject />,
  },
  {
    n: "05", agent: "Functional Agent", eyebrow: "BUILD", icon: Wrench,
    receives: "The system flow diagram.",
    does: "Turns each path in the flow into concrete behaviour — what the user does, what the system does in response, and what happens at the edges nobody mentioned in the brief.",
    decides: "The behaviour at every step, including the exceptions, the empty states and the failure paths.",
    produces: "Functional diagram",
    you: "Check that the behaviour is right while it is still a diagram, not after it is code.",
    viz: <VizFunctional />,
  },
  {
    n: "06", agent: "Technical Agent", eyebrow: "ARCHITECT", icon: Code2,
    receives: "The functional map.",
    does: "Decides how it gets built — the data model, the relationships, the endpoints, and the states a record moves through. This is the layer that becomes running code.",
    decides: "Schema, relationships, API surface and state transitions.",
    produces: "Technical diagram",
    you: "Review the architecture before anything is provisioned into your instance.",
    viz: <VizTechnical />,
  },
];

export default function PlatformPage() {
  return (
    <>
      <section className="v3-platform-page-hero">
        <span>WORKSIMPLIFIED PLATFORM</span>
        <h1>Six agents, one pipeline.<br/><em>Here is the whole system.</em></h1>
        <p>Worksimplified takes a business requirement and carries it all the way to a running Frappe application. Each agent does one job, produces one artifact, and hands it to the next. This page explains what each of them actually does — and where you sit in the loop.</p>
        <div><a href="#contact" className="v3-solid-button">Book a demo <ArrowUpRight size={14}/></a><Link href="/product/ba-agent">Start with the BA Agent <ArrowRight size={14}/></Link></div>
      </section>

      <section className="pf-gap">
        <div className="pf-system-head">
          <span>WHY IT EXISTS</span>
          <div>
            <h2>Most AI tooling stops before the work does.</h2>
            <p>You can already get an answer, or a loop, or a workflow graph. What you cannot get is the finished project — so the assembly is still your job.</p>
          </div>
        </div>

        <div className="pf-gap-grid">
          {gaps.map(({ label, gives, left }, i) => (
            <article className={i === gaps.length - 1 ? "is-ours" : ""} key={label}>
              <span>{label}</span>
              <b>{gives}</b>
              <p>{left}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="pf-how">
        <div className="pf-system-head">
          <span>THE PIPELINE</span>
          <div>
            <h2>Stage by stage.</h2>
            <p>Six agents run in sequence. Each one starts from the previous agent’s artifact — not from a fresh prompt — which is why nothing gets lost between steps, and why you only explain the project once. The artifact shown on each card is what that stage produces for a vendor onboarding brief.</p>
          </div>
        </div>

        <ol className="pf-stages">
          {stages.map(({ n, agent, eyebrow, icon: Icon, receives, does, decides, produces, you, viz }) => (
            <li className="pf-stage" key={n}>
              <div className="pf-stage-visual">
                <div className="pf-stage-pin">
                  <div className="pf-pin-head">
                    <span className="pf-pin-n">{n}</span>
                    <b>{agent}</b>
                  </div>
                  {viz}
                </div>
              </div>
              <div className="pf-stage-main">
                <header>
                  <span className="pf-stage-n">{n}</span>
                  <h3>{agent}</h3>
                  <Icon size={15} />
                  <em>{eyebrow}</em>
                </header>
                <dl>
                  <div><dt>Receives</dt><dd>{receives}</dd></div>
                  <div><dt>Does</dt><dd>{does}</dd></div>
                  <div><dt>Decides</dt><dd>{decides}</dd></div>
                  <div className="is-out"><dt>Produces</dt><dd><Check size={12} />{produces}</dd></div>
                  <div className="is-you"><dt>You</dt><dd>{you}</dd></div>
                </dl>
              </div>
            </li>
          ))}
        </ol>

        <div className="pf-handoff">
          <h3>How the pieces connect</h3>
          <p>The flow diagram becomes the functional map. The functional map becomes the schema, the states and the endpoints. Because every agent starts from the previous artifact rather than a fresh prompt, changing the flow moves everything downstream with it. You never re-explain the project to a later stage.</p>
          <div className="pf-handoff-chain" aria-hidden="true">
            {["Requirement", "Flow diagram", "Functional map", "Technical design", "Running app"].map((x, i, arr) => (
              <span key={x}><b>{x}</b>{i < arr.length - 1 && <ArrowRight size={12} />}</span>
            ))}
          </div>
        </div>
      </section>

      <section className="v3-page-cta" id="contact"><span>BUILD THE AGENT PIPELINE</span><h2>Move from disconnected AI tools to one pipeline that ships.</h2><a href="mailto:hello@aegisos.ai">Book a demo <ArrowUpRight size={15}/></a></section>
    </>
  );
}

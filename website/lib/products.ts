export type ProductPageData = {
  slug: string;
  eyebrow: string;
  title: string;
  description: string;
  primary: string;
  secondary: string;
  metrics: { value: string; label: string }[];
  capabilities: { title: string; text: string }[];
  steps: { number: string; title: string; text: string }[];
};

export const products: ProductPageData[] = [
  {
    slug: "business-analyst",
    eyebrow: "Understand",
    title: "Start with the business requirement. Not the technology.",
    description:
      "AegisOS turns a business problem into a structured, executable plan before anyone has to think about models, agents, tools, or workflows.",
    primary: "Business intent",
    secondary: "Executable plan",
    metrics: [
      { value: "01", label: "Clarify the objective" },
      { value: "02", label: "Map systems and stakeholders" },
      { value: "03", label: "Define execution and controls" },
    ],
    capabilities: [
      { title: "Requirement discovery", text: "Capture goals, constraints, systems, data, owners, and success criteria in business language." },
      { title: "Work decomposition", text: "Break an objective into tasks, dependencies, checkpoints, and required specialist roles." },
      { title: "Execution planning", text: "Produce an actionable plan that can be handed directly to the orchestration layer." },
      { title: "Human checkpoints", text: "Place reviews and approvals where business risk requires human judgment." },
    ],
    steps: [
      { number: "01", title: "Describe the outcome", text: "The user explains what should happen in natural language." },
      { number: "02", title: "AegisOS reasons about the work", text: "The Business Analyst identifies actors, systems, constraints, and missing context." },
      { number: "03", title: "A governed plan is created", text: "AegisOS produces a workflow-ready execution plan with clear controls." },
    ],
  },
  {
    slug: "memory",
    eyebrow: "Remember",
    title: "Organizational memory that compounds with every workflow.",
    description:
      "AegisOS keeps business context close to execution: terminology, processes, decisions, policies, previous runs, and the knowledge each AI worker needs.",
    primary: "Business context",
    secondary: "Reusable memory",
    metrics: [
      { value: "Shared", label: "Organization context" },
      { value: "Scoped", label: "Role-specific knowledge" },
      { value: "Traceable", label: "Decision history" },
    ],
    capabilities: [
      { title: "Organization knowledge", text: "Centralize the language, policies, procedures, and operating context unique to your business." },
      { title: "Role memory", text: "Give every digital employee only the knowledge relevant to its responsibilities." },
      { title: "Run history", text: "Use outcomes from previous work to improve consistency and reduce repeated discovery." },
      { title: "Context boundaries", text: "Keep memory scoped to the users, teams, workflows, and data domains that should access it." },
    ],
    steps: [
      { number: "01", title: "Capture", text: "AegisOS records useful business context from approved sources and completed work." },
      { number: "02", title: "Scope", text: "Knowledge is attached to the organization, team, workflow, or digital worker that needs it." },
      { number: "03", title: "Reuse", text: "Future work starts with context instead of starting from zero." },
    ],
  },
  {
    slug: "workforce",
    eyebrow: "Orchestrate",
    title: "Digital employees built for real work.",
    description:
      "Create specialized AI workers with a clear role, skills, tools, memory, permissions, policies, and supervisor — then deploy them as a coordinated workforce.",
    primary: "Specialist roles",
    secondary: "Coordinated workforce",
    metrics: [
      { value: "Role", label: "Clear responsibility" },
      { value: "Tools", label: "Approved systems" },
      { value: "Policy", label: "Bounded autonomy" },
    ],
    capabilities: [
      { title: "Role design", text: "Define what each digital employee is responsible for and what is outside its scope." },
      { title: "Skills and tools", text: "Attach the capabilities and enterprise systems required to perform the role." },
      { title: "Supervision", text: "Assign review, approval, and escalation relationships just like an operating team." },
      { title: "Reusable workforce", text: "Deploy the same specialists across many workflows without rebuilding them every time." },
    ],
    steps: [
      { number: "01", title: "Define the role", text: "Start with responsibility, not a generic agent prompt." },
      { number: "02", title: "Attach context and controls", text: "Add memory, systems, data permissions, and policies." },
      { number: "03", title: "Assign to workflows", text: "Use the worker wherever that business role is required." },
    ],
  },
  {
    slug: "workflows",
    eyebrow: "Execute",
    title: "From one AI assistant to an entire execution workflow.",
    description:
      "AegisOS coordinates people, digital employees, systems, approvals, and automations as one continuous business workflow.",
    primary: "Business plan",
    secondary: "Completed work",
    metrics: [
      { value: "Multi-agent", label: "Coordinated execution" },
      { value: "Stateful", label: "Long-running work" },
      { value: "Resilient", label: "Retries and escalation" },
    ],
    capabilities: [
      { title: "Workflow orchestration", text: "Coordinate many workers, tools, branches, and dependencies in a single execution graph." },
      { title: "Long-running state", text: "Keep track of work that spans hours, days, reviews, and external events." },
      { title: "Exception handling", text: "Route failures and ambiguity to recovery steps or the right human owner." },
      { title: "Reusable patterns", text: "Standardize proven workflows and deploy them across teams." },
    ],
    steps: [
      { number: "01", title: "Plan", text: "The requirement becomes an execution graph with clear responsibilities." },
      { number: "02", title: "Run", text: "Digital employees and systems execute tasks while AegisOS keeps state." },
      { number: "03", title: "Complete", text: "Outputs, approvals, exceptions, and audit information are consolidated into one run." },
    ],
  },
  {
    slug: "governance",
    eyebrow: "Govern",
    title: "Autonomy where you want it. Control where you need it.",
    description:
      "Put permissions, approval gates, execution limits, auditability, and human intervention around every AI workflow.",
    primary: "AI autonomy",
    secondary: "Enterprise control",
    metrics: [
      { value: "RBAC", label: "Permission boundaries" },
      { value: "HITL", label: "Human checkpoints" },
      { value: "Audit", label: "Traceable execution" },
    ],
    capabilities: [
      { title: "Permissions", text: "Control what each worker, team, and workflow can see and do." },
      { title: "Approval policies", text: "Require human authorization for actions based on risk, data, value, or workflow stage." },
      { title: "Execution limits", text: "Bound spend, retries, tool access, external actions, and escalation behavior." },
      { title: "Audit trail", text: "Inspect what happened, who or what acted, which systems were touched, and what was approved." },
    ],
    steps: [
      { number: "AUTO", title: "Execute", text: "Low-risk work can run independently inside defined policy boundaries." },
      { number: "REVIEW", title: "Execute then review", text: "Work completes but remains visible for human oversight." },
      { number: "APPROVE", title: "Prepare then authorize", text: "High-impact actions wait for a human decision before execution." },
    ],
  },
  {
    slug: "integrations",
    eyebrow: "Connect",
    title: "Connect AI to the systems your organization already uses.",
    description:
      "AegisOS turns enterprise tools into governed capabilities that digital employees can use within workflows.",
    primary: "Existing systems",
    secondary: "AI-ready capabilities",
    metrics: [
      { value: "API", label: "Custom systems" },
      { value: "Data", label: "Business context" },
      { value: "Actions", label: "Real execution" },
    ],
    capabilities: [
      { title: "Business applications", text: "Connect CRM, ERP, support, collaboration, productivity, and internal platforms." },
      { title: "Data systems", text: "Use databases, warehouses, documents, and APIs as governed business context." },
      { title: "Action interfaces", text: "Expose safe actions instead of giving agents unrestricted access to entire systems." },
      { title: "Custom connectors", text: "Wrap proprietary services and internal APIs as reusable capabilities." },
    ],
    steps: [
      { number: "01", title: "Connect", text: "Register enterprise systems and authenticate through organization-approved methods." },
      { number: "02", title: "Define capabilities", text: "Choose the data and actions that AegisOS may use." },
      { number: "03", title: "Govern access", text: "Assign those capabilities to the right workers and workflows." },
    ],
  },
  {
    slug: "observability",
    eyebrow: "Observe",
    title: "Know what every AI workflow is doing — and what it costs.",
    description:
      "One control center for runs, workforce activity, human reviews, reliability, cost, and business outcomes.",
    primary: "Execution data",
    secondary: "Operational intelligence",
    metrics: [
      { value: "Runs", label: "Live execution" },
      { value: "Cost", label: "Workflow economics" },
      { value: "ROI", label: "Business outcomes" },
    ],
    capabilities: [
      { title: "Run visibility", text: "Inspect every workflow, task, worker, tool call, exception, and approval." },
      { title: "Reliability", text: "Track success, failure, latency, recovery, and escalation patterns." },
      { title: "Cost intelligence", text: "Attribute model, tool, and execution cost to workflows, teams, and outcomes." },
      { title: "Operational metrics", text: "Measure work completed, cycle time, human effort avoided, and business impact." },
    ],
    steps: [
      { number: "01", title: "Watch", text: "See what is running across the organization right now." },
      { number: "02", title: "Understand", text: "Inspect cost, failures, approvals, and execution quality in context." },
      { number: "03", title: "Improve", text: "Use operational evidence to tune workforce design, policies, and workflows." },
    ],
  },
];

export function getProduct(slug: string) {
  return products.find((product) => product.slug === slug);
}

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
    slug: "ba-agent",
    eyebrow: "Discover",
    title: "Start with a conversation. Leave with a flow diagram.",
    description:
      "The BA Agent discusses your project, gathers requirements, and builds the foundational Flow Diagram for the entire system. It understands scope, stakeholders, and objectives before any code is written.",
    primary: "Business intent",
    secondary: "Flow diagram",
    metrics: [
      { value: "Chat", label: "Interactive discussion" },
      { value: "Analyze", label: "Requirements extracted" },
      { value: "Diagram", label: "System flow created" },
    ],
    capabilities: [
      { title: "Interactive Discovery", text: "Discuss your project naturally — the BA Agent asks the right questions to uncover scope, constraints, and success criteria." },
      { title: "Flow Diagram Generation", text: "Automatically creates a comprehensive flow diagram showing the entire project lifecycle." },
      { title: "Requirement Structuring", text: "Transforms unstructured business intent into actionable, structured specifications." },
      { title: "Stakeholder Mapping", text: "Identifies key roles, systems, dependencies, and control points." },
    ],
    steps: [
      { number: "01", title: "Describe your project", text: "Tell the BA Agent what you want to build in natural language." },
      { number: "02", title: "Discuss and refine", text: "The agent asks clarifying questions and maps out the full system." },
      { number: "03", title: "Get your flow diagram", text: "A complete flow diagram is generated, ready for the next agent." },
    ],
  },
  {
    slug: "frappe-agent",
    eyebrow: "Connect",
    title: "Link your project to Frappe. Start interacting.",
    description:
      "The Frappe Agent securely gets your Frappe credentials, provisions the project, connects the backend, and enables you to interact with your new system directly through the Frappe portal.",
    primary: "Frappe credentials",
    secondary: "Live project",
    metrics: [
      { value: "Secure", label: "Credentials handled" },
      { value: "Setup", label: "Project created" },
      { value: "Live", label: "Interactive portal" },
    ],
    capabilities: [
      { title: "Credential Handling", text: "Securely receives and stores your Frappe credentials for backend connection." },
      { title: "Project Provisioning", text: "Creates the project structure and configures it within your Frappe environment." },
      { title: "Backend Integration", text: "Links the designed system to your live Frappe instance." },
      { title: "Interactive Portal", text: "Enables direct interaction with the created project through Frappe." },
    ],
    steps: [
      { number: "01", title: "Provide Frappe credentials", text: "Securely connect your Frappe instance to the agent." },
      { number: "02", title: "Project creation", text: "The agent provisions and configures the project in Frappe." },
      { number: "03", title: "Start interacting", text: "Use your new project directly through the Frappe portal." },
    ],
  },
  {
    slug: "project-agent",
    eyebrow: "Manage",
    title: "End-to-end project oversight, handled by an agent.",
    description:
      "The Project Agent looks entirely after the project's requirements, ensuring scope, milestones, and deliverables are strictly managed from start to finish.",
    primary: "Requirements",
    secondary: "Deliverables",
    metrics: [
      { value: "Scope", label: "Fully tracked" },
      { value: "On Time", label: "Milestones met" },
      { value: "Quality", label: "Verified" },
    ],
    capabilities: [
      { title: "Scope Management", text: "Tracks the full project scope and ensures nothing falls through the cracks." },
      { title: "Milestone Tracking", text: "Monitors progress against key milestones and deadlines." },
      { title: "Deliverable Quality", text: "Verifies that each deliverable meets the defined standards." },
      { title: "Requirement Fulfillment", text: "Ensures all requirements are addressed and completed." },
    ],
    steps: [
      { number: "01", title: "Scope defined", text: "Project requirements and boundaries are established." },
      { number: "02", title: "Milestones tracked", text: "Progress is continuously monitored against the plan." },
      { number: "03", title: "Deliverables verified", text: "Each output is quality-checked before completion." },
    ],
  },
  {
    slug: "functional-agent",
    eyebrow: "Build",
    title: "Functionalities designed, mapped, and ready.",
    description:
      "The Functional Agent works on the core functionalities of the project, mapping out user actions, edge cases, and creating the comprehensive Functional Diagram.",
    primary: "Functional logic",
    secondary: "Feature diagram",
    metrics: [
      { value: "Features", label: "Fully defined" },
      { value: "Mapped", label: "Logic covered" },
      { value: "Ready", label: "Diagram generated" },
    ],
    capabilities: [
      { title: "Feature Design", text: "Defines every feature and functionality the project needs." },
      { title: "Logic Mapping", text: "Maps out core logic, user actions, and edge cases comprehensively." },
      { title: "Functional Diagram", text: "Generates a complete functional diagram showing all feature interactions." },
      { title: "User Action Flow", text: "Details how users interact with each feature and the expected outcomes." },
    ],
    steps: [
      { number: "01", title: "Define functionalities", text: "Identify and design all features the project requires." },
      { number: "02", title: "Map the logic", text: "Create detailed logic maps covering user actions and edge cases." },
      { number: "03", title: "Generate diagram", text: "The functional diagram is produced, ready for technical design." },
    ],
  },
  {
    slug: "technical-agent",
    eyebrow: "Architect",
    title: "Technical architecture designed and documented.",
    description:
      "The Technical Agent translates requirements into the Technical Diagram — designing database schemas, API endpoints, system architecture, and handling all technical aspects of the project.",
    primary: "Technical design",
    secondary: "System architecture",
    metrics: [
      { value: "Database", label: "Schema designed" },
      { value: "APIs", label: "Endpoints mapped" },
      { value: "Deployed", label: "Implementation ready" },
    ],
    capabilities: [
      { title: "Database Design", text: "Creates optimized database schemas that support the functional requirements." },
      { title: "API Architecture", text: "Maps all API endpoints, their inputs, outputs, and relationships." },
      { title: "Technical Diagram", text: "Produces a comprehensive technical diagram of the entire system architecture." },
      { title: "Implementation Spec", text: "Delivers detailed specifications ready for deployment." },
    ],
    steps: [
      { number: "01", title: "Design the database", text: "Schema is created based on functional and project requirements." },
      { number: "02", title: "Map APIs", text: "All endpoints and their contracts are defined and documented." },
      { number: "03", title: "Generate technical diagram", text: "Complete technical architecture diagram is produced for implementation." },
    ],
  },
];

export function getProduct(slug: string) {
  return products.find((product) => product.slug === slug);
}

import React, { useState, useEffect } from 'react';
import { Layout, Typography, Card, Row, Col, List, Tag, Button, Input, Space, Progress, Tooltip, Avatar, ConfigProvider, theme, message, Drawer, Select, Modal, Form, Divider, Switch, Checkbox, Tabs, Spin, Skeleton, Popconfirm } from 'antd';
import { RobotOutlined, UserOutlined, SendOutlined, CheckCircleOutlined, SyncOutlined, DatabaseOutlined, WarningOutlined, ApiOutlined, PartitionOutlined, FileTextOutlined, ArrowLeftOutlined, ThunderboltOutlined, LockOutlined, InfoCircleOutlined, BookOutlined, RightOutlined, DownOutlined, SearchOutlined, PlayCircleOutlined, PlusOutlined, SettingOutlined, EyeOutlined, CheckOutlined, CloseOutlined, CalendarOutlined, AuditOutlined, LoadingOutlined, DeleteOutlined, FolderOutlined, FolderOpenOutlined, ReloadOutlined, ClockCircleOutlined, ExportOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { ApiClient } from '../api/client';
import { ChatView } from '../components/ChatView';
import EvalsTab from '../components/EvalsTab';
import MeetingsCalendarDashboard from '../components/MeetingsCalendarDashboard';
import { ProjectConnectorsPanel } from '../components/ProjectConnectorsPanel';
import { ProjectWorkBoard } from '../components/ProjectWorkBoard';
import { ui, SectionLabel, STATUS_STYLE } from './workspaceTokens';

const { Content, Sider, Header } = Layout;
const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface WorkerHierarchyNode {
  id: string;
  name: string;
  type: 'human' | 'digital' | 'agent';
  status: 'RUNNING' | 'WAITING' | 'BLOCKED' | 'COMPLETED';
  task: string;
  progress: number;
  assignedWork: string;
  role?: string;
  model?: string;
  goal?: string;
  instructions?: string;
  memory?: string[];
  knowledge?: string[];
  tools?: string[];
  logs?: string[];
  artifacts?: string[];
  certificates?: Array<string | {
    name?: string;
    title?: string;
    url?: string;
    issuer?: string;
    issuedAt?: string;
    expiresAt?: string;
  }>;
  organizationMemberId?: string;
  department?: string;
  responsibility?: string;
  positionId?: string;
  assignedAgentId?: string;
  requiredDesignation?: string;
  vacant?: boolean;
  children?: WorkerHierarchyNode[];
}

export const ProjectWorkspace = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isLegacyDemoId = id === 'migration-hr-001' || (id || '').startsWith('demo');
  const [data, setData] = useState<any>(null);
  const [projectData, setProjectData] = useState<any>(null);
  const [projectNotFound, setProjectNotFound] = useState(false);

  // Fetch project data from API
  useEffect(() => {
    if (isLegacyDemoId) {
      navigate('/projects', { replace: true });
      return;
    }
    if (id) {
      ApiClient.get(`/projects/${id}`)
        .then((project) => {
          setProjectData(project);
          setProjectNotFound(false);
        })
        .catch(() => setProjectNotFound(true));
    }
  }, [id, isLegacyDemoId, navigate]);

  // The `requirements` column is stored as a JSON string in the DB and returned
  // raw, so normalize it to an object before any consumer reads it.
  const requirements: any = React.useMemo(() => {
    const raw = projectData?.requirements ?? data?.requirements;
    if (!raw) return null;
    if (typeof raw === 'string') {
      try { return JSON.parse(raw); } catch { return null; }
    }
    return raw;
  }, [projectData, data]);

  const projectTitle = projectData?.name || data?.project?.name || 'Project Workspace';

  // Center column view: 'overview' (stats + timeline), 'blueprint' (governance/
  // guardrails/infra), 'harness' (agent execution-stack visual), or 'board'.
  const [centerTab, setCenterTab] = useState<'overview' | 'meetings' | 'knowledge' | 'blueprint' | 'board' | 'connectors'>('overview');

  // Harness tab scope: the whole-project stack, or a single agent's stack.
  const [harnessScope, setHarnessScope] = useState<'project' | 'agent'>('project');
  // Which harness layers are expanded (all collapsed by default — clean stack).
  const [harnessOpen, setHarnessOpen] = useState<Record<string, boolean>>({});

  const [chatMessages, setChatMessages] = useState<any[]>([]);
  const [inputValue, setInputValue] = useState('');

  // Human Intervention Queue State
  const [queueItems, setQueueItems] = useState<any[]>([]);

  // Live execution states
  const [progress, setProgress] = useState<number | null>(null);
  const [phase, setPhase] = useState('');
  const [loading, setLoading] = useState(true);

  // Drawer / Worker inspection state
  const [selectedWorkerId, setSelectedWorkerId] = useState<string>('');
  const [isWorkerInspectorOpen, setIsWorkerInspectorOpen] = useState(false);

  // Task scheduling state
  const [scheduledTasks, setScheduledTasks] = useState<any[]>([]);
  const [showScheduleForm, setShowScheduleForm] = useState(false);
  const [scheduleTaskName, setScheduleTaskName] = useState('');
  const [scheduleTaskCron, setScheduleTaskCron] = useState('');
  const [scheduleTaskDesc, setScheduleTaskDesc] = useState('');

  // Bottom Console log search & filter
  const [logSearch, setLogSearch] = useState('');
  const [logFilter, setLogFilter] = useState('ALL LOGS');
  const [autoScroll, setAutoScroll] = useState(true);

  // Collapsible panels
  const [collapseState, setCollapseState] = useState({
    understanding: true,
    reasoning: true,
    decision: true,
    artifacts: true
  });

  // Worker-specific connectors state
  const WORKER_CONNECTORS = [
    { id: 'mysql', name: 'MySQL', category: 'Database', logo: '🐬', description: 'Connect to MySQL databases for data queries and migrations', fields: [
      { key: 'host', label: 'Host', placeholder: 'localhost', type: 'text' },
      { key: 'port', label: 'Port', placeholder: '3306', type: 'text' },
      { key: 'database', label: 'Database', placeholder: 'my_database', type: 'text' },
      { key: 'username', label: 'Username', placeholder: 'root', type: 'text' },
      { key: 'password', label: 'Password', placeholder: '••••••••', type: 'password' },
    ]},
    { id: 'postgres', name: 'PostgreSQL', category: 'Database', logo: '🐘', description: 'Connect to PostgreSQL databases', fields: [
      { key: 'host', label: 'Host', placeholder: 'localhost', type: 'text' },
      { key: 'port', label: 'Port', placeholder: '5432', type: 'text' },
      { key: 'database', label: 'Database', placeholder: 'my_database', type: 'text' },
      { key: 'username', label: 'Username', placeholder: 'postgres', type: 'text' },
      { key: 'password', label: 'Password', placeholder: '••••••••', type: 'password' },
    ]},
    { id: 'mongodb', name: 'MongoDB', category: 'Database', logo: '🍃', description: 'Connect to MongoDB for document operations', fields: [
      { key: 'connection_string', label: 'Connection String', placeholder: 'mongodb://localhost:27017', type: 'text' },
      { key: 'database', label: 'Database', placeholder: 'my_database', type: 'text' },
    ]},
    { id: 'gcp-pubsub', name: 'GCP Pub/Sub', category: 'Messaging', logo: '📨', description: 'Publish and subscribe to GCP Pub/Sub topics', fields: [
      { key: 'project_id', label: 'GCP Project ID', placeholder: 'my-project-123', type: 'text' },
      { key: 'service_account_key', label: 'Service Account Key (JSON)', placeholder: 'Paste JSON key...', type: 'textarea' },
      { key: 'topic', label: 'Default Topic', placeholder: 'my-topic', type: 'text' },
    ]},
    { id: 'gcp-storage', name: 'GCP Cloud Storage', category: 'Storage', logo: '☁️', description: 'Read and write files from GCP Cloud Storage', fields: [
      { key: 'project_id', label: 'GCP Project ID', placeholder: 'my-project-123', type: 'text' },
      { key: 'bucket', label: 'Bucket Name', placeholder: 'my-bucket', type: 'text' },
      { key: 'service_account_key', label: 'Service Account Key (JSON)', placeholder: 'Paste JSON key...', type: 'textarea' },
    ]},
    { id: 'frappe-api', name: 'Frappe HR API', category: 'Application', logo: '🏢', description: 'Interact with Frappe HR REST API endpoints', fields: [
      { key: 'base_url', label: 'Instance URL', placeholder: 'https://hr.example.com', type: 'text' },
      { key: 'api_key', label: 'API Key', placeholder: 'xxxxxxxx', type: 'text' },
      { key: 'api_secret', label: 'API Secret', placeholder: '••••••••', type: 'password' },
    ]},
    { id: 'adrenaline-api', name: 'Adrenaline API', category: 'Application', logo: '💊', description: 'Read data from Adrenaline HR system', fields: [
      { key: 'base_url', label: 'Instance URL', placeholder: 'https://adrenaline.example.com', type: 'text' },
      { key: 'api_token', label: 'API Token', placeholder: 'xxxxxxxx', type: 'password' },
    ]},
    { id: 'redis', name: 'Redis', category: 'Cache', logo: '⚡', description: 'Connect to Redis for caching and queues', fields: [
      { key: 'host', label: 'Host', placeholder: 'localhost', type: 'text' },
      { key: 'port', label: 'Port', placeholder: '6379', type: 'text' },
      { key: 'password', label: 'Password (optional)', placeholder: '••••••••', type: 'password' },
    ]},
    { id: 'kafka', name: 'Apache Kafka', category: 'Messaging', logo: '📊', description: 'Produce and consume Kafka messages', fields: [
      { key: 'bootstrap_servers', label: 'Bootstrap Servers', placeholder: 'localhost:9092', type: 'text' },
      { key: 'topic', label: 'Default Topic', placeholder: 'my-topic', type: 'text' },
      { key: 'group_id', label: 'Consumer Group ID', placeholder: 'my-group', type: 'text' },
    ]},
    { id: 'rest-api', name: 'REST API', category: 'Integration', logo: '🔗', description: 'Make generic HTTP REST API calls', fields: [
      { key: 'base_url', label: 'Base URL', placeholder: 'https://api.example.com', type: 'text' },
      { key: 'auth_header', label: 'Auth Header', placeholder: 'Bearer xxxxx', type: 'password' },
    ]},
    { id: 'webhook', name: 'Webhooks', category: 'Integration', logo: '🪝', description: 'Register and receive webhook callbacks', fields: [
      { key: 'callback_url', label: 'Callback URL', placeholder: 'https://your-app.com/webhook', type: 'text' },
      { key: 'secret', label: 'Webhook Secret', placeholder: 'whsec_xxxxx', type: 'password' },
    ]},
    { id: 's3', name: 'AWS S3', category: 'Storage', logo: '🪣', description: 'Read and write objects from S3 buckets', fields: [
      { key: 'region', label: 'Region', placeholder: 'us-east-1', type: 'text' },
      { key: 'bucket', label: 'Bucket Name', placeholder: 'my-bucket', type: 'text' },
      { key: 'access_key', label: 'Access Key ID', placeholder: 'AKIA...', type: 'text' },
      { key: 'secret_key', label: 'Secret Access Key', placeholder: '••••••••', type: 'password' },
    ]},
  ];

  const [workerConnectors, setWorkerConnectors] = useState<Record<string, string[]>>({});

  const [connectorConfigs, setConnectorConfigs] = useState<Record<string, Record<string, string>>>({});
  const [configuringConnector, setConfiguringConnector] = useState<{ workerId: string; connectorId: string } | null>(null);
  const [connectorSearch, setConnectorSearch] = useState('');

  const GUARDRAIL_TEMPLATES: Record<string, { name: string; type: 'hard' | 'soft'; category: string; description: string; enforcement: string }[]> = {
    'Data Migration Specialist': [
      { name: 'No Unapproved Schema Changes', type: 'hard', category: 'Access Control', description: 'Agent must not modify any database schema without explicit human approval.', enforcement: 'Blocks DDL statements. Requires human sign-off via approval queue.' },
      { name: 'Batch Size Limit', type: 'hard', category: 'Performance', description: 'Maximum 1000 records per migration batch to prevent resource exhaustion.', enforcement: 'Automatically splits larger batches. Logs warning if batch exceeds limit.' },
      { name: 'Data Validation Before Write', type: 'soft', category: 'Data Integrity', description: 'Agent should validate field mappings before writing to target database.', enforcement: 'Runs validation checks. Logs warnings for mismatches but allows override.' },
      { name: 'Rollback on Error Rate > 5%', type: 'hard', category: 'Operational', description: 'Automatically rollback a migration batch if error rate exceeds 5%.', enforcement: 'Monitors error rate in real-time. Triggers automatic rollback and alerts.' },
      { name: 'PII Data Masking', type: 'hard', category: 'Compliance', description: 'Agent must mask PII fields (SSN, salary, medical) in all logs and outputs.', enforcement: 'Regex-based PII detection on all outputs. Blocks unmasked PII.' },
    ],
    'Sync Pipeline Engineer': [
      { name: 'Idempotent Writes Only', type: 'hard', category: 'Data Integrity', description: 'All sync operations must be idempotent to prevent duplicate data on retry.', enforcement: 'Validates write operations use upsert semantics. Blocks insert-only operations.' },
      { name: 'Sync Lag Alert at 5s', type: 'soft', category: 'Performance', description: 'Alert when sync latency exceeds 5 seconds.', enforcement: 'Monitors end-to-end latency. Sends alert to ops channel.' },
      { name: 'Dead Letter Queue Review', type: 'soft', category: 'Operational', description: 'Messages in DLQ must be reviewed within 1 hour.', enforcement: 'Tracks DLQ age. Escalates to human if messages exceed TTL.' },
      { name: 'No Direct Database Writes', type: 'hard', category: 'Access Control', description: 'Agent must only write through the sync pipeline, never directly to the database.', enforcement: 'Blocks direct SQL connections. Only API/pipeline writes allowed.' },
    ],
    'Migration Orchestrator': [
      { name: 'Phase Gate Approval', type: 'hard', category: 'Operational', description: 'Each phase transition requires explicit human approval.', enforcement: 'Pauses simulation at phase boundaries. Cannot auto-advance.' },
      { name: 'Rollback Window 24h', type: 'hard', category: 'Operational', description: 'Rollback capability must be maintained for 24 hours after each phase.', enforcement: 'Keeps point-in-time snapshots. Blocks snapshot deletion within window.' },
      { name: 'Stakeholder Notification', type: 'soft', category: 'Operational', description: 'Notify stakeholders before each phase transition.', enforcement: 'Sends email/Slack notification 1 hour before phase boundary.' },
      { name: 'Risk Threshold Enforcement', type: 'hard', category: 'Operational', description: 'Block phase transition if any risk is rated High and unresolved.', enforcement: 'Checks risk register. Blocks if unresolved High risks exist.' },
    ],
    'Business Analyst': [
      { name: 'Requirement Sign-off Required', type: 'hard', category: 'Compliance', description: 'Finalized requirements must be signed off by client before project creation.', enforcement: 'Blocks project creation until sign-off status is confirmed.' },
      { name: 'Scope Change Logging', type: 'soft', category: 'Compliance', description: 'All scope changes must be logged with justification.', enforcement: 'Tracks requirement diffs. Auto-generates change log entry.' },
      { name: 'Ambiguity Flagging', type: 'soft', category: 'Data Integrity', description: 'Agent must flag ambiguous requirements rather than making assumptions.', enforcement: 'Monitors agent responses for hedging language. Prompts for clarification.' },
    ],
  };

  const [agentGuardrails, setAgentGuardrails] = useState<Record<string, { name: string; enabled: boolean; type: string }[]>>({});
  const [testingGuardrail, setTestingGuardrail] = useState<string | null>(null);
  const [guardrailResult, setGuardrailResult] = useState<{ name: string; triggered: boolean; action: string; cascade: string[] } | null>(null);
  const [violations, setViolations] = useState<{ name: string; time: string; action: string }[]>([]);
  const [showNewGuardrail, setShowNewGuardrail] = useState(false);
  const [newGuardrailName, setNewGuardrailName] = useState('');
  const [newGuardrailType, setNewGuardrailType] = useState<'hard' | 'soft'>('soft');
  const [newGuardrailDesc, setNewGuardrailDesc] = useState('');
  const [newGuardrailEnforcement, setNewGuardrailEnforcement] = useState('');

  const getAgentGuardrails = (agentName: string) => {
    if (agentGuardrails[agentName]) return agentGuardrails[agentName];
    const templates = GUARDRAIL_TEMPLATES[agentName] || GUARDRAIL_TEMPLATES['Migration Orchestrator'];
    return templates.map(t => ({ name: t.name, enabled: true, type: t.type }));
  };

  const toggleGuardrail = (agentName: string, name: string) => {
    const current = getAgentGuardrails(agentName);
    setAgentGuardrails(prev => ({ ...prev, [agentName]: current.map(g => g.name === name ? { ...g, enabled: !g.enabled } : g) }));
  };

  const addGuardrail = (agentName: string) => {
    if (!newGuardrailName.trim()) return;
    const current = getAgentGuardrails(agentName);
    setAgentGuardrails(prev => ({ ...prev, [agentName]: [...current, { name: newGuardrailName.trim(), enabled: true, type: newGuardrailType }] }));
    if (newGuardrailDesc.trim()) {
      const templates = GUARDRAIL_TEMPLATES[agentName] || [];
      templates.push({ name: newGuardrailName.trim(), type: newGuardrailType, category: 'Other', description: newGuardrailDesc.trim(), enforcement: newGuardrailEnforcement.trim() || 'Manual enforcement' });
    }
    setNewGuardrailName(''); setNewGuardrailDesc(''); setNewGuardrailEnforcement(''); setNewGuardrailType('soft');
    setShowNewGuardrail(false);
  };

  const testGuardrail = (agentName: string, name: string) => {
    setTestingGuardrail(name);
    setGuardrailResult(null);
    const templates = GUARDRAIL_TEMPLATES[agentName] || GUARDRAIL_TEMPLATES['Migration Orchestrator'];
    const template = templates.find(t => t.name === name);
    setTimeout(() => {
      const triggered = Math.random() > 0.3;
      const action = triggered
        ? (template?.type === 'hard' ? 'Operation blocked. ' + (template?.enforcement || 'Guardrail enforced.') : 'Warning logged. ' + (template?.enforcement || 'Soft guardrail triggered.'))
        : 'No violation detected. Operation within bounds.';
      const cascade = triggered && template?.type === 'hard'
        ? ['Operation halted', 'Alert sent to ops team', 'Incident logged', 'Rollback checkpoint created']
        : triggered ? ['Warning logged', 'Metrics updated'] : [];
      setGuardrailResult({ name, triggered, action, cascade });
      if (triggered) {
        setViolations(prev => [{ name, time: new Date().toLocaleTimeString(), action }, ...prev].slice(0, 10));
      }
      setTestingGuardrail(null);
    }, 2000);
  };

  const toggleWorkerConnector = (workerId: string, connectorId: string) => {
    setWorkerConnectors(prev => {
      const current = prev[workerId] || [];
      const updated = current.includes(connectorId)
        ? current.filter(c => c !== connectorId)
        : [...current, connectorId];
      return { ...prev, [workerId]: updated };
    });
  };

  const updateConnectorConfig = (workerId: string, connectorId: string, field: string, value: string) => {
    const key = `${workerId}:${connectorId}`;
    setConnectorConfigs(prev => ({ ...prev, [key]: { ...(prev[key] || {}), [field]: value } }));
  };

  const opportunitiesList = React.useMemo(() => (
    projectData?.id
      ? [{
          id: projectData.id,
          label: projectData.name || 'Project',
          goal: projectData.businessgoal || '',
          phase: phase || projectData.status || '',
          progress: typeof progress === 'number' ? progress : undefined,
        }]
      : []
  ), [projectData, phase, progress]);
  const [activeOpportunityId, setActiveOpportunityId] = useState('');

  useEffect(() => {
    if (projectData?.id) setActiveOpportunityId(projectData.id);
  }, [projectData?.id]);

  // Expanded tree keys state
  const [expandedKeys, setExpandedKeys] = useState<Record<string, boolean>>({});

  // Project Meetings context
  const [meetings, setMeetings] = useState<any[]>([]);

  // Project Documents list
  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<any>(null);
  const [documentLoading, setDocumentLoading] = useState(false);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());

  const toggleFolder = (folder: string) => {
    setExpandedFolders(prev => {
      const next = new Set(prev);
      next.has(folder) ? next.delete(folder) : next.add(folder);
      return next;
    });
  };

  // Mapped human -> digital -> subagent hierarchy
  const [workerTree, setWorkerTree] = useState<WorkerHierarchyNode[]>([]);

  // Real BA-designed team: status + polling ──────────────────────────
  // team_status: 'pending' | 'generating' | 'ready' | 'failed' (from backend).
  // While generating we show a realistic "assembling team" state; when ready
  // we replace the mock workerTree with the real agent org chart.
  const [teamStatus, setTeamStatus] = useState<string>('pending');
  const [teamLoaded, setTeamLoaded] = useState(false);
  // Raw agent rows from /team (full fields: tool_policy, designation, department,
  // status, …) — the Harness tab reads these directly, not the pruned tree nodes.
  const [teamAgents, setTeamAgents] = useState<any[]>([]);
  const [teamPositions, setTeamPositions] = useState<any[]>([]);
  const [hirePosition, setHirePosition] = useState<any | null>(null);
  const [hiringPositionId, setHiringPositionId] = useState<string | null>(null);
  const [hireAgentForm] = Form.useForm();

  const applyWorkspaceData = (res: any) => {
    setData(res);
    if (res.project) setProjectData(res.project);
    setQueueItems(res.queue || []);
    setDocuments(res.documents || []);
    setProjectTimeline(res.timeline || []);
    setExecutionLogs(res.logs || []);
    setMeetings(res.meetings || []);
    setPhase(res.currentPhase || '');
    setProgress(typeof res.progress === 'number' ? res.progress : null);
    setProjectNotFound(false);
  };

  const flattenTeamAgents = (positions: any[]) =>
    positions.map((position) => {
      const assigned = position.assigned_agent || {};
      return {
        ...position,
        ...assigned,
        id: position.id,
        position_id: position.id,
        agent_id: assigned.id,
        name: assigned.name || position.name,
        role: position.role,
        designation: position.designation,
        department: position.department,
        skills: assigned.skills || position.skills || [],
        certificates: assigned.certificates || [],
        automation: position.automation || assigned.automation || {},
        features: position.features || assigned.features || {},
        filled: Boolean(position.assigned_agent),
      };
    });

  const buildTeamTree = (
    positions: any[],
    humanOwner?: any,
    organizationMembers: any[] = [],
    humanAssignments: any[] = [],
  ): WorkerHierarchyNode[] => {
    const agentNodes: Record<string, WorkerHierarchyNode> = {};

    for (const position of positions) {
      const assigned = position.assigned_agent;
      const policy = assigned?.tool_policy || position.tool_policy || {};
      agentNodes[position.id] = {
        id: position.id,
        positionId: position.id,
        assignedAgentId: assigned?.id,
        name: assigned?.name || position.name || position.designation || 'Required Agent',
        type: 'agent',
        status: assigned ? 'WAITING' : 'BLOCKED',
        task: position.designation || position.role,
        progress: 0,
        assignedWork: position.role_description || '',
        role: position.role,
        model: assigned?.model || position.model || undefined,
        goal: position.role_description || undefined,
        instructions: assigned?.system_prompt_addon || position.system_prompt_addon || undefined,
        knowledge: Array.isArray(assigned?.skills) ? assigned.skills : (Array.isArray(position.skills) ? position.skills : []),
        tools: Array.isArray(policy.allowed_tools) ? policy.allowed_tools : [],
        certificates: Array.isArray(assigned?.certificates) ? assigned.certificates : [],
        department: position.department,
        requiredDesignation: position.designation || position.role,
        vacant: !assigned,
        children: [],
      };
    }

    const membersById = new Map<string, any>(
      organizationMembers.map((member: any) => [member.id, member]),
    );
    if (humanOwner?.id && !membersById.has(humanOwner.id)) {
      membersById.set(humanOwner.id, humanOwner);
    }

    const ownerByPosition = new Map<string, any>();
    for (const assignment of humanAssignments || []) {
      if (assignment?.scope === 'position_owner' && assignment.position_id && assignment.organization_member) {
        ownerByPosition.set(assignment.position_id, assignment.organization_member);
        membersById.set(assignment.organization_member.id, assignment.organization_member);
      }
    }

    const participatingMemberIds = new Set<string>();
    const includeMemberAndManagers = (memberId?: string) => {
      let currentId = memberId;
      const seen = new Set<string>();
      while (currentId && !seen.has(currentId)) {
        seen.add(currentId);
        const member = membersById.get(currentId);
        if (!member) break;
        participatingMemberIds.add(currentId);
        currentId = member.reports_to || undefined;
      }
    };

    if (humanOwner?.id) includeMemberAndManagers(humanOwner.id);
    for (const owner of ownerByPosition.values()) includeMemberAndManagers(owner.id);

    if (participatingMemberIds.size === 0 && humanOwner?.id) {
      participatingMemberIds.add(humanOwner.id);
    }

    const humanNodes = new Map<string, WorkerHierarchyNode>();
    for (const memberId of participatingMemberIds) {
      const member = membersById.get(memberId);
      if (!member) continue;
      humanNodes.set(memberId, {
        id: `human:${member.id}`,
        organizationMemberId: member.id,
        name: member.name || 'Project Owner',
        type: 'human',
        status: 'RUNNING',
        task: member.designation || member.role || 'Project Owner',
        progress: 0,
        assignedWork: member.role_description || 'Owns project governance and human oversight for this workspace.',
        role: member.role,
        department: member.department,
        knowledge: Array.isArray(member.skills) ? member.skills : [],
        children: [],
      });
    }

    const roots: WorkerHierarchyNode[] = [];
    for (const memberId of participatingMemberIds) {
      const member = membersById.get(memberId);
      const node = humanNodes.get(memberId);
      if (!member || !node) continue;
      const parent = member.reports_to ? humanNodes.get(member.reports_to) : undefined;
      if (parent) parent.children!.push(node);
      else roots.push(node);
    }

    const fallbackHuman = humanOwner?.id ? humanNodes.get(humanOwner.id) : undefined;
    for (const position of positions) {
      const owner = ownerByPosition.get(position.id);
      const humanNode = owner?.id ? humanNodes.get(owner.id) : fallbackHuman;
      const agentNode = agentNodes[position.id];
      if (humanNode) {
        agentNode.responsibility = 'primary_owner';
        humanNode.children!.push(agentNode);
      } else {
        roots.push(agentNode);
      }
    }

    const sortNodes = (items: WorkerHierarchyNode[]) => {
      items.sort((left, right) => {
        if (left.type !== right.type) return left.type === 'human' ? -1 : 1;
        return left.name.localeCompare(right.name);
      });
      items.forEach((item) => { if (item.children?.length) sortNodes(item.children); });
    };
    sortNodes(roots);
    return roots;
  };

  const applyTeamPayload = (res: any) => {
    const positions = Array.isArray(res.positions) ? res.positions : [];
    const tree = buildTeamTree(
      positions,
      res.human_owner,
      Array.isArray(res.organization_members) ? res.organization_members : [],
      Array.isArray(res.human_assignments) ? res.human_assignments : [],
    );
    setWorkerTree(tree);
    setTeamPositions(positions);
    setTeamAgents(flattenTeamAgents(positions));
    setSelectedWorkerId(tree[0]?.id || '');
    setExpandedKeys(expandedNodeMap(tree));
    setTeamLoaded(true);
  };

  const expandedNodeMap = (nodes: WorkerHierarchyNode[]) => {
    const expanded: Record<string, boolean> = {};
    const visit = (items: WorkerHierarchyNode[]) => {
      for (const item of items) {
        expanded[item.id] = true;
        if (item.children?.length) visit(item.children);
      }
    };
    visit(nodes);
    return expanded;
  };

  useEffect(() => {
    if (!id || isLegacyDemoId) return;
    let cancelled = false;
    let timer: any;

    const poll = async () => {
      try {
        const res = await ApiClient.get(`/discovery/projects/${id}/team`);
        if (cancelled) return;
        setTeamStatus(res.team_status || 'pending');
        if (res.team_status === 'ready') {
          if (cancelled) return;
          applyTeamPayload(res);
          void ApiClient.get(`/projects/${id}/workspace`)
            .then((workspace) => { if (!cancelled) applyWorkspaceData(workspace); })
            .catch(() => {});
          return; // stop polling
        }
        if (res.team_status === 'failed') return; // stop polling; show retry
        // still pending/generating — keep polling
        timer = setTimeout(poll, 3000);
      } catch {
        // Endpoint may 404 for legacy/mock projects — stop quietly, keep mock tree.
        if (!cancelled) {
          setTeamStatus('none');
          setWorkerTree([]);
          setTeamAgents([]);
          setSelectedWorkerId('');
          setTeamLoaded(true);
        }
      }
    };
    poll();
    return () => { cancelled = true; if (timer) clearTimeout(timer); };
  }, [id, isLegacyDemoId]);

  const openHireRequest = (positionOrNode: any) => {
    const position = teamPositions.find((p) => p.id === (positionOrNode.positionId || positionOrNode.id)) || positionOrNode;
    setHirePosition(position);
    hireAgentForm.setFieldsValue({
      name: `${position.designation || position.requiredDesignation || position.role || 'Project'} Agent`,
      role: position.role || 'agent',
      department: position.department || 'delivery',
      role_description: position.role_description || position.assignedWork || '',
      skills: (position.skills || position.knowledge || []).join(', '),
    });
  };

  const requestToHire = async () => {
    if (!hirePosition) return;
    if (!id) return;
    setHiringPositionId(hirePosition.id);
    try {
      const values = await hireAgentForm.validateFields();
      const token = localStorage.getItem('auth_token');
      const headers: HeadersInit = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };
      const hireRes = await fetch('/agents/hire-for-position', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          position_id: hirePosition.id,
          name: values.name,
          role: values.role,
          department: values.department,
          role_description: values.role_description || '',
          skills: values.skills ? values.skills.split(',').map((s: string) => s.trim()).filter(Boolean) : [],
        }),
      });
      if (!hireRes.ok) throw new Error((await hireRes.json()).detail || 'Failed to hire agent');
      await hireRes.json();
      const teamPayload = await ApiClient.get(`/discovery/projects/${id}/team`);
      applyTeamPayload(teamPayload);
      setHirePosition(null);
      hireAgentForm.resetFields();
      message.success(`Agent hired for "${hirePosition.designation || hirePosition.role}"`);
    } catch (err) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      message.error(`Request to hire failed: ${err instanceof Error ? err.message : 'unknown error'}`);
    } finally {
      setHiringPositionId(null);
    }
  };

  // Re-trigger team design (from the 'failed' state), then resume polling.
  const regenerateTeam = async () => {
    if (!id) return;
    try {
      setTeamStatus('generating');
      await ApiClient.post(`/discovery/projects/${id}/design-team`, {});
      const poll = async () => {
        try {
          const res = await ApiClient.get(`/discovery/projects/${id}/team`);
          setTeamStatus(res.team_status || 'pending');
          if (res.team_status === 'ready') {
            applyTeamPayload(res);
            void ApiClient.get(`/projects/${id}/workspace`)
              .then(applyWorkspaceData)
              .catch(() => {});
            return;
          }
          if (res.team_status === 'failed') return;
          setTimeout(poll, 3000);
        } catch {
          /* stop quietly */
        }
      };
      setTimeout(poll, 3000);
    } catch {
      message.error('Could not restart team assignment.');
      setTeamStatus('failed');
    }
  };

  // Project Stage & Procurement Events History
  const [projectTimeline, setProjectTimeline] = useState<any[]>([]);

  // Execution Feed Logs (aggregated logs of the OS)
  const [executionLogs, setExecutionLogs] = useState<string[]>([]);

  // Modals for Actions
  const [activeActionModal, setActiveActionModal] = useState<string | null>(null);
  const [selectedHumanOwnerId, setSelectedHumanOwnerId] = useState<string>('emp-1');
  const [actionForm] = Form.useForm();

  const fetchWorkspaceData = async () => {
    if (isLegacyDemoId) return;
    try {
      setLoading(true);
      const res = await ApiClient.get(`/projects/${id}/workspace`);
      applyWorkspaceData(res);
    } catch (err) {
      setProjectNotFound(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id && !isLegacyDemoId) fetchWorkspaceData();
  }, [id, isLegacyDemoId]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;
    const val = inputValue;
    setChatMessages(prev => [...prev, { sender: 'User', text: val, time: new Date().toLocaleTimeString() }]);
    setInputValue('');

    setExecutionLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] [USER] Instructed: "${val}"`]);

    try {
      const res = await ApiClient.post(`/projects/${id || 'demo'}/workspace/chat`, { message: val });
      setChatMessages(prev => [...prev, {
        sender: 'Chief of Staff',
        text: res.reply,
        understanding: res.understanding,
        reasoning: res.reasoning,
        decision: res.decision,
        planUpdate: res.planUpdate,
        workerActions: res.workerActions,
        requiredApprovals: res.requiredApprovals,
        expectedOutcome: res.time
      }]);
      setExecutionLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] [CO-PILOT] Decision updated: ${res.decision}`]);
    } catch (e) {
      message.error('Failed to communicate with General AI');
    }
  };

  const openDocument = async (doc: any) => {
    if (!id || !doc?.id) {
      message.warning('This document is missing a backend artifact id.');
      return;
    }
    setSelectedDocument({ ...doc, content: '' });
    setDocumentLoading(true);
    try {
      const loaded = await ApiClient.get(`/projects/${id}/documents/${encodeURIComponent(doc.id)}`);
      setSelectedDocument(loaded);
    } catch (err) {
      ApiClient.handleError(err);
      setSelectedDocument(null);
    } finally {
      setDocumentLoading(false);
    }
  };

  const handleApproveQueueItem = async (itemId: string) => {
    try {
      await ApiClient.post(`/queue/${itemId}/action`, { action: 'approve' });
      await fetchWorkspaceData();
      message.success('Human intervention approved.');
    } catch (err) {
      ApiClient.handleError(err);
    }
  };

  const handleRejectQueueItem = async (itemId: string) => {
    try {
      await ApiClient.post(`/queue/${itemId}/action`, { action: 'reject' });
      await fetchWorkspaceData();
      message.warning('Human intervention rejected.');
    } catch (err) {
      ApiClient.handleError(err);
    }
  };

  const handleDeleteCurrentProject = async () => {
    if (!id) return;
    try {
      await ApiClient.delete(`/projects/${id}`);
      message.success('Project deleted.');
      navigate('/projects', { replace: true });
    } catch (err) {
      ApiClient.handleError(err);
    }
  };

  const handleCreateDigitalEmployee = (_values: any) => {
    message.info('Worker hierarchy is generated from finalized project requirements.');
    setActiveActionModal(null);
    actionForm.resetFields();
  };

  const updateAgentInTree = (nodes: WorkerHierarchyNode[], targetId: string, updates: Partial<WorkerHierarchyNode>): WorkerHierarchyNode[] => {
    return nodes.map(node => {
      if (node.id === targetId) {
        return { ...node, ...updates };
      }
      if (node.children) {
        return {
          ...node,
          children: updateAgentInTree(node.children, targetId, updates)
        };
      }
      return node;
    });
  };

  const handleUpdateAgentConfig = (updates: Partial<WorkerHierarchyNode>) => {
    setWorkerTree(prev => updateAgentInTree(prev, selectedWorkerId, updates));
    message.success('Agent operational parameters synced.');
    setExecutionLogs(prev => [...prev, `[SYSTEM] Updated parameters for node ID: ${selectedWorkerId}`]);
  };

  const findWorkerInTree = (nodes: WorkerHierarchyNode[], targetId: string): WorkerHierarchyNode | undefined => {
    for (const node of nodes) {
      if (node.id === targetId) return node;
      if (node.children) {
        const found = findWorkerInTree(node.children, targetId);
        if (found) return found;
      }
    }
    return undefined;
  };

  const emptyWorker: WorkerHierarchyNode = {
    id: '',
    name: 'No worker selected',
    type: 'agent',
    status: 'WAITING',
    task: '',
    progress: 0,
    assignedWork: '',
    role: '',
    memory: [],
    knowledge: [],
    tools: [],
    logs: [],
    artifacts: [],
    certificates: [],
  };
  const selectedWorker = findWorkerInTree(workerTree, selectedWorkerId) || workerTree[0] || emptyWorker;

  const renderTreeNodes = (nodes: WorkerHierarchyNode[]) => {
    return nodes.map(node => {
      const isExpanded = !!expandedKeys[node.id];
      const hasChildren = node.children && node.children.length > 0;
      const isSelected = selectedWorkerId === node.id;

      const badgeColors = {
        human: { bg: '#ECFDF5', text: '#047857' },
        digital: { bg: ui.color.primarySoft, text: ui.color.primary },
        agent: node.vacant ? { bg: '#F3F4F6', text: '#94A3B8' } : { bg: ui.color.violetSoft, text: ui.color.violet }
      };
      const st = node.type === 'human'
        ? { bg: '#ECFDF5', text: '#047857', dot: '#10B981', label: 'Human' }
        : STATUS_STYLE[node.status] || STATUS_STYLE.WAITING;
      const selectedBackground = node.vacant ? '#F9FAFB' : (node.type === 'human' ? '#F0FDF4' : ui.color.primarySoft);
      const selectedBorder = node.vacant ? '#D1D5DB' : (node.type === 'human' ? '#86EFAC' : '#BFDBFE');

      return (
        <div key={node.id} style={{ marginLeft: node.type === 'human' ? 0 : 14, marginBottom: 6 }}>
          <div
            onClick={() => {
              if (node.vacant) {
                openHireRequest(node);
                return;
              }
              setSelectedWorkerId(node.id);
              setIsWorkerInspectorOpen(true);
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '8px 10px',
              borderRadius: ui.radius.sm,
              background: isSelected ? selectedBackground : ui.color.surface,
              border: node.vacant ? `1px dashed ${isSelected ? selectedBorder : '#CBD5E1'}` : `1px solid ${isSelected ? selectedBorder : ui.color.border}`,
              cursor: 'pointer',
              opacity: node.vacant ? 0.72 : 1,
              boxShadow: isSelected ? 'none' : ui.shadow.xs,
              transition: 'all 0.15s',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
              {hasChildren ? (
                <span
                  onClick={(e) => {
                    e.stopPropagation();
                    setExpandedKeys({ ...expandedKeys, [node.id]: !isExpanded });
                  }}
                  style={{ color: ui.color.textFaint, display: 'flex', width: 12 }}
                >
                  {isExpanded ? <DownOutlined style={{ fontSize: 9 }} /> : <RightOutlined style={{ fontSize: 9 }} />}
                </span>
              ) : <span style={{ width: 12 }} />}
              <Avatar size={28} icon={node.type === 'human' ? <UserOutlined /> : <RobotOutlined />} style={{ background: badgeColors[node.type].bg, color: badgeColors[node.type].text, flexShrink: 0 }} />
              <div style={{ minWidth: 0 }}>
                <Text strong style={{ fontSize: 12, color: node.vacant ? '#94A3B8' : ui.color.text, display: 'block', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{node.name}</Text>
                <Text type="secondary" style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: 0.4 }}>
                  {node.vacant ? node.requiredDesignation || node.task || 'Required agent' : (node.type === 'human' ? node.task || 'Human' : 'Agent')}
                </Text>
              </div>
            </div>

            {node.vacant ? (
              <Button
                size="small"
                onClick={(event) => {
                  event.stopPropagation();
                  openHireRequest(node);
                }}
                style={{ fontSize: 9, padding: '0 7px', height: 22, borderColor: '#93C5FD', color: '#2563EB', background: '#EFF6FF' }}
              >
                Request Hire
              </Button>
            ) : (
              <Tooltip title={st.label}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '3px 8px', borderRadius: ui.radius.pill, background: st.bg, flexShrink: 0 }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: st.dot }} />
                  <span style={{ fontSize: 9, fontWeight: 600, color: st.text }}>{st.label}</span>
                </div>
              </Tooltip>
            )}
          </div>

          {hasChildren && isExpanded && (
            <div style={{ marginTop: 6, borderLeft: `1px dashed ${ui.color.borderStrong}`, paddingLeft: 8 }}>
              {renderTreeNodes(node.children!)}
            </div>
          )}
        </div>
      );
    });
  };

  const glassStyle = {
    background: '#FFFFFF',
    border: '1px solid #E2E8F0',
    borderRadius: 6,
    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.02)',
    marginBottom: 16
  };

  const workspaceKpis = Array.isArray(data?.kpis) ? data.kpis : [];
  const kpiMeta: Record<string, { accent: string; soft: string; icon: React.ReactNode }> = {
    currentPhase: { accent: ui.color.primary, soft: ui.color.primarySoft, icon: <ThunderboltOutlined /> },
    progress: { accent: ui.color.success, soft: ui.color.successSoft, icon: <CheckCircleOutlined /> },
    pendingApprovals: { accent: ui.color.warning, soft: '#FEF3C7', icon: <AuditOutlined /> },
    activeWorkers: { accent: ui.color.violet, soft: ui.color.violetSoft, icon: <RobotOutlined /> },
  };
  const projectRecord = data?.project || projectData || {};
  const formatShortDate = (value?: string) => {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value).slice(0, 10);
    return date.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
  };
  const ownerDisplay = projectRecord.ownername || projectRecord.ownerName || projectRecord.owner || projectRecord.owneremail || projectRecord.ownerEmail || (projectRecord.ownerid ? 'Project Owner' : '');
  const projectDetails = [
    { label: 'Status', value: projectRecord.status },
    { label: 'Priority', value: projectRecord.priority },
    { label: 'Department', value: projectRecord.department },
    { label: 'Owner', value: ownerDisplay },
    { label: 'Created', value: formatShortDate(projectRecord.createdat) },
    { label: 'Updated', value: formatShortDate(projectRecord.updatedat) },
  ].filter((item) => item.value);
  const scopeSignals = [
    { label: 'Requirements', value: requirements?.functionalReqs?.length || 0, icon: <CheckCircleOutlined /> },
    { label: 'Risks', value: requirements?.risks?.length || 0, icon: <WarningOutlined /> },
    { label: 'Documents', value: documents.length, icon: <FileTextOutlined /> },
    { label: 'Workers', value: teamAgents.length, icon: <RobotOutlined /> },
    { label: 'Meetings', value: meetings.length, icon: <CalendarOutlined /> },
    { label: 'Approvals', value: queueItems.length, icon: <AuditOutlined /> },
  ];
  const detailPhases = Array.isArray(requirements?.phases) ? requirements.phases : [];
  const detailRequirementGroups = [
    { title: 'Functional Requirements', items: requirements?.functionalReqs || [] },
    { title: 'Tech Stack', items: requirements?.techStack || [] },
    { title: 'Required Skills', items: requirements?.skills || [] },
    { title: 'Connectors', items: requirements?.connectors || [] },
    { title: 'Risks', items: requirements?.risks || [] },
  ].filter((group) => group.items.length > 0);
  const detailControlGroups = [
    { title: 'Governance', items: requirements?.governance || [] },
    { title: 'Guardrails', items: requirements?.guardrails || [] },
    { title: 'Infrastructure', items: requirements?.infrastructure || [] },
  ].filter((group) => group.items.length > 0);
  const detailText = (item: any) => {
    if (typeof item === 'string') return item;
    if (!item || typeof item !== 'object') return String(item || '');
    return [item.label, item.detail].filter(Boolean).join(': ') || JSON.stringify(item);
  };
  const documentGroups = documents.reduce((groups: Record<string, any[]>, doc) => {
    const key = doc.category || doc.type || 'Document';
    groups[key] = groups[key] || [];
    groups[key].push(doc);
    return groups;
  }, {});

  if (isLegacyDemoId) return null;

  if (loading) {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: ui.color.bg }}>
        <Spin indicator={<LoadingOutlined style={{ fontSize: 22, color: ui.color.primary }} spin />} />
      </div>
    );
  }

  if (projectNotFound) {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: ui.color.bg }}>
        <Card style={{ width: 420, border: `1px solid ${ui.color.border}`, borderRadius: ui.radius.md }} bodyStyle={{ padding: 24, textAlign: 'center' }}>
          <Text strong style={{ display: 'block', fontSize: 15, color: ui.color.text, marginBottom: 8 }}>Project not found</Text>
          <Text style={{ display: 'block', fontSize: 12, color: ui.color.textMuted, marginBottom: 16 }}>This workspace route does not point to a saved backend project.</Text>
          <Button type="primary" onClick={() => navigate('/projects')}>Back to projects</Button>
        </Card>
      </div>
    );
  }

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: ui.color.primary,
          colorBgContainer: ui.color.surface,
          colorBgLayout: ui.color.bg,
          colorBorder: ui.color.border,
          colorText: ui.color.text,
          colorTextSecondary: ui.color.textMuted,
          borderRadius: ui.radius.sm,
          fontFamily: 'Inter, system-ui, sans-serif',
        },
        components: {
          Card: { borderRadiusLG: ui.radius.md },
          Button: { borderRadius: ui.radius.sm, fontWeight: 500 },
          Tag: { borderRadiusSM: ui.radius.pill },
        },
      }}
    >
      <Layout style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: ui.color.bg, color: ui.color.text, fontFamily: 'Inter, system-ui, sans-serif' }}>

        {/* TOP BAR */}
        <Header style={{ background: ui.color.surface, padding: '0 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: `1px solid ${ui.color.border}`, height: 64, lineHeight: 'normal', flexShrink: 0, zIndex: 20, boxShadow: ui.shadow.xs }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, minWidth: 0 }}>
            <Tooltip title="Back to projects">
              <Button type="text" shape="circle" icon={<ArrowLeftOutlined />} onClick={() => navigate('/projects')} style={{ color: ui.color.textMuted }} />
            </Tooltip>
            <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0, lineHeight: 1.25 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <SectionLabel style={{ fontSize: 9.5 }}>Workspace</SectionLabel>
                <span style={{ width: 3, height: 3, borderRadius: '50%', background: ui.color.textFaint }} />
                <SectionLabel style={{ fontSize: 9.5, color: ui.color.textFaint }}>{phase}</SectionLabel>
              </div>
              <Text strong style={{ fontSize: 15, color: ui.color.text, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {projectTitle}
              </Text>
            </div>
            <div style={{ width: 1, height: 28, background: ui.color.border, margin: '0 4px' }} />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 1, lineHeight: 1.2 }}>
              <SectionLabel style={{ fontSize: 9 }}>Opportunity</SectionLabel>
              <Select
                value={activeOpportunityId}
                variant="borderless"
                onChange={setActiveOpportunityId}
                style={{ width: 210, fontWeight: 600, marginLeft: -11 }}
                size="small"
                options={opportunitiesList.map(o => ({ value: o.id, label: o.label }))}
              />
            </div>
          </div>

          <Space size={12}>
            {progress !== null && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '5px 12px', borderRadius: ui.radius.pill, background: ui.color.surfaceMuted, border: `1px solid ${ui.color.border}` }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', lineHeight: 1.1 }}>
                  <Text strong style={{ fontSize: 12, color: ui.color.text }}>{progress}%</Text>
                  <SectionLabel style={{ fontSize: 8 }}>Complete</SectionLabel>
                </div>
                <Progress type="circle" percent={progress} size={30} strokeColor={ui.color.primary} trailColor={ui.color.border} strokeWidth={10} format={() => ''} />
              </div>
            )}
            <Button icon={<PlayCircleOutlined />} disabled onClick={() => navigate(`/projects/${id}/simulation`)} style={{ color: '#aaa', borderColor: '#ddd', background: '#f5f5f5', fontWeight: 500, opacity: 0.6, cursor: 'not-allowed' }}>
              Simulate
            </Button>
            <Popconfirm
              title="Delete project?"
              description="This will remove this workspace, meetings, workers, documents, and board items."
              okText="Delete"
              okButtonProps={{ danger: true }}
              cancelText="Cancel"
              onConfirm={handleDeleteCurrentProject}
            >
              <Button danger icon={<DeleteOutlined />}>Delete</Button>
            </Popconfirm>
            <Button type="primary" onClick={() => navigate('/home')} style={{ fontWeight: 600 }}>Dashboard</Button>
          </Space>
        </Header>

        {/* WORKSPACE LAYOUT PANELS */}
        <Layout style={{ flex: 1, overflow: 'hidden', background: ui.color.bg, display: 'flex', flexDirection: 'row', gap: 16, padding: 16 }}>

          {/* LEFT PANEL: WORKER HIERARCHY & DOCUMENT KNOWLEDGE */}
          <Sider width={340} style={{ background: ui.color.surface, border: `1px solid ${ui.color.border}`, borderRadius: ui.radius.md, padding: '18px 14px', overflowY: 'auto', boxShadow: ui.shadow.sm }} className="custom-scroll">
            <div style={{ marginBottom: 22 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                <SectionLabel>Worker Hierarchy</SectionLabel>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {teamStatus === 'generating' || teamStatus === 'pending' ? (
                  <div style={{ padding: '8px 2px', display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                      <Spin indicator={<LoadingOutlined style={{ fontSize: 14, color: ui.color.primary }} spin />} />
                      <Text style={{ fontSize: 12, color: ui.color.textMuted, fontWeight: 500 }}>Assigning your project team…</Text>
                    </div>
                    {[0, 1, 2].map((i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px', borderRadius: ui.radius.sm, background: ui.color.surface, border: `1px solid ${ui.color.border}`, opacity: 1 - i * 0.25 }}>
                        <Skeleton.Avatar active size={28} shape="circle" />
                        <Skeleton.Input active size="small" style={{ width: 140 - i * 30, height: 12 }} />
                      </div>
                    ))}
                  </div>
                ) : teamStatus === 'failed' ? (
                  <div style={{ padding: '10px 12px', borderRadius: ui.radius.sm, background: '#FEF2F2', border: '1px solid #FECACA', display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <Text style={{ fontSize: 12, color: '#B91C1C' }}>Team assignment didn't complete.</Text>
                    <Button size="small" onClick={regenerateTeam} icon={<RobotOutlined style={{ fontSize: 11 }} />} style={{ fontSize: 11, alignSelf: 'flex-start' }}>
                      Regenerate team
                    </Button>
                  </div>
                ) : workerTree.length === 0 ? (
                  <Text style={{ fontSize: 12, color: ui.color.textMuted }}>No worker hierarchy has been generated yet.</Text>
                ) : (
                  renderTreeNodes(workerTree)
                )}
              </div>
            </div>

            <Divider style={{ margin: '18px 0', borderColor: ui.color.border }} />

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                <SectionLabel>Knowledge Base</SectionLabel>
                <Text style={{ fontSize: 10, fontWeight: 600, color: ui.color.textFaint }}>{documents.length} files</Text>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {documents.length === 0 && (
                  <Text style={{ fontSize: 12, color: ui.color.textMuted }}>No project documents yet.</Text>
                )}
                {Object.entries(documentGroups).sort(([a], [b]) => a.localeCompare(b)).map(([folder, docs]) => {
                  const isOpen = expandedFolders.has(folder);
                  return (
                    <div key={folder}>
                      <div
                        role="button"
                        tabIndex={0}
                        onClick={() => toggleFolder(folder)}
                        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') toggleFolder(folder); }}
                        style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px', borderRadius: ui.radius.sm, cursor: 'pointer', background: isOpen ? ui.color.primarySoft : ui.color.surface, border: `1px solid ${isOpen ? ui.color.primary + '33' : ui.color.border}`, transition: 'all 0.15s' }}
                      >
                        {isOpen
                          ? <FolderOpenOutlined style={{ fontSize: 15, color: ui.color.primary }} />
                          : <FolderOutlined style={{ fontSize: 15, color: ui.color.textMuted }} />
                        }
                        <Text style={{ fontSize: 12, fontWeight: 600, color: isOpen ? ui.color.primary : ui.color.text, flex: 1 }}>{folder}</Text>
                        <Tag style={{ margin: 0, fontSize: 9, border: 'none', background: ui.color.surfaceMuted, color: ui.color.textMuted }}>{(docs as any[]).length}</Tag>
                      </div>
                      {isOpen && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 4, paddingLeft: 12 }}>
                          {(docs as any[]).map((doc, i) => (
                            <div
                              key={i}
                              role="button"
                              tabIndex={0}
                              onClick={() => openDocument(doc)}
                              onKeyDown={(event) => {
                                if (event.key === 'Enter' || event.key === ' ') openDocument(doc);
                              }}
                              style={{ background: ui.color.surface, border: `1px solid ${ui.color.border}`, padding: '8px 10px', borderRadius: ui.radius.sm, display: 'flex', alignItems: 'center', gap: 10, transition: 'all 0.15s', cursor: 'pointer', boxShadow: ui.shadow.xs }}
                            >
                              <div style={{ width: 28, height: 28, borderRadius: ui.radius.sm, background: ui.color.surfaceMuted, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                                <FileTextOutlined style={{ color: ui.color.primary, fontSize: 13 }} />
                              </div>
                              <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
                                <Text strong style={{ fontSize: 11, color: ui.color.text, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{doc.name}</Text>
                                <Text type="secondary" style={{ fontSize: 9 }}>{doc.size} • {doc.category}</Text>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </Sider>

          {/* CENTER PANEL: MILESTONES */}
          <Content style={{ display: 'flex', flexDirection: 'column', overflowY: 'auto' }} className="custom-scroll">

            {/* PHASE SUMMARY STRIP */}
            {workspaceKpis.length > 0 && (
            <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
              {workspaceKpis.map((k: any, i: number) => {
                const meta = kpiMeta[k.key] || kpiMeta.currentPhase;
                return (
                <Card
                  key={i}
                  role="button"
                  tabIndex={0}
                  onClick={() => setCenterTab('board')}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') setCenterTab('board');
                  }}
                  style={{ flex: 1, border: `1px solid ${ui.color.border}`, borderRadius: ui.radius.md, boxShadow: ui.shadow.sm, cursor: 'pointer' }}
                  bodyStyle={{ padding: 14 }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ width: 36, height: 36, borderRadius: ui.radius.sm, background: meta.soft, color: meta.accent, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16 }}>
                      {meta.icon}
                    </div>
                    <div style={{ minWidth: 0 }}>
                      <SectionLabel style={{ fontSize: 9 }}>{k.label}</SectionLabel>
                      <Text strong style={{ fontSize: 16, color: ui.color.text, display: 'block', lineHeight: 1.2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{k.value}</Text>
                    </div>
                  </div>
                </Card>
                );
              })}
            </div>
            )}

            {/* CENTER TAB BAR */}
            <div style={{ display: 'flex', gap: 4, marginBottom: 18, borderBottom: `1px solid ${ui.color.border}` }}>
              {[
                { key: 'overview', label: 'Overview', icon: <CalendarOutlined /> },
                { key: 'meetings', label: 'Meetings', icon: <CalendarOutlined /> },
                { key: 'knowledge', label: 'Knowledge', icon: <BookOutlined /> },
                { key: 'blueprint', label: 'Blueprint', icon: <PartitionOutlined /> },
                { key: 'board', label: 'Board', icon: null },
                { key: 'connectors', label: 'Connectors', icon: <ApiOutlined /> },
              ].map((t) => (
                <button
                  key={t.key}
                  onClick={() => setCenterTab(t.key as 'overview' | 'meetings' | 'knowledge' | 'blueprint' | 'board' | 'connectors')}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px',
                    border: 'none', background: 'transparent', cursor: 'pointer',
                    fontSize: 13, fontWeight: centerTab === t.key ? 600 : 500,
                    color: centerTab === t.key ? ui.color.primary : ui.color.textMuted,
                    borderBottom: `2px solid ${centerTab === t.key ? ui.color.primary : 'transparent'}`,
                    marginBottom: -1,
                  }}
                >
                  {t.icon}{t.label}
                </button>
              ))}
            </div>

            {/* OVERVIEW — objective summary + refined milestone rail */}
            {centerTab === 'connectors' && (
              <ProjectConnectorsPanel
                requirementConnectors={requirements?.connectors || []}
                workers={teamAgents}
              />
            )}

            {centerTab === 'board' && (
              <div style={{ marginBottom: 20 }}>
                <div style={{ padding: '10px 12px', borderRadius: 8, border: '1px solid #FED7AA', background: '#FFF7ED', marginBottom: 16 }}>
                  <Text style={{ fontSize: 12, color: '#9A3412' }}>This board will be connected to the company's scrum board to maintain transparency between aegisOS and the company.</Text>
                </div>
                <ProjectWorkBoard projectId={id || 'demo'} />
              </div>
            )}

            {centerTab === 'overview' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 20 }}>

                {/* PROJECT DETAILS */}
                <Card style={{ border: `1px solid ${ui.color.border}`, borderRadius: ui.radius.md, boxShadow: ui.shadow.sm }} bodyStyle={{ padding: 18 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start', marginBottom: 14 }}>
                    <div style={{ minWidth: 0 }}>
                      <SectionLabel style={{ fontSize: 9, marginBottom: 6 }}>Project Details</SectionLabel>
                      <Text strong style={{ fontSize: 15, color: ui.color.text, display: 'block', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{projectTitle}</Text>
                      {projectRecord.businessgoal && (
                        <Text style={{ fontSize: 12, color: ui.color.textMuted, lineHeight: 1.5, display: 'block', marginTop: 4 }}>{projectRecord.businessgoal}</Text>
                      )}
                    </div>
                    {teamStatus === 'ready' ? (
                      <Tag style={{ margin: 0, border: 'none', background: ui.color.successSoft, color: '#15803D', fontSize: 11 }}>Workspace ready</Tag>
                    ) : (
                      <Tag style={{ margin: 0, border: 'none', background: ui.color.surfaceMuted, color: ui.color.textMuted, fontSize: 11 }}>{teamStatus || 'Loading'}</Tag>
                    )}
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 8, marginBottom: 14 }}>
                    {projectDetails.map((item) => (
                      <div key={item.label} style={{ border: `1px solid ${ui.color.border}`, borderRadius: ui.radius.sm, padding: '8px 10px', background: ui.color.surfaceMuted, minWidth: 0 }}>
                        <SectionLabel style={{ fontSize: 8, marginBottom: 4 }}>{item.label}</SectionLabel>
                        <Text style={{ fontSize: 12, color: ui.color.text, fontWeight: 600, display: 'block', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.value}</Text>
                      </div>
                    ))}
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(92px, 1fr))', gap: 8 }}>
                    {scopeSignals.map((item) => (
                      <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px', borderRadius: ui.radius.sm, border: `1px solid ${ui.color.border}`, background: ui.color.surface }}>
                        <span style={{ color: ui.color.primary, fontSize: 13 }}>{item.icon}</span>
                        <div style={{ minWidth: 0 }}>
                          <Text strong style={{ display: 'block', color: ui.color.text, fontSize: 13, lineHeight: 1 }}>{item.value}</Text>
                          <Text style={{ color: ui.color.textMuted, fontSize: 10 }}>{item.label}</Text>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>

                {/* OBJECTIVE SUMMARY */}
                {(requirements?.objective || (requirements?.techStack?.length ?? 0) > 0) && (
                  <Card style={{ border: `1px solid ${ui.color.border}`, borderRadius: ui.radius.md, boxShadow: ui.shadow.sm }} bodyStyle={{ padding: 18 }}>
                    {requirements?.objective && (
                      <>
                        <SectionLabel style={{ fontSize: 9, marginBottom: 6 }}>Objective</SectionLabel>
                        <Text style={{ fontSize: 13, color: ui.color.text, lineHeight: 1.6, display: 'block' }}>{requirements.objective}</Text>
                      </>
                    )}
                    {(requirements?.techStack?.length ?? 0) > 0 && (
                      <div style={{ marginTop: requirements?.objective ? 14 : 0 }}>
                        <SectionLabel style={{ fontSize: 9, marginBottom: 8 }}>Tech Stack</SectionLabel>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                          {requirements.techStack.slice(0, 12).map((t: string, i: number) => (
                            <span key={i} style={{ fontSize: 11, padding: '2px 9px', border: `1px solid ${ui.color.border}`, background: ui.color.surfaceMuted, color: ui.color.textMuted, borderRadius: ui.radius.pill }}>{t}</span>
                          ))}
                          {requirements.techStack.length > 12 && (
                            <span style={{ fontSize: 11, padding: '2px 9px', color: ui.color.textFaint }}>+{requirements.techStack.length - 12}</span>
                          )}
                        </div>
                      </div>
                    )}
                  </Card>
                )}

                {/* MILESTONE RAIL */}
                <Card style={{ border: `1px solid ${ui.color.border}`, borderRadius: ui.radius.md, boxShadow: ui.shadow.sm }} bodyStyle={{ padding: 18 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                    <CalendarOutlined style={{ color: ui.color.primary, fontSize: 13 }} />
                    <Text strong style={{ fontSize: 13, color: ui.color.text }}>Milestones & History</Text>
                    <Tag style={{ fontSize: 9, margin: 0, marginLeft: 'auto', border: 'none', background: ui.color.surfaceMuted, color: ui.color.textMuted }}>{projectTimeline.length}</Tag>
                  </div>
                  <div style={{ position: 'relative', paddingLeft: 18 }}>
                    <div style={{ position: 'absolute', left: 4, top: 6, bottom: 6, width: 2, background: ui.color.border }} />
                    {projectTimeline.length === 0 && (
                      <Text style={{ fontSize: 12, color: ui.color.textMuted }}>No milestones or history have been recorded yet.</Text>
                    )}
                    {projectTimeline.map((item, idx) => (
                      <div key={idx} style={{ position: 'relative', paddingBottom: idx < projectTimeline.length - 1 ? 16 : 0 }}>
                        <div style={{
                          position: 'absolute', left: -17.5, top: 4, width: 9, height: 9, borderRadius: '50%',
                          background: idx === 0 ? ui.color.primary : ui.color.surface,
                          border: `2px solid ${idx === 0 ? ui.color.primary : ui.color.borderStrong}`,
                        }} />
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 8 }}>
                          <Text strong style={{ fontSize: 12, color: ui.color.text }}>{item.event}</Text>
                          <Text style={{ fontSize: 9.5, color: ui.color.textFaint, flexShrink: 0, textTransform: 'uppercase', letterSpacing: 0.3 }}>{item.date}</Text>
                        </div>
                        {item.desc && <Text style={{ fontSize: 11, color: ui.color.textMuted, lineHeight: 1.5, display: 'block', marginTop: 2 }}>{item.desc}</Text>}
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            )}

            {/* MEETINGS TAB */}
            {centerTab === 'meetings' && (
              <div style={{ marginBottom: 20 }}>
                <MeetingsCalendarDashboard
                  projectId={id}
                  meetings={meetings}
                  onMeetingsChanged={async () => {
                    if (!id) return;
                    const workspace = await ApiClient.get(`/projects/${id}/workspace`);
                    applyWorkspaceData(workspace);
                  }}
                />
              </div>
            )}

            {/* KNOWLEDGE TAB */}
            {centerTab === 'knowledge' && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12, marginBottom: 20 }}>
                <div style={{ border: `1px solid ${ui.color.border}`, borderRadius: ui.radius.sm, background: ui.color.surface, overflow: 'hidden' }}>
                  <div style={{ padding: '12px 14px', borderBottom: `1px solid ${ui.color.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text strong style={{ fontSize: 13, color: ui.color.text }}>Documents</Text>
                    <Tag style={{ margin: 0, fontSize: 10, border: 'none', background: ui.color.surfaceMuted, color: ui.color.textMuted }}>{documents.length}</Tag>
                  </div>
                  {documents.length === 0 ? (
                    <div style={{ padding: 18 }}>
                      <Text style={{ fontSize: 12, color: ui.color.textMuted }}>No Knowledge Base documents have been generated yet.</Text>
                    </div>
                  ) : Object.entries(documentGroups).sort(([a], [b]) => a.localeCompare(b)).map(([category, docs]) => (
                    <div key={category} style={{ borderTop: `1px solid ${ui.color.border}` }}>
                      <div style={{ padding: '9px 14px', background: ui.color.surfaceMuted }}>
                        <SectionLabel style={{ fontSize: 8 }}>{category}</SectionLabel>
                      </div>
                      {(docs as any[]).map((doc, index) => (
                        <div key={doc.id || `${category}-${index}`} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', borderTop: index === 0 ? 'none' : `1px solid ${ui.color.border}` }}>
                          <FileTextOutlined style={{ color: ui.color.primary, fontSize: 14 }} />
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <Text strong style={{ display: 'block', fontSize: 12, color: ui.color.text, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{doc.name}</Text>
                            <Text style={{ fontSize: 10.5, color: ui.color.textFaint }}>{doc.size || doc.path || 'Stored artifact'}</Text>
                          </div>
                          <Button size="small" icon={<EyeOutlined />} onClick={() => openDocument(doc)}>Open</Button>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {[...detailRequirementGroups, ...detailControlGroups].map((group) => (
                    <div key={group.title} style={{ border: `1px solid ${ui.color.border}`, borderRadius: ui.radius.sm, padding: 12, background: ui.color.surface }}>
                      <SectionLabel style={{ fontSize: 8, marginBottom: 8 }}>{group.title}</SectionLabel>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {group.items.slice(0, 8).map((item: any, index: number) => (
                          <Text key={index} style={{ fontSize: 11.5, color: ui.color.textMuted, lineHeight: 1.45 }}>{detailText(item)}</Text>
                        ))}
                        {group.items.length > 8 && <Text style={{ fontSize: 10.5, color: ui.color.textFaint }}>+{group.items.length - 8} more</Text>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {centerTab === 'blueprint' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 20 }}>
                {(() => {
                  const sections = [
                    { title: 'Governance', icon: <AuditOutlined />, accent: ui.color.primary, soft: ui.color.primarySoft, items: requirements?.governance || [] },
                    { title: 'Guardrails', icon: <ThunderboltOutlined />, accent: ui.color.warning, soft: '#FEF3C7', items: requirements?.guardrails || [] },
                    { title: 'Infrastructure', icon: <DatabaseOutlined />, accent: ui.color.violet, soft: ui.color.violetSoft, items: requirements?.infrastructure || [] },
                  ];
                  const hasAny = sections.some((s) => s.items.length > 0);
                  if (!hasAny) {
                    return (
                      <Card style={{ border: `1px solid ${ui.color.border}`, borderRadius: ui.radius.md, boxShadow: ui.shadow.sm }} bodyStyle={{ padding: 40, textAlign: 'center' }}>
                        <PartitionOutlined style={{ fontSize: 28, color: ui.color.textMuted, marginBottom: 12 }} />
                        <Text style={{ display: 'block', fontSize: 13, color: ui.color.textMuted }}>
                          No blueprint yet. Governance, guardrails, and infrastructure appear here once the BA discovery is finalized for this project.
                        </Text>
                      </Card>
                    );
                  }
                  return sections.map((section) => (
                    <Card key={section.title} style={{ border: `1px solid ${ui.color.border}`, borderRadius: ui.radius.md, boxShadow: ui.shadow.sm }} bodyStyle={{ padding: 20 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                        <div style={{ width: 30, height: 30, borderRadius: ui.radius.sm, background: section.soft, color: section.accent, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>
                          {section.icon}
                        </div>
                        <Text strong style={{ fontSize: 14, color: ui.color.text }}>{section.title}</Text>
                        <Tag style={{ fontSize: 10, margin: 0, marginLeft: 'auto', border: 'none', background: ui.color.surfaceMuted, color: ui.color.textMuted }}>{section.items.length}</Tag>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        {section.items.map((item: any, idx: number) => (
                          <div key={idx} style={{ display: 'flex', gap: 12, padding: '12px 14px', background: ui.color.surfaceMuted, borderRadius: ui.radius.sm, border: `1px solid ${ui.color.border}` }}>
                            <div style={{ minWidth: 150, maxWidth: 150 }}>
                              <Text strong style={{ fontSize: 12.5, color: ui.color.text }}>{item.label}</Text>
                            </div>
                            <Text style={{ fontSize: 12, color: ui.color.textMuted, lineHeight: 1.55, flex: 1 }}>{item.detail}</Text>
                          </div>
                        ))}
                      </div>
                    </Card>
                  ));
                })()}
              </div>
            )}

          </Content>

          {/* RIGHT PANEL: AI CHAT */}
          <Sider width={390} style={{ background: ui.color.surface, border: `1px solid ${ui.color.border}`, borderRadius: ui.radius.md, overflow: 'hidden', boxShadow: ui.shadow.sm }}>
            <ChatView
              workspaceId={id || 'default'}
              initialMessages={undefined}
            />
          </Sider>

        </Layout>

        <Modal
          title="Request to Hire Agent"
          open={!!hirePosition}
          onCancel={() => {
            setHirePosition(null);
            hireAgentForm.resetFields();
          }}
          onOk={requestToHire}
          okText="Hire and Assign"
          confirmLoading={!!hiringPositionId}
          width={620}
        >
          <div style={{ padding: '4px 0 12px' }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              Required designation: <Text strong>{hirePosition?.designation || hirePosition?.requiredDesignation || hirePosition?.role}</Text>
            </Text>
          </div>
          <Form form={hireAgentForm} layout="vertical">
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="name" label="Agent Name" rules={[{ required: true, message: 'Agent name is required' }]}>
                  <Input placeholder="e.g. Backend/API Engineer Agent" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="role" label="Role" rules={[{ required: true, message: 'Role is required' }]}>
                  <Input />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="department" label="Department" rules={[{ required: true, message: 'Department is required' }]}>
                  <Input />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="Designation">
                  <Input value={hirePosition?.designation || hirePosition?.requiredDesignation || hirePosition?.role || ''} disabled />
                </Form.Item>
              </Col>
            </Row>
            <Form.Item name="role_description" label="Role Description">
              <Input.TextArea rows={3} />
            </Form.Item>
            <Form.Item name="skills" label="Skills (comma-separated)">
              <Input placeholder="Python, FastAPI, SQL" />
            </Form.Item>
          </Form>
        </Modal>

        <Drawer
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
              <FileTextOutlined style={{ color: ui.color.primary, fontSize: 18 }} />
              <div style={{ minWidth: 0 }}>
                <Text strong style={{ display: 'block', fontSize: 14, color: ui.color.text, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {selectedDocument?.name || 'Document'}
                </Text>
                <Text style={{ fontSize: 10.5, color: ui.color.textFaint }}>
                  {selectedDocument?.category || selectedDocument?.type || 'Knowledge Base'}
                </Text>
              </div>
            </div>
          }
          placement="right"
          width={720}
          open={!!selectedDocument}
          onClose={() => setSelectedDocument(null)}
          headerStyle={{ background: ui.color.surface, borderBottom: `1px solid ${ui.color.border}` }}
          bodyStyle={{ background: ui.color.surfaceMuted, padding: 18 }}
        >
          {documentLoading ? (
            <div style={{ minHeight: 220, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Spin indicator={<LoadingOutlined style={{ fontSize: 22, color: ui.color.primary }} spin />} />
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                {(selectedDocument?.type || selectedDocument?.category) && (
                  <Tag style={{ margin: 0, fontSize: 10, border: 'none', background: ui.color.primarySoft, color: ui.color.primary }}>
                    {selectedDocument.type || selectedDocument.category}
                  </Tag>
                )}
                {selectedDocument?.size && (
                  <Tag style={{ margin: 0, fontSize: 10, border: 'none', background: ui.color.surface, color: ui.color.textMuted }}>
                    {selectedDocument.size}
                  </Tag>
                )}
                {selectedDocument?.path && (
                  <Text style={{ fontSize: 10.5, color: ui.color.textFaint, wordBreak: 'break-all' }}>{selectedDocument.path}</Text>
                )}
              </div>
              <div style={{ border: `1px solid ${ui.color.border}`, borderRadius: ui.radius.sm, background: ui.color.surface, padding: 16, minHeight: 360 }}>
                {selectedDocument?.content ? (
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontFamily: 'Inter, system-ui, sans-serif', fontSize: 12.5, lineHeight: 1.65, color: ui.color.text }}>
                    {selectedDocument.content}
                  </pre>
                ) : (
                  <Text style={{ fontSize: 12, color: ui.color.textMuted }}>No stored content was found for this document.</Text>
                )}
              </div>
            </div>
          )}
        </Drawer>

        {/* Human / Agent Details Inspector Drawer */}
        <Drawer
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Avatar
                size={32}
                icon={selectedWorker.type === 'human' ? <UserOutlined /> : <RobotOutlined />}
                style={{
                  background: selectedWorker.type === 'human' ? '#ECFDF5' : ui.color.primarySoft,
                  color: selectedWorker.type === 'human' ? '#047857' : ui.color.primary,
                }}
              />
              <div style={{ lineHeight: 1.2 }}>
                <Text style={{ color: ui.color.text, fontSize: 14, fontWeight: 600, display: 'block' }}>{selectedWorker.name}</Text>
                <Text type="secondary" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 0.4 }}>{selectedWorker.role || selectedWorker.type}</Text>
                {selectedWorker.type === 'human' ? (
                  <Text style={{ color: '#047857', fontSize: 10, display: 'block', marginTop: 5 }}>
                    {selectedWorker.task}{selectedWorker.department ? ` · ${selectedWorker.department.replace(/_/g, ' ')}` : ''}
                  </Text>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginTop: 5 }}>
                    <RobotOutlined style={{ color: selectedWorker.vacant ? ui.color.textFaint : ui.color.primary, fontSize: 10 }} />
                    <Text style={{ color: selectedWorker.vacant ? ui.color.textFaint : ui.color.textMuted, fontSize: 10 }}>
                      {selectedWorker.vacant ? 'No agent hired for this position' : `Assigned agent: ${selectedWorker.assignedAgentId || selectedWorker.name}`}
                    </Text>
                  </div>
                )}
              </div>
              {(() => { const st = STATUS_STYLE[selectedWorker.status] || STATUS_STYLE.WAITING; return (
                <div style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '3px 9px', borderRadius: ui.radius.pill, background: st.bg }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: st.dot }} />
                  <span style={{ fontSize: 10, fontWeight: 600, color: st.text }}>{st.label}</span>
                </div>
              ); })()}
            </div>
          }
          placement="right"
          width={620}
          onClose={() => setIsWorkerInspectorOpen(false)}
          open={isWorkerInspectorOpen}
          headerStyle={{ background: ui.color.surface, borderBottom: `1px solid ${ui.color.border}`, padding: '16px 20px' }}
          bodyStyle={{ background: ui.color.surfaceMuted, padding: 0 }}
        >
          {selectedWorker.type === 'human' ? (
            <div style={{ padding: 20 }}>
              <div style={{ padding: 18, background: '#FFFFFF', border: '1px solid #D1FAE5', borderRadius: 10, marginBottom: 14 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                  <Avatar size={44} icon={<UserOutlined />} style={{ background: '#ECFDF5', color: '#047857', border: '1px solid #A7F3D0' }} />
                  <div>
                    <Text strong style={{ color: ui.color.text, fontSize: 14, display: 'block' }}>{selectedWorker.name}</Text>
                    <Text style={{ color: '#047857', fontSize: 11 }}>{selectedWorker.task || selectedWorker.role}</Text>
                  </div>
                  <Tag style={{ marginLeft: 'auto', color: '#047857', background: '#ECFDF5', borderColor: '#A7F3D0' }}>Project head</Tag>
                </div>
                <Row gutter={[12, 12]}>
                  <Col span={12}>
                    <Text type="secondary" style={{ fontSize: 9, textTransform: 'uppercase', display: 'block', marginBottom: 3 }}>Department</Text>
                    <Text style={{ fontSize: 12, textTransform: 'capitalize' }}>{(selectedWorker.department || 'Organization').replace(/_/g, ' ')}</Text>
                  </Col>
                  <Col span={12}>
                    <Text type="secondary" style={{ fontSize: 9, textTransform: 'uppercase', display: 'block', marginBottom: 3 }}>Project workers</Text>
                    <Text style={{ fontSize: 12 }}>{selectedWorker.children?.filter(child => child.type === 'agent').length || 0} directly assigned</Text>
                  </Col>
                </Row>
              </div>

              {selectedWorker.assignedWork ? (
                <div style={{ padding: 16, background: '#FFFFFF', border: `1px solid ${ui.color.border}`, borderRadius: 10, marginBottom: 14 }}>
                  <Text type="secondary" style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: 0.5, display: 'block', marginBottom: 6 }}>Organization responsibility</Text>
                  <Text style={{ fontSize: 12, color: ui.color.textMuted, lineHeight: 1.6 }}>{selectedWorker.assignedWork}</Text>
                </div>
              ) : null}

              <div style={{ padding: 16, background: '#FFFFFF', border: `1px solid ${ui.color.border}`, borderRadius: 10 }}>
                <Text type="secondary" style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: 0.5, display: 'block', marginBottom: 8 }}>Skills</Text>
                {selectedWorker.knowledge?.length ? (
                  <Space wrap size={6}>
                    {selectedWorker.knowledge.map((skill, index) => (
                      <Tag key={`${skill}-${index}`} style={{ margin: 0, color: '#047857', background: '#F0FDF4', borderColor: '#BBF7D0' }}>{skill}</Tag>
                    ))}
                  </Space>
                ) : (
                  <Text type="secondary" style={{ fontSize: 11 }}>No organization skills recorded.</Text>
                )}
              </div>
            </div>
          ) : (
          <Tabs
            defaultActiveKey="overview"
            style={{ padding: '0 16px' }}
            items={[
              // ── OVERVIEW TAB ──
              {
                key: 'overview', label: 'Overview',
                children: (
                  <div style={{ padding: '16px 0' }}>
                    {/* Agent Info Card */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 16, background: '#f8fafc', borderRadius: 10, border: '1px solid #e2e8f0', marginBottom: 20 }}>
                      <div style={{ width: 44, height: 44, borderRadius: '50%', background: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '2px solid #bfdbfe' }}>
                        <RobotOutlined style={{ fontSize: 20, color: '#2563eb' }} />
                      </div>
                      <div style={{ flex: 1 }}>
                        <Text strong style={{ fontSize: 14, display: 'block' }}>{selectedWorker.name}</Text>
                        <Text type="secondary" style={{ fontSize: 11 }}>{selectedWorker.model || 'GPT-4o (Reasoning)'}</Text>
                      </div>
                      <Tag color={selectedWorker.status === 'RUNNING' ? 'green' : 'orange'}>{selectedWorker.status}</Tag>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', background: selectedWorker.vacant ? '#f9fafb' : '#f0f9ff', borderRadius: 8, border: selectedWorker.vacant ? '1px dashed #cbd5e1' : '1px solid #bae6fd', marginBottom: 16 }}>
                      <RobotOutlined style={{ fontSize: 16, color: selectedWorker.vacant ? '#94a3b8' : '#2563eb' }} />
                      <div>
                        <Text type="secondary" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 0.5, display: 'block' }}>Project position</Text>
                        <Text strong style={{ fontSize: 13 }}>{selectedWorker.requiredDesignation || selectedWorker.task}</Text>
                      </div>
                      <Tag color={selectedWorker.vacant ? 'default' : 'blue'} style={{ marginLeft: 'auto', fontSize: 10 }}>
                        {selectedWorker.vacant ? 'Vacant' : 'Filled'}
                      </Tag>
                    </div>

                    {/* Goal */}
                    <div style={{ marginBottom: 16 }}>
                      <Text type="secondary" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 0.5, display: 'block', marginBottom: 4 }}>Agent Goal</Text>
                      <Text style={{ fontSize: 12, color: '#374151' }}>{selectedWorker.goal}</Text>
                    </div>

                    {/* Instructions */}
                    <div style={{ marginBottom: 16 }}>
                      <Text type="secondary" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 0.5, display: 'block', marginBottom: 4 }}>System Prompt</Text>
                      <div style={{ padding: '8px 10px', background: '#f8fafc', borderRadius: 6, border: '1px solid #e2e8f0' }}>
                        <Text style={{ fontSize: 11, color: '#475569', lineHeight: 1.5 }}>{selectedWorker.instructions}</Text>
                      </div>
                    </div>

                    {/* Memory + Knowledge inline */}
                    <Row gutter={12} style={{ marginBottom: 16 }}>
                      <Col span={12}>
                        <Text type="secondary" style={{ fontSize: 10, textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>Memory State</Text>
                        <Space wrap size={4}>{selectedWorker.memory?.map((m: string, i: number) => <Tag key={i} color="blue" style={{ fontSize: 9 }}>{m}</Tag>)}</Space>
                      </Col>
                      <Col span={12}>
                        <Text type="secondary" style={{ fontSize: 10, textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>Knowledge Assets</Text>
                        <Space wrap size={4}>{selectedWorker.knowledge?.map((k: string, i: number) => <Tag key={i} color="cyan" style={{ fontSize: 9 }}>{k}</Tag>)}</Space>
                      </Col>
                    </Row>

                    <Divider style={{ margin: '12px 0' }} />

                    {/* Current Task */}
                    <div style={{ marginBottom: 16 }}>
                      <Text type="secondary" style={{ fontSize: 10, textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>Current Task</Text>
                      <div style={{ padding: '8px 12px', background: '#fef3c7', borderRadius: 6, border: '1px solid #fde68a' }}>
                        <Text style={{ fontSize: 12, color: '#92400e' }}>● {selectedWorker.task}</Text>
                      </div>
                    </div>

                    {/* Execution Logs */}
                    <div>
                      <Text type="secondary" style={{ fontSize: 10, textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>Execution Logs</Text>
                      <div style={{ background: '#f8fafc', padding: 10, borderRadius: 6, border: '1px solid #e2e8f0', fontFamily: 'monospace', fontSize: 10, maxHeight: 120, overflowY: 'auto' }}>
                        {selectedWorker.logs?.map((log: string, i: number) => <div key={i} style={{ color: '#475569', marginBottom: 3 }}>{log}</div>)}
                      </div>
                    </div>
                  </div>
                ),
              },
              // ── TOOLS TAB ──
              {
                key: 'tools', label: 'Tools',
                children: (
                  <div style={{ padding: '16px 0' }}>
                    <Text type="secondary" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 0.5, display: 'block', marginBottom: 10 }}>Configured Tools</Text>
                    <Space wrap size={8} style={{ marginBottom: 20 }}>
                      {selectedWorker.tools?.map((t: string, i: number) => (
                        <div key={i} style={{ padding: '8px 14px', background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#f59e0b' }} />
                          <Text style={{ fontSize: 11, fontWeight: 500 }}>{t}</Text>
                        </div>
                      ))}
                    </Space>
                    <Divider style={{ margin: '12px 0' }} />
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                      <Text type="secondary" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 0.5 }}>Connectors</Text>
                      <Tag color="blue" style={{ fontSize: 9 }}>{(workerConnectors[selectedWorkerId] || []).length} connected</Tag>
                    </div>
                    <Input placeholder="Search connectors..." prefix={<SearchOutlined style={{ color: '#94a3b8' }} />} value={connectorSearch} onChange={e => setConnectorSearch(e.target.value)} size="small" style={{ marginBottom: 10, fontSize: 11 }} allowClear />
                    <div style={{ maxHeight: 300, overflowY: 'auto' }}>
                      {WORKER_CONNECTORS
                        .filter(c => !connectorSearch || c.name.toLowerCase().includes(connectorSearch.toLowerCase()) || c.category.toLowerCase().includes(connectorSearch.toLowerCase()))
                        .map(connector => {
                          const isConnected = (workerConnectors[selectedWorkerId] || []).includes(connector.id);
                          const configKey = `${selectedWorkerId}:${connector.id}`;
                          const hasConfig = connectorConfigs[configKey] && Object.values(connectorConfigs[configKey]).some(v => v);
                          return (
                            <div key={connector.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px', marginBottom: 4, borderRadius: 6, background: isConnected ? '#eff6ff' : '#fff', border: isConnected ? '1px solid #bfdbfe' : '1px solid #e2e8f0' }}>
                              <span style={{ fontSize: 16, flexShrink: 0 }}>{connector.logo}</span>
                              <div style={{ flex: 1, minWidth: 0 }}>
                                <Text strong style={{ fontSize: 11, display: 'block', color: '#0f172a' }}>{connector.name}</Text>
                                <Text type="secondary" style={{ fontSize: 9 }}>{connector.category} — {connector.description}</Text>
                              </div>
                              <Space size={4}>
                                {isConnected && (
                                  <Button size="small" type={hasConfig ? 'default' : 'dashed'} icon={<SettingOutlined />} style={{ fontSize: 9, height: 22, padding: '0 6px' }} onClick={(e) => { e.stopPropagation(); setConfiguringConnector({ workerId: selectedWorkerId, connectorId: connector.id }); }}>
                                    {hasConfig ? 'Edit' : 'Configure'}
                                  </Button>
                                )}
                                <Switch size="small" checked={isConnected} onChange={() => toggleWorkerConnector(selectedWorkerId, connector.id)} />
                              </Space>
                            </div>
                          );
                        })}
                    </div>
                  </div>
                ),
              },
              // ── KNOWLEDGE TAB ──
              {
                key: 'knowledge', label: 'Knowledge',
                children: (
                  <div style={{ padding: '16px 0' }}>
                    <Text style={{ fontSize: 13, color: '#0f172a', display: 'block', marginBottom: 16 }}>Configure which knowledge sources this agent can access.</Text>

                    <Text strong style={{ fontSize: 11, display: 'block', marginBottom: 8 }}>Connected Repositories</Text>
                    <Space wrap size={6} style={{ marginBottom: 16 }}>
                      {['acme-corp/hr-migration-scripts', 'acme-corp/frappe-hr-config', 'acme-corp/mysql-sync-service'].map(repo => (
                        <Tag key={repo} color="blue" closable style={{ fontSize: 10 }}>{repo}</Tag>
                      ))}
                    </Space>

                    <Text strong style={{ fontSize: 11, display: 'block', marginBottom: 8 }}>Allowed Node Types</Text>
                    <Space wrap size={6} style={{ marginBottom: 16 }}>
                      {['backend', 'database', 'configuration', 'security'].map(nt => (
                        <Tag key={nt} color="green" style={{ fontSize: 10, cursor: 'pointer' }}>✓ {nt}</Tag>
                      ))}
                      {['frontend', 'documentation', 'testing', 'ci/cd', 'infrastructure'].map(nt => (
                        <Tag key={nt} style={{ fontSize: 10, cursor: 'pointer', border: '1px dashed #d1d5db', color: '#9ca3af' }}>{nt}</Tag>
                      ))}
                    </Space>

                    <Card size="small" style={{ background: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: 8 }} bodyStyle={{ padding: '10px 14px' }}>
                      <Text style={{ fontSize: 11, color: '#475569', lineHeight: 1.6 }}>
                        This agent can access <Text strong>3 repositories</Text> and <Text strong>4 node type categories</Text> from the knowledge graph.
                      </Text>
                    </Card>
                  </div>
                ),
              },
              // ── EVALS TAB ──
              {
                key: 'evals', label: 'Evals',
                children: <EvalsTab agentName={selectedWorker.name} />,
              },
              // ── GUARDRAILS TAB ──
              {
                key: 'guardrails', label: 'Guardrails',
                children: (
                  <div style={{ padding: '16px 0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                      <div>
                        <Text style={{ fontSize: 13, fontWeight: 600, color: '#0f172a', display: 'block' }}>Guardrails</Text>
                        <Text type="secondary" style={{ fontSize: 11 }}>Safety rules enforced during agent execution</Text>
                      </div>
                      <Button size="small" type="primary" icon={<PlusOutlined />} onClick={() => setShowNewGuardrail(!showNewGuardrail)}>Add Guardrail</Button>
                    </div>

                    {showNewGuardrail && (
                      <div style={{ marginBottom: 16, borderRadius: 10, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
                        <div style={{ padding: '10px 14px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Text strong style={{ fontSize: 12 }}>New Guardrail</Text>
                          <Button type="text" size="small" icon={<CloseOutlined />} onClick={() => setShowNewGuardrail(false)} style={{ color: '#94a3b8' }} />
                        </div>
                        <div style={{ padding: 14 }}>
                          <div style={{ marginBottom: 12 }}>
                            <Text style={{ fontSize: 10, fontWeight: 600, color: '#6b7280', display: 'block', marginBottom: 4 }}>GUARDRAIL NAME</Text>
                            <Input size="small" placeholder="e.g. No Direct Database Writes" value={newGuardrailName} onChange={e => setNewGuardrailName(e.target.value)} />
                          </div>
                          <div style={{ marginBottom: 12 }}>
                            <Text style={{ fontSize: 10, fontWeight: 600, color: '#6b7280', display: 'block', marginBottom: 4 }}>ENFORCEMENT TYPE</Text>
                            <div style={{ display: 'flex', gap: 8 }}>
                              <div onClick={() => setNewGuardrailType('hard')} style={{ flex: 1, padding: '10px 12px', borderRadius: 8, cursor: 'pointer', background: newGuardrailType === 'hard' ? '#fef2f2' : '#f9fafb', border: `1px solid ${newGuardrailType === 'hard' ? '#fecaca' : '#e5e7eb'}`, textAlign: 'center' }}>
                                <div style={{ width: 20, height: 20, borderRadius: '50%', background: newGuardrailType === 'hard' ? '#dc2626' : '#d1d5db', margin: '0 auto 6px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                  <LockOutlined style={{ fontSize: 10, color: '#fff' }} />
                                </div>
                                <Text style={{ fontSize: 11, fontWeight: newGuardrailType === 'hard' ? 600 : 400, color: newGuardrailType === 'hard' ? '#dc2626' : '#6b7280' }}>Hard Block</Text>
                                <Text style={{ fontSize: 9, color: '#9ca3af', display: 'block' }}>Stops execution</Text>
                              </div>
                              <div onClick={() => setNewGuardrailType('soft')} style={{ flex: 1, padding: '10px 12px', borderRadius: 8, cursor: 'pointer', background: newGuardrailType === 'soft' ? '#fffbeb' : '#f9fafb', border: `1px solid ${newGuardrailType === 'soft' ? '#fde68a' : '#e5e7eb'}`, textAlign: 'center' }}>
                                <div style={{ width: 20, height: 20, borderRadius: '50%', background: newGuardrailType === 'soft' ? '#d97706' : '#d1d5db', margin: '0 auto 6px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                  <WarningOutlined style={{ fontSize: 10, color: '#fff' }} />
                                </div>
                                <Text style={{ fontSize: 11, fontWeight: newGuardrailType === 'soft' ? 600 : 400, color: newGuardrailType === 'soft' ? '#d97706' : '#6b7280' }}>Soft Warning</Text>
                                <Text style={{ fontSize: 9, color: '#9ca3af', display: 'block' }}>Logs warning</Text>
                              </div>
                            </div>
                          </div>
                          <div style={{ marginBottom: 12 }}>
                            <Text style={{ fontSize: 10, fontWeight: 600, color: '#6b7280', display: 'block', marginBottom: 4 }}>DESCRIPTION</Text>
                            <Input.TextArea size="small" placeholder="What does this guardrail prevent?" value={newGuardrailDesc} onChange={e => setNewGuardrailDesc(e.target.value)} rows={3} />
                          </div>
                          <div style={{ marginBottom: 14 }}>
                            <Text style={{ fontSize: 10, fontWeight: 600, color: '#6b7280', display: 'block', marginBottom: 4 }}>ENFORCEMENT MECHANISM</Text>
                            <Input.TextArea size="small" placeholder="How is this enforced?" value={newGuardrailEnforcement} onChange={e => setNewGuardrailEnforcement(e.target.value)} rows={3} />
                          </div>
                          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                            <Button size="small" onClick={() => setShowNewGuardrail(false)}>Cancel</Button>
                            <Button size="small" type="primary" icon={<PlusOutlined />} onClick={() => addGuardrail(selectedWorker.name)} disabled={!newGuardrailName.trim()}>Add Guardrail</Button>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Guardrails grouped by category */}
                    {(() => {
                      const allGuardrails = getAgentGuardrails(selectedWorker.name);
                      const allTemplates = GUARDRAIL_TEMPLATES[selectedWorker.name] || GUARDRAIL_TEMPLATES['Migration Orchestrator'];
                      const categories: Record<string, { guardrail: any; template: any }[]> = {};
                      allGuardrails.forEach((g) => {
                        const template = allTemplates.find(t => t.name === g.name);
                        const cat = template?.category || 'Other';
                        if (!categories[cat]) categories[cat] = [];
                        categories[cat].push({ guardrail: g, template });
                      });

                      const categoryMeta: Record<string, { color: string; desc: string }> = {
                        'Data Integrity': { color: '#3b82f6', desc: 'Validates data correctness and consistency' },
                        'Access Control': { color: '#8b5cf6', desc: 'Manages permissions and blocks unauthorized ops' },
                        'Performance': { color: '#f59e0b', desc: 'Monitors latency, throughput, resources' },
                        'Compliance': { color: '#10b981', desc: 'PII masking, audit trails, sign-offs' },
                        'Operational': { color: '#06b6d4', desc: 'Rollbacks, monitoring, phase gates' },
                        'Other': { color: '#6b7280', desc: 'Custom guardrails' },
                      };

                      return Object.entries(categories).map(([cat, items]) => {
                        const meta = categoryMeta[cat] || categoryMeta['Other'];
                        return (
                          <div key={cat} style={{ marginBottom: 12, borderRadius: 10, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
                            <div style={{ padding: '10px 14px', background: `${meta.color}08`, borderBottom: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: 8 }}>
                              <div style={{ width: 8, height: 8, borderRadius: '50%', background: meta.color }} />
                              <div style={{ flex: 1 }}>
                                <Text strong style={{ fontSize: 12 }}>{cat}</Text>
                                <Text style={{ fontSize: 10, color: '#94a3b8', display: 'block' }}>{meta.desc}</Text>
                              </div>
                              <Tag style={{ fontSize: 9 }}>{items.length}</Tag>
                            </div>
                            <div style={{ padding: '8px 10px' }}>
                              {items.map(({ guardrail: g, template }, i) => {
                                const isTesting = testingGuardrail === g.name;
                                const isViolated = violations.some(v => v.name === g.name);
                                return (
                                  <div key={i} style={{ padding: '8px 10px', marginBottom: i < items.length - 1 ? 6 : 0, borderRadius: 6, background: isViolated ? '#fef2f2' : '#fff', border: `1px solid ${isViolated ? '#fecaca' : '#f3f4f6'}` }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                                      <div style={{ width: 20, height: 20, borderRadius: 4, background: g.type === 'hard' ? '#fef2f2' : '#fffbeb', display: 'flex', alignItems: 'center', justifyContent: 'center', border: `1px solid ${g.type === 'hard' ? '#fecaca' : '#fde68a'}` }}>
                                        <LockOutlined style={{ fontSize: 9, color: g.type === 'hard' ? '#dc2626' : '#d97706' }} />
                                      </div>
                                      <Text style={{ fontSize: 11, fontWeight: 500, flex: 1 }}>{g.name}</Text>
                                      <Tag color={g.type === 'hard' ? 'red' : 'orange'} style={{ fontSize: 9, margin: 0 }}>{g.type}</Tag>
                                      <Switch size="small" checked={g.enabled} onChange={() => toggleGuardrail(selectedWorker.name, g.name)} />
                                    </div>
                                    {template && (
                                      <div style={{ marginLeft: 28, marginBottom: 6 }}>
                                        <Text type="secondary" style={{ fontSize: 9, display: 'block' }}>{template.description}</Text>
                                        <Text style={{ fontSize: 9, color: '#6b7280', display: 'block', marginTop: 2 }}>Enforcement: {template.enforcement}</Text>
                                      </div>
                                    )}
                                    <div style={{ marginLeft: 28 }}>
                                      <Button size="small" loading={isTesting} onClick={() => testGuardrail(selectedWorker.name, g.name)} style={{ fontSize: 9, height: 22, padding: '0 8px' }}>{isTesting ? 'Testing...' : 'Test'}</Button>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        );
                      });
                    })()}

                    {guardrailResult && (
                      <Card size="small" style={{ marginTop: 8, marginBottom: 12, background: guardrailResult.triggered ? '#fef2f2' : '#f0fdf4', border: `1px solid ${guardrailResult.triggered ? '#fecaca' : '#bbf7d0'}`, borderRadius: 8 }} bodyStyle={{ padding: '10px 12px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                          <Text strong style={{ fontSize: 11 }}>{guardrailResult.name} — Test Result</Text>
                          <Tag color={guardrailResult.triggered ? 'red' : 'green'} style={{ fontSize: 9 }}>{guardrailResult.triggered ? 'VIOLATION' : 'PASSED'}</Tag>
                        </div>
                        <Text style={{ fontSize: 10, color: '#374151', display: 'block', marginBottom: 8 }}>{guardrailResult.action}</Text>
                        {guardrailResult.cascade.length > 0 && (
                          <div>
                            <Text style={{ fontSize: 9, color: '#6b7280', display: 'block', marginBottom: 4 }}>Cascade Effects:</Text>
                            {guardrailResult.cascade.map((c, i) => (
                              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                                <div style={{ width: 4, height: 4, borderRadius: '50%', background: guardrailResult.triggered ? '#ef4444' : '#10b981' }} />
                                <Text style={{ fontSize: 10 }}>{c}</Text>
                              </div>
                            ))}
                          </div>
                        )}
                      </Card>
                    )}

                    {violations.length > 0 && (
                      <div style={{ marginTop: 8 }}>
                        <Text style={{ fontSize: 10, fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', display: 'block', marginBottom: 8 }}>Violation History</Text>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                          {violations.map((v, i) => (
                            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 8px', borderRadius: 4, background: '#fef2f2', border: '1px solid #fecaca' }}>
                              <WarningOutlined style={{ fontSize: 10, color: '#dc2626' }} />
                              <Text style={{ fontSize: 10, fontWeight: 500, flex: 1 }}>{v.name}</Text>
                              <Text style={{ fontSize: 9, color: '#9ca3af' }}>{v.time}</Text>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ),
              },
              // ── SKILLS TAB ──
              {
                key: 'skills', label: 'Skills',
                children: (
                  <div style={{ padding: '16px 0' }}>
                    <Text style={{ fontSize: 13, fontWeight: 600, color: '#0f172a', display: 'block', marginBottom: 4 }}>Agent Skills</Text>
                    <Text type="secondary" style={{ fontSize: 11, marginBottom: 16, display: 'block' }}>Specialized capabilities assigned to this agent.</Text>

                    {(() => {
                      const agentData = teamAgents.find(a => a.id === selectedWorkerId);
                      const skills: string[] = agentData?.skills || selectedWorker?.knowledge || [];
                      return skills.length === 0 ? (
                        <div style={{ padding: 20, textAlign: 'center', background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                          <Text style={{ fontSize: 12, color: '#94a3b8' }}>No skills assigned to this agent yet.</Text>
                        </div>
                      ) : (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10 }}>
                          {skills.map((skill, i) => (
                            <div key={i} style={{ padding: '10px 14px', background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: 10 }}>
                              <div style={{ width: 28, height: 28, borderRadius: 6, background: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                                <ThunderboltOutlined style={{ fontSize: 13, color: '#2563eb' }} />
                              </div>
                              <Text style={{ fontSize: 12, fontWeight: 500 }}>{skill}</Text>
                            </div>
                          ))}
                        </div>
                      );
                    })()}
                  </div>
                ),
              },
              // ── CERTIFICATIONS TAB ──
              {
                key: 'certifications', label: 'Certifications',
                children: (
                  <div style={{ padding: '16px 0' }}>
                    <Text style={{ fontSize: 13, fontWeight: 600, color: '#0f172a', display: 'block', marginBottom: 4 }}>Agent Certifications</Text>
                    <Text type="secondary" style={{ fontSize: 11, marginBottom: 16, display: 'block' }}>
                      Verified credentials associated with this agent&apos;s specialist capabilities.
                    </Text>

                    {(() => {
                      const agentData = teamAgents.find(a => a.id === selectedWorkerId);
                      const certificates = Array.isArray(agentData?.certificates)
                        ? agentData.certificates
                        : selectedWorker.certificates || [];

                      if (certificates.length === 0) {
                        return (
                          <div style={{ padding: '28px 20px', textAlign: 'center', background: '#f8fafc', borderRadius: 10, border: '1px solid #e2e8f0' }}>
                            <img src="/assets/certificate.webp" alt="" style={{ width: 40, height: 40, objectFit: 'contain', opacity: 0.55, marginBottom: 10 }} />
                            <Text style={{ fontSize: 12, fontWeight: 600, color: '#64748b', display: 'block' }}>No certifications assigned</Text>
                            <Text type="secondary" style={{ fontSize: 10.5 }}>Certifications added to this agent&apos;s profile will appear here.</Text>
                          </div>
                        );
                      }

                      return (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 10 }}>
                          {certificates.map((certificate: any, index: number) => {
                            const isTextCertificate = typeof certificate === 'string';
                            const name = isTextCertificate
                              ? certificate
                              : certificate.name || certificate.title || 'Certification';
                            const url = isTextCertificate ? undefined : certificate.url;
                            const issuer = isTextCertificate ? undefined : certificate.issuer;
                            const issuedAt = isTextCertificate ? undefined : certificate.issuedAt || certificate.issued_at;
                            const expiresAt = isTextCertificate ? undefined : certificate.expiresAt || certificate.expires_at;

                            const content = (
                              <div style={{ minHeight: 82, padding: '12px 14px', background: '#fff', borderRadius: 9, border: '1px solid #e2e8f0', display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                                <div style={{ width: 38, height: 38, borderRadius: 8, background: '#fffbeb', border: '1px solid #fde68a', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                                  <img src="/assets/certificate.webp" alt="" style={{ width: 24, height: 24, objectFit: 'contain' }} />
                                </div>
                                <div style={{ flex: 1, minWidth: 0 }}>
                                  <Text style={{ fontSize: 11.5, fontWeight: 600, color: '#0f172a', lineHeight: 1.45, display: 'block' }}>{name}</Text>
                                  {issuer ? <Text type="secondary" style={{ fontSize: 10, display: 'block', marginTop: 3 }}>{issuer}</Text> : null}
                                  {(issuedAt || expiresAt) ? (
                                    <Text type="secondary" style={{ fontSize: 9.5, display: 'block', marginTop: 4 }}>
                                      {issuedAt ? `Issued ${issuedAt}` : ''}
                                      {issuedAt && expiresAt ? ' · ' : ''}
                                      {expiresAt ? `Expires ${expiresAt}` : ''}
                                    </Text>
                                  ) : null}
                                </div>
                                {url ? <ExportOutlined style={{ color: '#64748b', fontSize: 11, marginTop: 3 }} /> : null}
                              </div>
                            );

                            return url ? (
                              <a
                                key={`${name}-${index}`}
                                href={url}
                                target="_blank"
                                rel="noopener noreferrer"
                                aria-label={`Open ${name} certification`}
                                style={{ color: 'inherit', textDecoration: 'none' }}
                              >
                                {content}
                              </a>
                            ) : (
                              <div key={`${name}-${index}`}>{content}</div>
                            );
                          })}
                        </div>
                      );
                    })()}
                  </div>
                ),
              },
              // ── AUTOMATION TAB ──
              {
                key: 'automation', label: 'Automation',
                children: (
                  <div style={{ padding: '16px 0' }}>
                    <Text style={{ fontSize: 13, fontWeight: 600, color: '#0f172a', display: 'block', marginBottom: 4 }}>Automation Rules</Text>
                    <Text type="secondary" style={{ fontSize: 11, marginBottom: 16, display: 'block' }}>How this agent handles retries, escalations, and self-healing.</Text>

                    {(() => {
                      const agentData = teamAgents.find(a => a.id === selectedWorkerId);
                      const automation = agentData?.automation || {};
                      const rules = [
                        { label: 'Auto Retry on Failure', value: automation.autoRetry !== false ? 'Enabled' : 'Disabled', color: automation.autoRetry !== false ? '#16a34a' : '#dc2626', icon: <SyncOutlined /> },
                        { label: 'Max Retries', value: String(automation.maxRetries ?? 3), color: '#2563eb', icon: <ReloadOutlined /> },
                        { label: 'Retry Delay', value: `${automation.retryDelaySeconds ?? 30}s`, color: '#2563eb', icon: <ClockCircleOutlined /> },
                        { label: 'Escalate on Failure', value: automation.escalateOnFailure !== false ? 'Yes' : 'No', color: automation.escalateOnFailure !== false ? '#d97706' : '#6b7280', icon: <WarningOutlined /> },
                        { label: 'Heartbeat Interval', value: `${automation.heartbeatIntervalSeconds ?? 60}s`, color: '#2563eb', icon: <SyncOutlined /> },
                      ];

                      return (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                          {rules.map((rule, i) => (
                            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px', background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                              <div style={{ width: 28, height: 28, borderRadius: 6, background: '#f0fdf4', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: rule.color }}>
                                {rule.icon}
                              </div>
                              <Text style={{ fontSize: 12, flex: 1 }}>{rule.label}</Text>
                              <Tag style={{ margin: 0, fontSize: 11, fontWeight: 600, border: 'none', background: rule.color === '#dc2626' ? '#fef2f2' : '#eff6ff', color: rule.color }}>{rule.value}</Tag>
                            </div>
                          ))}
                        </div>
                      );
                    })()}

                    <Divider style={{ margin: '20px 0 16px' }} />

                    {/* Scheduled Tasks */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                      <div>
                        <Text style={{ fontSize: 13, fontWeight: 600, color: '#0f172a', display: 'block' }}>Scheduled Tasks</Text>
                        <Text type="secondary" style={{ fontSize: 11 }}>Recurring tasks this agent runs on a schedule.</Text>
                      </div>
                      <Button size="small" type="primary" icon={<PlusOutlined />} onClick={() => setShowScheduleForm(!showScheduleForm)}>Schedule Task</Button>
                    </div>

                    {showScheduleForm && (
                      <div style={{ marginBottom: 16, borderRadius: 10, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
                        <div style={{ padding: '10px 14px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Text strong style={{ fontSize: 12 }}>New Scheduled Task</Text>
                          <Button type="text" size="small" icon={<CloseOutlined />} onClick={() => setShowScheduleForm(false)} style={{ color: '#94a3b8' }} />
                        </div>
                        <div style={{ padding: 14 }}>
                          <div style={{ marginBottom: 12 }}>
                            <Text style={{ fontSize: 10, fontWeight: 600, color: '#6b7280', display: 'block', marginBottom: 4 }}>TASK NAME</Text>
                            <Input size="small" placeholder="e.g. Daily Data Sync" value={scheduleTaskName} onChange={e => setScheduleTaskName(e.target.value)} />
                          </div>
                          <div style={{ marginBottom: 12 }}>
                            <Text style={{ fontSize: 10, fontWeight: 600, color: '#6b7280', display: 'block', marginBottom: 4 }}>SCHEDULE (CRON)</Text>
                            <Select size="small" style={{ width: '100%' }} placeholder="Select schedule" value={scheduleTaskCron || undefined} onChange={v => setScheduleTaskCron(v)}>
                              <Select.Option value="0 */1 * * *">Every hour</Select.Option>
                              <Select.Option value="0 9 * * *">Daily at 9:00 AM</Select.Option>
                              <Select.Option value="0 9 * * 1">Weekly on Monday</Select.Option>
                              <Select.Option value="0 1 1 * *">Monthly on 1st</Select.Option>
                              <Select.Option value="*/15 * * * *">Every 15 minutes</Select.Option>
                              <Select.Option value="0 */6 * * *">Every 6 hours</Select.Option>
                            </Select>
                          </div>
                          <div style={{ marginBottom: 14 }}>
                            <Text style={{ fontSize: 10, fontWeight: 600, color: '#6b7280', display: 'block', marginBottom: 4 }}>DESCRIPTION</Text>
                            <Input.TextArea size="small" placeholder="What should this task do?" value={scheduleTaskDesc} onChange={e => setScheduleTaskDesc(e.target.value)} rows={2} />
                          </div>
                          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                            <Button size="small" onClick={() => setShowScheduleForm(false)}>Cancel</Button>
                            <Button size="small" type="primary" icon={<PlusOutlined />}
                              onClick={() => {
                                if (!scheduleTaskName.trim()) return;
                                const newTask = {
                                  id: `task-${Date.now()}`,
                                  name: scheduleTaskName,
                                  cron: scheduleTaskCron,
                                  description: scheduleTaskDesc,
                                  enabled: true,
                                  lastRun: null,
                                  nextRun: scheduleTaskCron ? 'Pending' : 'Not scheduled',
                                };
                                setScheduledTasks(prev => [...prev, newTask]);
                                setScheduleTaskName('');
                                setScheduleTaskCron('');
                                setScheduleTaskDesc('');
                                setShowScheduleForm(false);
                                message.success(`Task "${newTask.name}" scheduled`);
                              }}
                              disabled={!scheduleTaskName.trim()}>Save Task</Button>
                          </div>
                        </div>
                      </div>
                    )}

                    {scheduledTasks.length === 0 ? (
                      <div style={{ padding: 20, textAlign: 'center', background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                        <ClockCircleOutlined style={{ fontSize: 20, color: '#94a3b8', marginBottom: 8 }} />
                        <Text style={{ fontSize: 12, color: '#94a3b8', display: 'block' }}>No scheduled tasks yet.</Text>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {scheduledTasks.map((task) => (
                          <div key={task.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px', background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                            <div style={{ width: 28, height: 28, borderRadius: 6, background: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                              <ClockCircleOutlined style={{ fontSize: 13, color: '#2563eb' }} />
                            </div>
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <Text style={{ fontSize: 12, fontWeight: 500, display: 'block' }}>{task.name}</Text>
                              <Text style={{ fontSize: 10, color: '#94a3b8' }}>{task.cron} · {task.description || 'No description'}</Text>
                            </div>
                            <Tag style={{ margin: 0, fontSize: 9, border: 'none', background: task.enabled ? '#f0fdf4' : '#fef2f2', color: task.enabled ? '#16a34a' : '#dc2626' }}>{task.enabled ? 'Active' : 'Paused'}</Tag>
                            <Button size="small" type="text" icon={<DeleteOutlined />} onClick={() => setScheduledTasks(prev => prev.filter(t => t.id !== task.id))} style={{ color: '#94a3b8' }} />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ),
              },
              // ── FEATURES TAB ──
              {
                key: 'features', label: 'Features',
                children: (
                  <div style={{ padding: '16px 0' }}>
                    <Text style={{ fontSize: 13, fontWeight: 600, color: '#0f172a', display: 'block', marginBottom: 4 }}>Agent Features & Capabilities</Text>
                    <Text type="secondary" style={{ fontSize: 11, marginBottom: 16, display: 'block' }}>Memory, data access, rate limits, and other configurable features.</Text>

                    {(() => {
                      const agentData = teamAgents.find(a => a.id === selectedWorkerId);
                      const features = agentData?.features || {};
                      const items = [
                        { label: 'Memory Retention', value: `${features.memoryRetentionDays ?? 30} days`, desc: 'How long agent memory persists between sessions', icon: <BookOutlined /> },
                        { label: 'Data Query Access', value: features.dataQueryAccess === 'read' ? 'Read Only' : features.dataQueryAccess === 'write' ? 'Read & Write' : 'Read Only', desc: 'Permission level for database operations', icon: <DatabaseOutlined /> },
                        { label: 'Max Concurrent Tasks', value: String(features.maxConcurrentTasks ?? 5), desc: 'Maximum parallel task executions', icon: <PartitionOutlined /> },
                        { label: 'Rate Limit', value: `${features.rateLimitPerMinute ?? 60} req/min`, desc: 'API call throttling threshold', icon: <ThunderboltOutlined /> },
                        { label: 'Streaming', value: features.streamingEnabled !== false ? 'Enabled' : 'Disabled', desc: 'Real-time SSE response streaming', icon: <ApiOutlined /> },
                        { label: 'Audit Logging', value: features.auditLogging !== false ? 'Enabled' : 'Disabled', desc: 'Full action trace for compliance', icon: <AuditOutlined /> },
                        { label: 'PII Masking', value: features.piiMasking ? 'Enabled' : 'Disabled', desc: 'Automatic redaction of sensitive data', icon: <LockOutlined /> },
                      ];

                      return (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                          {items.map((item, i) => (
                            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px', background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                              <div style={{ width: 28, height: 28, borderRadius: 6, background: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: '#2563eb' }}>
                                {item.icon}
                              </div>
                              <div style={{ flex: 1, minWidth: 0 }}>
                                <Text style={{ fontSize: 12, fontWeight: 500, display: 'block' }}>{item.label}</Text>
                                <Text style={{ fontSize: 10, color: '#94a3b8' }}>{item.desc}</Text>
                              </div>
                              <Tag style={{ margin: 0, fontSize: 11, fontWeight: 600, border: 'none', background: '#eff6ff', color: '#2563eb' }}>{item.value}</Tag>
                            </div>
                          ))}
                        </div>
                      );
                    })()}
                  </div>
                ),
              },
            ]}
          />
          )}
        </Drawer>

        {/* Connector Configuration Modal */}
        <Modal
          title={
            <Space>
              <span style={{ fontSize: 18 }}>{WORKER_CONNECTORS.find(c => c.id === configuringConnector?.connectorId)?.logo}</span>
              <span>Configure {WORKER_CONNECTORS.find(c => c.id === configuringConnector?.connectorId)?.name}</span>
            </Space>
          }
          open={!!configuringConnector}
          onCancel={() => setConfiguringConnector(null)}
          onOk={() => {
            message.success(`${WORKER_CONNECTORS.find(c => c.id === configuringConnector?.connectorId)?.name} configured successfully`);
            setConfiguringConnector(null);
          }}
          okText="Save Configuration"
          width={500}
        >
          {configuringConnector && (() => {
            const connector = WORKER_CONNECTORS.find(c => c.id === configuringConnector.connectorId);
            if (!connector) return null;
            const configKey = `${configuringConnector.workerId}:${configuringConnector.connectorId}`;
            const config = connectorConfigs[configKey] || {};
            return (
              <Form layout="vertical" style={{ marginTop: 16 }}>
                <div style={{ marginBottom: 16, padding: '10px 12px', background: '#f8fafc', borderRadius: 6, border: '1px solid #e2e8f0' }}>
                  <Text style={{ fontSize: 11, color: '#475569' }}>{connector.description}</Text>
                </div>
                {connector.fields.map(field => (
                  <Form.Item key={field.key} label={field.label} required style={{ marginBottom: 12 }}>
                    {field.type === 'textarea' ? (
                      <Input.TextArea
                        placeholder={field.placeholder}
                        rows={3}
                        value={config[field.key] || ''}
                        onChange={e => updateConnectorConfig(configuringConnector.workerId, configuringConnector.connectorId, field.key, e.target.value)}
                      />
                    ) : field.type === 'password' ? (
                      <Input.Password
                        placeholder={field.placeholder}
                        value={config[field.key] || ''}
                        onChange={e => updateConnectorConfig(configuringConnector.workerId, configuringConnector.connectorId, field.key, e.target.value)}
                      />
                    ) : (
                      <Input
                        placeholder={field.placeholder}
                        value={config[field.key] || ''}
                        onChange={e => updateConnectorConfig(configuringConnector.workerId, configuringConnector.connectorId, field.key, e.target.value)}
                      />
                    )}
                  </Form.Item>
                ))}
              </Form>
            );
          })()}
        </Modal>

        {/* Create Digital Employee Modal */}
        <Modal
          title="Provision Digital Employee"
          open={activeActionModal === 'Digital Employee'}
          onCancel={() => setActiveActionModal(null)}
          onOk={() => actionForm.submit()}
          okText="Bind & Provision"
          cancelText="Cancel"
        >
          <Form form={actionForm} layout="vertical" onFinish={handleCreateDigitalEmployee} style={{ marginTop: 16 }}>
            <Form.Item label="Select Human Owner (Supervisor)" required>
              <Select value={selectedHumanOwnerId} onChange={setSelectedHumanOwnerId}>
                <Option value="project-owner">Project Owner</Option>
              </Select>
            </Form.Item>
            <Form.Item name="name" label="Digital Worker Name" rules={[{ required: true, message: 'Please enter name' }]}>
              <Input placeholder="e.g. DBA Automation Node" />
            </Form.Item>
            <Form.Item name="description" label="Operational Task Scope">
              <TextArea rows={3} placeholder="Provide instructions, endpoints, or parameter definitions..." />
            </Form.Item>
          </Form>
        </Modal>

      </Layout>
    </ConfigProvider>
  );
};

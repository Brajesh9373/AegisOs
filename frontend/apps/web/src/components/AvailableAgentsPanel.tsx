/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useEffect, useMemo } from 'react';
import {
  ApartmentOutlined,
  ApiOutlined,
  AppstoreOutlined,
  AuditOutlined,
  BookOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  EditOutlined,
  ExportOutlined,
  LockOutlined,
  MoreOutlined,
  PartitionOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
  SyncOutlined,
  TeamOutlined,
  ThunderboltOutlined,
  RobotOutlined,
  ToolOutlined,
  WarningOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import {
  Avatar,
  Button,
  Card,
  Col,
  Divider,
  Dropdown,
  Empty,
  Input,
  Row,
  Select,
  Skeleton,
  Tabs,
  Tag,
  Tree,
  Typography,
  Space,
  message,
} from 'antd';
import type { DataNode } from 'antd/es/tree';
import EvalsTab from './EvalsTab';

const { Text, Title, Paragraph } = Typography;

interface Agent {
  id: string;
  name: string;
  role?: string;
  department?: string;
  designation?: string;
  role_description?: string;
  reports_to?: string | null;
  skills?: string[];
  status?: string;
  model?: string;
  certificates?: any[];
  tool_policy?: any;
  workspace_scope?: any;
  system_prompt_addon?: string | null;
  automation?: any;
  features?: any;
}

type ViewMode = 'hierarchy' | 'departments' | 'certifications';

const VIEW_OPTIONS = [
  { label: 'Hierarchy', value: 'hierarchy', icon: <ApartmentOutlined /> },
  { label: 'Departments', value: 'departments', icon: <AppstoreOutlined /> },
  { label: 'Certifications', value: 'certifications', icon: <SettingOutlined /> },
];

const normalizeDepartment = (value?: string) =>
  (value || 'Unassigned')
    .replace(/[-_]+/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());

const normalizeRole = (value?: string) =>
  (value || 'Agent')
    .replace(/[-_]+/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());

const initials = (name: string) =>
  name
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase();

const avatarTone = (value: string) => {
  const tones = [
    ['#dbeafe', '#1d4ed8'],
    ['#ede9fe', '#6d28d9'],
    ['#dcfce7', '#15803d'],
    ['#ffedd5', '#c2410c'],
    ['#fce7f3', '#be185d'],
  ];
  const idx = [...value].reduce((s, c) => s + c.charCodeAt(0), 0) % tones.length;
  return tones[idx];
};

interface Props {
  agents: Agent[];
  selectedAgent: Agent | null;
  loading?: boolean;
  onSelect: (a: Agent | null) => void;
  onCreate: () => void;
  onEdit: (a: Agent) => void;
  onDelete: (a: Agent) => void;
}

export const AvailableAgentsPanel: React.FC<Props> = ({
  agents,
  selectedAgent,
  loading = false,
  onSelect,
  onCreate,
  onEdit,
  onDelete,
}) => {
  const [view, setView] = useState<ViewMode>('hierarchy');
  const [query, setQuery] = useState('');
  const [department, setDepartment] = useState('all');
  const [status, setStatus] = useState('all');

  const agentById = useMemo(() => new Map(agents.map((a) => [a.id, a])), [agents]);

  const childCount = useMemo(() => {
    const counts = new Map<string, number>();
    agents.forEach((a) => {
      if (a.reports_to) counts.set(a.reports_to, (counts.get(a.reports_to) || 0) + 1);
    });
    return counts;
  }, [agents]);

  const departments = useMemo(
    () =>
      Array.from(
        new Set(agents.map((a) => a.department).filter(Boolean) as string[]),
      ).sort(),
    [agents],
  );

  const filteredAgents = useMemo(() => {
    const search = query.trim().toLowerCase();
    return agents.filter((a) => {
      const searchable = `${a.name} ${a.designation || ''} ${a.role || ''} ${a.department || ''} ${(a.skills || []).join(' ')}`.toLowerCase();
      return (
        (!search || searchable.includes(search)) &&
        (department === 'all' || a.department === department) &&
        (status === 'all' || (a.status || 'active') === status)
      );
    });
  }, [agents, department, query, status]);

  const visibleHierarchyAgents = useMemo(() => {
    if (!query.trim() && department === 'all' && status === 'all') return agents;
    const visibleIds = new Set(filteredAgents.map((a) => a.id));
    filteredAgents.forEach((a) => {
      let parentId = a.reports_to;
      while (parentId) {
        visibleIds.add(parentId);
        parentId = agentById.get(parentId)?.reports_to;
      }
    });
    return agents.filter((a) => visibleIds.has(a.id));
  }, [agentById, agents, department, filteredAgents, query, status]);

  const treeData = useMemo<DataNode[]>(() => {
    const visibleIds = new Set(visibleHierarchyAgents.map((a) => a.id));
    const children = new Map<string, Agent[]>();
    visibleHierarchyAgents.forEach((a) => {
      const parent = a.reports_to && visibleIds.has(a.reports_to) ? a.reports_to : '__root__';
      const group = children.get(parent) || [];
      group.push(a);
      children.set(parent, group);
    });

    const walk = (parentId: string): DataNode[] =>
      (children.get(parentId) || [])
        .sort((l, r) => l.name.localeCompare(r.name))
        .map((agent) => {
          const [background, color] = avatarTone(agent.id);
          const reports = childCount.get(agent.id) || 0;
          return {
            key: agent.id,
            title: (
              <div style={{
                display: 'flex', alignItems: 'center', gap: 8, padding: '3px 0',
                opacity: agent.status === 'inactive' ? 0.55 : 1,
              }}>
                <Avatar size={28} style={{ background, color, flexShrink: 0 }}>{initials(agent.name)}</Avatar>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <Text strong style={{ fontSize: 12, display: 'block', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{agent.name}</Text>
                  <Text style={{ fontSize: 10, color: '#64748b', display: 'block' }}>
                    {agent.designation || normalizeRole(agent.role)} · {normalizeDepartment(agent.department)}
                  </Text>
                </div>
                <div style={{ display: 'flex', gap: 4, flexShrink: 0 }}>
                  {reports > 0 && (
                    <Tag style={{ margin: 0, fontSize: 9 }}>
                      {reports} report{reports === 1 ? '' : 's'}
                    </Tag>
                  )}
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: agent.status === 'active' ? '#16a34a' : '#94a3b8' }} />
                </div>
              </div>
            ),
            children: walk(agent.id),
            isLeaf: reports === 0,
          };
        });

    return walk('__root__');
  }, [childCount, visibleHierarchyAgents]);

  const departmentGroups = useMemo(() => {
    const groups = new Map<string, Agent[]>();
    filteredAgents.forEach((a) => {
      const key = a.department || 'unassigned';
      groups.set(key, [...(groups.get(key) || []), a]);
    });
    return Array.from(groups.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [filteredAgents]);

  const activeCount = agents.filter((a) => (a.status || 'active') === 'active').length;
  const tools = selectedAgent ? (selectedAgent.tool_policy || {}).allowed_tools || [] : [];

  const renderDetail = () => {
    if (!selectedAgent) {
      return (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#94a3b8' }}>
          <RobotOutlined style={{ fontSize: 28, marginBottom: 8, color: '#cbd5e1' }} />
          <Title level={5}>Select an agent</Title>
          <Text>Choose a reusable agent to review its designation, skills, tools, and certifications.</Text>
        </div>
      );
    }

    const [background, color] = avatarTone(selectedAgent.id);
    const profileDesignation = selectedAgent.designation || normalizeRole(selectedAgent.role);
    const policy = selectedAgent.tool_policy || {};
    const automation = selectedAgent.automation || {};
    const features = selectedAgent.features || {};
    const workspaceScope = selectedAgent.workspace_scope || {};
    const runtimeStatus = selectedAgent.status === 'inactive' ? 'INACTIVE' : 'WAITING';
    const goal = selectedAgent.role_description || `Own ${profileDesignation.toLowerCase()} responsibilities across project execution.`;
    const systemPrompt = selectedAgent.system_prompt_addon || `Execute the ${profileDesignation} role using assigned tools, available knowledge, and configured guardrails.`;
    const memoryState = Array.isArray(workspaceScope.memory) ? workspaceScope.memory : [];
    const knowledgeAssets = Array.isArray(selectedAgent.skills) ? selectedAgent.skills : [];
    const executionLogs = Array.isArray(workspaceScope.logs) ? workspaceScope.logs : [];
    const guardrails = Array.isArray(policy.guardrails) && policy.guardrails.length > 0
      ? policy.guardrails
      : [
          { name: 'Allowed tool policy', type: 'hard', enabled: true, description: 'Agent can only use tools listed in its configured tool policy.' },
          { name: 'Audit logging', type: 'soft', enabled: features.auditLogging !== false, description: 'Agent actions should remain traceable for administrative review.' },
          { name: 'PII masking', type: 'hard', enabled: !!features.piiMasking, description: 'Sensitive data is masked when this feature is enabled.' },
        ];
    const automationRules = [
      { label: 'Auto Retry on Failure', value: automation.autoRetry !== false ? 'Enabled' : 'Disabled', color: automation.autoRetry !== false ? '#16a34a' : '#dc2626', icon: <SyncOutlined /> },
      { label: 'Max Retries', value: String(automation.maxRetries ?? 3), color: '#2563eb', icon: <ReloadOutlined /> },
      { label: 'Retry Delay', value: `${automation.retryDelaySeconds ?? 30}s`, color: '#2563eb', icon: <ClockCircleOutlined /> },
      { label: 'Escalate on Failure', value: automation.escalateOnFailure !== false ? 'Yes' : 'No', color: automation.escalateOnFailure !== false ? '#d97706' : '#6b7280', icon: <WarningOutlined /> },
      { label: 'Heartbeat Interval', value: `${automation.heartbeatIntervalSeconds ?? 60}s`, color: '#2563eb', icon: <SyncOutlined /> },
    ];
    const featureItems = [
      { label: 'Memory Retention', value: `${features.memoryRetentionDays ?? 30} days`, desc: 'How long agent memory persists between sessions', icon: <BookOutlined /> },
      { label: 'Data Query Access', value: features.dataQueryAccess === 'write' ? 'Read & Write' : 'Read Only', desc: 'Permission level for database operations', icon: <DatabaseOutlined /> },
      { label: 'Max Concurrent Tasks', value: String(features.maxConcurrentTasks ?? 5), desc: 'Maximum parallel task executions', icon: <PartitionOutlined /> },
      { label: 'Rate Limit', value: `${features.rateLimitPerMinute ?? 60} req/min`, desc: 'API call throttling threshold', icon: <ThunderboltOutlined /> },
      { label: 'Streaming', value: features.streamingEnabled !== false ? 'Enabled' : 'Disabled', desc: 'Real-time response streaming', icon: <ApiOutlined /> },
      { label: 'Audit Logging', value: features.auditLogging !== false ? 'Enabled' : 'Disabled', desc: 'Full action trace for compliance', icon: <AuditOutlined /> },
      { label: 'PII Masking', value: features.piiMasking ? 'Enabled' : 'Disabled', desc: 'Automatic redaction of sensitive data', icon: <LockOutlined /> },
    ];

    return (
      <div>
        <header style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <Avatar size={56} style={{ background, color }}>{initials(selectedAgent.name)}</Avatar>
          <div>
            <Title level={4} style={{ margin: 0 }}>{selectedAgent.name}</Title>
            <Text type="secondary" style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.4 }}>{selectedAgent.role || 'agent'}</Text>
            <Text style={{ color: '#64748b', fontSize: 11, display: 'block', marginTop: 4 }}>
              Assigned agent: {selectedAgent.id}
            </Text>
            <div style={{ marginTop: 4, display: 'flex', gap: 4 }}>
              <Tag color={runtimeStatus === 'WAITING' ? 'orange' : 'default'}>{runtimeStatus}</Tag>
              {selectedAgent.model && <Tag color="blue">{selectedAgent.model}</Tag>}
            </div>
          </div>
        </header>

        <Tabs
          defaultActiveKey="overview"
          style={{ marginTop: 12 }}
          items={[
            {
              key: 'overview',
              label: 'Overview',
              children: (
                <div style={{ padding: '12px 0' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 16, background: '#f8fafc', borderRadius: 10, border: '1px solid #e2e8f0', marginBottom: 16 }}>
                    <div style={{ width: 44, height: 44, borderRadius: '50%', background: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '2px solid #bfdbfe' }}>
                      <RobotOutlined style={{ fontSize: 20, color: '#2563eb' }} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <Text strong style={{ fontSize: 14, display: 'block' }}>{selectedAgent.name}</Text>
                      <Text type="secondary" style={{ fontSize: 11 }}>{selectedAgent.model || 'gpt-4o'}</Text>
                    </div>
                    <Tag color={runtimeStatus === 'WAITING' ? 'orange' : 'default'}>{runtimeStatus}</Tag>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', background: '#f0f9ff', borderRadius: 8, border: '1px solid #bae6fd', marginBottom: 16 }}>
                    <RobotOutlined style={{ fontSize: 16, color: '#2563eb' }} />
                    <div>
                      <Text type="secondary" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 0.5, display: 'block' }}>Agent designation</Text>
                      <Text strong style={{ fontSize: 13 }}>{profileDesignation}</Text>
                    </div>
                    <Tag color="blue" style={{ marginLeft: 'auto', fontSize: 10 }}>Available</Tag>
                  </div>

                  <div style={{ marginBottom: 16 }}>
                    <Text type="secondary" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 0.5, display: 'block', marginBottom: 4 }}>Agent Goal</Text>
                    <Text style={{ fontSize: 12, color: '#374151' }}>{goal}</Text>
                  </div>

                  <div style={{ marginBottom: 16 }}>
                    <Text type="secondary" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 0.5, display: 'block', marginBottom: 4 }}>System Prompt</Text>
                    <div style={{ padding: '8px 10px', background: '#f8fafc', borderRadius: 6, border: '1px solid #e2e8f0' }}>
                      <Text style={{ fontSize: 11, color: '#475569', lineHeight: 1.5 }}>{systemPrompt}</Text>
                    </div>
                  </div>

                  <Row gutter={12} style={{ marginBottom: 16 }}>
                    <Col span={12}>
                      <Text type="secondary" style={{ fontSize: 10, textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>Memory State</Text>
                      <Space wrap size={4}>
                        {memoryState.length > 0
                          ? memoryState.map((m: string, i: number) => <Tag key={`${m}-${i}`} color="blue" style={{ fontSize: 9 }}>{m}</Tag>)
                          : <Text type="secondary" style={{ fontSize: 11 }}>No memory state recorded.</Text>}
                      </Space>
                    </Col>
                    <Col span={12}>
                      <Text type="secondary" style={{ fontSize: 10, textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>Knowledge Assets</Text>
                      <Space wrap size={4}>
                        {knowledgeAssets.length > 0
                          ? knowledgeAssets.map((k: string, i: number) => <Tag key={`${k}-${i}`} color="cyan" style={{ fontSize: 9 }}>{k}</Tag>)
                          : <Text type="secondary" style={{ fontSize: 11 }}>No knowledge assets recorded.</Text>}
                      </Space>
                    </Col>
                  </Row>

                  <Divider style={{ margin: '12px 0' }} />

                  <div style={{ marginBottom: 16 }}>
                    <Text type="secondary" style={{ fontSize: 10, textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>Current Task</Text>
                    <div style={{ padding: '8px 12px', background: '#fef3c7', borderRadius: 6, border: '1px solid #fde68a' }}>
                      <Text style={{ fontSize: 12, color: '#92400e' }}>● {profileDesignation}</Text>
                    </div>
                  </div>

                  <div>
                    <Text type="secondary" style={{ fontSize: 10, textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>Execution Logs</Text>
                    <div style={{ background: '#f8fafc', padding: 10, borderRadius: 6, border: '1px solid #e2e8f0', fontFamily: 'monospace', fontSize: 10, maxHeight: 120, overflowY: 'auto' }}>
                      {executionLogs.length > 0
                        ? executionLogs.map((log: string, i: number) => <div key={i} style={{ color: '#475569', marginBottom: 3 }}>{log}</div>)
                        : <Text type="secondary" style={{ fontSize: 10 }}>No execution logs yet.</Text>}
                    </div>
                  </div>
                </div>
              ),
            },
            {
              key: 'tools',
              label: 'Tools',
              children: (
                <div style={{ padding: '16px 0' }}>
                  <Text type="secondary" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 0.5, display: 'block', marginBottom: 10 }}>Configured Tools</Text>
                  {tools.length > 0 ? (
                    <Space wrap size={8}>
                      {tools.map((t: string) => (
                        <div key={t} style={{ padding: '8px 14px', background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: 8 }}>
                          <ToolOutlined style={{ color: '#f59e0b', fontSize: 12 }} />
                          <Text style={{ fontSize: 11, fontWeight: 500 }}>{t}</Text>
                        </div>
                      ))}
                    </Space>
                  ) : (
                    <Text type="secondary">No tools assigned yet.</Text>
                  )}
                </div>
              ),
            },
            {
              key: 'knowledge',
              label: 'Knowledge',
              children: (
                <div style={{ padding: '16px 0' }}>
                  <Text style={{ fontSize: 13, color: '#0f172a', display: 'block', marginBottom: 16 }}>Knowledge sources and scopes available to this reusable agent.</Text>
                  <Text strong style={{ fontSize: 11, display: 'block', marginBottom: 8 }}>Knowledge Assets</Text>
                  <Space wrap size={6} style={{ marginBottom: 16 }}>
                    {knowledgeAssets.length > 0
                      ? knowledgeAssets.map((asset: string) => <Tag key={asset} color="cyan">{asset}</Tag>)
                      : <Text type="secondary">No knowledge assets recorded.</Text>}
                  </Space>
                  <Card size="small" style={{ background: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: 8 }} bodyStyle={{ padding: '10px 14px' }}>
                    <Text style={{ fontSize: 11, color: '#475569', lineHeight: 1.6 }}>
                      Workspace scope: <Text code>{Object.keys(workspaceScope).length ? JSON.stringify(workspaceScope) : 'global reusable agent pool'}</Text>
                    </Text>
                  </Card>
                </div>
              ),
            },
            {
              key: 'evals',
              label: 'Evals',
              children: <EvalsTab agentName={selectedAgent.name} />,
            },
            {
              key: 'guardrails',
              label: 'Guardrails',
              children: (
                <div style={{ padding: '16px 0' }}>
                  <Text style={{ fontSize: 13, fontWeight: 600, color: '#0f172a', display: 'block' }}>Guardrails</Text>
                  <Text type="secondary" style={{ fontSize: 11, marginBottom: 16, display: 'block' }}>Safety rules enforced during agent execution.</Text>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {guardrails.map((guardrail: any, i: number) => (
                      <div key={`${guardrail.name || 'guardrail'}-${i}`} style={{ padding: '10px 12px', borderRadius: 8, background: '#fff', border: '1px solid #e2e8f0' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                          <LockOutlined style={{ fontSize: 11, color: guardrail.type === 'soft' ? '#d97706' : '#dc2626' }} />
                          <Text strong style={{ fontSize: 12, flex: 1 }}>{guardrail.name || 'Guardrail'}</Text>
                          <Tag color={guardrail.type === 'soft' ? 'orange' : 'red'} style={{ margin: 0, fontSize: 9 }}>{guardrail.type || 'hard'}</Tag>
                          <Tag color={guardrail.enabled === false ? 'default' : 'green'} style={{ margin: 0, fontSize: 9 }}>{guardrail.enabled === false ? 'Disabled' : 'Enabled'}</Tag>
                        </div>
                        {guardrail.description && <Text type="secondary" style={{ fontSize: 10, display: 'block', marginLeft: 19 }}>{guardrail.description}</Text>}
                      </div>
                    ))}
                  </div>
                </div>
              ),
            },
            {
              key: 'skills',
              label: 'Skills',
              children: (
                <div style={{ padding: '16px 0' }}>
                  <Text style={{ fontSize: 13, fontWeight: 600, color: '#0f172a', display: 'block', marginBottom: 4 }}>Agent Skills</Text>
                  <Text type="secondary" style={{ fontSize: 11, marginBottom: 16, display: 'block' }}>Specialized capabilities assigned to this agent.</Text>
                  {knowledgeAssets.length === 0 ? (
                    <div style={{ padding: 20, textAlign: 'center', background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                      <Text style={{ fontSize: 12, color: '#94a3b8' }}>No skills assigned to this agent yet.</Text>
                    </div>
                  ) : (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10 }}>
                      {knowledgeAssets.map((skill: string, i: number) => (
                        <div key={`${skill}-${i}`} style={{ padding: '10px 14px', background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: 10 }}>
                          <div style={{ width: 28, height: 28, borderRadius: 6, background: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                            <ThunderboltOutlined style={{ fontSize: 13, color: '#2563eb' }} />
                          </div>
                          <Text style={{ fontSize: 12, fontWeight: 500 }}>{skill}</Text>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ),
            },
            {
              key: 'certifications',
              label: 'Certifications',
              children: (
                <div style={{ padding: '16px 0' }}>
                  <Text style={{ fontSize: 13, fontWeight: 600, color: '#0f172a', display: 'block', marginBottom: 4 }}>Agent Certifications</Text>
                  <Text type="secondary" style={{ fontSize: 11, marginBottom: 16, display: 'block' }}>Verified credentials associated with this agent&apos;s specialist capabilities.</Text>
                  {(selectedAgent.certificates || []).length > 0 ? (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10 }}>
                      {selectedAgent.certificates!.map((c: any, i: number) => {
                        const name = typeof c === 'string' ? c : c.name || c.title || 'Certification';
                        const issuer = typeof c === 'string' ? '' : c.issuer || '';
                        const url = typeof c === 'string' ? '' : c.url || '';
                        return (
                          <div key={`${name}-${i}`} style={{ minHeight: 82, padding: '12px 14px', background: '#fff', borderRadius: 9, border: '1px solid #e2e8f0', display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                            <div style={{ width: 38, height: 38, borderRadius: 8, background: '#fffbeb', border: '1px solid #fde68a', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                              <img src="/assets/certificate.webp" alt="" style={{ width: 24, height: 24, objectFit: 'contain' }} />
                            </div>
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <Text strong style={{ fontSize: 11.5, lineHeight: 1.45, display: 'block' }}>{name}</Text>
                              {issuer && <Text type="secondary" style={{ fontSize: 10, display: 'block', marginTop: 3 }}>{issuer}</Text>}
                            </div>
                            {url && <ExportOutlined style={{ color: '#64748b', fontSize: 11, marginTop: 3 }} />}
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <Text type="secondary">No certifications assigned.</Text>
                  )}
                </div>
              ),
            },
            {
              key: 'automation',
              label: 'Automation',
              children: (
                <div style={{ padding: '16px 0' }}>
                  <Text style={{ fontSize: 13, fontWeight: 600, color: '#0f172a', display: 'block', marginBottom: 4 }}>Automation Rules</Text>
                  <Text type="secondary" style={{ fontSize: 11, marginBottom: 16, display: 'block' }}>How this agent handles retries, escalations, and self-healing.</Text>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {automationRules.map((rule, i) => (
                      <div key={`${rule.label}-${i}`} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px', background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                        <div style={{ width: 28, height: 28, borderRadius: 6, background: '#f0fdf4', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: rule.color }}>
                          {rule.icon}
                        </div>
                        <Text style={{ fontSize: 12, flex: 1 }}>{rule.label}</Text>
                        <Tag style={{ margin: 0, fontSize: 11, fontWeight: 600, border: 'none', background: rule.color === '#dc2626' ? '#fef2f2' : '#eff6ff', color: rule.color }}>{rule.value}</Tag>
                      </div>
                    ))}
                  </div>
                </div>
              ),
            },
            {
              key: 'features',
              label: 'Features',
              children: (
                <div style={{ padding: '16px 0' }}>
                  <Text style={{ fontSize: 13, fontWeight: 600, color: '#0f172a', display: 'block', marginBottom: 4 }}>Agent Features & Capabilities</Text>
                  <Text type="secondary" style={{ fontSize: 11, marginBottom: 16, display: 'block' }}>Memory, data access, rate limits, and other configurable features.</Text>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {featureItems.map((item, i) => (
                      <div key={`${item.label}-${i}`} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px', background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
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
                </div>
              ),
            },
          ]}
        />

        <footer style={{ display: 'flex', gap: 8, marginTop: 12 }}>
          <Button icon={<EditOutlined />} onClick={() => onEdit(selectedAgent)}>Edit agent</Button>
          <Dropdown
            menu={{
              items: [{ key: 'delete', label: 'Delete agent', danger: true }],
              onClick: ({ key }) => { if (key === 'delete') onDelete(selectedAgent); },
            }}
          >
            <Button icon={<MoreOutlined />}>More</Button>
          </Dropdown>
        </footer>
      </div>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>
            <RobotOutlined style={{ marginRight: 8 }} />Available Agent Hierarchy
          </Title>
          <Text>{agents.length} agents · {departments.length} departments · {activeCount} active</Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={onCreate}>Hire Agent</Button>
      </div>

      {/* Toolbar */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <Input
          allowClear
          prefix={<SearchOutlined />}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search agents, designations, or skills"
          style={{ width: 240 }}
        />
        <Select
          value={department}
          onChange={setDepartment}
          style={{ width: 150 }}
          options={[
            { value: 'all', label: 'All departments' },
            ...departments.map((d) => ({ value: d, label: normalizeDepartment(d) })),
          ]}
        />
        <Select
          value={status}
          onChange={setStatus}
          style={{ width: 120 }}
          options={[
            { value: 'all', label: 'All statuses' },
            { value: 'active', label: 'Active' },
            { value: 'inactive', label: 'Inactive' },
          ]}
        />
      </div>

      {/* View switcher */}
      <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid #e2e8f0', paddingBottom: 8 }}>
        {VIEW_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => setView(opt.value as ViewMode)}
            style={{
              display: 'flex', alignItems: 'center', gap: 4, padding: '6px 12px',
              border: 'none', background: view === opt.value ? '#eff6ff' : 'transparent',
              cursor: 'pointer', fontSize: 12, fontWeight: view === opt.value ? 600 : 400,
              color: view === opt.value ? '#1d4ed8' : '#64748b',
              borderRadius: 6,
            }}
          >
            {opt.icon}{opt.label}
          </button>
        ))}
      </div>

      {/* Main content */}
      <div style={{ display: 'flex', gap: 16, flex: 1, minHeight: 0 }}>
        {/* Left: tree / departments / certifications */}
        <div style={{ flex: 1, overflowY: 'auto', maxHeight: 500 }}>
          {loading ? (
            <Skeleton active paragraph={{ rows: 8 }} />
          ) : filteredAgents.length === 0 ? (
            <Empty description="No agents match these filters" />
          ) : view === 'hierarchy' ? (
            <Tree
              treeData={treeData}
              defaultExpandedKeys={treeData.slice(0, 2).map((n) => n.key)}
              blockNode
              showLine={{ showLeafIcon: false }}
              selectedKeys={selectedAgent ? [selectedAgent.id] : []}
              onSelect={(keys) => onSelect(agentById.get(String(keys[0])) || null)}
              style={{ fontSize: 12 }}
            />
          ) : view === 'departments' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {departmentGroups.map(([dept, members]) => (
                <article key={dept} style={{ border: '1px solid #e2e8f0', borderRadius: 8, overflow: 'hidden' }}>
                  <header style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 12px', background: '#f8fafc' }}>
                    <ApartmentOutlined style={{ color: '#2563eb' }} />
                    <div>
                      <Text strong>{normalizeDepartment(dept)}</Text>
                      <Text style={{ fontSize: 10, color: '#64748b', display: 'block' }}>{members.length} agent{members.length === 1 ? '' : 's'}</Text>
                    </div>
                  </header>
                  <div style={{ padding: '8px 12px', display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {members.map((agent) => (
                      <button
                        key={agent.id}
                        type="button"
                        onClick={() => onSelect(agent)}
                        style={{
                          display: 'flex', alignItems: 'center', gap: 6, padding: '6px 10px',
                          border: '1px solid #e2e8f0', borderRadius: 6, background: selectedAgent?.id === agent.id ? '#eff6ff' : '#fff',
                          cursor: 'pointer', fontSize: 11, color: '#111827',
                        }}
                      >
                        <Avatar size={22}>{initials(agent.name)}</Avatar>
                        <span>{agent.name}<small style={{ color: '#64748b', marginLeft: 4 }}>{agent.designation || normalizeRole(agent.role)}</small></span>
                      </button>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          ) : view === 'certifications' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {filteredAgents.map((agent) => {
                const certs = agent.certificates || [];
                return (
                  <div key={agent.id} style={{ padding: '10px 12px', border: '1px solid #e2e8f0', borderRadius: 8, background: '#fff' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                      <Avatar size={24}>{initials(agent.name)}</Avatar>
                      <Text strong style={{ fontSize: 12 }}>{agent.name}</Text>
                      <Tag style={{ margin: 0, marginLeft: 'auto', fontSize: 9 }}>{certs.length} cert{certs.length === 1 ? '' : 's'}</Tag>
                    </div>
                    {certs.length > 0 ? (
                      <Space wrap size={4}>
                        {certs.map((c: any, i: number) => (
                          <Tag key={i} color="gold" style={{ fontSize: 9 }}>{typeof c === 'string' ? c : c.name || c.title}</Tag>
                        ))}
                      </Space>
                    ) : (
                      <Text style={{ fontSize: 10, color: '#94a3b8' }}>No certifications</Text>
                    )}
                  </div>
                );
              })}
            </div>
          ) : null}
        </div>

        {/* Right: detail */}
        <div style={{ width: 320, flexShrink: 0, borderLeft: '1px solid #e2e8f0', paddingLeft: 16, overflowY: 'auto', maxHeight: 500 }}>
          {renderDetail()}
        </div>
      </div>
    </div>
  );
};

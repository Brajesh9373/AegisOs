import React, { useEffect, useMemo, useState } from 'react';
import {
  ApartmentOutlined,
  AppstoreOutlined,
  EditOutlined,
  MoreOutlined,
  PlusOutlined,
  SearchOutlined,
  SettingOutlined,
  TeamOutlined,
  ToolOutlined,
} from '@ant-design/icons';
import {
  Avatar,
  Button,
  Dropdown,
  Empty,
  Input,
  Select,
  Skeleton,
  Tabs,
  Tag,
  Tree,
  Typography,
} from 'antd';
import type { DataNode } from 'antd/es/tree';
import './OrganizationPanel.css';

const { Paragraph, Text, Title } = Typography;

export interface OrganizationMember {
  id: string;
  name: string;
  role?: string;
  department?: string;
  designation?: string;
  role_description?: string;
  reports_to?: string | null;
  skills?: string[];
  status?: string;
  project_id?: null;
  assigned_tools?: string[];
}

export interface ProjectAgent {
  id: string;
  project_id: string;
  name: string;
  role?: string;
  department?: string;
  designation?: string;
  status?: string;
}

interface OrganizationPanelProps {
  members: OrganizationMember[];
  projectAgents: ProjectAgent[];
  selectedMember: OrganizationMember | null;
  loading?: boolean;
  onSelect: (member: OrganizationMember | null) => void;
  onCreate: () => void;
  onEdit: (member: OrganizationMember) => void;
  onDelete: (member: OrganizationMember) => void;
}

type OrganizationView = 'hierarchy' | 'departments';

const VIEW_OPTIONS = [
  { label: 'Hierarchy', value: 'hierarchy', icon: <ApartmentOutlined /> },
  { label: 'Departments', value: 'departments', icon: <AppstoreOutlined /> },
];

const normalizeDepartment = (value?: string) =>
  (value || 'Unassigned')
    .replace(/[-_]+/g, ' ')
    .replace(/\b\w/g, character => character.toUpperCase());

const normalizeRole = (value?: string) =>
  (value || 'Team member')
    .replace(/[-_]+/g, ' ')
    .replace(/\b\w/g, character => character.toUpperCase());

const initials = (name: string) =>
  name
    .split(/\s+/)
    .slice(0, 2)
    .map(part => part[0])
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
  const index = [...value].reduce((sum, character) => sum + character.charCodeAt(0), 0) % tones.length;
  return tones[index];
};

export const OrganizationPanel: React.FC<OrganizationPanelProps> = ({
  members: agents,
  projectAgents,
  selectedMember: selectedAgent,
  loading = false,
  onSelect,
  onCreate,
  onEdit,
  onDelete,
}) => {
  const [view, setView] = useState<OrganizationView>('hierarchy');
  const [query, setQuery] = useState('');
  const [department, setDepartment] = useState('all');
  const [status, setStatus] = useState('all');
  const [assignments, setAssignments] = useState<any[]>([]);
  const [toolAssignments, setToolAssignments] = useState<any[]>([]);

  useEffect(() => {
    if (!selectedAgent) { setAssignments([]); return; }
    const token = localStorage.getItem('auth_token');
    const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
    fetch(`/organization/members/${selectedAgent.id}/assignments`, { headers })
      .then(res => res.ok ? res.json() : [])
      .then(data => { if (Array.isArray(data)) setAssignments(data); })
      .catch(() => setAssignments([]));
  }, [selectedAgent?.id]);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
    fetch('/organization/tool-assignments', { headers })
      .then(res => res.ok ? res.json() : [])
      .then(data => { if (Array.isArray(data)) setToolAssignments(data); })
      .catch(() => setToolAssignments([]));
  }, []);

  const agentById = useMemo(() => new Map(agents.map(agent => [agent.id, agent])), [agents]);
  const childCount = useMemo(() => {
    const counts = new Map<string, number>();
    agents.forEach(agent => {
      if (agent.reports_to) counts.set(agent.reports_to, (counts.get(agent.reports_to) || 0) + 1);
    });
    return counts;
  }, [agents]);

  const departments = useMemo(
    () => Array.from(new Set(agents.map(agent => agent.department).filter(Boolean) as string[])).sort(),
    [agents],
  );

  const filteredAgents = useMemo(() => {
    const search = query.trim().toLowerCase();
    return agents.filter(agent => {
      const searchable = `${agent.name} ${agent.designation || ''} ${agent.role || ''} ${agent.department || ''}`.toLowerCase();
      return (
        (!search || searchable.includes(search)) &&
        (department === 'all' || agent.department === department) &&
        (status === 'all' || (agent.status || 'active') === status)
      );
    });
  }, [agents, department, query, status]);

  const visibleHierarchyAgents = useMemo(() => {
    if (!query.trim() && department === 'all' && status === 'all') return agents;
    const visibleIds = new Set(filteredAgents.map(agent => agent.id));
    filteredAgents.forEach(agent => {
      let parentId = agent.reports_to;
      while (parentId) {
        visibleIds.add(parentId);
        parentId = agentById.get(parentId)?.reports_to;
      }
    });
    return agents.filter(agent => visibleIds.has(agent.id));
  }, [agentById, agents, department, filteredAgents, query, status]);

  const treeData = useMemo<DataNode[]>(() => {
    const visibleIds = new Set(visibleHierarchyAgents.map(agent => agent.id));
    const children = new Map<string, OrganizationMember[]>();
    visibleHierarchyAgents.forEach(agent => {
      const parent = agent.reports_to && visibleIds.has(agent.reports_to) ? agent.reports_to : '__root__';
      const group = children.get(parent) || [];
      group.push(agent);
      children.set(parent, group);
    });

    const walk = (parentId: string): DataNode[] =>
      (children.get(parentId) || [])
        .sort((left, right) => left.name.localeCompare(right.name))
        .map(agent => {
          const [background, color] = avatarTone(agent.id);
          const reports = childCount.get(agent.id) || 0;
          return {
            key: agent.id,
            title: (
              <div className={`org-node ${selectedAgent?.id === agent.id ? 'org-node--selected' : ''}`}>
                <Avatar style={{ background, color }}>{initials(agent.name)}</Avatar>
                <div className="org-node__identity">
                  <Text strong>{agent.name}</Text>
                  <Text>{agent.designation || normalizeRole(agent.role)}</Text>
                </div>
                <div className="org-node__reports">
                  <TeamOutlined />
                  {reports} direct {reports === 1 ? 'report' : 'reports'}
                </div>
                <div className="org-node__status">
                  <span className={`org-status-dot org-status-dot--${agent.status || 'active'}`} />
                  {normalizeRole(agent.status || 'active')}
                </div>
              </div>
            ),
            children: walk(agent.id),
            isLeaf: reports === 0,
          };
        });

    return walk('__root__');
  }, [childCount, selectedAgent?.id, visibleHierarchyAgents]);

  const departmentGroups = useMemo(() => {
    const groups = new Map<string, OrganizationMember[]>();
    filteredAgents.forEach(agent => {
      const key = agent.department || 'unassigned';
      groups.set(key, [...(groups.get(key) || []), agent]);
    });
    return Array.from(groups.entries()).sort(([left], [right]) => left.localeCompare(right));
  }, [filteredAgents]);

  const directReports = selectedAgent ? childCount.get(selectedAgent.id) || 0 : 0;
  const manager = selectedAgent?.reports_to ? agentById.get(selectedAgent.reports_to) : null;
  const activeCount = agents.filter(agent => (agent.status || 'active') === 'active').length;

  // Compute tools assigned to the selected member
  const selectedMemberTools = selectedAgent
    ? toolAssignments.filter(ta => ta.organization_member_id === selectedAgent.id).map(ta => ta.tool_name)
    : [];

  // Map real governance assignments
  const displayAssignments = assignments.length > 0
    ? assignments.map(a => ({
        id: a.project_agent_id,
        name: a.agent_name || a.project_agent_id,
        role: a.agent_role || '',
        designation: a.agent_designation || '',
        project_id: a.project_id,
        status: a.status || 'active',
        responsibility: (a.responsibility || 'primary_owner').replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()),
      }))
    : [];

  const renderDetail = () => {
    if (!selectedAgent) {
      return (
        <div className="org-detail-empty">
          <div className="org-detail-empty__icon"><TeamOutlined /></div>
          <Title level={5}>Select a team member</Title>
          <Text>Choose someone from the organization to review their role, skills, and assignments.</Text>
        </div>
      );
    }

    const [background, color] = avatarTone(selectedAgent.id);
    return (
      <div className="org-detail">
        <header className="org-detail__header">
          <Avatar size={64} style={{ background, color }}>{initials(selectedAgent.name)}</Avatar>
          <div>
            <Title level={3}>{selectedAgent.name}</Title>
            <Text>{selectedAgent.designation || normalizeRole(selectedAgent.role)}</Text>
            <div className="org-detail__identity-meta">
              <span><ApartmentOutlined /> {normalizeDepartment(selectedAgent.department)}</span>
              <span><i className={`org-status-dot org-status-dot--${selectedAgent.status || 'active'}`} /> {normalizeRole(selectedAgent.status || 'active')}</span>
            </div>
          </div>
        </header>

        <Tabs
          className="org-detail__tabs"
          items={[
            {
              key: 'overview',
              label: 'Overview',
              children: (
                <div className="org-detail__content">
                  <dl className="org-facts">
                    <div>
                      <dt>Reports to</dt>
                      <dd>{manager?.name || 'No manager assigned'}</dd>
                    </div>
                    <div>
                      <dt>Direct reports</dt>
                      <dd>{directReports}</dd>
                    </div>
                    <div>
                      <dt>Role</dt>
                      <dd>{normalizeRole(selectedAgent.role)}</dd>
                    </div>
                  </dl>

                  <section className="org-detail__section">
                    <Text className="org-section-label">Skills</Text>
                    <div className="org-skill-list">
                      {selectedAgent.skills?.length ? (
                        selectedAgent.skills.map(skill => <Tag key={skill}>{skill}</Tag>)
                      ) : (
                        <Text type="secondary">No skills recorded</Text>
                      )}
                    </div>
                  </section>

                  <section className="org-detail__section">
                    <Text className="org-section-label">Role ownership</Text>
                    <Paragraph>
                      {selectedAgent.role_description || 'Responsibilities and role ownership have not been documented yet.'}
                    </Paragraph>
                  </section>

                  <section className="org-detail__section">
                    <Text className="org-section-label">Governance summary</Text>
                    <div className="org-governance-summary">
                      <div><strong>{displayAssignments.length}</strong><span>Assigned agents</span></div>
                      <div><strong>{new Set(displayAssignments.map(agent => agent.project_id)).size}</strong><span>Projects</span></div>
                      <div><strong>{displayAssignments.filter(agent => agent.responsibility === 'Primary owner').length}</strong><span>Primary ownerships</span></div>
                    </div>
                  </section>
                </div>
              ),
            },
            {
              key: 'capabilities',
              label: 'Capabilities',
              children: (
                <div className="org-detail__content">
                  <section className="org-detail__section">
                    <Text className="org-section-label">Assigned Tools</Text>
                    <Paragraph type="secondary">
                      Tools assigned to {selectedAgent.name} based on their role and department. Manage assignments in Administration → Tools.
                    </Paragraph>
                    <div className="org-skill-list">
                      {selectedMemberTools.length > 0 ? (
                        selectedMemberTools.map(tool => (
                          <Tag key={tool} color="blue" style={{ fontSize: 13, padding: '2px 10px' }}>{tool}</Tag>
                        ))
                      ) : (
                        <Text type="secondary">No tools assigned yet. Use "Auto-Assign by Role" in the Tools tab.</Text>
                      )}
                    </div>
                  </section>

                  <section className="org-detail__section">
                    <Text className="org-section-label">Core Capabilities</Text>
                    <div className="org-skill-list">
                      {(selectedAgent.skills || []).map(skill => (
                        <Tag key={skill}>{skill}</Tag>
                      ))}
                      {(!selectedAgent.skills || selectedAgent.skills.length === 0) && (
                        <Text type="secondary">No skills recorded</Text>
                      )}
                    </div>
                  </section>
                </div>
              ),
            },
            {
              key: 'assignments',
              label: 'Assignments',
              children: (
                <div className="org-mock-tab">
                  <div className="org-assignment-heading">
                    <div>
                      <Text strong>Project-agent governance</Text>
                      <Text>Agents this company member oversees as primary owner, monitor, or approver.</Text>
                    </div>
                  </div>
                  {displayAssignments.length ? (
                    <div className="org-mock-content">
                      {displayAssignments.map(projectAgent => (
                        <article className="org-assignment-card" key={`${projectAgent.id}-${projectAgent.responsibility}`}>
                          <div>
                            <Text strong>{projectAgent.name}</Text>
                            <Text>{projectAgent.designation || normalizeRole(projectAgent.role)}</Text>
                          </div>
                          <Tag color={projectAgent.responsibility === 'Primary owner' ? 'blue' : undefined}>
                            {projectAgent.responsibility}
                          </Tag>
                          <dl>
                            <div><dt>Project</dt><dd>{projectAgent.project_id}</dd></div>
                            <div><dt>Status</dt><dd>{normalizeRole(projectAgent.status || 'active')}</dd></div>
                          </dl>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <div className="org-assignment-empty">
                      <TeamOutlined />
                      <Text strong>No project agents available</Text>
                      <Text>Assignments will appear after a project team has been generated.</Text>
                    </div>
                  )}
                </div>
              ),
            },
          ]}
        />

        <footer className="org-detail__actions">
          <Button icon={<EditOutlined />} onClick={() => onEdit(selectedAgent)}>Edit member</Button>
          <Dropdown
            menu={{
              items: [{ key: 'delete', label: 'Delete member', danger: true }],
              onClick: ({ key }) => {
                if (key === 'delete') onDelete(selectedAgent);
              },
            }}
          >
            <Button icon={<MoreOutlined />}>More</Button>
          </Dropdown>
        </footer>
      </div>
    );
  };

  return (
    <div className="organization">
      <header className="organization__header">
        <div>
          <Title level={2}>Organization</Title>
          <Text>{agents.length} permanent members · {departments.length} departments · {activeCount} active</Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={onCreate}>Add member</Button>
      </header>

      <div className="organization__toolbar">
        <Input
          allowClear
          prefix={<SearchOutlined />}
          value={query}
          onChange={event => setQuery(event.target.value)}
          placeholder="Search people or roles"
          aria-label="Search organization"
        />
        <Select
          value={department}
          onChange={setDepartment}
          aria-label="Filter by department"
          options={[
            { value: 'all', label: 'All departments' },
            ...departments.map(value => ({ value, label: normalizeDepartment(value) })),
          ]}
        />
        <Select
          value={status}
          onChange={setStatus}
          aria-label="Filter by status"
          options={[
            { value: 'all', label: 'All statuses' },
            { value: 'active', label: 'Active' },
            { value: 'inactive', label: 'Inactive' },
          ]}
        />
      </div>

      <div className="organization__view-switcher" role="tablist" aria-label="Organization view">
        {VIEW_OPTIONS.map(option => (
          <button
            key={option.value}
            type="button"
            className={view === option.value ? 'is-active' : ''}
            onClick={() => setView(option.value as OrganizationView)}
            role="tab"
            aria-selected={view === option.value}
          >
            {option.icon}
            {option.label}
          </button>
        ))}
      </div>

      <div className="organization__workspace">
        <section className="organization__browser">
          {loading ? (
            <Skeleton active paragraph={{ rows: 8 }} />
          ) : filteredAgents.length === 0 ? (
            <Empty description="No members match these filters" />
          ) : view === 'hierarchy' ? (
            <Tree
              className="org-tree"
              treeData={treeData}
              defaultExpandedKeys={treeData.slice(0, 2).map(node => node.key)}
              blockNode
              showLine={{ showLeafIcon: false }}
              selectedKeys={selectedAgent ? [selectedAgent.id] : []}
              onSelect={keys => onSelect(agentById.get(String(keys[0])) || null)}
            />
          ) : view === 'departments' ? (
            <div className="org-departments">
              {departmentGroups.map(([name, members]) => (
                <article key={name} className="org-department-card">
                  <header>
                    <div className="org-department-card__icon"><ApartmentOutlined /></div>
                    <div>
                      <Title level={5}>{normalizeDepartment(name)}</Title>
                      <Text>{members.length} {members.length === 1 ? 'member' : 'members'}</Text>
                    </div>
                  </header>
                  <div className="org-department-card__people">
                    {members.map(member => (
                      <button type="button" key={member.id} onClick={() => onSelect(member)}>
                        <Avatar size={28}>{initials(member.name)}</Avatar>
                        <span>{member.name}<small>{member.designation || normalizeRole(member.role)}</small></span>
                      </button>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          ) : null}
        </section>

        <aside className="organization__detail">{renderDetail()}</aside>
      </div>
    </div>
  );
};

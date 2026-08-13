import React, { useState, useEffect } from 'react';
import { Typography, Row, Col, Card, Tabs, Table, Tag, Button, Space, Input, Select, Switch, Form, Divider, List, Avatar, message, Progress, Checkbox, Badge, Modal, Statistic, Tooltip } from 'antd';
import { SettingOutlined, SearchOutlined, CloudUploadOutlined, RobotOutlined, UserOutlined, DatabaseOutlined, LockOutlined, AlertOutlined, CloudServerOutlined, CreditCardOutlined, HistoryOutlined, KeyOutlined, CheckCircleOutlined, PlusOutlined, CopyOutlined, DeleteOutlined, CloseCircleOutlined, FileTextOutlined, TagOutlined, ShareAltOutlined, TeamOutlined, EditOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { PageContainer } from '../components/ui/PageContainer';
import { Panel } from '../components/ui/Panel';
import { ApiClient } from '../api/client';
import { KnowledgeGraph } from '../components/KnowledgeGraph';
import { CollaborationPanel } from '../components/CollaborationPanel';
import { OrganizationPanel } from '../components/OrganizationPanel';
import { AvailableAgentsPanel } from '../components/AvailableAgentsPanel';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

const WorkInProgressNotice = ({ children }: { children: React.ReactNode }) => (
  <div style={{ marginBottom: 16, padding: '10px 12px', borderRadius: 8, border: '1px solid #FED7AA', background: '#FFF7ED' }}>
    <Text style={{ fontSize: 12, color: '#9A3412' }}>{children}</Text>
  </div>
);

export function Administration() {
  const [activeTab, setActiveTab] = useState('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();
  const [graphRefreshKey, setGraphRefreshKey] = useState(0);
  const [graphNotice, setGraphNotice] = useState<{ provider: string; repoUrl: string; nodeCount: number } | null>(null);

  // Knowledge state
  const [knowledgeItems, setKnowledgeItems] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // RBAC permissions state
  const [roles] = useState(['Super Admin', 'Admin', 'Project Manager', 'Team Lead', 'Employee', 'Viewer']);
  const [modules] = useState(['Projects', 'Documents', 'Knowledge', 'Agents', 'Billing', 'Administration']);
  const [matrix, setMatrix] = useState<Record<string, string[]>>({
    'Super Admin': ['Projects', 'Documents', 'Knowledge', 'Agents', 'Billing', 'Administration'],
    'Admin': ['Projects', 'Documents', 'Knowledge', 'Agents', 'Administration'],
    'Project Manager': ['Projects', 'Documents', 'Knowledge', 'Agents']
  });

  const handleSaveSettings = () => {
    message.success('Administration settings locked and saved successfully.');
  };

  // ── AI Models state ──
  const [aiModels, setAiModels] = useState<any[]>([]);
  const [showModelForm, setShowModelForm] = useState(false);
  const [editingModel, setEditingModel] = useState<any>(null);
  const [modelForm, setModelForm] = useState<Record<string, any>>({});

  const fetchAIModels = async () => {
    try {
      const res = await ApiClient.get('/ai-models');
      setAiModels(res || []);
    } catch { setAiModels([]); }
  };

  useEffect(() => { fetchAIModels(); }, []);

  const handleSaveModel = async () => {
    try {
      if (editingModel) {
        await ApiClient.put(`/ai-models/${editingModel.id}`, modelForm);
        message.success('Model updated');
      } else {
        await ApiClient.post('/ai-models', modelForm);
        message.success('Model added');
      }
      setShowModelForm(false); setEditingModel(null); setModelForm({});
      fetchAIModels();
    } catch (err: any) { message.error(err?.data?.detail || 'Failed to save model'); }
  };

  const handleDeleteModel = (model: any) => {
    Modal.confirm({
      title: 'Delete Model',
      content: `Delete "${model.name}"?`,
      okText: 'Delete', okType: 'danger',
      onOk: async () => {
        await ApiClient.delete(`/ai-models/${model.id}`);
        message.success('Model deleted');
        fetchAIModels();
      },
    });
  };

  const openNewModelForm = () => {
    setEditingModel(null);
    setModelForm({ name: '', provider: 'openai', model_id: '', api_key: '', base_url: '', is_default: false });
    setShowModelForm(true);
  };

  const openEditModelForm = (model: any) => {
    setEditingModel(model);
    setModelForm({
      name: model.name, provider: model.provider, model_id: model.model_id,
      api_key: model.api_key || '', base_url: model.base_url || '',
      is_default: model.is_default === 1 || model.is_default === true,
    });
    setShowModelForm(true);
  };
  const [allAgents, setAllAgents] = useState<any[]>([]);
  const [projectAgents, setProjectAgents] = useState<any[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<any>(null);
  const [showAgentForm, setShowAgentForm] = useState(false);
  const [editingAgent, setEditingAgent] = useState<any>(null);
  const [agentForm, setAgentForm] = useState<Record<string, any>>({});
  const [loadingAgents, setLoadingAgents] = useState(false);

  // Available Agents state
  const [availableAgents, setAvailableAgents] = useState<any[]>([]);
  const [selectedAvailableAgent, setSelectedAvailableAgent] = useState<any>(null);
  const [showHireForm, setShowHireForm] = useState(false);
  const [hireForm, setHireForm] = useState<Record<string, any>>({});
  const [editingAvailableAgent, setEditingAvailableAgent] = useState<any>(null);
  const [loadingAvailable, setLoadingAvailable] = useState(false);

  const fetchAvailableAgents = async () => {
    setLoadingAvailable(true);
    try {
      const token = localStorage.getItem('auth_token');
      const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch('/agents/available', { headers });
      const data = await res.json();
      setAvailableAgents(Array.isArray(data) ? data : []);
    } catch {
      setAvailableAgents([]);
    } finally {
      setLoadingAvailable(false);
    }
  };

  useEffect(() => { fetchAvailableAgents(); }, []);

  const handleHireAgent = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const body = {
        name: hireForm.name, role: hireForm.role || 'mid_dev', department: hireForm.department || 'backend',
        reports_to: hireForm.reports_to || null, designation: hireForm.designation || '',
        role_description: hireForm.role_description || '',
        skills: hireForm.skills ? hireForm.skills.split(',').map((s: string) => s.trim()).filter(Boolean) : [],
        status: 'active',
      };
      const payload = editingAvailableAgent ? body : { id: `agent-${Date.now()}`, ...body };
      const res = await fetch(editingAvailableAgent ? `/agents/${editingAvailableAgent.id}` : '/agents', {
        method: editingAvailableAgent ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed');
      message.success(editingAvailableAgent ? `Agent "${hireForm.name}" updated` : `Agent "${hireForm.name}" hired and added to the reusable workforce`);
      setShowHireForm(false);
      setEditingAvailableAgent(null);
      setHireForm({});
      fetchAvailableAgents();
    } catch (err: any) { message.error(err?.message || 'Failed to hire agent'); }
  };

  const openHireForm = () => {
    setEditingAvailableAgent(null);
    setHireForm({ name: '', role: 'mid_dev', department: 'backend', reports_to: '', designation: '', role_description: '', skills: '' });
    setShowHireForm(true);
  };

  const openEditAvailableAgentForm = (agent: any) => {
    setEditingAvailableAgent(agent);
    setHireForm({
      name: agent.name,
      role: agent.role,
      department: agent.department,
      reports_to: agent.reports_to || '',
      designation: agent.designation || '',
      role_description: agent.role_description || '',
      skills: (agent.skills || []).join(', '),
    });
    setShowHireForm(true);
  };

  const fetchAgents = async () => {
    setLoadingAgents(true);
    try {
      const token = localStorage.getItem('auth_token');
      const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : { 'Content-Type': 'application/json' };

      // Fetch org members from dedicated endpoint
      let orgRes = await fetch('/organization/members', { headers });
      let orgList = await orgRes.json();
      let orgRecords = Array.isArray(orgList) ? orgList : [];

      // Auto-seed if empty
      if (orgRecords.length === 0) {
        try {
          await fetch('/organization/members/seed', { method: 'POST', headers });
          orgRes = await fetch('/organization/members', { headers });
          orgList = await orgRes.json();
          orgRecords = Array.isArray(orgList) ? orgList : [];
        } catch { /* seeding failed silently */ }
      }
      setAllAgents(orgRecords);

      // Fetch project agents separately
      const listRes = await fetch('/agents', { headers });
      const list = await listRes.json();
      const records = Array.isArray(list) ? list : [];
      setProjectAgents(records.filter((agent: any) => Boolean(agent.project_id)));
    } catch {
      setAllAgents([]);
      setProjectAgents([]);
    }
    finally { setLoadingAgents(false); }
  };

  useEffect(() => { fetchAgents(); }, []);

  const roleOptions = ['ceo','cto','cpo','coo','cfo','director_engineering','engineering_manager','tech_lead','senior_dev','mid_dev','junior_dev','quality_engineering_manager','security_lead','product_manager','product_designer','customer_success_head','program_manager','people_operations_head','financial_controller','finance_analyst'];
  const deptOptions = ['leadership','backend','frontend','platform','data','qa','devops','security','engineering','product','design','customer_success','delivery_operations','people_operations','finance'];

  const handleCreateAgent = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const id = `org-${Date.now()}`;
      const body = {
        id, name: agentForm.name, role: agentForm.role, department: agentForm.department,
        reports_to: agentForm.reports_to || null, designation: agentForm.designation || '',
        role_description: agentForm.role_description || '',
        skills: agentForm.skills?.split?.(',')?.map((s: string) => s.trim()).filter(Boolean) || [],
        status: 'active',
      };
      const res = await fetch('/organization/members', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed');
      message.success(`Organization member "${agentForm.name}" created`);
      setShowAgentForm(false);
      setAgentForm({});
      fetchAgents();
    } catch (err: any) { message.error(err?.message || 'Failed to create agent'); }
  };

  const handleUpdateAgent = async () => {
    if (!editingAgent) return;
    try {
      const token = localStorage.getItem('auth_token');
      const body = {
        name: agentForm.name || editingAgent.name,
        role: agentForm.role || editingAgent.role,
        department: agentForm.department || editingAgent.department,
        reports_to: agentForm.reports_to ?? editingAgent.reports_to,
        designation: agentForm.designation ?? editingAgent.designation,
        role_description: agentForm.role_description ?? editingAgent.role_description,
        skills: agentForm.skills ? agentForm.skills.split(',').map((s: string) => s.trim()).filter(Boolean) : undefined,
      };
      const res = await fetch(`/organization/members/${editingAgent.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed');
      message.success(`Organization member "${agentForm.name || editingAgent.name}" updated`);
      setShowAgentForm(false);
      setEditingAgent(null);
      setAgentForm({});
      setSelectedAgent(null);
      fetchAgents();
    } catch (err: any) { message.error(err?.message || 'Failed to update'); }
  };

  const handleDeleteAgent = (agent: any) => {
    Modal.confirm({
      title: 'Delete organization member',
      content: `Delete "${agent.name}"? Direct reports will be reassigned up the company hierarchy.`,
      okText: 'Delete',
      okType: 'danger',
      onOk: async () => {
        try {
          const token = localStorage.getItem('auth_token');
          const res = await fetch(`/organization/members/${agent.id}`, {
            method: 'DELETE',
            headers: token ? { Authorization: `Bearer ${token}` } : {},
          });
          if (!res.ok) throw new Error('Failed');
          message.success(`Organization member "${agent.name}" deleted`);
          setSelectedAgent(null);
          fetchAgents();
        } catch (err: any) { message.error('Failed to delete'); }
      },
    });
  };

  const openCreateForm = () => {
    setEditingAgent(null);
    setAgentForm({ name: '', role: 'junior_dev', department: 'backend', reports_to: '', designation: '', role_description: '', skills: '' });
    setShowAgentForm(true);
  };

  const openEditForm = (agent: any) => {
    setEditingAgent(agent);
    setAgentForm({
      name: agent.name, role: agent.role, department: agent.department,
      reports_to: agent.reports_to || '', designation: agent.designation || '',
      role_description: agent.role_description || '',
      skills: (agent.skills || []).join(', '),
    });
    setShowAgentForm(true);
  };

  // Fetch knowledge data
  useEffect(() => {
    ApiClient.get('/knowledge').then(setKnowledgeItems).catch(() => {});
    ApiClient.get('/knowledge/categories').then(setCategories).catch(() => {});
  }, []);

  const filteredKnowledge = selectedCategory
    ? knowledgeItems.filter((k) => k.tags?.some((t: string) => t.toLowerCase() === selectedCategory.toLowerCase()))
    : knowledgeItems;

  const cardStyle = {
    background: '#FFFFFF',
    border: '1px solid #E2E8F0',
    borderRadius: 12,
    boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
  };

  const handleKnowledgeGraphCreated = (summary: { provider: string; repoUrl: string; nodeCount: number }) => {
    setGraphNotice(summary);
    setGraphRefreshKey((key) => key + 1);
    setActiveTab('knowledge');
  };

  return (
    <PageContainer maxWidth={1800}>

      {/* HEADER SECTION */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <Title level={3} style={{ margin: 0, fontWeight: 700, color: '#0F172A' }}>
            <SettingOutlined style={{ marginRight: 12 }} /> Administration
          </Title>
          <Text type="secondary" style={{ fontSize: 13 }}>
            Manage your entire aegisOS from a single control center.
          </Text>
        </div>
        <Space>
          <Input
            placeholder="Search settings..."
            prefix={<SearchOutlined style={{ color: '#94A3B8' }} />}
            style={{ width: 220 }}
          />
          <Button style={{ background: '#FFFFFF', border: '1px solid #E2E8F0', fontWeight: 500 }}>Import</Button>
          <Button style={{ background: '#FFFFFF', border: '1px solid #E2E8F0', fontWeight: 500 }}>Export</Button>
          <Button type="primary" onClick={handleSaveSettings} style={{ background: '#2563EB', fontWeight: 600 }}>Save Changes</Button>
        </Space>
      </div>

      {/* HORIZONTAL TABS CONTAINER */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        type="card"
        tabBarStyle={{ marginBottom: 24, position: 'sticky', top: 0, zIndex: 10, background: '#F8FAFC' }}
        items={[
          {
            key: 'overview',
            label: 'Overview',
            children: (
              <div>
                <WorkInProgressNotice>
                  This overview is in progress. The KPI cards and recent administrative logs here are sample operating data until they are connected to live usage, cost, and audit aggregates.
                </WorkInProgressNotice>
                <div style={{ opacity: 0.5, pointerEvents: 'none', transition: 'opacity 0.3s' }}>
                <Row gutter={[16, 16]}>
                  {[
                    { title: 'Human Employees', value: '14 Active', icon: <UserOutlined style={{ color: '#2563EB' }} /> },
                    { title: 'Digital Employees', value: '4 Spawned', icon: <RobotOutlined style={{ color: '#7C3AED' }} /> },
                    { title: 'Active Projects', value: '3 Running', icon: <DatabaseOutlined style={{ color: '#16A34A' }} /> },
                    { title: 'Knowledge Files', value: '124 Vectorized', icon: <FileTextOutlined style={{ color: '#EA580C' }} /> },
                    { title: 'Today\'s AI Cost', value: '$24.50', icon: <CreditCardOutlined style={{ color: '#EAB308' }} /> },
                    { title: 'Today\'s Tokens', value: '1.2M', icon: <CloudServerOutlined style={{ color: '#6366F1' }} /> },
                    { title: 'Pending Approvals', value: '2 In Queue', icon: <AlertOutlined style={{ color: '#DC2626' }} /> }
                  ].map((card, idx) => (
                    <Col span={6} key={idx}>
                      <Card style={cardStyle} bodyStyle={{ padding: 20 }}>
                        <Space style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                          <div>
                            <Text type="secondary" style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>{card.title}</Text>
                            <Title level={4} style={{ margin: '8px 0 0 0', fontWeight: 700, color: '#0F172A' }}>{card.value}</Title>
                          </div>
                          <Avatar style={{ background: '#F1F5F9' }} icon={card.icon} />
                        </Space>
                      </Card>
                    </Col>
                  ))}
                </Row>

                <Card style={{ ...cardStyle, marginTop: 24 }} title="Recent OS Administrative Logs" bodyStyle={{ padding: 0 }}>
                  <List
                    dataSource={[
                      'Sarah Jenkins assigned "Schema Analyzer Node" to database modernization stream (10:30 AM)',
                      'DevOps cloud provisioner integration tested successfully for AWS RDS (09:12 AM)',
                      'KMS target policy modified by Super Admin account (Yesterday, 04:00 PM)'
                    ]}
                    renderItem={item => <div style={{ padding: '12px 24px', borderBottom: '1px solid #E2E8F0', fontSize: 12, color: '#334155' }}>• {item}</div>}
                  />
                </Card>
                </div>
              </div>
            )
          },
          {
            key: 'organization',
            label: 'Organization',
            children: (
              <div>
                {/* Agent Form Modal */}
                <Modal
                  title={editingAgent ? `Edit ${editingAgent.name}` : 'Add organization member'}
                  open={showAgentForm}
                  onCancel={() => { setShowAgentForm(false); setEditingAgent(null); setAgentForm({}); }}
                  onOk={editingAgent ? handleUpdateAgent : handleCreateAgent}
                  okText={editingAgent ? 'Update member' : 'Create member'}
                  width={600}
                >
                  <Form layout="vertical">
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item label="Name" required>
                          <Input value={agentForm.name} onChange={(e) => setAgentForm({ ...agentForm, name: e.target.value })} placeholder="e.g. John Doe" />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item label="Designation">
                          <Input value={agentForm.designation || ''} onChange={(e) => setAgentForm({ ...agentForm, designation: e.target.value })} placeholder="e.g. Senior Engineer" />
                        </Form.Item>
                      </Col>
                    </Row>
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item label="Role" required>
                          <Select value={agentForm.role} onChange={(v) => setAgentForm({ ...agentForm, role: v })}>
                            {roleOptions.map((r) => <Option key={r} value={r}>{r.replace(/_/g, ' ')}</Option>)}
                          </Select>
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item label="Department" required>
                          <Select value={agentForm.department} onChange={(v) => setAgentForm({ ...agentForm, department: v })}>
                            {deptOptions.map((d) => <Option key={d} value={d}>{d}</Option>)}
                          </Select>
                        </Form.Item>
                      </Col>
                    </Row>
                    <Form.Item label="Reports To">
                      <Select
                        value={agentForm.reports_to || undefined}
                        onChange={(v) => setAgentForm({ ...agentForm, reports_to: v })}
                        allowClear
                        showSearch
                        optionFilterProp="label"
                        placeholder="Select a manager..."
                      >
                        {allAgents.map((a) => (
                          <Option key={a.id} value={a.id} label={a.name}>
                            {a.name} <Tag style={{ fontSize: 10 }}>{a.role?.replace(/_/g, ' ')}</Tag>
                          </Option>
                        ))}
                      </Select>
                    </Form.Item>
                    <Form.Item label="Role Description">
                      <Input.TextArea value={agentForm.role_description || ''} onChange={(e) => setAgentForm({ ...agentForm, role_description: e.target.value })} rows={3} placeholder="Describes what this agent owns..." />
                    </Form.Item>
                    <Form.Item label="Skills (comma-separated)">
                      <Input value={agentForm.skills || ''} onChange={(e) => setAgentForm({ ...agentForm, skills: e.target.value })} placeholder="Python, FastAPI, Docker" />
                    </Form.Item>
                  </Form>
                </Modal>

                <OrganizationPanel
                  members={allAgents}
                  projectAgents={projectAgents}
                  selectedMember={selectedAgent}
                  loading={loadingAgents}
                  onSelect={setSelectedAgent}
                  onCreate={openCreateForm}
                  onEdit={openEditForm}
                  onDelete={handleDeleteAgent}
                />
              </div>
            )
          },
          {
            key: 'available-agents',
            label: 'Available Agents',
            children: (
              <div>
                <Modal
                  title={editingAvailableAgent ? `Edit ${editingAvailableAgent.name}` : 'Hire Certified Agent'}
                  open={showHireForm}
                  onCancel={() => { setShowHireForm(false); setEditingAvailableAgent(null); setHireForm({}); }}
                  onOk={handleHireAgent}
                  okText={editingAvailableAgent ? 'Update Agent' : 'Hire Agent'}
                  width={600}
                >
                  <Form layout="vertical">
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item label="Name" required>
                          <Input value={hireForm.name} onChange={(e) => setHireForm({ ...hireForm, name: e.target.value })} placeholder="e.g. Data Migration Specialist" />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item label="Designation" required>
                          <Input value={hireForm.designation || ''} onChange={(e) => setHireForm({ ...hireForm, designation: e.target.value })} placeholder="e.g. Senior Data Engineer" />
                        </Form.Item>
                      </Col>
                    </Row>
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item label="Role" required>
                          <Select value={hireForm.role} onChange={(v) => setHireForm({ ...hireForm, role: v })}>
                            {roleOptions.map((r) => <Option key={r} value={r}>{r.replace(/_/g, ' ')}</Option>)}
                          </Select>
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item label="Department" required>
                          <Select value={hireForm.department} onChange={(v) => setHireForm({ ...hireForm, department: v })}>
                            {deptOptions.map((d) => <Option key={d} value={d}>{d}</Option>)}
                          </Select>
                        </Form.Item>
                      </Col>
                    </Row>
                    <Form.Item label="Reports To">
                      <Select
                        value={hireForm.reports_to || undefined}
                        onChange={(v) => setHireForm({ ...hireForm, reports_to: v })}
                        allowClear
                        showSearch
                        optionFilterProp="label"
                        placeholder="Select a manager from agent workforce..."
                      >
                        {availableAgents.map((a) => (
                          <Option key={a.id} value={a.id} label={a.name}>
                            {a.name} <Tag style={{ fontSize: 10 }}>{a.designation || a.role?.replace(/_/g, ' ')}</Tag>
                          </Option>
                        ))}
                      </Select>
                    </Form.Item>
                    <Form.Item label="Role Description">
                      <Input.TextArea value={hireForm.role_description || ''} onChange={(e) => setHireForm({ ...hireForm, role_description: e.target.value })} rows={3} placeholder="What does this agent do?" />
                    </Form.Item>
                    <Form.Item label="Skills (comma-separated)">
                      <Input value={hireForm.skills || ''} onChange={(e) => setHireForm({ ...hireForm, skills: e.target.value })} placeholder="Python, SQL, Docker" />
                    </Form.Item>
                  </Form>
                </Modal>
                <AvailableAgentsPanel
                  agents={availableAgents}
                  selectedAgent={selectedAvailableAgent}
                  loading={loadingAvailable}
                  onSelect={setSelectedAvailableAgent}
                  onCreate={openHireForm}
                  onEdit={openEditAvailableAgentForm}
                  onDelete={(agent) => {
                    Modal.confirm({
                      title: 'Delete agent',
                      content: `Remove "${agent.name}" from the available agent pool?`,
                      okText: 'Delete',
                      okType: 'danger',
                      onOk: async () => {
                        const token = localStorage.getItem('auth_token');
                        await fetch(`/agents/${agent.id}`, { method: 'DELETE', headers: token ? { Authorization: `Bearer ${token}` } : {} });
                        message.success('Agent removed');
                        setSelectedAvailableAgent(null);
                        fetchAvailableAgents();
                      },
                    });
                  }}
                />
              </div>
            )
          },
          {
            key: 'collaboration',
            label: 'Tools',
            children: <CollaborationPanel onKnowledgeGraphCreated={handleKnowledgeGraphCreated} />
          },
          {
            key: 'knowledge',
            label: 'Knowledge',
            children: (
              <div>
                {graphNotice && (
                  <div style={{ marginBottom: 16, padding: '10px 12px', borderRadius: 8, border: '1px solid #BBF7D0', background: '#F0FDF4' }}>
                    <Text style={{ fontSize: 12, color: '#166534' }}>
                      Knowledge graph created from {graphNotice.provider}: <Text code style={{ fontSize: 11 }}>{graphNotice.repoUrl}</Text> ({graphNotice.nodeCount} indexed objects).
                    </Text>
                  </div>
                )}
                {/* Knowledge Graph */}
                <Card
                  title={
                    <Space>
                      <ShareAltOutlined />
                      <span>Knowledge Graph</span>
                    </Space>
                  }
                  style={cardStyle}
                  bodyStyle={{ padding: 0 }}
                >
                  <KnowledgeGraph height={700} refreshKey={graphRefreshKey} />
                </Card>
              </div>
            )
          },
          {
            key: 'ai-models',
            label: 'AI Models',
            children: (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                  <Text strong style={{ fontSize: 15 }}>
                    <RobotOutlined style={{ marginRight: 8 }} />AI Model Configurations
                  </Text>
                  <Button type="primary" icon={<PlusOutlined />} onClick={openNewModelForm} style={{ background: '#2563EB' }}>
                    Add Model
                  </Button>
                </div>

                {/* Model Form Modal */}
                <Modal
                  title={editingModel ? 'Edit Model' : 'Add AI Model'}
                  open={showModelForm}
                  onCancel={() => { setShowModelForm(false); setEditingModel(null); setModelForm({}); }}
                  onOk={handleSaveModel}
                  okText={editingModel ? 'Update' : 'Add'}
                  width={560}
                >
                  <Form layout="vertical">
                    <Form.Item label="Display Name" required>
                      <Input value={modelForm.name} onChange={(e) => setModelForm({ ...modelForm, name: e.target.value })} placeholder="e.g. GPT-4o via CommandCode" />
                    </Form.Item>
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item label="Provider">
                          <Select value={modelForm.provider} onChange={(v) => setModelForm({ ...modelForm, provider: v })}>
                            <Option value="openai">OpenAI Compatible</Option>
                            <Option value="gemini">Google Gemini</Option>
                            <Option value="ollama">Ollama (Local)</Option>
                          </Select>
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item label="Model ID" required>
                          <Input value={modelForm.model_id} onChange={(e) => setModelForm({ ...modelForm, model_id: e.target.value })} placeholder="e.g. gpt-4o" />
                        </Form.Item>
                      </Col>
                    </Row>
                    <Form.Item label="API Key">
                      <Input.Password value={modelForm.api_key} onChange={(e) => setModelForm({ ...modelForm, api_key: e.target.value })} placeholder="sk-..." />
                    </Form.Item>
                    <Form.Item label="Base URL (optional)">
                      <Input value={modelForm.base_url} onChange={(e) => setModelForm({ ...modelForm, base_url: e.target.value })} placeholder="https://api.openai.com/v1" />
                    </Form.Item>
                    <Form.Item>
                      <Checkbox checked={modelForm.is_default} onChange={(e) => setModelForm({ ...modelForm, is_default: e.target.checked })}>
                        Set as default model
                      </Checkbox>
                    </Form.Item>
                  </Form>
                </Modal>

                {/* Models Grid */}
                <Row gutter={[16, 16]}>
                  {aiModels.map((model) => (
                    <Col span={8} key={model.id}>
                      <Card
                        style={{
                          ...cardStyle,
                          border: model.is_default === 1 || model.is_default === true ? '2px solid #2563EB' : cardStyle.border,
                        }}
                        bodyStyle={{ padding: 20 }}
                        title={
                          <Space>
                            <RobotOutlined style={{ color: model.provider === 'ollama' ? '#10b981' : '#2563EB' }} />
                            <Text strong>{model.name}</Text>
                            {(model.is_default === 1 || model.is_default === true) && <Tag color="blue" style={{ marginLeft: 4 }}>Default</Tag>}
                          </Space>
                        }
                        extra={
                          <Space>
                            <Button size="small" icon={<EditOutlined />} onClick={() => openEditModelForm(model)} />
                            <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDeleteModel(model)} />
                          </Space>
                        }
                      >
                        <div style={{ marginBottom: 8 }}>
                          <Text type="secondary" style={{ fontSize: 11 }}>Provider:</Text>
                          <Tag style={{ fontSize: 11, marginLeft: 8 }}>{model.provider}</Tag>
                        </div>
                        <div style={{ marginBottom: 8 }}>
                          <Text type="secondary" style={{ fontSize: 11 }}>Model:</Text>
                          <Text code style={{ fontSize: 11, marginLeft: 8 }}>{model.model_id}</Text>
                        </div>
                        {model.base_url && (
                          <div style={{ marginBottom: 8 }}>
                            <Text type="secondary" style={{ fontSize: 11 }}>Endpoint:</Text>
                            <Text style={{ fontSize: 10, marginLeft: 8, wordBreak: 'break-all' }}>{model.base_url}</Text>
                          </div>
                        )}
                        <div>
                          <Text type="secondary" style={{ fontSize: 11 }}>API Key:</Text>
                          <Text style={{ fontSize: 11, marginLeft: 8 }}>••••{model.api_key?.slice(-4) || 'none'}</Text>
                        </div>
                      </Card>
                    </Col>
                  ))}
                </Row>

                {aiModels.length === 0 && (
                  <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>
                    <RobotOutlined style={{ fontSize: 36, marginBottom: 12, color: '#cbd5e1' }} />
                    <div style={{ fontSize: 13, marginBottom: 4 }}>No AI models configured</div>
                    <div style={{ fontSize: 11 }}>Click "Add Model" to configure an OpenAI-compatible model</div>
                  </div>
                )}
              </div>
            )
          },
          {
            key: 'ai-policies',
            label: 'AI Policies',
            children: (
              <Panel bodyStyle={{ padding: 32 }}>
                <WorkInProgressNotice>
                  AI policy persistence is in progress. These controls currently show the intended policy surface and are not yet backed by live enforcement records.
                </WorkInProgressNotice>
                <Form layout="vertical">
                  <Title level={5} style={{ marginBottom: 16 }}>Budget & Safety Ceiling Limits</Title>
                  <Form.Item label="PII Verification Shield">
                    <Switch defaultChecked /> <Text style={{ marginLeft: 12 }}>Filter compliance tokens against sensitive tax formats</Text>
                  </Form.Item>
                  <Form.Item label="Human intervention validation trigger">
                    <Switch defaultChecked /> <Text style={{ marginLeft: 12 }}>Trigger human verification on target schema mutations</Text>
                  </Form.Item>
                  <Form.Item label="Monthly Token Budget Limits ($)">
                    <Input defaultValue="2500" suffix="USD" />
                  </Form.Item>
                </Form>
              </Panel>
            )
          },
          {
            key: 'permissions',
            label: 'Permissions',
            children: (
              <Panel bodyStyle={{ padding: 24 }}>
                <WorkInProgressNotice>
                  Permission matrix editing is in progress. The matrix is a UI planning surface until role capability changes are persisted through the backend RBAC service.
                </WorkInProgressNotice>
                <Text style={{ display: 'block', marginBottom: 20, fontSize: 13, color: '#475569' }}>Configure standard enterprise permissions across system modules.</Text>
                <Table
                  dataSource={roles.map(role => ({ role, modules: matrix[role] || [] }))}
                  pagination={false}
                  rowKey="role"
                  size="middle"
                  columns={[
                    { title: 'Enterprise Role', dataIndex: 'role', key: 'role', render: r => <Text strong>{r}</Text> },
                    {
                      title: 'Module Capabilities Access Matrix',
                      dataIndex: 'modules',
                      key: 'modules',
                      render: (perms: string[], record: any) => (
                        <Checkbox.Group
                          defaultValue={perms}
                          onChange={vals => setMatrix({ ...matrix, [record.role]: vals as string[] })}
                        >
                          <Space wrap>
                            {modules.map(mod => (
                              <Checkbox key={mod} value={mod} style={{ fontSize: 11 }}>{mod}</Checkbox>
                            ))}
                          </Space>
                        </Checkbox.Group>
                      )
                    }
                  ]}
                />
              </Panel>
            )
          },
          {
            key: 'notifications',
            label: 'Notifications',
            children: (
              <Panel bodyStyle={{ padding: 32 }}>
                <WorkInProgressNotice>
                  Notification routing is in progress. These fields are static until Slack and email delivery settings are stored and verified by the backend.
                </WorkInProgressNotice>
                <Form layout="vertical">
                  <Title level={5} style={{ marginBottom: 16 }}>Notification Routing Configurations</Title>
                  <Form.Item label="Email Digests Uptime">
                    <Switch defaultChecked /> <Text style={{ marginLeft: 12 }}>Trigger daily summary emails to delivery managers</Text>
                  </Form.Item>
                  <Form.Item label="Slack Alerts Integration">
                    <Input placeholder="Enter slack webhook URL..." defaultValue="https://hooks.slack.com/services/vnu-channel" />
                  </Form.Item>
                </Form>
              </Panel>
            )
          },
          {
            key: 'system',
            label: 'System',
            children: (
              <Row gutter={[16, 16]}>
                <Col span={24}>
                  <WorkInProgressNotice>
                    System health cards are in progress. They are static status examples until each service reports live health and uptime metrics.
                  </WorkInProgressNotice>
                </Col>
                {[
                  { component: 'aegisOS Database (SQLite)', health: 100, status: 'Online' },
                  { component: 'Redis Cache Memory', health: 100, status: 'Online' },
                  { component: 'Agent Execution workers pool', health: 98, status: 'Uptime Stable' },
                  { component: 'Debezium CDC streaming webhook', health: 100, status: 'Uptime Stable' }
                ].map((sys, idx) => (
                  <Col span={6} key={idx}>
                    <Card style={cardStyle} bodyStyle={{ padding: 20 }}>
                      <Text strong style={{ fontSize: 12, display: 'block', color: '#0F172A' }}>{sys.component}</Text>
                      <Tag color="green" style={{ margin: '8px 0 16px 0' }}>{sys.status}</Tag>
                      <Progress percent={sys.health} size="small" strokeColor="#2563EB" />
                    </Card>
                  </Col>
                ))}
              </Row>
            )
          },
          {
            key: 'billing',
            label: 'Billing',
            children: (
              <Panel bodyStyle={{ padding: 32 }}>
                <WorkInProgressNotice>
                  Billing metrics are in progress. Current billing period, projected charges, and subscription actions are placeholders until usage metering is connected.
                </WorkInProgressNotice>
                <Title level={5} style={{ marginBottom: 16 }}>Usage Metrics Breakdown</Title>
                <div style={{ display: 'flex', gap: 48, marginBottom: 24 }}>
                  <div>
                    <Text type="secondary" style={{ fontSize: 10 }}>CURRENT BILLING PERIOD</Text>
                    <Title level={3} style={{ margin: '4px 0 0 0', color: '#0F172A', fontWeight: 700 }}>$1,248.50</Title>
                  </div>
                  <div>
                    <Text type="secondary" style={{ fontSize: 10 }}>PROJECTED CHARGES</Text>
                    <Title level={3} style={{ margin: '4px 0 0 0', color: '#0F172A', fontWeight: 700 }}>$1,850.00</Title>
                  </div>
                </div>
                <Progress percent={64} status="active" strokeColor="#2563EB" style={{ maxWidth: 400 }} />
                <Divider style={{ borderColor: '#E2E8F0', margin: '24px 0' }} />
                <Button icon={<CreditCardOutlined />} type="primary" style={{ background: '#2563EB' }}>Manage Subscriptions</Button>
              </Panel>
            )
          },
          {
            key: 'audit-logs',
            label: 'Audit Logs',
            children: (
              <Panel bodyStyle={{ padding: 24 }}>
                <WorkInProgressNotice>
                  Audit log display is in progress. The table below is sample audit history until the live audit log endpoint is connected to this tab.
                </WorkInProgressNotice>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
                  <Input placeholder="Search administrative audit trail..." prefix={<SearchOutlined />} style={{ width: 300 }} />
                  <Button icon={<CloudUploadOutlined />}>Export Audit CSV</Button>
                </div>
                <Table
                  dataSource={[
                    { key: '1', who: 'Sarah Jenkins', action: 'Configured Debezium CDC Connector', date: 'Today, 10:30 AM', project: 'VNU Database Modernization', entity: 'Integrations' },
                    { key: '2', who: 'Super Admin', action: 'Modified model API key configurations', date: 'Yesterday, 04:00 PM', project: 'N/A', entity: 'System Config' }
                  ]}
                  size="middle"
                  pagination={false}
                  columns={[
                    { title: 'User / Actor', dataIndex: 'who', key: 'who', render: w => <Text strong>{w}</Text> },
                    { title: 'Action Details', dataIndex: 'action', key: 'action' },
                    { title: 'Date Timestamp', dataIndex: 'date', key: 'date' },
                    { title: 'Workspace Context', dataIndex: 'project', key: 'project' },
                    { title: 'Entity Class', dataIndex: 'entity', key: 'entity' }
                  ]}
                />
              </Panel>
            )
          },
          {
            key: 'advanced',
            label: 'Advanced',
            children: (
              <Panel bodyStyle={{ padding: 32 }}>
                <WorkInProgressNotice>
                  Advanced settings are in progress. Secret keys, webhook targets, and feature flags shown here are static examples until settings persistence is enabled.
                </WorkInProgressNotice>
                <Form layout="vertical">
                  <Form.Item label="API Secret Keys Access Header">
                    <Input.Password value="sk-proj-aegisOS-os-secret-authentication-token-key" />
                  </Form.Item>
                  <Form.Item label="System Webhook Target Gateways">
                    <Input defaultValue="https://vnu.com/api/webhooks/aegisOS-sync" />
                  </Form.Item>
                  <Form.Item label="Feature Flags Mapping">
                    <Checkbox defaultChecked>Enable DeepSeek R1 local code compile validations</Checkbox>
                  </Form.Item>
                </Form>
              </Panel>
            )
          }
        ]}
      />

    </PageContainer>
  );
}

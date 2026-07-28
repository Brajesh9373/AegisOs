import React, { useState } from 'react';
import { Typography, Button, Space, ConfigProvider, theme, Steps, Spin, Result, Row, Col, Form, Input, Select, Checkbox, InputNumber, Table, List, message, Alert, Divider, Tag } from 'antd';
import { DatabaseOutlined, FileTextOutlined, RobotOutlined, TeamOutlined, ScheduleOutlined, CheckCircleOutlined, ControlOutlined, ArrowLeftOutlined, WarningOutlined, SyncOutlined, LockOutlined, CloudUploadOutlined, PlusOutlined, DeleteOutlined, AlertOutlined, SafetyOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { PageContainer } from '../components/ui/PageContainer';
import { Panel } from '../components/ui/Panel';
import { ActionToolbar } from '../components/ui/ActionToolbar';
import { StatusBadge } from '../components/ui/StatusBadge';
import { LifecycleStepper } from '../components/ui/LifecycleStepper';
import { OpportunitySidebar } from '../components/ui/OpportunitySidebar';
import { ActivityCenter } from '../components/ui/ActivityCenter';
import { useLifecycle } from '../context/LifecycleContext';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TextArea } = Input;

interface HumanEmployee {
  id: string;
  name: string;
  department: string;
  designation: string;
  skills: string;
  email: string;
  phone: string;
  manager: string;
}

interface DigitalEmployee {
  id: string;
  name: string;
  ownerId: string;
  role: string;
  goal: string;
  instructions: string;
  model: string;
  temp: number;
  mcpServer: string;
  guardrails: string;
}

export function ProjectInitialization() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [current, setCurrent] = useState(0);
  const [loading, setLoading] = useState(false);
  const { createProjectFromInitialization } = useLifecycle();

  // Step 1 State: Scrum Board
  const [boardConfig, setBoardConfig] = useState({
    type: 'Scrum',
    duration: 2,
    dailyStandup: '09:30 AM',
    weeklySync: 'Monday 10:00 AM'
  });

  // Step 2 & 3 State: Documents & Knowledge Base
  const [kbDocs, setKbDocs] = useState<string[]>([
    'Original_Requirements.pdf',
    'Scope_Draft.docx',
    'Final_Proposal.pdf'
  ]);

  // Step 4 State: Integrations
  const [integrations, setIntegrations] = useState([
    { id: '1', name: 'Jira', status: 'Not Configured', loading: false },
    { id: '2', name: 'GitHub', status: 'Connected', loading: false },
    { id: '3', name: 'Slack', status: 'Connected', loading: false },
    { id: '4', name: 'Confluence', status: 'Not Configured', loading: false }
  ]);

  // Step 5 State: Org Employees and filters
  const [orgEmployees] = useState<HumanEmployee[]>([
    { id: 'emp-1', name: 'Sarah Jenkins', department: 'Data Engineering', designation: 'Lead Migration Architect', skills: 'Oracle, PL/SQL, Aurora PG', email: 'sarah.j@vnu.com', phone: '+1 555-0199', manager: 'Current User' },
    { id: 'emp-2', name: 'David Miller', department: 'DevOps', designation: 'Senior Cloud Engineer', skills: 'AWS, Terraform, Kubernetes', email: 'david.m@vnu.com', phone: '+1 555-0188', manager: 'Sarah Jenkins' },
    { id: 'emp-3', name: 'Jane Doe', department: 'QA', designation: 'Integration Tester', skills: 'Selenium, Postman, Jmeter', email: 'jane.d@vnu.com', phone: '+1 555-0177', manager: 'Sarah Jenkins' },
    { id: 'emp-4', name: 'Robert Chen', department: 'Engineering', designation: 'Database Administrator', skills: 'PostgreSQL, Performance Tuning', email: 'robert.c@vnu.com', phone: '+1 555-0166', manager: 'Sarah Jenkins' }
  ]);
  const [employees, setEmployees] = useState<HumanEmployee[]>([
    { id: 'emp-1', name: 'Sarah Jenkins', department: 'Data Engineering', designation: 'Lead Migration Architect', skills: 'Oracle, PL/SQL, Aurora PG', email: 'sarah.j@vnu.com', phone: '+1 555-0199', manager: 'Current User' }
  ]);
  const [empSearch, setEmpSearch] = useState('');
  const [empDeptFilter, setEmpDeptFilter] = useState('All');
  const [empSkillFilter, setEmpSkillFilter] = useState('All');

  // Step 6 & 7 State: Digital Employees
  const [digitals, setDigitals] = useState<DigitalEmployee[]>([
    {
      id: 'dig-1',
      name: 'Schema Analyzer Node',
      ownerId: 'emp-1',
      role: 'DDL Parsing & Constraint Translation',
      goal: 'Identify complex data mappings and recommend target types.',
      instructions: 'Analyze Oracle schema structures and convert tables to PostGIS or native PG datatypes.',
      model: 'GPT-4o Reasoning',
      temp: 0.1,
      mcpServer: 'Database Connector',
      guardrails: 'Strict HIPAA data masking rules enforced.'
    }
  ]);
  const [newDig, setNewDig] = useState<Partial<DigitalEmployee>>({
    ownerId: 'emp-1',
    model: 'GPT-4o Reasoning',
    temp: 0.1
  });

  // Step 8 State: AI Policies
  const [policies, setPolicies] = useState({
    allowedModels: ['GPT-4o Reasoning', 'Claude 3.5 Sonnet'],
    piiRules: true,
    humanApprovalRequired: true,
    maxTokenLimit: 500000
  });

  // Step 9 State: Permissions Matrix
  const [rbac, setRbac] = useState<any>({
    Admin: ['View', 'Create', 'Edit', 'Delete', 'Approve', 'Deploy', 'Manage Agents'],
    Architect: ['View', 'Create', 'Edit', 'Approve', 'Manage Agents'],
    Developer: ['View', 'Create', 'Edit'],
    'AI Employee': ['View', 'Create', 'Edit']
  });

  // Step 10 State: Notifications
  const [notifs, setNotifs] = useState({
    email: true,
    slack: true,
    webhook: false
  });

  // Step 11 State: Validation results
  const [validationRun, setValidationRun] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  const handleTestIntegration = (id: string) => {
    setIntegrations(prev => prev.map(item => item.id === id ? { ...item, loading: true } : item));
    setTimeout(() => {
      setIntegrations(prev => prev.map(item => item.id === id ? { ...item, status: 'Connected', loading: false } : item));
      message.success('Integration connection verified successfully!');
    }, 1200);
  };



  const handleAddDigitalEmployee = () => {
    if (!newDig.name || !newDig.role) {
      message.error('Digital Employee name and role are mandatory.');
      return;
    }
    const created: DigitalEmployee = {
      id: `dig-${Date.now()}`,
      name: newDig.name,
      ownerId: newDig.ownerId || 'emp-1',
      role: newDig.role,
      goal: newDig.goal || 'Modernization task automation',
      instructions: newDig.instructions || 'Follow project rules.',
      model: newDig.model || 'GPT-4o Reasoning',
      temp: newDig.temp ?? 0.1,
      mcpServer: newDig.mcpServer || 'None',
      guardrails: newDig.guardrails || 'Standard PII masking'
    };
    setDigitals(prev => [...prev, created]);
    setNewDig({ ownerId: 'emp-1', model: 'GPT-4o Reasoning', temp: 0.1 });
    message.success('Mapped digital employee initialized and bound to owner.');
  };

  const runSystemValidation = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setValidationRun(true);
      const errors: string[] = [];
      if (kbDocs.length === 0) errors.push('No target documents uploaded in knowledge assets.');
      if (employees.length === 0) errors.push('Human employee directory cannot be empty.');
      if (digitals.length === 0) errors.push('At least one mapped digital employee is required to launch execution workspace.');
      if (integrations.filter(i => i.status === 'Connected').length === 0) errors.push('No third-party integrations configured.');

      setValidationErrors(errors);
      if (errors.length === 0) {
        message.success('System configuration validation passed! Workspace ready to deploy.');
      } else {
        message.warning('Mandatory items are missing. Resolve compilation alerts to proceed.');
      }
    }, 1500);
  };

  const steps = [
    { title: 'Create Scrum Board', icon: <ScheduleOutlined />, desc: 'Configure sprint settings and target project columns.' },
    { title: 'Knowledge Base', icon: <DatabaseOutlined />, desc: 'Provision semantic directory permissions and formats.' },
    { title: 'Import Documents', icon: <FileTextOutlined />, desc: 'Ingest legacy PDFs, RFQs, and SOW specifications.' },
    { title: 'Configure Integrations', icon: <SyncOutlined />, desc: 'Authenticate Jira, GitHub, Slack, and DB connectors.' },
    { title: 'Human Employee Directory', icon: <TeamOutlined />, desc: 'Register human supervisors and assign ownership keys.' },
    { title: 'Digital Employees', icon: <RobotOutlined />, desc: 'Map digital worker nodes to human supervisor records.' },
    { title: 'Agent Configuration', icon: <ControlOutlined />, desc: 'Apply target models, temperature settings, and MCP tools.' },
    { title: 'AI Policies', icon: <SafetyOutlined />, desc: 'Enforce allowed models, token limits, and PII guardrails.' },
    { title: 'Permissions', icon: <LockOutlined />, desc: 'Configure role-based access control (RBAC) permission matrices.' },
    { title: 'Notifications', icon: <ScheduleOutlined />, desc: 'Establish webhook alerts for human-in-the-loop triggers.' },
    { title: 'System Validation', icon: <AlertOutlined />, desc: 'Verify required files, tokens, and agent allocations.' },
    { title: 'Launch Workspace', icon: <CheckCircleOutlined />, desc: 'Deploy VNU Modernization environment.' }
  ];

  return (
    <PageContainer maxWidth={1800}>
      <LifecycleStepper currentStage="Initialization" />

      <ActionToolbar>
        <Space direction="vertical" size="small">
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate(`/opportunities/${id || 'demo'}/approve`)} style={{ padding: 0 }}>Back to Approval</Button>
          <Space>
            <Title level={3} style={{ margin: 0, fontWeight: 600 }}>Project Initialization Wizard</Title>
            <Tag color="blue">VNU Database Modernization</Tag>
          </Space>
        </Space>
      </ActionToolbar>

      <div style={{ background: '#FFFFFF', border: '1px solid #E5E7EB', padding: '12px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, borderRadius: 8 }}>
        <Space direction="vertical" size={2}>
          <Text strong style={{ fontSize: 15, color: '#111827' }}>VNU Database Modernization</Text>
          <Space size="large" style={{ fontSize: 11, color: '#6B7280' }}>
            <span>Customer: <b>VNU</b></span>
            <span>|</span>
            <span>Current Stage: <Tag color="blue" style={{ margin: 0, fontSize: 10 }}>Initialization</Tag></span>
            <span>|</span>
            <span>Status: <Tag color="success" style={{ margin: 0, fontSize: 10 }}>Active</Tag></span>
            <span>|</span>
            <span>Last Updated: <b>Today 10:30 AM</b></span>
          </Space>
        </Space>
      </div>

      <Row gutter={24}>
        <Col span={7}>
          <Panel bodyStyle={{ padding: 24, background: '#FFFFFF' }}>
            <Steps
              current={current}
              onChange={setCurrent}
              direction="vertical"
              items={steps.map((s, i) => ({
                title: <span style={{ fontSize: 13, fontWeight: current === i ? 600 : 500, color: current >= i ? '#111827' : '#9CA3AF' }}>{s.title}</span>,
                description: <span style={{ fontSize: 11, color: '#6B7280' }}>{s.desc}</span>,
                icon: current === i && loading ? <Spin size="small" /> : (current > i ? <CheckCircleOutlined style={{ color: '#22C55E' }} /> : <span style={{ color: current === i ? '#2563EB' : '#9CA3AF' }}>{s.icon}</span>)
              }))}
            />
          </Panel>
        </Col>

        <Col span={17}>
          <Panel bodyStyle={{ padding: 32, background: '#FFFFFF', border: '1px solid #E5E7EB', borderRadius: 8 }}>

            {/* 1. Create Scrum Board */}
            {current === 0 && (
              <div>
                <Title level={4} style={{ marginBottom: 16 }}>Create Scrum Board</Title>
                <Paragraph style={{ color: '#6B7280', fontSize: 12 }}>Configure execution sprints and daily sync checkpoints.</Paragraph>
                <Form layout="vertical">
                  <Form.Item label="Board Execution Framework">
                    <Select value={boardConfig.type} onChange={val => setBoardConfig({ ...boardConfig, type: val })}>
                      <Option value="Scrum">Scrum (Recommended)</Option>
                      <Option value="Kanban">Kanban</Option>
                      <Option value="Hybrid">Hybrid Delivery Mode</Option>
                    </Select>
                  </Form.Item>
                  <Form.Item label="Sprint Duration">
                    <Select value={boardConfig.duration} onChange={val => setBoardConfig({ ...boardConfig, duration: val })}>
                      <Option value={1}>1 Week Sprints</Option>
                      <Option value={2}>2 Weeks Sprints</Option>
                      <Option value={3}>3 Weeks Sprints</Option>
                    </Select>
                  </Form.Item>
                  <Form.Item label="Daily Standup Time">
                    <Input value={boardConfig.dailyStandup} onChange={e => setBoardConfig({ ...boardConfig, dailyStandup: e.target.value })} />
                  </Form.Item>
                  <Form.Item label="Default Milestones">
                    <Checkbox.Group defaultValue={['blueprint', 'staging', 'live']} style={{ width: '100%' }}>
                      <Row>
                        <Col span={12}><Checkbox value="blueprint">Blueprint Approval</Checkbox></Col>
                        <Col span={12}><Checkbox value="staging">Staging Validation</Checkbox></Col>
                        <Col span={12}><Checkbox value="live">Go-Live Cutover</Checkbox></Col>
                      </Row>
                    </Checkbox.Group>
                  </Form.Item>
                  <Button type="primary" onClick={() => { message.success('Scrum board successfully created.'); setCurrent(1); }} style={{ background: '#2563EB', width: '100%', marginTop: 12 }}>
                    Save & Initialize Board
                  </Button>
                </Form>
              </div>
            )}

            {/* 2. Knowledge Base */}
            {current === 1 && (
              <div>
                <Title level={4} style={{ marginBottom: 16 }}>Knowledge Base Setup</Title>
                <Paragraph style={{ color: '#6B7280', fontSize: 12 }}>Establish target vector databases and sync rules.</Paragraph>
                <Form layout="vertical">
                  <Form.Item label="KB Storage Classification">
                    <Select defaultValue="Confidential">
                      <Option value="Internal">Internal Org Use</Option>
                      <Option value="Confidential">Confidential VNU Modernization Only</Option>
                      <Option value="Public">Shared Partner Access</Option>
                    </Select>
                  </Form.Item>
                  <Form.Item label="Auto-Versioning">
                    <Checkbox defaultChecked>Log full history of vector updates</Checkbox>
                  </Form.Item>
                  <Form.Item label="Target Semantic Dimensions">
                    <Select defaultValue="1536">
                      <Option value="1536">1536 dimensions (OpenAI text-embedding-3-small)</Option>
                      <Option value="3072">3072 dimensions (OpenAI text-embedding-3-large)</Option>
                    </Select>
                  </Form.Item>
                  <Button type="primary" onClick={() => { message.success('Semantic Knowledge Base directory established.'); setCurrent(2); }} style={{ background: '#2563EB', width: '100%', marginTop: 12 }}>
                    Apply Directory Settings
                  </Button>
                </Form>
              </div>
            )}

            {/* 3. Import Documents */}
            {current === 2 && (
              <div>
                <Title level={4} style={{ marginBottom: 16 }}>Import Procurement & Design Documents</Title>
                <Paragraph style={{ color: '#6B7280', fontSize: 12 }}>Vectorize project documentation to prime digital employee memory nodes.</Paragraph>
                <div style={{ background: '#F8FAFC', border: '1px dashed #D1D5DB', padding: 24, textAlign: 'center', borderRadius: 8, marginBottom: 20 }}>
                  <CloudUploadOutlined style={{ fontSize: 32, color: '#2563EB', marginBottom: 8 }} />
                  <Text style={{ display: 'block', fontWeight: 600 }}>Click or Drag and Drop files to upload</Text>
                  <Text type="secondary" style={{ fontSize: 11 }}>Signed SOW, Architecture designs, RFQ sheets (up to 20MB)</Text>
                </div>
                <List
                  size="small"
                  bordered
                  dataSource={kbDocs}
                  renderItem={doc => (
                    <List.Item actions={[<Button size="small" type="text" icon={<DeleteOutlined />} danger onClick={() => setKbDocs(prev => prev.filter(d => d !== doc))} />]}>
                      <Space><FileTextOutlined style={{ color: '#2563EB' }} /> <Text style={{ fontSize: 12 }}>{doc}</Text></Space>
                    </List.Item>
                  )}
                />
                <Button type="primary" onClick={() => { message.success('Procurement documentation successfully vectorized.'); setCurrent(3); }} style={{ background: '#2563EB', width: '100%', marginTop: 24 }}>
                  Vectorize & Continue
                </Button>
              </div>
            )}

            {/* 4. Configure Integrations */}
            {current === 3 && (
              <div>
                <Title level={4} style={{ marginBottom: 16 }}>Enterprise Third-Party Integrations</Title>
                <Table
                  dataSource={integrations}
                  pagination={false}
                  rowKey="id"
                  size="small"
                  columns={[
                    { title: 'Tool Integration', dataIndex: 'name', key: 'name', render: t => <Text strong style={{ fontSize: 12 }}>{t}</Text> },
                    { title: 'Status', dataIndex: 'status', key: 'status', render: s => <Tag color={s === 'Connected' ? 'green' : 'default'}>{s}</Tag> },
                    {
                      title: 'Actions',
                      key: 'actions',
                      render: (_, r) => (
                        <Button
                          size="small"
                          type="primary"
                          ghost
                          loading={r.loading}
                          onClick={() => handleTestIntegration(r.id)}
                          style={{ fontSize: 11 }}
                        >
                          Test Connection
                        </Button>
                      )
                    }
                  ]}
                />
                <Button type="primary" onClick={() => { message.success('Integrations mapped.'); setCurrent(4); }} style={{ background: '#2563EB', width: '100%', marginTop: 24 }}>
                  Proceed to Employee Allocation
                </Button>
              </div>
            )}

            {/* 5. Human Employee Directory */}
            {current === 4 && (
              <div>
                <Title level={4} style={{ marginBottom: 16 }}>Human Employee Directory Allocation</Title>
                <Paragraph style={{ color: '#6B7280', fontSize: 12 }}>Register the delivery engineers, architects, and managers responsible for supervisor sign-offs.</Paragraph>

                <div style={{ background: '#F9FAFB', padding: 16, borderRadius: 8, border: '1px solid #E5E7EB', marginBottom: 20 }}>
                  <Form layout="vertical">
                    <Row gutter={12}>
                      <Col span={12}>
                        <Form.Item label="Search Employees">
                          <Input placeholder="Search name or skill..." value={empSearch} onChange={e => setEmpSearch(e.target.value)} />
                        </Form.Item>
                      </Col>
                      <Col span={6}>
                        <Form.Item label="Department">
                          <Select value={empDeptFilter} onChange={setEmpDeptFilter}>
                            <Option value="All">All Departments</Option>
                            <Option value="Data Engineering">Data Engineering</Option>
                            <Option value="DevOps">DevOps</Option>
                            <Option value="QA">QA</Option>
                            <Option value="Engineering">Engineering</Option>
                          </Select>
                        </Form.Item>
                      </Col>
                      <Col span={6}>
                        <Form.Item label="Skills Filter">
                          <Select value={empSkillFilter} onChange={setEmpSkillFilter}>
                            <Option value="All">All Skills</Option>
                            <Option value="Oracle">Oracle</Option>
                            <Option value="AWS">AWS</Option>
                            <Option value="PostgreSQL">PostgreSQL</Option>
                            <Option value="QA">QA / Testing</Option>
                          </Select>
                        </Form.Item>
                      </Col>
                    </Row>
                  </Form>

                  <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>Available Organization Employees:</Text>
                  <List
                    size="small"
                    bordered
                    dataSource={orgEmployees.filter(emp => {
                      const matchesSearch = emp.name.toLowerCase().includes(empSearch.toLowerCase()) ||
                                            emp.skills.toLowerCase().includes(empSearch.toLowerCase()) ||
                                            emp.designation.toLowerCase().includes(empSearch.toLowerCase());
                      const matchesDept = empDeptFilter === 'All' || emp.department === empDeptFilter;
                      const matchesSkill = empSkillFilter === 'All' || emp.skills.includes(empSkillFilter);
                      return matchesSearch && matchesDept && matchesSkill;
                    })}
                    renderItem={emp => {
                      const isAssigned = employees.some(e => e.id === emp.id);
                      return (
                        <List.Item actions={[
                          isAssigned ? (
                            <Tag color="green">Assigned</Tag>
                          ) : (
                            <Button size="small" type="primary" ghost onClick={() => {
                              setEmployees(prev => [...prev, emp]);
                              message.success(`${emp.name} assigned to project.`);
                            }}>Assign</Button>
                          )
                        ]}>
                          <Space direction="vertical" size={2}>
                            <Text strong style={{ fontSize: 12 }}>{emp.name} ({emp.designation})</Text>
                            <Text type="secondary" style={{ fontSize: 11 }}>Skills: {emp.skills} • Dept: {emp.department}</Text>
                          </Space>
                        </List.Item>
                      );
                    }}
                  />
                </div>

                <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 8 }}>Assigned Project Employees:</Text>
                <List
                  size="small"
                  bordered
                  dataSource={employees}
                  renderItem={emp => (
                    <List.Item actions={[
                      <Button size="small" type="text" danger onClick={() => {
                        setEmployees(prev => prev.filter(e => e.id !== emp.id));
                        message.warning(`${emp.name} removed from assignment.`);
                      }}>Remove</Button>
                    ]}>
                      <Space direction="vertical" size={2}>
                        <Text strong style={{ fontSize: 12 }}>{emp.name} ({emp.designation})</Text>
                        <Text type="secondary" style={{ fontSize: 11 }}>{emp.email} • Dept: {emp.department}</Text>
                      </Space>
                    </List.Item>
                  )}
                />
                <Button type="primary" onClick={() => setCurrent(5)} style={{ background: '#2563EB', width: '100%', marginTop: 24 }}>
                  Map Digital Workers
                </Button>
              </div>
            )}

            {/* 6. Digital Employees */}
            {current === 5 && (
              <div>
                <Title level={4} style={{ marginBottom: 16 }}>Map Digital Workers to Human Supervisors</Title>
                <Paragraph style={{ color: '#6B7280', fontSize: 12 }}>Initialize digital employees. Every worker node must belong to exactly one human owner to ensure governance policies.</Paragraph>

                <div style={{ background: '#F9FAFB', padding: 16, borderRadius: 8, border: '1px solid #E5E7EB', marginBottom: 20 }}>
                  <Form layout="vertical">
                    <Form.Item label="Select Human Owner (Supervisor)" required>
                      <Select value={newDig.ownerId} onChange={val => setNewDig({ ...newDig, ownerId: val })}>
                        {employees.map(emp => (
                          <Option key={emp.id} value={emp.id}>{emp.name} ({emp.designation})</Option>
                        ))}
                      </Select>
                    </Form.Item>
                    <Form.Item label="Digital Agent Name" required>
                      <Input placeholder="e.g. Code Translation Agent" value={newDig.name} onChange={e => setNewDig({ ...newDig, name: e.target.value })} />
                    </Form.Item>
                    <Form.Item label="Target Operational Role" required>
                      <Input placeholder="e.g. PL/SQL to pgSQL translation" value={newDig.role} onChange={e => setNewDig({ ...newDig, role: e.target.value })} />
                    </Form.Item>
                    <Button type="primary" icon={<PlusOutlined />} onClick={handleAddDigitalEmployee} style={{ background: '#2563EB', width: '100%' }}>
                      Bind & Provision Digital Employee
                    </Button>
                  </Form>
                </div>

                <List
                  size="small"
                  bordered
                  dataSource={digitals}
                  renderItem={dig => {
                    const owner = employees.find(e => e.id === dig.ownerId);
                    return (
                      <List.Item>
                        <Space direction="vertical" size={2}>
                          <Text strong style={{ fontSize: 12 }}><RobotOutlined /> {dig.name}</Text>
                          <Text type="secondary" style={{ fontSize: 11 }}>Role: {dig.role} • Owner: <b>{owner ? owner.name : 'Unknown'}</b></Text>
                        </Space>
                      </List.Item>
                    );
                  }}
                />
                <Button type="primary" onClick={() => setCurrent(6)} style={{ background: '#2563EB', width: '100%', marginTop: 24 }}>
                  Configure Agent Parameters
                </Button>
              </div>
            )}

            {/* 7. Agent Configuration */}
            {current === 6 && (
              <div>
                <Title level={4} style={{ marginBottom: 16 }}>Autonomous Agent Studio</Title>
                <Paragraph style={{ color: '#6B7280', fontSize: 12 }}>Configure hyper-parameters, LLM settings, and tools for active digital workers.</Paragraph>
                <Form layout="vertical">
                  {digitals.map((dig, idx) => (
                    <div key={dig.id} style={{ borderBottom: '1px solid #E5E7EB', paddingBottom: 16, marginBottom: 16 }}>
                      <Text strong style={{ color: '#2563EB', display: 'block', marginBottom: 12 }}>🤖 Parameters: {dig.name}</Text>
                      <Form.Item label="Target AI Model">
                        <Select value={dig.model} onChange={val => setDigitals(prev => prev.map((d, i) => i === idx ? { ...d, model: val } : d))}>
                          <Option value="GPT-4o Reasoning">GPT-4o (Reasoning)</Option>
                          <Option value="Claude 3.5 Sonnet">Claude 3.5 Sonnet</Option>
                          <Option value="Gemini 1.5 Pro">Gemini 1.5 Pro</Option>
                        </Select>
                      </Form.Item>
                      <Form.Item label="Temperature (Creativity & Precision Limits)">
                        <InputNumber min={0} max={1} step={0.1} value={dig.temp} onChange={val => setDigitals(prev => prev.map((d, i) => i === idx ? { ...d, temp: val || 0.1 } : d))} />
                      </Form.Item>
                      <Form.Item label="MCP Servers & Tools">
                        <Select defaultValue="db_conn">
                          <Option value="db_conn">Database Direct Connector (MCP)</Option>
                          <Option value="schema_verify">Schema Parity Verifier (MCP)</Option>
                        </Select>
                      </Form.Item>
                      <Form.Item label="Agent Goal / Mandate">
                        <TextArea rows={2} value={dig.goal} onChange={e => setDigitals(prev => prev.map((d, i) => i === idx ? { ...d, goal: e.target.value } : d))} />
                      </Form.Item>
                    </div>
                  ))}
                  <Button type="primary" onClick={() => { message.success('Agent parameters updated.'); setCurrent(7); }} style={{ background: '#2563EB', width: '100%' }}>
                    Save Studio Settings
                  </Button>
                </Form>
              </div>
            )}

            {/* 8. AI Policies */}
            {current === 7 && (
              <div>
                <Title level={4} style={{ marginBottom: 16 }}>Configure AI Safety & Compliance Policies</Title>
                <Paragraph style={{ color: '#6B7280', fontSize: 12 }}>Apply strict prompt governance rules, model filters, and token ceilings.</Paragraph>
                <Form layout="vertical">
                  <Form.Item label="Allowed Models In Project Scope">
                    <Checkbox.Group defaultValue={policies.allowedModels} onChange={vals => setPolicies({ ...policies, allowedModels: vals as string[] })}>
                      <Space direction="vertical">
                        <Checkbox value="GPT-4o Reasoning">GPT-4o (Reasoning)</Checkbox>
                        <Checkbox value="Claude 3.5 Sonnet">Claude 3.5 Sonnet</Checkbox>
                        <Checkbox value="Local DeepSeek R1">Local DeepSeek R1 (Air-Gapped)</Checkbox>
                      </Space>
                    </Checkbox.Group>
                  </Form.Item>
                  <Form.Item label="Sensitive Data Rules">
                    <Checkbox checked={policies.piiRules} onChange={e => setPolicies({ ...policies, piiRules: e.target.checked })}>
                      Enforce automatic regex hashing filter on HIPAA/PCI-DSS fields
                    </Checkbox>
                  </Form.Item>
                  <Form.Item label="Human Supervisor Sign-Off">
                    <Checkbox checked={policies.humanApprovalRequired} onChange={e => setPolicies({ ...policies, humanApprovalRequired: e.target.checked })}>
                      Require explicit human approval for schema mutation tasks
                    </Checkbox>
                  </Form.Item>
                  <Form.Item label="Maximum Token Ceiling (Budget Guardrail)">
                    <InputNumber value={policies.maxTokenLimit} onChange={val => setPolicies({ ...policies, maxTokenLimit: val || 500000 })} style={{ width: '100%' }} />
                  </Form.Item>
                  <Button type="primary" onClick={() => { message.success('AI execution policies registered.'); setCurrent(8); }} style={{ background: '#2563EB', width: '100%', marginTop: 12 }}>
                    Lock Policy Controls
                  </Button>
                </Form>
              </div>
            )}

            {/* 9. Permissions Matrix (RBAC) */}
            {current === 8 && (
              <div>
                <Title level={4} style={{ marginBottom: 16 }}>Role Based Access Control (RBAC) Matrix</Title>
                <Paragraph style={{ color: '#6B7280', fontSize: 12 }}>Configure capabilities across standard project roles.</Paragraph>
                <Table
                  dataSource={Object.keys(rbac).map(role => ({ role, permissions: rbac[role] }))}
                  pagination={false}
                  rowKey="role"
                  size="small"
                  columns={[
                    { title: 'Project Role', dataIndex: 'role', key: 'role', render: r => <Text strong>{r}</Text> },
                    {
                      title: 'Capabilities Matrix',
                      dataIndex: 'permissions',
                      key: 'permissions',
                      render: (perms: string[], record: any) => (
                        <Checkbox.Group
                          defaultValue={perms}
                          onChange={vals => setRbac({ ...rbac, [record.role]: vals })}
                          style={{ width: '100%' }}
                        >
                          <Space wrap>
                            {['View', 'Create', 'Edit', 'Delete', 'Approve', 'Deploy', 'Manage Agents'].map(p => (
                              <Checkbox key={p} value={p} style={{ fontSize: 10 }}>{p}</Checkbox>
                            ))}
                          </Space>
                        </Checkbox.Group>
                      )
                    }
                  ]}
                />
                <Button type="primary" onClick={() => { message.success('Role-based capabilities finalized.'); setCurrent(9); }} style={{ background: '#2563EB', width: '100%', marginTop: 24 }}>
                  Save Permission Matrix
                </Button>
              </div>
            )}

            {/* 10. Notifications */}
            {current === 9 && (
              <div>
                <Title level={4} style={{ marginBottom: 16 }}>Configure Alert Notification Channels</Title>
                <Paragraph style={{ color: '#6B7280', fontSize: 12 }}>Select which channels receive human-intervention triggers and critical event alerts.</Paragraph>
                <Form layout="vertical">
                  <Form.Item label="Notification Channels">
                    <Space direction="vertical">
                      <Checkbox checked={notifs.email} onChange={e => setNotifs({ ...notifs, email: e.target.checked })}>
                        Corporate Email Digest (sarah.j@vnu.com)
                      </Checkbox>
                      <Checkbox checked={notifs.slack} onChange={e => setNotifs({ ...notifs, slack: e.target.checked })}>
                        Slack Integration alerts (#vnu-migration-alerts)
                      </Checkbox>
                      <Checkbox checked={notifs.webhook} onChange={e => setNotifs({ ...notifs, webhook: e.target.checked })}>
                        Post execution notifications via custom HTTP Webhook
                      </Checkbox>
                    </Space>
                  </Form.Item>
                  <Button type="primary" onClick={() => { message.success('Notification channels configured.'); setCurrent(10); }} style={{ background: '#2563EB', width: '100%', marginTop: 12 }}>
                    Save Notification Rules
                  </Button>
                </Form>
              </div>
            )}

            {/* 11. System Validation */}
            {current === 10 && (
              <div>
                <Title level={4} style={{ marginBottom: 16 }}>System Integrity & Validation Check</Title>
                <Paragraph style={{ color: '#6B7280', fontSize: 12 }}>Before launching the project execution workspace, the aegisOS orchestrator runs static checks on required components.</Paragraph>

                {validationRun ? (
                  <div>
                    {validationErrors.length === 0 ? (
                      <Alert
                        message="Configuration Verified"
                        description="All mandatory components (SOW assets, human employee logs, mapped digital nodes, and integrations) are fully configured."
                        type="success"
                        showIcon
                        style={{ marginBottom: 24 }}
                      />
                    ) : (
                      <Alert
                        message="Validation Errors Found"
                        description={
                          <List
                            size="small"
                            dataSource={validationErrors}
                            renderItem={err => <Text type="danger" style={{ fontSize: 11, display: 'block' }}>• {err}</Text>}
                          />
                        }
                        type="error"
                        showIcon
                        style={{ marginBottom: 24 }}
                      />
                    )}
                  </div>
                ) : (
                  <Alert
                    message="Validation Required"
                    description="Run the orchestrator checks to verify the project deployment footprint."
                    type="info"
                    showIcon
                    style={{ marginBottom: 24 }}
                  />
                )}

                <Row gutter={12}>
                  <Col span={12}>
                    <Button onClick={runSystemValidation} loading={loading} style={{ width: '100%' }}>
                      Run Integrity Check
                    </Button>
                  </Col>
                  <Col span={12}>
                    <Button
                      type="primary"
                      onClick={() => setCurrent(11)}
                      disabled={!validationRun || validationErrors.length > 0}
                      style={{ background: '#2563EB', width: '100%' }}
                    >
                      Deploy Workspace
                    </Button>
                  </Col>
                </Row>
              </div>
            )}

            {/* 12. Launch Workspace */}
            {current === 11 && (
              <Result
                icon={<CheckCircleOutlined style={{ color: '#22C55E' }} />}
                title={<span style={{ color: '#111827', fontWeight: 600 }}>Project Modernization Workspace Ready!</span>}
                subTitle={<span style={{ color: '#6B7280', fontSize: 13 }}>All directories, policies, digital workers, and human roles have been compiled.</span>}
                extra={[
                  <Button key="registry" onClick={() => navigate('/projects')} style={{ background: 'transparent', fontWeight: 500 }}>
                    Go to Project Registry
                  </Button>,
                  <Button
                    key="workspace"
                    type="primary"
                    icon={<ControlOutlined />}
                    onClick={() => {
                      createProjectFromInitialization(id || 'demo');
                      navigate(`/projects/${id || 'demo'}/workspace`);
                    }}
                    style={{ background: '#2563EB', fontWeight: 600 }}
                  >
                    Open AI OS Workspace
                  </Button>
                ]}
              />
            )}

          </Panel>
        </Col>

      </Row>
    </PageContainer>
  );
}

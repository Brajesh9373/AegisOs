import React, { useEffect, useState } from 'react';
import { ApiClient } from '../api/client';
import {
  Button, Modal, Form, Input, Select, Switch, Checkbox,
  Card, Tag, Space, message, Tabs, Divider, Alert, Spin, Tooltip
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined,
  RobotOutlined, SettingOutlined, KeyOutlined,
  DatabaseOutlined, ApiOutlined, CopyOutlined
} from '@ant-design/icons';

const { TextArea } = Input;
const { Option } = Select;

interface ProfileStage {
  stage_id: string;
  description: string;
  capability_ids: string[];
  max_capability_requests: number;
}

interface MemoryScope {
  read: boolean;
  write: boolean;
  categories: string[];
  retention_days: number;
}

interface KnowledgeScope {
  graphs: string[];
  read: boolean;
  write: boolean;
  node_types: string[];
}

interface ToolScope {
  allowed_tools: string[];
  rate_limit: number;
  restrictions: Record<string, any>;
}

interface ScopeRecommendations {
  memory_scope: MemoryScope;
  knowledge_scope: KnowledgeScope;
  tool_scope: ToolScope;
  reasoning?: string;
}

interface ProfileInfo {
  id?: string;
  profile_id: string;
  version: string;
  name: string;
  description: string;
  stages: string[] | ProfileStage[];
  capabilities?: string[];
  role?: string;
  parent_profile_id?: string;
  system_prompt?: string;
  memory_scope?: MemoryScope;
  knowledge_scope?: KnowledgeScope;
  tool_scope?: ToolScope;
  scope_recommendations?: ScopeRecommendations;
  model_provider?: string;
  model_name?: string;
  source?: string;
  status?: string;
}

interface ProfilesResponse {
  profiles: ProfileInfo[];
  total: number;
}

const ROLE_OPTIONS = [
  'senior_dev', 'mid_dev', 'junior_dev', 'tech_lead', 'engineering_manager',
  'data_engineer', 'data_analyst', 'qa_engineer', 'devops_engineer',
  'security_engineer', 'product_manager', 'product_designer',
  'business_analyst', 'project_manager', 'architect'
];

const TOOL_OPTIONS = [
  'search', 'read', 'write', 'create', 'update', 'delete',
  'list', 'execute', 'deploy', 'test', 'analyze', 'report'
];

const MEMORY_CATEGORIES = [
  'project_context', 'user_preferences', 'conversation_history',
  'business_rules', 'technical_specs', 'decisions', 'learnings'
];

const KNOWLEDGE_NODE_TYPES = [
  'document', 'concept', 'entity', 'relationship', 'process', 'policy'
];

const DEFAULT_STAGES = [
  { stage_id: 'understand', description: 'Understand the task', max_capability_requests: 0 },
  { stage_id: 'execute', description: 'Execute the task', max_capability_requests: 3 },
  { stage_id: 'finalize', description: 'Finalize and report', max_capability_requests: 0 },
];

export function AgentProfiles() {
  const [profiles, setProfiles] = useState<ProfileInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProfile, setSelectedProfile] = useState<ProfileInfo | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState('list');

  useEffect(() => {
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    try {
      setLoading(true);
      const response = await ApiClient.get('/agent-profiles') as ProfilesResponse;
      setProfiles(response.profiles || []);
      setError(null);
    } catch (err) {
      setError('Failed to load agent profiles');
      console.error('Error loading profiles:', err);
    } finally {
      setLoading(false);
    }
  };

  const analyzeScopes = async (values: any) => {
    setAnalyzing(true);
    try {
      const result = await ApiClient.post('/agent-profiles/analyze-scopes', {
        name: values.name,
        description: values.description,
        system_prompt: values.system_prompt,
        role: values.role,
        parent_profile_id: values.parent_profile_id,
      }) as { recommendations: ScopeRecommendations };

      if (result.recommendations) {
        form.setFieldsValue({
          memory_scope: result.recommendations.memory_scope,
          knowledge_scope: result.recommendations.knowledge_scope,
          tool_scope: result.recommendations.tool_scope,
        });
        message.success('AI analyzed scopes and made recommendations');
      }
    } catch (err) {
      console.error('Scope analysis failed:', err);
      message.warning('AI analysis failed, using defaults');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleCreateProfile = async (values: any) => {
    try {
      const profileData = {
        profile_id: values.profile_id,
        name: values.name,
        description: values.description,
        version: values.version || '1.0.0',
        role: values.role,
        parent_profile_id: values.parent_profile_id,
        system_prompt: values.system_prompt,
        user_prompt_template: values.user_prompt_template,
        stages: values.stages?.map((s: string, i: number) => ({
          stage_id: s,
          description: DEFAULT_STAGES[i]?.description || s,
          capability_ids: [],
          max_capability_requests: 0,
        })) || DEFAULT_STAGES,
        memory_scope: values.memory_scope,
        knowledge_scope: values.knowledge_scope,
        tool_scope: values.tool_scope,
        model_provider: values.model_provider,
        model_name: values.model_name,
        temperature: values.temperature,
        max_tokens: values.max_tokens,
      };

      await ApiClient.post('/agent-profiles', profileData);
      message.success('Profile created successfully');
      setShowCreateModal(false);
      form.resetFields();
      loadProfiles();
      setActiveTab('list');
    } catch (err: any) {
      message.error(err?.data?.detail || 'Failed to create profile');
    }
  };

  const handleUpdateProfile = async (values: any) => {
    if (!selectedProfile?.profile_id) return;
    try {
      await ApiClient.put(`/agent-profiles/${selectedProfile.profile_id}`, values);
      message.success('Profile updated successfully');
      setShowEditModal(false);
      loadProfiles();
    } catch (err: any) {
      message.error(err?.data?.detail || 'Failed to update profile');
    }
  };

  const handleDeleteProfile = async (profileId: string) => {
    Modal.confirm({
      title: 'Delete Profile',
      content: `Are you sure you want to delete "${profileId}"?`,
      okText: 'Delete',
      okType: 'danger',
      onOk: async () => {
        try {
          await ApiClient.delete(`/agent-profiles/${profileId}`);
          message.success('Profile deleted');
          loadProfiles();
        } catch (err) {
          message.error('Failed to delete profile');
        }
      },
    });
  };

  const applyRecommendations = async (profileId: string) => {
    try {
      await ApiClient.post(`/agent-profiles/${profileId}/apply-recommendations`, {});
      message.success('Recommendations applied');
      loadProfiles();
    } catch (err) {
      console.error('Apply recommendations error:', err);
      message.error('Failed to apply recommendations');
    }
  };

  const getStageColor = (stage: string) => {
    const colors: Record<string, string> = {
      'understand': '#48bb78', 'clarify': '#4299e1', 'finalize': '#ed8936',
      'design-team': '#9f7aea', 'review': '#f56565', 'audit': '#667eea',
      'execute': '#38b2ac', 'analyze': '#ed64a6',
    };
    return colors[stage] || '#718096';
  };

  const dbProfiles = profiles.filter(p => !p.source || p.source !== 'plugin');

  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center' }}><Spin size="large" /></div>;
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 600, color: '#1a202c', marginBottom: '0.5rem' }}>
            <RobotOutlined style={{ marginRight: 12 }} />
            Agent Profiles
          </h1>
          <p style={{ color: '#718096' }}>
            Create and manage AI agent profiles with intelligent scope recommendations
          </p>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreateModal(true)}>
          Create Profile
        </Button>
      </div>

      {error && <Alert message={error} type="error" style={{ marginBottom: '1rem' }} />}

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'list',
            label: 'All Profiles',
            children: (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: '1.5rem' }}>
                {profiles.map((profile) => (
                  <Card
                    key={profile.profile_id}
                    hoverable
                    onClick={() => setSelectedProfile(profile)}
                    style={{
                      border: selectedProfile?.profile_id === profile.profile_id ? '2px solid #4299e1' : '1px solid #e2e8f0',
                      borderRadius: 12
                    }}
                    extra={
                      <Space>
                        {profile.source !== 'plugin' && (
                          <>
                            <Tooltip title="Edit">
                              <Button type="text" icon={<EditOutlined />} onClick={(e) => { e.stopPropagation(); setSelectedProfile(profile); setShowEditModal(true); }} />
                            </Tooltip>
                            <Tooltip title="Delete">
                              <Button type="text" danger icon={<DeleteOutlined />} onClick={(e) => { e.stopPropagation(); handleDeleteProfile(profile.profile_id); }} />
                            </Tooltip>
                          </>
                        )}
                      </Space>
                    }
                    title={
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span>{profile.name}</span>
                        {profile.source === 'plugin' && <Tag color="purple">Built-in</Tag>}
                        {profile.status === 'active' && <Tag color="green">Active</Tag>}
                      </div>
                    }
                  >
                    <p style={{ color: '#718096', marginBottom: '1rem', minHeight: 40 }}>
                      {profile.description || 'No description'}
                    </p>

                    <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
                      {profile.role && <Tag icon={<SettingOutlined />}>{profile.role}</Tag>}
                      {profile.model_name && <Tag icon={<ApiOutlined />}>{profile.model_name}</Tag>}
                      <Tag>v{profile.version}</Tag>
                    </div>

                    {Array.isArray(profile.stages) && profile.stages.length > 0 && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                        {profile.stages.map((stage: any) => (
                          <span key={stage.stage_id || stage} style={{
                            background: getStageColor(stage.stage_id || stage),
                            color: '#fff', padding: '2px 8px', borderRadius: 4, fontSize: 11
                          }}>
                            {stage.stage_id || stage}
                          </span>
                        ))}
                      </div>
                    )}

                    {profile.scope_recommendations && (
                      <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid #e2e8f0' }}>
                        <Button size="small" onClick={(e) => { e.stopPropagation(); applyRecommendations(profile.profile_id); }}>
                          Apply AI Recommendations
                        </Button>
                      </div>
                    )}
                  </Card>
                ))}

                {profiles.length === 0 && (
                  <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem', background: '#f7fafc', borderRadius: 12, border: '2px dashed #e2e8f0' }}>
                    <RobotOutlined style={{ fontSize: 48, color: '#cbd5e0', marginBottom: 16 }} />
                    <h3>No Profiles Yet</h3>
                    <p style={{ color: '#718096' }}>Create your first agent profile to get started</p>
                  </div>
                )}
              </div>
            ),
          },
          {
            key: 'db',
            label: `Custom Profiles (${dbProfiles.length})`,
            children: (
              <div>
                {dbProfiles.length === 0 ? (
                  <Alert
                    message="No custom profiles"
                    description="Create a profile using the Create Profile button to add custom agent configurations."
                    type="info"
                    showIcon
                  />
                ) : (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1rem' }}>
                    {dbProfiles.map(profile => (
                      <ProfileDetailCard
                        key={profile.profile_id}
                        profile={profile}
                        onEdit={() => { setSelectedProfile(profile); setShowEditModal(true); }}
                        onDelete={() => handleDeleteProfile(profile.profile_id)}
                      />
                    ))}
                  </div>
                )}
              </div>
            ),
          },
        ]}
      />

      {/* Profile Detail Modal */}
      <Modal
        title={selectedProfile?.name}
        open={!!selectedProfile && !showEditModal}
        onCancel={() => setSelectedProfile(null)}
        footer={<Button onClick={() => setSelectedProfile(null)}>Close</Button>}
        width={700}
      >
        {selectedProfile && <ProfileDetailView profile={selectedProfile} />}
      </Modal>

      {/* Create Profile Modal */}
      <Modal
        title="Create New Agent Profile"
        open={showCreateModal}
        onCancel={() => { setShowCreateModal(false); form.resetFields(); }}
        footer={null}
        width={900}
        styles={{ body: { maxHeight: '70vh', overflowY: 'auto' } }}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateProfile}>
          <Divider>Basic Information</Divider>

          <Form.Item name="profile_id" label="Profile ID" rules={[{ required: true, message: 'Unique profile identifier' }]}>
            <Input placeholder="e.g., data-engineer, qa-automation" />
          </Form.Item>

          <Form.Item name="name" label="Profile Name" rules={[{ required: true }]}>
            <Input placeholder="e.g., Data Engineer Agent" />
          </Form.Item>

          <Form.Item name="description" label="Description">
            <TextArea rows={2} placeholder="What does this agent do?" />
          </Form.Item>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="role" label="Role">
              <Select placeholder="Select role">
                {ROLE_OPTIONS.map(r => <Option key={r} value={r}>{r.replace(/_/g, ' ')}</Option>)}
              </Select>
            </Form.Item>
            <Form.Item name="parent_profile_id" label="Reports To">
              <Select placeholder="Select parent profile" allowClear>
                {profiles.filter(p => p.source !== 'plugin').map(p => (
                  <Option key={p.profile_id} value={p.profile_id}>{p.name}</Option>
                ))}
              </Select>
            </Form.Item>
          </div>

          <Form.Item name="version" label="Version" initialValue="1.0.0">
            <Input placeholder="1.0.0" />
          </Form.Item>

          <Divider>System Prompt</Divider>

          <Form.Item name="system_prompt" label="System Prompt" rules={[{ required: true }]}>
            <TextArea rows={6} placeholder="Define the agent's behavior, responsibilities, and constraints..." />
          </Form.Item>

          <Form.Item name="user_prompt_template" label="User Prompt Template (optional)">
            <TextArea rows={3} placeholder="Template for user inputs with {variable} substitution" />
          </Form.Item>

          <Divider>AI Scope Analysis</Divider>

          <Form.Item>
            <Button
              onClick={() => analyzeScopes(form.getFieldsValue())}
              loading={analyzing}
              icon={<KeyOutlined />}
            >
              Analyze & Recommend Scopes
            </Button>
            <p style={{ color: '#718096', fontSize: 12, marginTop: 8 }}>
              AI will analyze your profile configuration and recommend appropriate memory, knowledge, and tool scopes
            </p>
          </Form.Item>

          <Divider>Memory Scope</Divider>

          <Form.Item name={['memory_scope', 'read']} valuePropName="checked" initialValue={true}>
            <Checkbox>Read Access</Checkbox>
          </Form.Item>
          <Form.Item name={['memory_scope', 'write']} valuePropName="checked">
            <Checkbox>Write Access</Checkbox>
          </Form.Item>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name={['memory_scope', 'categories']} label="Memory Categories">
              <Select mode="multiple" placeholder="Select categories">
                {MEMORY_CATEGORIES.map(c => <Option key={c} value={c}>{c}</Option>)}
              </Select>
            </Form.Item>
            <Form.Item name={['memory_scope', 'retention_days']} label="Retention (days)" initialValue={30}>
              <Input type="number" min={1} max={365} />
            </Form.Item>
          </div>

          <Divider>Knowledge Graph Scope</Divider>

          <Form.Item name={['knowledge_scope', 'read']} valuePropName="checked" initialValue={true}>
            <Checkbox>Read Access</Checkbox>
          </Form.Item>
          <Form.Item name={['knowledge_scope', 'write']} valuePropName="checked">
            <Checkbox>Write Access</Checkbox>
          </Form.Item>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name={['knowledge_scope', 'graphs']} label="Knowledge Graphs">
              <Select mode="multiple" placeholder="Select graphs" defaultValue={['default']}>
                <Option value="default">default</Option>
                <Option value="projects">projects</Option>
                <Option value="technical">technical</Option>
              </Select>
            </Form.Item>
            <Form.Item name={['knowledge_scope', 'node_types']} label="Node Types">
              <Select mode="multiple" placeholder="Select node types">
                {KNOWLEDGE_NODE_TYPES.map(n => <Option key={n} value={n}>{n}</Option>)}
              </Select>
            </Form.Item>
          </div>

          <Divider>Tool Scope</Divider>

          <Form.Item name={['tool_scope', 'allowed_tools']} label="Allowed Tools">
            <Select mode="multiple" placeholder="Select tools">
              {TOOL_OPTIONS.map(t => <Option key={t} value={t}>{t}</Option>)}
            </Select>
          </Form.Item>

          <Form.Item name={['tool_scope', 'rate_limit']} label="Rate Limit (req/min)" initialValue={60}>
            <Input type="number" min={1} max={1000} />
          </Form.Item>

          <Divider>LLM Configuration (Optional)</Divider>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
            <Form.Item name="model_provider" label="Provider">
              <Select placeholder="Select provider" allowClear>
                <Option value="openai">OpenAI</Option>
                <Option value="anthropic">Anthropic</Option>
                <Option value="deepseek">DeepSeek</Option>
              </Select>
            </Form.Item>
            <Form.Item name="model_name" label="Model">
              <Input placeholder="e.g., gpt-4o" />
            </Form.Item>
            <Form.Item name="temperature" label="Temperature">
              <Input type="number" step={0.1} min={0} max={2} placeholder="0.7" />
            </Form.Item>
          </div>

          <Form.Item style={{ marginTop: 24 }}>
            <Space>
              <Button type="primary" htmlType="submit">Create Profile</Button>
              <Button onClick={() => setShowCreateModal(false)}>Cancel</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit Profile Modal */}
      <Modal
        title={`Edit: ${selectedProfile?.name}`}
        open={showEditModal}
        onCancel={() => { setShowEditModal(false); setSelectedProfile(null); }}
        footer={null}
        width={900}
        styles={{ body: { maxHeight: '70vh', overflowY: 'auto' } }}
      >
        {selectedProfile && (
          <Form
            layout="vertical"
            initialValues={selectedProfile}
            onFinish={handleUpdateProfile}
          >
            <Form.Item name="name" label="Profile Name" rules={[{ required: true }]}>
              <Input />
            </Form.Item>

            <Form.Item name="description" label="Description">
              <TextArea rows={2} />
            </Form.Item>

            <Form.Item name="system_prompt" label="System Prompt">
              <TextArea rows={4} />
            </Form.Item>

            {selectedProfile.scope_recommendations && (
              <Alert
                message="AI Recommendations Available"
                description={selectedProfile.scope_recommendations.reasoning || "Click 'Apply AI Recommendations' to use AI-suggested scopes"}
                type="info"
                showIcon
                action={
                  <Button size="small" onClick={() => applyRecommendations(selectedProfile.profile_id)}>
                    Apply
                  </Button>
                }
                style={{ marginBottom: 16 }}
              />
            )}

            <Form.Item name={['memory_scope', 'read']} valuePropName="checked">
              <Checkbox>Memory Read Access</Checkbox>
            </Form.Item>
            <Form.Item name={['memory_scope', 'write']} valuePropName="checked">
              <Checkbox>Memory Write Access</Checkbox>
            </Form.Item>

            <Form.Item name={['knowledge_scope', 'read']} valuePropName="checked">
              <Checkbox>Knowledge Read Access</Checkbox>
            </Form.Item>
            <Form.Item name={['knowledge_scope', 'write']} valuePropName="checked">
              <Checkbox>Knowledge Write Access</Checkbox>
            </Form.Item>

            <Form.Item name={['tool_scope', 'allowed_tools']} label="Allowed Tools">
              <Select mode="multiple">
                {TOOL_OPTIONS.map(t => <Option key={t} value={t}>{t}</Option>)}
              </Select>
            </Form.Item>

            <Form.Item style={{ marginTop: 24 }}>
              <Space>
                <Button type="primary" htmlType="submit">Save Changes</Button>
                <Button onClick={() => setShowEditModal(false)}>Cancel</Button>
              </Space>
            </Form.Item>
          </Form>
        )}
      </Modal>
    </div>
  );
}

function ProfileDetailCard({ profile, onEdit, onDelete }: {
  profile: ProfileInfo;
  onEdit: () => void;
  onDelete: () => void;
}) {
  return (
    <Card
      size="small"
      title={profile.name}
      extra={<Space><Button size="small" icon={<EditOutlined />} onClick={onEdit}>Edit</Button><Button size="small" danger icon={<DeleteOutlined />} onClick={onDelete} /></Space>}
    >
      <p style={{ fontSize: 13, color: '#718096' }}>{profile.description}</p>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
        {profile.role && <Tag>{profile.role}</Tag>}
        {profile.parent_profile_id && <Tag color="orange">reports to: {profile.parent_profile_id}</Tag>}
      </div>
      {profile.memory_scope && (
        <div style={{ fontSize: 11, color: '#718096' }}>
          <DatabaseOutlined /> Memory: {profile.memory_scope.read ? 'R' : ''}{profile.memory_scope.write ? 'W' : ''} |
          <ApiOutlined /> Tools: {profile.tool_scope?.allowed_tools?.length || 0}
        </div>
      )}
    </Card>
  );
}

function ProfileDetailView({ profile }: { profile: ProfileInfo }) {
  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Tag color="blue">{profile.profile_id}</Tag>
        <Tag>v{profile.version}</Tag>
        {profile.role && <Tag>{profile.role}</Tag>}
      </div>

      <p><strong>Description:</strong> {profile.description || 'None'}</p>

      {profile.parent_profile_id && (
        <p><strong>Reports to:</strong> {profile.parent_profile_id}</p>
      )}

      {profile.system_prompt && (
        <div style={{ marginTop: 16 }}>
          <strong>System Prompt:</strong>
          <pre style={{ background: '#f7fafc', padding: 12, borderRadius: 6, marginTop: 8, fontSize: 12, whiteSpace: 'pre-wrap' }}>
            {profile.system_prompt}
          </pre>
        </div>
      )}

      <Divider />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
        <div>
          <h4><DatabaseOutlined /> Memory Scope</h4>
          <pre style={{ fontSize: 12, background: '#f7fafc', padding: 8, borderRadius: 4 }}>
            {JSON.stringify(profile.memory_scope || {}, null, 2)}
          </pre>
        </div>
        <div>
          <h4><KeyOutlined /> Knowledge Scope</h4>
          <pre style={{ fontSize: 12, background: '#f7fafc', padding: 8, borderRadius: 4 }}>
            {JSON.stringify(profile.knowledge_scope || {}, null, 2)}
          </pre>
        </div>
        <div>
          <h4><ApiOutlined /> Tool Scope</h4>
          <pre style={{ fontSize: 12, background: '#f7fafc', padding: 8, borderRadius: 4 }}>
            {JSON.stringify(profile.tool_scope || {}, null, 2)}
          </pre>
        </div>
      </div>

      {profile.scope_recommendations && (
        <>
          <Divider />
          <Alert
            message="AI Scope Recommendations"
            description={
              <div>
                <p>{profile.scope_recommendations.reasoning}</p>
                <details>
                  <summary style={{ cursor: 'pointer', color: '#4299e1' }}>View recommendations</summary>
                  <pre style={{ fontSize: 11, marginTop: 8 }}>
                    {JSON.stringify(profile.scope_recommendations, null, 2)}
                  </pre>
                </details>
              </div>
            }
            type="info"
            showIcon
          />
        </>
      )}
    </div>
  );
}
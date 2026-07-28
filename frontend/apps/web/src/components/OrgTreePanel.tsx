/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useEffect } from 'react';
import { Tree, Card, Button, Space, Typography, Tag, Input, Select, Modal, Form, message, Badge, Popconfirm } from 'antd';
import {
  TeamOutlined, UserOutlined, PlusOutlined, DeleteOutlined,
  EditOutlined, ApartmentOutlined, CrownOutlined,
} from '@ant-design/icons';
import { ApiClient } from '../api/client';

const { Text } = Typography;

const agentFetch = async (method: string, path: string, body?: any) => {
  const token = localStorage.getItem('auth_token');
  const res = await fetch(`/agents${path}`, {
    method,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  if (!res.ok) throw new Error(`Agent API ${res.status}`);
  return res.json().catch(() => ({}));
};

interface OrgAgent {
  id: string;
  name: string;
  designation: string;
  department: string;
  reports_to: string | null;
  skills: string[];
  status: string;
  role_description?: string;
}

interface OrgTreeProps {
  projectId?: string;
  preSelectedSkills?: string[];
  maxHeight?: number;
}

export const OrgTreePanel: React.FC<OrgTreeProps> = ({ projectId, preSelectedSkills = [], maxHeight = 500 }) => {
  const [agents, setAgents] = useState<OrgAgent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<OrgAgent | null>(null);
  const [editForm, setEditForm] = useState(false);
  const [form, setForm] = useState<any>({});
  const [loading, setLoading] = useState(false);

  const fetchAgents = () => {
    setLoading(true);
    agentFetch('GET', '')
      .then((data) => setAgents(Array.isArray(data) ? data : data.agents || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchAgents(); }, []);

  const buildTree = (): any[] => {
    const roots = agents.filter((a) => !a.reports_to);
    const children = (parentId: string): any[] =>
      agents
        .filter((a) => a.reports_to === parentId)
        .map((a) => ({ title: renderNode(a), key: a.id, children: children(a.id) }));
    return roots.map((r) => ({ title: renderNode(r), key: r.id, children: children(r.id) }));
  };

  const renderNode = (agent: OrgAgent) => (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '2px 0' }}>
      <UserOutlined style={{ color: agent.status === 'active' ? '#16a34a' : '#94a3b8', fontSize: 11 }} />
      <span style={{ fontSize: 12, fontWeight: 500 }}>{agent.name}</span>
      <Tag color={agent.department === 'leadership' ? 'gold' : 'geekblue'} style={{ fontSize: 9, lineHeight: '16px', padding: '0 4px' }}>
        {agent.designation || agent.department}
      </Tag>
    </div>
  );

  const handleSelect = (keys: any[]) => {
    if (keys.length === 0) { setSelectedAgent(null); return; }
    const agent = agents.find((a) => a.id === keys[0]);
    setSelectedAgent(agent || null);
  };

  const openEditForm = (agent: OrgAgent) => {
    setForm({ ...agent, skills: agent.skills || [] });
    setEditForm(true);
  };

  const saveAgent = async () => {
    try {
      if (form.id && agents.some((a) => a.id === form.id)) {
        await agentFetch('PUT', `/${form.id}`, form);
      } else {
        const res = await agentFetch('POST', '', { ...form });
        form.id = res.id;
      }
      message.success('Saved');
      setEditForm(false);
      fetchAgents();
    } catch { message.error('Failed to save'); }
  };

  const deleteAgent = async (agent: OrgAgent) => {
    try {
      await agentFetch('DELETE', `/${agent.id}`);
      message.success('Deleted');
      setSelectedAgent(null);
      fetchAgents();
    } catch { message.error('Failed to delete'); }
  };

  return (
    <div style={{ display: 'flex', gap: 16, height: '100%' }}>
      {/* Left: Tree */}
      <div style={{ flex: 1, overflowY: 'auto', maxHeight }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <Text strong style={{ fontSize: 13 }}><ApartmentOutlined style={{ marginRight: 6 }} />Organization Chart</Text>
          <Button type="primary" size="small" icon={<PlusOutlined />}
            onClick={() => { setForm({ name: '', designation: '', department: '', reports_to: null, skills: preSelectedSkills || [], status: 'active' }); setEditForm(true); }}>
            Add Role
          </Button>
        </div>
        <Tree
          treeData={buildTree()}
          showIcon={false}
          defaultExpandAll
          selectedKeys={selectedAgent ? [selectedAgent.id] : []}
          onSelect={handleSelect}
          style={{ fontSize: 12 }}
        />
      </div>

      {/* Right: Detail */}
      <div style={{ width: 260, flexShrink: 0, borderLeft: '1px solid #e5e7eb', paddingLeft: 16, overflowY: 'auto', maxHeight }}>
        {selectedAgent ? (
          <div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 14, display: 'block', color: '#0f172a' }}>{selectedAgent.name}</Text>
              <div style={{ marginTop: 6 }}>
                <Tag color="blue">{selectedAgent.designation}</Tag>
                <Tag color="geekblue">{selectedAgent.department}</Tag>
                {selectedAgent.status && <Tag color={selectedAgent.status === 'active' ? 'green' : 'default'}>{selectedAgent.status}</Tag>}
              </div>
            </div>
            {selectedAgent.role_description && (
              <div style={{ marginBottom: 8 }}>
                <Text type="secondary" style={{ fontSize: 10 }}>Description</Text>
                <div style={{ fontSize: 12, color: '#475569' }}>{selectedAgent.role_description}</div>
              </div>
            )}
            {(selectedAgent.skills || []).length > 0 && (
              <div style={{ marginBottom: 8 }}>
                <Text type="secondary" style={{ fontSize: 10, display: 'block', marginBottom: 4 }}>Skills</Text>
                <Space wrap size={4}>
                  {(selectedAgent.skills || []).map((s: string) => <Tag key={s} style={{ fontSize: 10 }}>{s}</Tag>)}
                </Space>
              </div>
            )}
            <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
              <Button icon={<EditOutlined />} size="small" onClick={() => openEditForm(selectedAgent)}>Edit</Button>
              <Popconfirm title="Delete this role?" onConfirm={() => deleteAgent(selectedAgent)}>
                <Button icon={<DeleteOutlined />} size="small" danger>Delete</Button>
              </Popconfirm>
            </div>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#94a3b8' }}>
            <TeamOutlined style={{ fontSize: 28, marginBottom: 8, color: '#cbd5e1' }} />
            <Text style={{ fontSize: 12, display: 'block' }}>Select a role from the chart</Text>
            <Text type="secondary" style={{ fontSize: 10, marginTop: 4 }}>or click "Add Role" to create one</Text>
          </div>
        )}
      </div>

      {/* Edit Modal */}
      <Modal
        title={form.id ? 'Edit Role' : 'Create Role'}
        open={editForm}
        onCancel={() => setEditForm(false)}
        onOk={saveAgent}
        okText="Save"
        width={400}
      >
        <Form layout="vertical" size="small">
          <Form.Item label="Name" required>
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Form.Item>
          <Form.Item label="Designation">
            <Input value={form.designation} onChange={(e) => setForm({ ...form, designation: e.target.value })} placeholder="e.g. Tech Lead" />
          </Form.Item>
          <Form.Item label="Department">
            <Select value={form.department} onChange={(v) => setForm({ ...form, department: v })} placeholder="Select...">
              {['leadership','backend','frontend','devops','qa','data'].map((d) => <Select.Option key={d} value={d}>{d}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item label="Reports To">
            <Select value={form.reports_to} onChange={(v) => setForm({ ...form, reports_to: v })} allowClear placeholder="None (root)">
              {agents.filter((a) => a.id !== form.id).map((a) => <Select.Option key={a.id} value={a.id}>{a.name}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item label="Skills">
            <Select mode="tags" value={form.skills || []} onChange={(v) => setForm({ ...form, skills: v })} placeholder="Type and press Enter" />
          </Form.Item>
          <Form.Item label="Description">
            <Input.TextArea value={form.role_description || ''} onChange={(e) => setForm({ ...form, role_description: e.target.value })} rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

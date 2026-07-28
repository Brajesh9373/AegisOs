import React, { useEffect, useState } from 'react';
import { Table, Button, Space, Typography, Tag, Modal, Form, Input, Select, Card, Row, Col, Statistic } from 'antd';
import { PlusOutlined, ProjectOutlined, RightOutlined } from '@ant-design/icons';
import { ApiClient } from '../api/client';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

export function Projects() {
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [pendingApprovals, setPendingApprovals] = useState(0);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const data = await ApiClient.get('/projects');
      setProjects(data);
      const summary = await ApiClient.get('/operations/summary');
      setPendingApprovals(summary?.stats?.pendingApprovals || 0);
    } catch (e) {
      ApiClient.handleError(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchProjects(); }, []);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      const created = await ApiClient.post('/projects', values);
      setIsModalOpen(false);
      form.resetFields();
      navigate(`/projects/${created.id}/workspace`);
    } catch (e: any) {
      if (e.data) ApiClient.handleError(e);
    }
  };

  const columns = [
    { title: 'Project Name', dataIndex: 'name', key: 'name', render: (t: string, r: any) => <a onClick={() => navigate(`/projects/${r.id}/workspace`)} style={{fontWeight: 600}}>{t}</a> },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: string) => <Tag color={s === 'Active' ? 'green' : s === 'Planning' ? 'blue' : 'default'}>{s}</Tag> },
    { title: 'Priority', dataIndex: 'priority', key: 'priority', render: (p: string) => <Tag color={p === 'High' ? 'red' : 'default'}>{p}</Tag> },
    { title: 'Department', dataIndex: 'department', key: 'department' },
    { title: 'Action', key: 'action', render: (_: any, r: any) => <Button type="link" onClick={() => navigate(`/projects/${r.id}/workspace`)}>Workspace <RightOutlined/></Button> }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col span={8}><Card><Statistic title="Total Projects" value={projects.length} prefix={<ProjectOutlined />} /></Card></Col>
        <Col span={8}><Card><Statistic title="Active Projects" value={projects.filter(p => ['Active', 'Execution'].includes(p.status)).length} valueStyle={{ color: '#3f8600' }} /></Card></Col>
        <Col span={8}><Card><Statistic title="Pending Approvals" value={pendingApprovals} /></Card></Col>
      </Row>

      <Card 
        title={<Title level={4} style={{ margin: 0 }}>Business Projects</Title>} 
        extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalOpen(true)}>New Project</Button>}
        bordered={false}
      >
        <Table dataSource={projects} columns={columns} rowKey="id" loading={loading} />
      </Card>

      <Modal title="Create New Project" open={isModalOpen} onOk={handleCreate} onCancel={() => setIsModalOpen(false)} okText="Create Project">
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Project Name" rules={[{ required: true }]}><Input placeholder="e.g. Automate Invoice Processing" /></Form.Item>
          <Form.Item name="businessGoal" label="Business Goal (Free Text)" rules={[{ required: true }]}><Input.TextArea rows={4} placeholder="Describe what this project should achieve..." /></Form.Item>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="department" label="Department"><Input placeholder="e.g. Finance" /></Form.Item></Col>
            <Col span={12}>
              <Form.Item name="priority" label="Priority" initialValue="Medium">
                <Select options={[{value:'High',label:'High'},{value:'Medium',label:'Medium'},{value:'Low',label:'Low'}]} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
}

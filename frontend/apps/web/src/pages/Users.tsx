
import React, { useEffect, useState } from 'react';
import { Table, Button, Space, Typography, Tag, Modal, Form, Input, Select, message } from 'antd';
import { ApiClient } from '../api/client';

const { Title } = Typography;

export function Users() {
  const [users, setUsers] = useState<Record<string, any>[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form] = Form.useForm();

  const fetchUsers = () => {
    ApiClient.get('/users').then(setUsers).catch(() => {});
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const toggleActive = async (record: Record<string, any>) => {
    try {
      await ApiClient.put(`/users/${record.id}/active`, { active: !record.active });
      message.success('User status updated');
      fetchUsers();
    } catch {
      message.error('Failed to update status');
    }
  };

  const handleCreateUser = async (values: any) => {
    try {
      await ApiClient.post('/users', values);
      message.success('User registered successfully');
      setIsModalOpen(false);
      form.resetFields();
      fetchUsers();
    } catch {
      message.error('Registration failed');
    }
  };

  const columns = [
    { title: 'Email', dataIndex: 'email', key: 'email' },
    { title: 'Role', dataIndex: 'role', key: 'role', render: (role: string) => <Tag color="blue">{role}</Tag> },
    { title: 'Status', dataIndex: 'active', key: 'active', render: (active: boolean) => (
      <Tag color={active ? 'success' : 'error'}>{active ? 'Active' : 'Inactive'}</Tag>
    )},
    {
      title: 'Action',
      key: 'action',
      render: (_: unknown, record: Record<string, any>) => (
        <Space size="middle">
          <Button type="link" size="small" onClick={() => toggleActive(record)}>
            {record.active ? 'Deactivate' : 'Activate'}
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <Title level={3} style={{ margin: 0 }}>User Management</Title>
        <Button type="primary" onClick={() => setIsModalOpen(true)}>Invite User</Button>
      </div>

      <Table columns={columns} dataSource={users} rowKey="id" />

      <Modal
        title="Invite New User"
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateUser}>
          <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
            <Input placeholder="user@company.com" />
          </Form.Item>
          <Form.Item name="password" label="Password" rules={[{ required: true }]}>
            <Input.Password placeholder="••••••••" />
          </Form.Item>
          <Form.Item name="role" label="Role" rules={[{ required: true }]}>
            <Select placeholder="Select role">
              <Select.Option value="Viewer">Viewer</Select.Option>
              <Select.Option value="Analyst">Analyst</Select.Option>
              <Select.Option value="Developer">Developer</Select.Option>
              <Select.Option value="Manager">Manager</Select.Option>
              <Select.Option value="Org Admin">Org Admin</Select.Option>
              <Select.Option value="Super Admin">Super Admin</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="department" label="Department" rules={[{ required: true }]}>
            <Select placeholder="Select department">
              <Select.Option value="General">General</Select.Option>
              <Select.Option value="Operations">Operations</Select.Option>
              <Select.Option value="Finance">Finance</Select.Option>
              <Select.Option value="Engineering">Engineering</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>Create Account</Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

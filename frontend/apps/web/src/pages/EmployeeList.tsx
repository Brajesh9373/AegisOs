/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, Typography, Layout } from 'antd';
import { RobotOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { ApiClient } from '../api/client';

const { Title } = Typography;
const { Content } = Layout;

export const EmployeeList: React.FC = () => {
  const [employees, setEmployees] = useState<any[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    ApiClient.get('/employees').then(setEmployees);
  }, []);

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (t: string) => (
        <b>
          <RobotOutlined /> {t}
        </b>
      ),
    },
    { title: 'Role', dataIndex: 'role', key: 'role' },
    { title: 'Department', dataIndex: 'department', key: 'department' },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (t: string) => (
        <Tag color={t === 'Ready' ? 'green' : t === 'Disabled' ? 'red' : 'orange'}>{t}</Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'action',
      render: (_: any, r: any) => (
        <Button type="link" onClick={() => navigate(`/employees/${r.id}`)}>
          Configure
        </Button>
      ),
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh', padding: 24 }}>
      <Content>
        <Card
          title={
            <Title level={4}>
              <RobotOutlined /> Digital Employees Workspace
            </Title>
          }
        >
          <Table dataSource={employees} columns={columns} rowKey="id" />
        </Card>
      </Content>
    </Layout>
  );
};

/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, Typography, Layout } from 'antd';
import { ApiOutlined, PlusOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { ApiClient } from '../api/client';

const { Title } = Typography;
const { Content } = Layout;

export const ConnectorCatalog: React.FC = () => {
  const [connectors, setConnectors] = useState<any[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    ApiClient.get('/connectors').then(setConnectors);
  }, []);

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name', render: (t: string) => <b>{t}</b> },
    { title: 'Type', dataIndex: 'type', key: 'type' },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (t: string) => <Tag color={t === 'Source' ? 'purple' : 'cyan'}>{t}</Tag>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (t: string) => <Tag color={t === 'Connected' ? 'green' : 'orange'}>{t}</Tag>,
    },
    {
      title: 'Actions',
      key: 'action',
      render: (_: any, r: any) => (
        <Button type="link" onClick={() => navigate(`/connectors/${r.id}`)}>
          Configure
        </Button>
      ),
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh', padding: 24 }}>
      <Content>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
          <Title level={4}>
            <ApiOutlined /> Data Connectors
          </Title>
          <Button type="primary" icon={<PlusOutlined />}>
            Create Connector
          </Button>
        </div>
        <Card>
          <Table dataSource={connectors} columns={columns} rowKey="id" />
        </Card>
      </Content>
    </Layout>
  );
};

import React, { useState } from 'react';
import { Table, Tag, Button, Space, Typography, Card, Badge } from 'antd';
const { Title } = Typography;

export function Connectors() {
  const [data] = useState([
    { id: '1', name: 'GitHub', health: 98, status: 'Connected', lastSync: '10 mins ago' },
    { id: '2', name: 'Jira', health: 100, status: 'Connected', lastSync: '5 mins ago' },
    { id: '3', name: 'Confluence', health: 45, status: 'Error', lastSync: '2 hours ago' },
  ]);

  const columns = [
    {
      title: 'Connector',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <strong>{text}</strong>,
    },
    {
      title: 'Health',
      dataIndex: 'health',
      key: 'health',
      render: (v: number) => <Tag color={v > 90 ? 'green' : 'red'}>{v}%</Tag>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (v: string) => <Badge status={v === 'Connected' ? 'success' : 'error'} text={v} />,
    },
    { title: 'Last Sync', dataIndex: 'lastSync', key: 'lastSync' },
    {
      title: 'Actions',
      key: 'actions',
      render: () => (
        <Space size="middle">
          <Button size="small">Sync Now</Button>
          <Button size="small" type="dashed">
            Settings
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <Card>
      <Title level={3}>Connector Center</Title>
      <Table columns={columns} dataSource={data} rowKey="id" />
    </Card>
  );
}

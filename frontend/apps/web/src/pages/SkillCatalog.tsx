/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, Typography, Layout } from 'antd';
import { BookOutlined, PlusOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { ApiClient } from '../api/client';

const { Title } = Typography;
const { Content } = Layout;

export const SkillCatalog: React.FC = () => {
  const [skills, setSkills] = useState<any[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    ApiClient.get('/skills').then(setSkills);
  }, []);

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (t: string, r: any) => (
        <b>
          {t} {r.isBuiltIn === 1 && <Tag color="blue">Built-in</Tag>}
        </b>
      ),
    },
    { title: 'Version', dataIndex: 'version', key: 'version' },
    { title: 'Category', dataIndex: 'category', key: 'category' },
    {
      title: 'Tags',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[]) => tags?.map((t) => <Tag key={t}>{t}</Tag>),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (t: string) => <Tag color={t === 'Active' ? 'green' : 'orange'}>{t}</Tag>,
    },
    {
      title: 'Actions',
      key: 'action',
      render: (_: any, r: any) => (
        <Button type="link" onClick={() => navigate(`/skills/${r.id}`)}>
          View Details
        </Button>
      ),
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh', padding: 24 }}>
      <Content>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
          <Title level={4}>
            <BookOutlined /> Skill Registry
          </Title>
          <Button type="primary" icon={<PlusOutlined />}>
            Create Custom Skill
          </Button>
        </div>
        <Card>
          <Table dataSource={skills} columns={columns} rowKey="id" />
        </Card>
      </Content>
    </Layout>
  );
};

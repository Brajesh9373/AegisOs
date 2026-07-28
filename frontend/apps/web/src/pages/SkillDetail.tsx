/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Tabs, Typography, Button, Space, Tag, Descriptions } from 'antd';
import { ArrowLeftOutlined, BookOutlined } from '@ant-design/icons';
import { ApiClient } from '../api/client';
import { PageContainer } from '../components/ui/PageContainer';
import { Panel } from '../components/ui/Panel';

const { Title, Text } = Typography;

export const SkillDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [skill, setSkill] = useState<any>(null);

  useEffect(() => {
    ApiClient.get(`/skills/${id}`).then(setSkill);
  }, [id]);

  if (!skill) return <div style={{ padding: 48, textAlign: 'center' }}>Loading...</div>;

  return (
    <PageContainer maxWidth={1200}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, paddingBottom: 16, borderBottom: '1px solid #E5E7EB' }}>
        <Space size="middle">
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/home')} style={{ color: '#111827', padding: 0 }} />
          <Title level={4} style={{ margin: 0, fontWeight: 600, color: '#111827' }}>
            <BookOutlined style={{ marginRight: 8, color: '#2563EB' }} /> {skill.name}
          </Title>
          <Tag style={{ background: '#EEF2FF', color: '#2563EB', border: 'none', fontWeight: 600 }}>v{skill.version}</Tag>
        </Space>
      </div>

      <Panel bodyStyle={{ padding: 24 }}>
        <Tabs
          items={[
            {
              key: '1',
              label: 'Overview',
              children: (
                <div style={{ paddingTop: 16 }}>
                  <Descriptions column={2} bordered size="small">
                    <Descriptions.Item label="Description" span={2}>
                      {skill.description}
                    </Descriptions.Item>
                    <Descriptions.Item label="Category">{skill.category}</Descriptions.Item>
                    <Descriptions.Item label="Status">
                      <Tag style={{ background: '#DCFCE7', color: '#15803D', border: 'none', fontWeight: 600 }}>{skill.status}</Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="Owner">{skill.owner}</Descriptions.Item>
                    <Descriptions.Item label="Created">
                      {new Date(skill.createdAt).toLocaleDateString()}
                    </Descriptions.Item>
                    <Descriptions.Item label="Tags" span={2}>
                      {skill.tags?.map((t: string) => <Tag key={t} style={{ background: '#F3F4F6', color: '#4B5563', border: 'none' }}>{t}</Tag>)}
                    </Descriptions.Item>
                  </Descriptions>
                </div>
              ),
            },
            {
              key: '2',
              label: 'Dependencies',
              children: (
                <div style={{ paddingTop: 16 }}>
                  <pre style={{ background: '#F8FAFC', padding: 16, borderRadius: 8, border: '1px solid #E5E7EB', color: '#374151' }}>{JSON.stringify(skill.dependencies, null, 2)}</pre>
                </div>
              ),
            },
            { 
              key: '3', 
              label: 'Input Schema', 
              children: (
                <div style={{ paddingTop: 16 }}>
                  <pre style={{ background: '#F8FAFC', padding: 16, borderRadius: 8, border: '1px solid #E5E7EB', color: '#374151' }}>{skill.inputSchema}</pre>
                </div>
              )
            },
            { 
              key: '4', 
              label: 'Output Schema', 
              children: (
                <div style={{ paddingTop: 16 }}>
                  <pre style={{ background: '#F8FAFC', padding: 16, borderRadius: 8, border: '1px solid #E5E7EB', color: '#374151' }}>{skill.outputSchema}</pre>
                </div>
              )
            },
            {
              key: '5',
              label: 'Version History',
              children: (
                <div style={{ paddingTop: 16 }}>
                  <Text type="secondary">Initial Version 1.0.0 created.</Text>
                </div>
              ),
            },
          ]}
        />
      </Panel>
    </PageContainer>
  );
};

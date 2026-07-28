import React, { useState, useEffect } from 'react';
import { Typography, List, Spin, Result, Avatar, Tag, Button } from 'antd';
import { BellOutlined } from '@ant-design/icons';
import { ApiClient } from '../api/client';
import { PageContainer } from '../components/ui/PageContainer';
import { Panel } from '../components/ui/Panel';

const { Title, Text } = Typography;

export function Notifications() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [notifications, setNotifications] = useState<any[]>([]);

  useEffect(() => {
    ApiClient.get('/operations/summary')
      .then(res => {
        setNotifications(res.activities.map((act: any, i: number) => ({
          id: i,
          title: act.text,
          time: act.time,
          type: 'info'
        })));
        setLoading(false);
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  }, []);

  if (loading) return <div style={{ padding: 100, textAlign: 'center' }}><Spin size="large" /></div>;
  if (error) return <Result status="error" title="Failed to load" extra={<Button onClick={() => window.location.reload()}>Retry</Button>} />;

  return (
    <PageContainer maxWidth={1400}>
      <Title level={3} style={{ margin: 0, fontWeight: 600, color: '#111827', marginBottom: 24 }}>
        <BellOutlined style={{ marginRight: 12 }} /> Notifications
      </Title>
      <Panel bodyStyle={{ padding: 0 }}>
        <List
          itemLayout="horizontal"
          dataSource={notifications}
          renderItem={item => (
            <List.Item style={{ padding: '16px 24px', borderBottom: '1px solid #E5E7EB' }}>
              <List.Item.Meta
                avatar={<Avatar icon={<BellOutlined />} style={{ backgroundColor: '#EEF2FF', color: '#2563EB' }} />}
                title={<Text style={{ fontWeight: 500, color: '#111827' }}>{item.title}</Text>}
                description={<Text style={{ color: '#6B7280', fontSize: 13 }}>{item.time}</Text>}
              />
              <Tag style={{ background: '#EEF2FF', color: '#2563EB', border: 'none', fontWeight: 600 }}>Unread</Tag>
            </List.Item>
          )}
        />
      </Panel>
    </PageContainer>
  );
}

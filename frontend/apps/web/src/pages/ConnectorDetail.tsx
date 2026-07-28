/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Tabs, Typography, Button, Space, Tag, Descriptions, List, Card, message } from 'antd';
import { ArrowLeftOutlined, ApiOutlined, CheckCircleOutlined, SyncOutlined } from '@ant-design/icons';
import { ApiClient } from '../api/client';
import { PageContainer } from '../components/ui/PageContainer';
import { Panel } from '../components/ui/Panel';

const { Title, Text } = Typography;

export const ConnectorDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [connector, setConnector] = useState<any>(null);
  const [testing, setTesting] = useState(false);
  const [discovering, setDiscovering] = useState(false);

  useEffect(() => {
    fetchConnector();
  }, [id]);

  const fetchConnector = () => {
    ApiClient.get(`/connectors/${id}`).then(setConnector);
  };

  const handleTest = async () => {
    setTesting(true);
    try {
      const res = await ApiClient.post(`/connectors/${id}/test`, {});
      message.success(res.message);
      fetchConnector();
    } catch (e: any) {
      ApiClient.handleError(e);
    } finally {
      setTesting(false);
    }
  };

  const handleDiscover = async () => {
    setDiscovering(true);
    try {
      await ApiClient.post(`/connectors/${id}/discover`, {});
      message.success('Schema discovered successfully.');
      fetchConnector();
    } catch (e: any) {
      ApiClient.handleError(e);
    } finally {
      setDiscovering(false);
    }
  };

  if (!connector) return <div style={{ padding: 48, textAlign: 'center' }}>Loading...</div>;

  return (
    <PageContainer maxWidth={1200}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, paddingBottom: 16, borderBottom: '1px solid #E5E7EB' }}>
        <Space size="middle">
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/home')} style={{ color: '#111827', padding: 0 }} />
          <Title level={4} style={{ margin: 0, fontWeight: 600, color: '#111827' }}>
            <ApiOutlined style={{ marginRight: 8, color: '#2563EB' }} /> {connector.name}
          </Title>
          <Tag style={{ background: '#EEF2FF', color: '#2563EB', border: 'none', fontWeight: 600 }}>{connector.type}</Tag>
          <Tag style={{ background: connector.status === 'Connected' ? '#DCFCE7' : '#FEF3C7', color: connector.status === 'Connected' ? '#15803D' : '#D97706', border: 'none', fontWeight: 600 }}>
            {connector.status}
          </Tag>
        </Space>
        <Space>
          <Button onClick={handleTest} loading={testing} icon={<CheckCircleOutlined />} style={{ fontWeight: 500 }}>
            Test Connection
          </Button>
          <Button
            type="primary"
            onClick={handleDiscover}
            loading={discovering}
            icon={<SyncOutlined />}
            style={{ background: '#2563EB', fontWeight: 500 }}
          >
            Discover Schema
          </Button>
        </Space>
      </div>

      <Panel bodyStyle={{ padding: 24 }}>
        <Tabs
          items={[
            {
              key: '1',
              label: 'Configuration',
              children: (
                <div style={{ paddingTop: 16 }}>
                  <Descriptions column={2} bordered size="small">
                    <Descriptions.Item label="Type">{connector.type}</Descriptions.Item>
                    <Descriptions.Item label="Category">{connector.category}</Descriptions.Item>
                    <Descriptions.Item label="Created">
                      {new Date(connector.createdAt).toLocaleDateString()}
                    </Descriptions.Item>
                    <Descriptions.Item label="Configuration Profile" span={2}>
                      <pre style={{ background: '#F8FAFC', padding: 16, borderRadius: 8, border: '1px solid #E5E7EB', color: '#374151' }}>{JSON.stringify(connector.config, null, 2)}</pre>
                    </Descriptions.Item>
                  </Descriptions>
                </div>
              ),
            },
            {
              key: '2',
              label: 'Discovered Schema',
              children: (
                <div style={{ paddingTop: 16 }}>
                  {connector.schemaData?.tables ? (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
                      <Card title="Tables" size="small" style={{ borderRadius: 8, border: '1px solid #E5E7EB' }}>
                        <List
                          size="small"
                          dataSource={connector.schemaData.tables}
                          renderItem={(t: any) => (
                            <List.Item style={{ color: '#4B5563' }}>
                              <b>{t}</b>
                            </List.Item>
                          )}
                        />
                      </Card>
                      <Card title="Relationships" size="small" style={{ borderRadius: 8, border: '1px solid #E5E7EB' }}>
                        <List
                          size="small"
                          dataSource={connector.schemaData.relationships}
                          renderItem={(r: any) => (
                            <List.Item>
                              <Tag color="purple">{r}</Tag>
                            </List.Item>
                          )}
                        />
                      </Card>
                      <Card title="Columns Map" size="small" style={{ gridColumn: 'span 2', borderRadius: 8, border: '1px solid #E5E7EB' }}>
                        <pre style={{ background: '#F8FAFC', padding: 16, borderRadius: 8, border: 'none', color: '#374151', margin: 0 }}>{JSON.stringify(connector.schemaData.columns, null, 2)}</pre>
                      </Card>
                    </div>
                  ) : (
                    <div style={{ padding: '40px 0', textAlign: 'center' }}>
                      <Text type="secondary">No schema data discovered. Run Discovery first.</Text>
                    </div>
                  )}
                </div>
              ),
            },
          ]}
        />
      </Panel>
    </PageContainer>
  );
};

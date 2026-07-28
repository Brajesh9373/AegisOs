import React from 'react';
import { Layout, Typography, Card, Button, Steps, Descriptions, Space } from 'antd';
import { useNavigate } from 'react-router-dom';

const { Content } = Layout;
const { Title } = Typography;

export const DemoMigrationPlan = () => {
  const navigate = useNavigate();
  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      
      <Content style={{ padding: '24px 48px' }}>
        <Steps current={3} items={[{title: 'Discovery'}, {title: 'Gap Analysis'}, {title: 'Mapping'}, {title: 'Plan'}, {title: 'Execution'}]} style={{ marginBottom: 32 }} />
        <Card title="Migration Execution Plan" bordered={false} style={{ boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
          <Descriptions bordered column={1}>
            <Descriptions.Item label="Estimated Time">14 minutes</Descriptions.Item>
            <Descriptions.Item label="Total Records">24,592</Descriptions.Item>
            <Descriptions.Item label="Dependencies">Customer must precede Sales Order</Descriptions.Item>
            <Descriptions.Item label="Rollback Plan">Automated transactional savepoints per 1000 records</Descriptions.Item>
            <Descriptions.Item label="Validation Strategy">Post-migration SHA-256 checksum on data dumps</Descriptions.Item>
          </Descriptions>

          <div style={{ marginTop: 24, textAlign: 'center' }}>
            <Button type="primary" size="large" onClick={() => navigate('/demo/execute')}>Execute Migration</Button>
          </div>
        </Card>
      </Content>
    </Layout>
  );
};

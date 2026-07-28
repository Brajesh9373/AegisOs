import React from 'react';
import { Layout, Typography, Card, Button, Steps, Space, Descriptions, Tag, message } from 'antd';
import { CheckCircleOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Content } = Layout;
const { Title, Text } = Typography;

export const DemoHumanApproval = () => {
  const navigate = useNavigate();

  const handleApprove = () => {
    message.success('Workforce and Solution Plan Approved. Employees have been generated.');
    navigate('/employees');
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      
      <Content style={{ padding: '24px 48px' }}>
        <Steps current={4} items={[{title: 'Goal'}, {title: 'Analysis'}, {title: 'Solution'}, {title: 'Workforce'}, {title: 'Approval'}]} style={{ marginBottom: 32 }} />
        <Card title="Executive Approval Required" bordered={false} style={{ boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
          <div style={{ textAlign: 'center', margin: '24px 0' }}>
            <CheckCircleOutlined style={{ fontSize: 64, color: '#1677ff' }} />
            <Title level={3} style={{ marginTop: 16 }}>Ready for Generation</Title>
            <Text type="secondary">Only after approval will Digital Employees become finalized.</Text>
          </div>

          <Descriptions bordered column={1} size="small" style={{ marginTop: 24, maxWidth: 600, margin: '0 auto' }}>
            <Descriptions.Item label="Business Goal">Migrate MySQL ERP to Frappe ERPNext</Descriptions.Item>
            <Descriptions.Item label="Solution Plan">4 Phases (Discovery to Verification)</Descriptions.Item>
            <Descriptions.Item label="Digital Employees">3 (SchemaScout, DataMapper, Migrator)</Descriptions.Item>
            <Descriptions.Item label="AI Confidence">
              <Tag color="green">94% Average</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Reasoning">Based on historical Frappe migration templates.</Descriptions.Item>
          </Descriptions>

          <div style={{ marginTop: 32, textAlign: 'center' }}>
            <Space size="large">
              <Button danger>Reject Plan</Button>
              <Button>Modify Design</Button>
              <Button type="primary" size="large" onClick={handleApprove}>Approve & Generate Employees</Button>
            </Space>
          </div>
        </Card>
      </Content>
    </Layout>
  );
};

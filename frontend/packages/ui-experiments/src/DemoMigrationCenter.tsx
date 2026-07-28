import React from 'react';
import { Layout, Typography, Card, Button, Steps, Space, Descriptions, Tag, Table } from 'antd';
import { useNavigate } from 'react-router-dom';

const { Content } = Layout;
const { Title, Text } = Typography;

export const DemoGapAnalysis = () => {
  const navigate = useNavigate();
  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      
      <Content style={{ padding: '24px 48px' }}>
        <Steps current={1} items={[{title: 'Discovery'}, {title: 'Gap Analysis'}, {title: 'Mapping'}, {title: 'Plan'}, {title: 'Execution'}]} style={{ marginBottom: 32 }} />
        <Card title="AI Gap Analysis Report" bordered={false} style={{ boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
          <Descriptions column={2} bordered size="small" style={{ marginBottom: 24 }}>
            <Descriptions.Item label="Source Schema">MySQL Custom ERP (45 Tables)</Descriptions.Item>
            <Descriptions.Item label="Destination Schema">Frappe ERPNext (Core DocTypes)</Descriptions.Item>
          </Descriptions>
          
          <Title level={5}>Identified Gaps & Risks</Title>
          <Table pagination={false} columns={[
            {title: 'Type', dataIndex: 'type', render: (t) => <Tag color={t==='Risk' ? 'red' : 'orange'}>{t}</Tag>},
            {title: 'Description', dataIndex: 'desc'},
            {title: 'AI Decision / Action Required', dataIndex: 'action'},
          ]} dataSource={[
            {key:1, type: 'Missing DocType', desc: 'Custom table "legacy_taxes" has no direct ERPNext equivalent.', action: 'Create Custom DocType "Legacy Tax"'},
            {key:2, type: 'Data Quality', desc: 'Table "customers" has 450 rows with invalid email formats.', action: 'Apply Regex Cleansing Rule'},
            {key:3, type: 'Risk', desc: 'Missing foreign key constraint on "orders.item_id".', action: 'Human Decision Required'},
          ]} />

          <div style={{ marginTop: 24, textAlign: 'right' }}>
            <Button type="primary" onClick={() => navigate('/demo/mapping')}>Proceed to AI Mapping Studio</Button>
          </div>
        </Card>
      </Content>
    </Layout>
  );
};

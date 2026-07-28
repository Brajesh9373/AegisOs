import React from 'react';
import { Layout, Typography, Card, Button, Steps, Space, Tag } from 'antd';
import { useNavigate } from 'react-router-dom';

const { Content } = Layout;
const { Title, Text, Paragraph } = Typography;

export const DemoAIAnalysis = () => {
  const navigate = useNavigate();
  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      
      <Content style={{ padding: '24px 48px' }}>
        <Steps current={1} items={[{title: 'Goal'}, {title: 'Analysis'}, {title: 'Solution'}, {title: 'Workforce'}, {title: 'Approval'}]} style={{ marginBottom: 32 }} />
        <Card title="AI Business Goal Analysis" bordered={false} style={{ boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
          <Title level={4}>Goal: Migrate an existing MySQL ERP database into the latest Frappe ERPNext.</Title>
          <div style={{ marginTop: 24 }}>
            <Text strong>AI Interpretation:</Text>
            <Paragraph>The objective is to perform a cross-platform data migration from a custom MySQL schema to the standard Frappe/ERPNext DocType architecture. This requires schema discovery, semantic mapping, data transformation, and strict relational integrity validation.</Paragraph>
            
            <Text strong>Extracted Constraints:</Text>
            <ul>
              <li>Source: MySQL (SQL)</li>
              <li>Destination: Frappe Framework (REST/RPC or direct DB)</li>
              <li>Priority: Data Integrity & Relationship Mapping</li>
            </ul>

            <Title level={5} style={{ marginTop: 24 }}>AI Recommendations</Title>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Card size="small" type="inner" title="1. Schema Discovery Agent">
                Deploy an agent to map the MySQL schema dynamically. <Tag color="green">Confidence: 98%</Tag>
              </Card>
              <Card size="small" type="inner" title="2. Semantic Mapping Agent">
                Deploy an agent using LLMs to map custom MySQL tables to standard Frappe DocTypes. <Tag color="green">Confidence: 92%</Tag>
              </Card>
              <Card size="small" type="inner" title="3. ETL Execution Pipeline">
                Utilize batched data streaming to migrate records safely. <Tag color="green">Confidence: 99%</Tag>
              </Card>
            </Space>
          </div>
          <div style={{ marginTop: 24, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => navigate('/projects')}>Reject</Button>
              <Button type="primary" onClick={() => navigate('/demo/solution-planner')}>Approve Recommendations & Generate Plan</Button>
            </Space>
          </div>
        </Card>
      </Content>
    </Layout>
  );
};

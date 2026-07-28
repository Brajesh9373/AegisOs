import React from 'react';
import { Layout, Typography, Card, Button, Steps, Space, Timeline, Tag } from 'antd';
import { useNavigate } from 'react-router-dom';

const { Content } = Layout;
const { Title, Text } = Typography;

export const DemoSolutionPlanner = () => {
  const navigate = useNavigate();
  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      
      <Content style={{ padding: '24px 48px' }}>
        <Steps current={2} items={[{title: 'Goal'}, {title: 'Analysis'}, {title: 'Solution'}, {title: 'Workforce'}, {title: 'Approval'}]} style={{ marginBottom: 32 }} />
        <Card title="Generated Solution Plan" bordered={false} style={{ boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
          <Title level={4}>ERP Migration Solution</Title>
          <Text type="secondary">Do NOT execute. This is a blueprint.</Text>
          
          <div style={{ marginTop: 24 }}>
            <Title level={5}>Implementation Phases</Title>
            <Timeline
              items={[
                { color: 'blue', children: <><Text strong>Phase 1: Discovery</Text><br/><Text>Extract MySQL Schema & Frappe DocTypes</Text></> },
                { color: 'purple', children: <><Text strong>Phase 2: Mapping</Text><br/><Text>AI semantic mapping of fields and tables</Text></> },
                { color: 'orange', children: <><Text strong>Phase 3: Transformation</Text><br/><Text>Data formatting and foreign key resolution</Text></> },
                { color: 'green', children: <><Text strong>Phase 4: Execution & Verification</Text><br/><Text>Data streaming and checksum validation</Text></> },
              ]}
            />
          </div>

          <div style={{ marginTop: 24 }}>
            <Title level={5}>Suggested Digital Employee Roles</Title>
            <Space>
              <Tag color="geekblue">Database Discovery Specialist</Tag>
              <Tag color="cyan">Semantic Mapper</Tag>
              <Tag color="magenta">ETL Operator</Tag>
              <Tag color="red">Quality Assurance Agent</Tag>
            </Space>
          </div>

          <div style={{ marginTop: 32, textAlign: 'right' }}>
            <Space>
              <Button>Edit Plan</Button>
              <Button type="primary" onClick={() => navigate('/demo/workforce')}>Finalize Plan & Design Workforce</Button>
            </Space>
          </div>
        </Card>
      </Content>
    </Layout>
  );
};

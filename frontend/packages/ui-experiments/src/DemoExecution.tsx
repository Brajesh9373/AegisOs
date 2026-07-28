import React, { useEffect, useState } from 'react';
import { Layout, Typography, Card, Button, Steps, Progress, Space } from 'antd';
import { useNavigate } from 'react-router-dom';

const { Content } = Layout;
const { Title, Text } = Typography;

export const DemoExecution = () => {
  const navigate = useNavigate();
  const [percent, setPercent] = useState(0);
  const [status, setStatus] = useState('Initializing Digital Employees...');

  useEffect(() => {
    let p = 0;
    const interval = setInterval(() => {
      p += 10;
      setPercent(p);
      if (p === 20) setStatus('SchemaScout: Reading Source MySQL...');
      if (p === 40) setStatus('DataMapper: Analyzing and Transforming...');
      if (p === 60) setStatus('Migrator: Writing to Frappe ERPNext API...');
      if (p === 80) setStatus('QA Agent: Verifying Record Counts...');
      if (p >= 100) {
        setStatus('Migration Completed Successfully.');
        clearInterval(interval);
      }
    }, 600);
    return () => clearInterval(interval);
  }, []);

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      
      <Content style={{ padding: '24px 48px' }}>
        <Steps current={4} items={[{title: 'Discovery'}, {title: 'Gap Analysis'}, {title: 'Mapping'}, {title: 'Plan'}, {title: 'Execution'}]} style={{ marginBottom: 32 }} />
        <Card title="Migration In Progress" bordered={false} style={{ boxShadow: '0 1px 2px rgba(0,0,0,0.05)', textAlign: 'center' }}>
          <Progress type="circle" percent={percent} style={{ margin: '24px 0' }} />
          <Title level={4}>{status}</Title>
          <Text type="secondary">Simulation driven by realistic demo data.</Text>

          {percent >= 100 && (
            <div style={{ marginTop: 24 }}>
              <Button type="primary" onClick={() => navigate('/demo/verification')}>View Verification Report</Button>
            </div>
          )}
        </Card>
      </Content>
    </Layout>
  );
};

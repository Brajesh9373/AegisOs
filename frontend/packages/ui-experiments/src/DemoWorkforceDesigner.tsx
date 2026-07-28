import React from 'react';
import { Layout, Typography, Card, Button, Steps, Space, Table, Tag } from 'antd';
import { useNavigate } from 'react-router-dom';

const { Content } = Layout;
const { Title, Text } = Typography;

export const DemoWorkforceDesigner = () => {
  const navigate = useNavigate();
  const data = [
    { key: '1', name: 'SchemaScout', role: 'Database Discovery Specialist', skills: ['MySQL Dialect', 'Frappe API'], manager: 'Migration Orchestrator' },
    { key: '2', name: 'DataMapper', role: 'Semantic Mapper', skills: ['Vector DB Search', 'Schema Matching'], manager: 'Migration Orchestrator' },
    { key: '3', name: 'Migrator', role: 'ETL Operator', skills: ['Data Streaming', 'Data Cleansing'], manager: 'Migration Orchestrator' },
  ];
  
  const columns = [
    { title: 'Digital Employee Name', dataIndex: 'name', key: 'name', render: (t:string) => <Text strong>{t}</Text> },
    { title: 'Role', dataIndex: 'role', key: 'role' },
    { title: 'Skills Assigned', dataIndex: 'skills', key: 'skills', render: (skills: string[]) => <>{skills.map(s => <Tag key={s}>{s}</Tag>)}</> },
    { title: 'Manager', dataIndex: 'manager', key: 'manager' },
  ];

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      
      <Content style={{ padding: '24px 48px' }}>
        <Steps current={3} items={[{title: 'Goal'}, {title: 'Analysis'}, {title: 'Solution'}, {title: 'Workforce'}, {title: 'Approval'}]} style={{ marginBottom: 32 }} />
        <Card title="AI Workforce Design" bordered={false} style={{ boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
          <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>The system has generated the optimal digital employees for this solution.</Text>
          <Table dataSource={data} columns={columns} pagination={false} />
          
          <div style={{ marginTop: 32, textAlign: 'right' }}>
            <Space>
              <Button>Add Employee</Button>
              <Button type="primary" onClick={() => navigate('/demo/approval')}>Review & Request Human Approval</Button>
            </Space>
          </div>
        </Card>
      </Content>
    </Layout>
  );
};

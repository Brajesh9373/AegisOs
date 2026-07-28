import React from 'react';
import { Layout, Typography, Card, Button, Steps, Space, Table, Tag } from 'antd';
import { useNavigate } from 'react-router-dom';

const { Content } = Layout;
const { Title, Text } = Typography;

export const DemoMappingStudio = () => {
  const navigate = useNavigate();
  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      
      <Content style={{ padding: '24px 48px' }}>
        <Steps current={2} items={[{title: 'Discovery'}, {title: 'Gap Analysis'}, {title: 'Mapping'}, {title: 'Plan'}, {title: 'Execution'}]} style={{ marginBottom: 32 }} />
        <Card title="AI Mapping Studio" bordered={false} style={{ boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
          <Table pagination={false} columns={[
            {title: 'Source Table (MySQL)', dataIndex: 'src'},
            {title: 'Destination DocType (Frappe)', dataIndex: 'dest'},
            {title: 'Confidence', dataIndex: 'conf', render: (c) => <Tag color={c>90?'green':'orange'}>{c}%</Tag>},
            {title: 'Transformations', dataIndex: 'trans'},
            {title: 'Actions', render: () => <Space><Button size="small">Edit</Button><Button size="small" type="primary">Approve</Button></Space>}
          ]} dataSource={[
            {key:1, src: 'legacy_customers', dest: 'Customer', conf: 98, trans: 'Map `cust_name` to `customer_name`'},
            {key:2, src: 'tbl_items', dest: 'Item', conf: 95, trans: 'Map `item_code` to `item_code`'},
            {key:3, src: 'sales_orders', dest: 'Sales Order', conf: 82, trans: 'Complex child-table mapping required'},
          ]} />

          <div style={{ marginTop: 24, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => navigate('/queue')}>Send to Human Queue</Button>
              <Button type="primary" onClick={() => navigate('/demo/migration-plan')}>Approve All & Generate Plan</Button>
            </Space>
          </div>
        </Card>
      </Content>
    </Layout>
  );
};

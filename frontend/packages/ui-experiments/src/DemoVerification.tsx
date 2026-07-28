import React from 'react';
import { Layout, Typography, Card, Button, Row, Col, Statistic, Space } from 'antd';
import { useNavigate } from 'react-router-dom';

const { Content } = Layout;
const { Title } = Typography;

export const DemoVerification = () => {
  const navigate = useNavigate();
  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      
      <Content style={{ padding: '24px 48px' }}>
        <Card title="Final Verification & Audit Report" bordered={false} style={{ boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={6}>
              <Statistic title="Source Records" value={24592} />
            </Col>
            <Col span={6}>
              <Statistic title="Destination Records" value={24590} />
            </Col>
            <Col span={6}>
              <Statistic title="Skipped (Invalid)" value={2} valueStyle={{ color: '#cf1322' }} />
            </Col>
            <Col span={6}>
              <Statistic title="Validation Status" value="PASSED" valueStyle={{ color: '#3f8600' }} />
            </Col>
          </Row>

          <div style={{ textAlign: 'center' }}>
            <Space>
              <Button type="primary" onClick={() => navigate('/demo/final')}>View Final Dashboard</Button>
            </Space>
          </div>
        </Card>
      </Content>
    </Layout>
  );
};

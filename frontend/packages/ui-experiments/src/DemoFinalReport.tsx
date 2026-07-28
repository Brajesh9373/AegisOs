import React from 'react';
import { Layout, Typography, Card, Button, Result } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
const { Content } = Layout;
const { Title, Text } = Typography;

export const DemoFinalReport = () => {
  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      
      <Content style={{ padding: '24px 48px' }}>
        <Card bordered={false} style={{ boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
          <Result
            status="success"
            title="Migration Successfully Completed!"
            subTitle="Execution Time: 14m 23s. 24,590 records migrated. 3 AI Decisions automated. 1 Human Intervention."
            extra={[
              <Button type="primary" key="dashboard">Return to Workspace</Button>,
              <Button key="pdf" icon={<DownloadOutlined />}>Download PDF Report</Button>,
            ]}
          />
        </Card>
      </Content>
    </Layout>
  );
};

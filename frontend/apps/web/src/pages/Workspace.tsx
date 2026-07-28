import React from 'react';
import { Row, Col, Card, Tabs, List, Typography, Badge, Button, Timeline, Tag } from 'antd';
const { Title, Text } = Typography;

export function Workspace() {
  return (
    <Row gutter={16} style={{ height: '100%' }}>
      <Col span={5}>
        <Card title="Employees" size="small" style={{ height: '100%', overflowY: 'auto' }}>
          <List
            size="small"
            dataSource={['Alice (Researcher)', 'Bob (Writer)', 'Charlie (Reviewer)']}
            renderItem={(item) => (
              <List.Item>
                <Badge status="success" text={item} />
              </List.Item>
            )}
          />
        </Card>
      </Col>

      <Col span={12}>
        <Card
          title="Current Task"
          size="small"
          style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
        >
          <Title level={4}>Draft Q3 Report</Title>
          <Text type="secondary">Assigned to: Bob (Writer)</Text>
          <div
            style={{ marginTop: 24, flex: 1, background: '#f5f5f5', padding: 16, }}
          >
            <p>
              <strong>System:</strong> Gathering initial context from knowledge base...
            </p>
            <p>
              <strong>Bob:</strong> Analyzing financial metrics.
            </p>
          </div>
          <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
            <Button type="primary">Provide Feedback</Button>
            <Button danger>Halt Execution</Button>
          </div>
        </Card>
      </Col>

      <Col span={7}>
        <Card size="small" style={{ height: '100%' }} bodyStyle={{ padding: 0, height: '100%' }}>
          <Tabs
            defaultActiveKey="1"
            centered
            items={[
              {
                key: '1',
                label: 'Knowledge',
                children: (
                  <div style={{ padding: 16 }}>
                    <Tag color="blue">Q3_Financials.pdf</Tag>
                    <Tag color="blue">2025_Guidance.docx</Tag>
                  </div>
                ),
              },
              {
                key: '2',
                label: 'Memory',
                children: (
                  <div style={{ padding: 16 }}>
                    <Text>Remembering tone preferences from previous report.</Text>
                  </div>
                ),
              },
              {
                key: '3',
                label: 'Audit',
                children: (
                  <div style={{ padding: 16 }}>
                    <Timeline
                      items={[
                        { children: 'Task created' },
                        { children: 'Alice attached context' },
                        { children: 'Bob started writing' },
                      ]}
                    />
                  </div>
                ),
              },
            ]}
          />
        </Card>
      </Col>
    </Row>
  );
}

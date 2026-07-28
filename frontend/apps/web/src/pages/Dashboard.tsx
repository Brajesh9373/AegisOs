import React from 'react';
import { Typography, Row, Col, Space, Table, Tag } from 'antd';
import { ArrowRightOutlined } from '@ant-design/icons';
import { Panel } from '../components/ui/Panel';
import { PageContainer } from '../components/ui/PageContainer';

const { Title, Text } = Typography;

export function Dashboard() {
  const metricCardStyle = {
    background: '#FFFFFF',
    border: '1px solid #E5E7EB',
    borderRadius: 12,
    padding: '20px 24px',
    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    display: 'flex',
    flexDirection: 'column' as const,
    height: '100%',
  };

  const sectionHeaderStyle = {
    fontSize: 13,
    fontWeight: 600,
    color: '#111827',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
    marginBottom: 16,
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  };

  return (
    <PageContainer maxWidth={1400}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <Title level={3} style={{ margin: 0, fontWeight: 600, letterSpacing: '-0.02em', color: '#111827', textTransform: 'uppercase' }}>
          Dashboard
        </Title>
      </div>

      {/* Metrics Row */}
      <Row gutter={24} style={{ marginBottom: 32 }}>
        {[
          { title: 'ACTIVE PROJECTS', value: '14' },
          { title: 'RUNNING AGENTS', value: '38' },
          { title: 'QUEUE ITEMS', value: '7' },
          { title: 'REPORTS READY', value: '3' },
        ].map((metric, i) => (
          <Col span={6} key={i}>
            <div style={metricCardStyle}>
              <Text style={{ fontSize: 12, fontWeight: 600, color: '#6B7280', marginBottom: 12 }}>{metric.title}</Text>
              <Text style={{ fontSize: 36, fontWeight: 600, color: '#111827', lineHeight: 1, marginBottom: 24 }}>{metric.value}</Text>
              <div style={{ marginTop: 'auto', borderTop: '1px solid #E5E7EB', paddingTop: 12 }}>
                <Text style={{ fontSize: 12, color: '#6B7280', cursor: 'pointer' }}>View All <ArrowRightOutlined style={{ fontSize: 10 }} /></Text>
              </div>
            </div>
          </Col>
        ))}
      </Row>

      <Row gutter={24}>
        {/* Left Column */}
        <Col span={16}>
          {/* Projects */}
          <div style={{ marginBottom: 32 }}>
            <div style={sectionHeaderStyle}>
              <span>PROJECTS</span>
            </div>
            <Panel bodyStyle={{ padding: 0, border: '1px solid #E5E7EB', borderRadius: 12, overflow: 'hidden', background: '#FFFFFF' }}>
              <Table
                pagination={false}
                dataSource={[
                  { key: '1', name: 'Finance Automation', customer: 'VNU', status: 'Running', progress: '75%' },
                  { key: '2', name: 'HR Onboarding', customer: 'TechCo', status: 'Waiting', progress: '40%' },
                  { key: '3', name: 'Sales Pipeline', customer: 'VNU', status: 'Running', progress: '92%' },
                ]}
                columns={[
                  { title: 'NAME', dataIndex: 'name', key: 'name', render: (text) => <Text style={{ fontWeight: 500, color: '#111827' }}>{text}</Text> },
                  { title: 'CUSTOMER', dataIndex: 'customer', key: 'customer', render: (text) => <Text style={{ color: '#6B7280' }}>{text}</Text> },
                  { title: 'STATUS', dataIndex: 'status', key: 'status', render: (text) => <Text style={{ color: '#6B7280' }}>{text}</Text> },
                  { title: 'PROGRESS', dataIndex: 'progress', key: 'progress', render: (text) => <Text style={{ fontWeight: 600, color: '#2563EB' }}>{text}</Text> },
                ]}
              />
            </Panel>
          </div>

          {/* Execution Queue */}
          <div>
            <div style={sectionHeaderStyle}>EXECUTION QUEUE</div>
            <Panel bodyStyle={{ padding: '8px 24px', background: '#FFFFFF', border: '1px solid #E5E7EB', borderRadius: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', padding: '16px 0', borderBottom: '1px solid #E5E7EB' }}>
                <Tag style={{ background: '#EEF2FF', color: '#2563EB', border: 'none', fontWeight: 600, width: 80, textAlign: 'center' }}>RUNNING</Tag>
                <Text style={{ color: '#111827', marginLeft: 16 }}>Invoice Processing - Batch #42</Text>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', padding: '16px 0' }}>
                <Tag style={{ background: '#F8FAFC', color: '#6B7280', border: '1px solid #E5E7EB', fontWeight: 600, width: 80, textAlign: 'center' }}>WAITING</Tag>
                <Text style={{ color: '#111827', marginLeft: 16 }}>Report Generation - Q3 Summary</Text>
              </div>
            </Panel>
          </div>
        </Col>

        {/* Right Column */}
        <Col span={8}>
          {/* Activity */}
          <div style={{ marginBottom: 32 }}>
            <div style={sectionHeaderStyle}>ACTIVITY</div>
            <Panel bodyStyle={{ padding: 20, background: '#FFFFFF', border: '1px solid #E5E7EB', borderRadius: 12 }}>
              <Space direction="vertical" style={{ width: '100%' }} size={16}>
                {['Agent task completed', 'New project approved', 'Report generated', 'Tool access granted'].map((text, i) => (
                  <Text key={i} style={{ color: '#6B7280', display: 'block' }}>{text}</Text>
                ))}
              </Space>
            </Panel>
          </div>

          {/* Reports */}
          <div>
            <div style={sectionHeaderStyle}>REPORTS</div>
            <Panel bodyStyle={{ padding: 24, background: '#FFFFFF', border: '1px solid #E5E7EB', borderRadius: 12 }}>
              <Text style={{ color: '#6B7280' }}>No reports loaded in dashboard context.</Text>
            </Panel>
          </div>
        </Col>
      </Row>
    </PageContainer>
  );
}

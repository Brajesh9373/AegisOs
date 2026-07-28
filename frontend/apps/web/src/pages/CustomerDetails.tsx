import React, { useState } from 'react';
import { Typography, Row, Col, Button, Space, Tag, ConfigProvider, theme, Tabs, List, Divider, Avatar } from 'antd';
import { ArrowLeftOutlined, BankOutlined, MailOutlined, PhoneOutlined, GlobalOutlined, WarningOutlined, UserOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { Panel } from '../components/ui/Panel';
import { SectionHeader } from '../components/ui/SectionHeader';
import { LifecycleStepper } from '../components/ui/LifecycleStepper';
import { ExecutiveCard } from '../components/ui/ExecutiveCard';

const { Title, Text } = Typography;

export function CustomerDetails() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState('overview');

  const wipContent = (
    <div style={{ padding: 48, textAlign: 'center', border: '1px dashed #d9d9d9' }}>
      <WarningOutlined style={{ fontSize: 32, color: '#F59E0B', marginBottom: 16 }} />
      <Title level={4} style={{ margin: 0 }}>Work In Progress</Title>
      <Text type="secondary">Backend Integration Pending</Text>
    </div>
  );

  const overviewContent = (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={4}><ExecutiveCard title="Health Score" value="98/100" valueColor="#22C55E" /></Col>
        <Col span={4}><ExecutiveCard title="Revenue" value="$4.2M" valueColor="#2563EB" /></Col>
        <Col span={4}><ExecutiveCard title="Win Rate" value="84%" valueColor='#111827' bg='#FFFFFF' borderColor='#E5E7EB' /></Col>
        <Col span={4}><ExecutiveCard title="Projects" value="6" valueColor='#111827' bg='#FFFFFF' borderColor='#E5E7EB' /></Col>
        <Col span={4}><ExecutiveCard title="YTD Revenue" value="$842k" valueColor="#22C55E" bg='#FFFFFF' borderColor='#E5E7EB' /></Col>
        <Col span={4}><ExecutiveCard title="Est. ACV" value="$1.2M" valueColor="#2563EB" bg='#FFFFFF' borderColor='#E5E7EB' /></Col>
        <Col span={4}><ExecutiveCard title="Knowledge Size" value="12.4 GB" valueColor='#111827' bg='#FFFFFF' borderColor='#E5E7EB' /></Col>
        <Col span={4}><ExecutiveCard title="Memory Size" value="1.1 GB" valueColor='#111827' bg='#FFFFFF' borderColor='#E5E7EB' /></Col>
        <Col span={4}><ExecutiveCard title="Departments" value="4" valueColor='#111827' bg='#FFFFFF' borderColor='#E5E7EB' /></Col>
        <Col span={4}><ExecutiveCard title="Employees" value="14,020" valueColor='#111827' bg='#FFFFFF' borderColor='#E5E7EB' /></Col>
        <Col span={4}><ExecutiveCard title="Compliance" value="SOC2" valueColor='#111827' bg='#FFFFFF' borderColor='#E5E7EB' /></Col>
        <Col span={4}><ExecutiveCard title="Last Activity" value="2 hrs ago" valueColor='#6B7280' /></Col>
      </Row>

      <Row gutter={24}>
        <Col span={16}>
          <SectionHeader title="Company Overview" />
          <Panel bodyStyle={{ padding: 24, marginBottom: 24 }}>
            <Text>VNU is a leading manufacturer of industrial goods. They are looking to modernize their legacy Oracle billing infrastructure to cloud-native PostgreSQL.</Text>
          </Panel>
          
          <SectionHeader title="Key Contacts" />
          <Panel bodyStyle={{ padding: 0 }}>
            <List
              dataSource={[
                { name: 'Current User', role: 'VP of Engineering', email: 'sarah@vnu.com', phone: '+1 555-0192' },
                { name: 'Sarah Jenkins', role: 'CTO', email: 'sarah@vnu.com', phone: '+1 555-0193' }
              ]}
              renderItem={item => (
                <List.Item style={{ padding: '16px 24px' }}>
                  <List.Item.Meta
                    avatar={<Avatar icon={<UserOutlined />} />}
                    title={<Text strong>{item.name} <Tag color="blue" style={{ marginLeft: 8 }}>{item.role}</Tag></Text>}
                    description={
                      <Space direction="vertical" size="small" style={{ marginTop: 8 }}>
                        <Text type="secondary" style={{ fontSize: 12 }}><MailOutlined /> {item.email}</Text>
                        <Text type="secondary" style={{ fontSize: 12 }}><PhoneOutlined /> {item.phone}</Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Panel>
        </Col>
        <Col span={8}>
          <SectionHeader title="Metadata" />
          <Panel bodyStyle={{ padding: 24 }}>
            <Title level={5} style={{ marginBottom: 16 }}>Industry</Title>
            <div style={{ marginBottom: 16 }}>Manufacturing</div>
            
            <Title level={5} style={{ marginBottom: 16, marginTop: 24 }}>HQ Location</Title>
            <div style={{ marginBottom: 16 }}><GlobalOutlined /> New York, NY</div>

            <Divider />

            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                <Text type="secondary">Opportunities</Text>
                <Text strong>14</Text>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                <Text type="secondary">Active Projects</Text>
                <Text strong>6</Text>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                <Text type="secondary">Knowledge Documents</Text>
                <Text strong>3,042</Text>
              </div>
            </Space>
          </Panel>
        </Col>
      </Row>
    </div>
  );

  const tabItems = [
    { key: 'overview', label: 'Overview', children: overviewContent },
    { key: 'contacts', label: 'Contacts', children: wipContent },
    { key: 'projects', label: 'Projects', children: wipContent },
    { key: 'opportunities', label: 'Opportunities', children: wipContent },
    { key: 'documents', label: 'Documents', children: wipContent },
    { key: 'contracts', label: 'Contracts', children: wipContent },
    { key: 'timeline', label: 'Timeline', children: wipContent },
    { key: 'knowledge', label: 'Knowledge', children: wipContent },
    { key: 'memory', label: 'Memory', children: wipContent },
    { key: 'settings', label: 'Settings', children: wipContent },
  ];

  return (
    
      <div style={{ background: '#F8FAFC', minHeight: '100vh', padding: '24px 32px' }}>
        <div style={{ maxWidth: 1600, margin: '0 auto' }}>
          <LifecycleStepper currentStage="Lead" />
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
            <Space direction="vertical" size="small">
              <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/customers')} style={{ padding: 0 }}>Back to Customers</Button>
              <Space align="center" size="middle">
                <div style={{ width: 48, height: 48, background: '#FFFFFF', border: '1px solid #f0f0f0', display: 'flex', alignItems: 'center', justifyContent: 'center', }}>
                  <BankOutlined style={{ fontSize: 24, color: '#2563EB' }} />
                </div>
                <div>
                  <Title level={3} style={{ margin: 0, fontWeight: 600 }}>VNU</Title>
                  <Text type="secondary">Customer ID: {id || 'cust-1'}</Text>
                </div>
              </Space>
            </Space>
            <Space>
              <Button type="primary" style={{ fontWeight: 600, background: '#2563EB' }} onClick={() => navigate('/opportunities/new')}>Create Opportunity</Button>
              <Button style={{ fontWeight: 600 }}>Edit Customer</Button>
            </Space>
          </div>

          <Tabs 
            activeKey={activeTab} 
            onChange={setActiveTab} 
            items={tabItems}
          />

        </div>
      </div>
    
  );
}

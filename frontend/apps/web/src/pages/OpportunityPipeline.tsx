import React from 'react';
import { Typography, Row, Col, Tag, Space, Avatar, Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import { BankOutlined, ClockCircleOutlined, DollarOutlined, CheckCircleOutlined, WarningOutlined, PlusOutlined } from '@ant-design/icons';
import { PageContainer } from '../components/ui/PageContainer';

const { Title, Text } = Typography;

export function OpportunityPipeline() {
  const navigate = useNavigate();

  const columns = [
    { id: 'lead', title: 'Lead' },
    { id: 'qualified', title: 'Qualified' },
    { id: 'discovery', title: 'Discovery' },
    { id: 'proposal', title: 'Proposal' },
    { id: 'negotiation', title: 'Negotiation' },
    { id: 'won', title: 'Won' },
    { id: 'lost', title: 'Lost' }
  ];

  const opportunities = [
    {
      id: 'opp-1',
      stage: 'discovery',
      company: 'VNU',
      name: 'DB Modernization',
      value: '$57,385',
      probability: '60%',
      owner: 'Current User',
      lastActivity: '2 hours ago',
      priority: 'High',
      health: 'Green'
    },
    {
      id: 'opp-2',
      stage: 'qualified',
      company: 'VNU',
      name: 'Data Lake Migration',
      value: '$120,000',
      probability: '20%',
      owner: 'Sarah Jenkins',
      lastActivity: '1 day ago',
      priority: 'Medium',
      health: 'Yellow'
    }
  ];

  return (
    <PageContainer maxWidth={1800}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 32 }}>
        <Title level={3} style={{ margin: 0, fontWeight: 600, color: '#111827' }}>Opportunity Pipeline</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/opportunities/new')} style={{ fontWeight: 500, background: '#2563EB' }}>New Opportunity</Button>
      </div>

      <div style={{ display: 'flex', overflowX: 'auto', paddingBottom: 24, gap: 16 }}>
        {columns.map(col => (
          <div key={col.id} style={{ minWidth: 280, background: '#FFFFFF', border: '1px solid #E5E7EB', borderRadius: 12, display: 'flex', flexDirection: 'column', boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)' }}>
            <div style={{ padding: '14px 16px', borderBottom: '1px solid #E5E7EB', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text style={{ fontWeight: 600, textTransform: 'uppercase', fontSize: 11, letterSpacing: '0.05em', color: '#6B7280' }}>{col.title}</Text>
              <Tag style={{ margin: 0, background: '#F3F4F6', color: '#6B7280', border: 'none', fontWeight: 600 }}>
                {opportunities.filter(o => o.stage === col.id).length}
              </Tag>
            </div>
            <div style={{ padding: 12, flex: 1, minHeight: 500 }}>
              {opportunities.filter(o => o.stage === col.id).map(opp => (
                <div 
                  key={opp.id} 
                  onClick={() => navigate(`/opportunities/${opp.id}`)}
                  style={{ 
                    background: '#FFFFFF', 
                    border: '1px solid #E5E7EB', 
                    borderRadius: 10,
                    padding: 16, 
                    marginBottom: 12, 
                    cursor: 'pointer',
                    transition: 'border-color 0.2s, box-shadow 0.2s',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#2563EB'; e.currentTarget.style.boxShadow = '0 4px 12px rgba(37, 99, 235, 0.1)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#E5E7EB'; e.currentTarget.style.boxShadow = 'none'; }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <Space>
                      <Avatar size="small" icon={<BankOutlined />} style={{ background: '#EEF2FF', color: '#2563EB' }} />
                      <Text style={{ fontWeight: 600, fontSize: 12, color: '#111827' }}>{opp.company}</Text>
                    </Space>
                    {opp.health === 'Green' ? <CheckCircleOutlined style={{ color: '#16A34A' }} /> : <WarningOutlined style={{ color: '#D97706' }} />}
                  </div>
                  
                  <Text style={{ display: 'block', marginBottom: 12, color: '#111827', fontWeight: 500 }}>{opp.name}</Text>
                  
                  <Row gutter={8} style={{ marginBottom: 12 }}>
                    <Col span={12}>
                      <Text style={{ color: '#6B7280', fontSize: 10, display: 'block', textTransform: 'uppercase', fontWeight: 600 }}>VALUE</Text>
                      <Text style={{ color: '#16A34A', fontSize: 12, fontWeight: 600 }}><DollarOutlined /> {opp.value}</Text>
                    </Col>
                    <Col span={12}>
                      <Text style={{ color: '#6B7280', fontSize: 10, display: 'block', textTransform: 'uppercase', fontWeight: 600 }}>PROBABILITY</Text>
                      <Text style={{ color: '#2563EB', fontSize: 12, fontWeight: 600 }}>{opp.probability}</Text>
                    </Col>
                  </Row>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid #E5E7EB', paddingTop: 12 }}>
                    <Space>
                      <Avatar size="small" style={{ background: '#EEF2FF', color: '#2563EB', fontSize: 10, fontWeight: 600 }}>JD</Avatar>
                      <Text style={{ color: '#6B7280', fontSize: 10 }}>{opp.owner}</Text>
                    </Space>
                    <Space>
                      <ClockCircleOutlined style={{ color: '#9CA3AF', fontSize: 10 }} />
                      <Text style={{ color: '#9CA3AF', fontSize: 10 }}>{opp.lastActivity}</Text>
                    </Space>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </PageContainer>
  );
}

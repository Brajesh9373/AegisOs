import React from 'react';
import { Typography, Space, Divider, Progress, Avatar } from 'antd';
import { UserOutlined, DollarOutlined, WarningOutlined, PercentageOutlined, ClockCircleOutlined, CalendarOutlined, BankOutlined, TagOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import { Panel } from './Panel';

const { Text, Title } = Typography;

export const OpportunitySidebar = () => {
  return (
    <Panel bodyStyle={{ padding: 24, height: '100%', background: '#FFFFFF', border: '1px solid #E5E7EB' }}>
      <Title level={5} style={{ marginTop: 0, marginBottom: 24, fontWeight: 600, color: '#111827' }}>Deal Context</Title>
      
      <Space direction="vertical" style={{ width: '100%' }} size={24}>
        
        {/* SECTION 1: PROFILE */}
        <div>
          <Text style={{ color: '#6B7280', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: 12 }}>Profile</Text>
          <div style={{ background: '#F8FAFC', padding: 12, borderRadius: 10, border: '1px solid #E5E7EB' }}>
            <Space align="start">
              <Avatar icon={<BankOutlined />} style={{ background: '#2563EB', color: '#FFFFFF' }} />
              <div>
                <Text style={{ fontWeight: 600, color: '#111827', display: 'block' }}>VNU</Text>
                <Text style={{ color: '#6B7280', fontSize: 13 }}><TagOutlined /> Database Modernization</Text>
              </div>
            </Space>
          </div>
        </div>

        {/* SECTION 2: METRICS */}
        <div>
          <Text style={{ color: '#6B7280', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: 12 }}>Key Metrics</Text>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div style={{ border: '1px solid #E5E7EB', padding: '10px 12px', borderRadius: 8, background: '#FFFFFF' }}>
              <Text style={{ color: '#6B7280', fontSize: 11, display: 'block', marginBottom: 4 }}><DollarOutlined /> Budget</Text>
              <Text style={{ color: '#16A34A', fontWeight: 600, fontSize: 14 }}>$57,385</Text>
            </div>
            <div style={{ border: '1px solid #E5E7EB', padding: '10px 12px', borderRadius: 8, background: '#FFFFFF' }}>
              <Text style={{ color: '#6B7280', fontSize: 11, display: 'block', marginBottom: 4 }}><PercentageOutlined /> Match</Text>
              <Text style={{ color: '#2563EB', fontWeight: 600, fontSize: 14 }}>94%</Text>
            </div>
          </div>
        </div>

        {/* SECTION 3: RISK & STATUS */}
        <div>
          <Text style={{ color: '#6B7280', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: 12 }}>Execution Status</Text>
          <Space direction="vertical" style={{ width: '100%', background: '#FFFFFF', border: '1px solid #E5E7EB', padding: 16, borderRadius: 10 }} size={16}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Space><SafetyCertificateOutlined style={{ color: '#6B7280' }} /><Text style={{ color: '#111827', fontSize: 13, fontWeight: 500 }}>Risk Level</Text></Space>
              <Text style={{ color: '#F59E0B', fontWeight: 600, fontSize: 13, background: '#FEF3C7', padding: '2px 8px', borderRadius: 12 }}>Medium</Text>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <Space><ClockCircleOutlined style={{ color: '#6B7280' }} /><Text style={{ color: '#111827', fontSize: 13, fontWeight: 500 }}>Lifecycle</Text></Space>
                <Text style={{ color: '#6B7280', fontSize: 12 }}>Stage 6 / 10</Text>
              </div>
              <Progress percent={60} strokeColor="#2563EB" trailColor="#E5E7EB" showInfo={false} size="small" />
            </div>
          </Space>
        </div>

        {/* SECTION 4: OWNERSHIP */}
        <div>
          <Text style={{ color: '#6B7280', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: 12 }}>Ownership</Text>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Space>
              <Avatar icon={<UserOutlined />} style={{ background: '#F8FAFC', color: '#6B7280', border: '1px solid #E5E7EB' }} size="small" />
              <Text style={{ color: '#111827', fontWeight: 500, fontSize: 13 }}>Current User</Text>
            </Space>
            <Text style={{ color: '#6B7280', fontSize: 12 }}><CalendarOutlined /> Oct 1</Text>
          </div>
        </div>

      </Space>
    </Panel>
  );
};

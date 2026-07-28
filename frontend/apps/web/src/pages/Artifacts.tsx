import React from 'react';
import { Typography } from 'antd';
import { FileTextOutlined, ToolOutlined } from '@ant-design/icons';
import { PageContainer } from '../components/ui/PageContainer';

const { Title, Text } = Typography;

export function Artifacts() {
  return (
    <PageContainer maxWidth={1400}>
      <div style={{ opacity: 0.45, pointerEvents: 'none', userSelect: 'none' }}>
        <Title level={3} style={{ margin: 0, fontWeight: 600, color: '#111827', marginBottom: 24 }}>
          <FileTextOutlined style={{ marginRight: 12 }} /> Artifacts
        </Title>
        <div style={{
          background: '#fff',
          borderRadius: 12,
          border: '1px solid #E5E7EB',
          padding: '80px 40px',
          textAlign: 'center',
        }}>
          <ToolOutlined style={{ fontSize: 48, color: '#9CA3AF', marginBottom: 16 }} />
          <Title level={4} style={{ color: '#6B7280', fontWeight: 500, margin: '0 0 8px' }}>
            Under Development
          </Title>
          <Text style={{ color: '#9CA3AF', fontSize: 14, maxWidth: 480, display: 'inline-block' }}>
            This section will serve as the centralized knowledge repository for the entire organization — aggregating documents, designs, code assets, configurations, and deliverables across all projects and teams.
          </Text>
        </div>
      </div>
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        background: '#FEF3C7',
        border: '1px solid #F59E0B',
        borderRadius: 8,
        padding: '10px 20px',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        zIndex: 10,
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
      }}>
        <ToolOutlined style={{ color: '#D97706' }} />
        <Text style={{ color: '#92400E', fontWeight: 500, fontSize: 13 }}>
          This tab is under development. The full company knowledge base will be available here.
        </Text>
      </div>
    </PageContainer>
  );
}

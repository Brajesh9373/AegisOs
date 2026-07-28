import React from 'react';
import { Typography, Input, Button } from 'antd';
import { RobotOutlined } from '@ant-design/icons';
import { PageContainer } from '../components/ui/PageContainer';
import { Panel } from '../components/ui/Panel';

const { Title, Text } = Typography;

export function AIAgentChat() {
  return (
    <PageContainer maxWidth={1400}>
      <div style={{ marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0, fontWeight: 600, color: '#111827' }}>
          <RobotOutlined style={{ marginRight: 10, color: '#2563EB' }} />
          AI Agent Chat
        </Title>
        <Text style={{ color: '#6B7280', display: 'block', marginTop: 4 }}>
          Discuss ticket escalations directly with the AI agent that flagged the item.
        </Text>
      </div>

      <Panel bodyStyle={{ padding: 0, background: '#FFFFFF', border: '1px solid #E5E7EB', borderRadius: 12, overflow: 'hidden' }}>
        {/* Chat header */}
        <div style={{ padding: '14px 20px', borderBottom: '1px solid #E5E7EB', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 32, height: 32, borderRadius: 8, background: '#EEF2FF', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <RobotOutlined style={{ color: '#2563EB' }} />
            </div>
            <div>
              <Text style={{ fontWeight: 600, color: '#111827', display: 'block', fontSize: 13 }}>FinanceAgent-v2</Text>
              <Text style={{ color: '#9CA3AF', fontSize: 11 }}>ECMS-1024 · Invoice mismatch</Text>
            </div>
          </div>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#22C55E' }} />
        </div>

        {/* Messages */}
        <div style={{ padding: 20, minHeight: 400, display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Agent message */}
          <div style={{ display: 'flex', gap: 10, maxWidth: '75%' }}>
            <div style={{ width: 28, height: 28, borderRadius: 8, background: '#EEF2FF', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <RobotOutlined style={{ color: '#2563EB', fontSize: 12 }} />
            </div>
            <div>
              <div style={{ background: '#F3F4F6', padding: '10px 14px', borderRadius: '4px 12px 12px 12px', fontSize: 13, color: '#111827', lineHeight: 1.6 }}>
                Hello! I'm FinanceAgent-v2. I escalated ticket ECMS-1024 for your review. Here's what I found:
                <br /><br />
                Invoice total ($12,450) does not match PO amount ($11,800). Requires manual verification before payment release.
                <br /><br />
                How can I help you with this ticket?
              </div>
              <Text style={{ color: '#9CA3AF', fontSize: 11, marginTop: 4, display: 'block' }}>09:14 AM</Text>
            </div>
          </div>

          {/* User message */}
          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', maxWidth: '75%', alignSelf: 'flex-end' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ background: '#2563EB', padding: '10px 14px', borderRadius: '12px 4px 12px 12px', fontSize: 13, color: '#FFFFFF', lineHeight: 1.6 }}>
                What's the discrepancy amount?
              </div>
              <Text style={{ color: '#9CA3AF', fontSize: 11, marginTop: 4, display: 'block' }}>09:15 AM</Text>
            </div>
          </div>

          {/* Agent response */}
          <div style={{ display: 'flex', gap: 10, maxWidth: '75%' }}>
            <div style={{ width: 28, height: 28, borderRadius: 8, background: '#EEF2FF', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <RobotOutlined style={{ color: '#2563EB', fontSize: 12 }} />
            </div>
            <div>
              <div style={{ background: '#F3F4F6', padding: '10px 14px', borderRadius: '4px 12px 12px 12px', fontSize: 13, color: '#111827', lineHeight: 1.6 }}>
                The discrepancy is $650 (5.5% over PO). I detected the mismatch during automated invoice reconciliation. My confidence was only 34% because the vendor has a history of partial shipments that sometimes result in legitimate amount variations.
                <br /><br />
                Would you like me to pull the original PO and delivery receipts for comparison?
              </div>
              <Text style={{ color: '#9CA3AF', fontSize: 11, marginTop: 4, display: 'block' }}>09:15 AM</Text>
            </div>
          </div>
        </div>

        {/* Input bar */}
        <div style={{ padding: '12px 20px', borderTop: '1px solid #E5E7EB', display: 'flex', gap: 10 }}>
          <Input placeholder="Ask about this ticket..." style={{ flex: 1, borderRadius: 8, background: '#F8FAFC' }} />
          <Button type="primary" style={{ background: '#2563EB', borderRadius: 8 }}>Send</Button>
        </div>
      </Panel>
    </PageContainer>
  );
}

import React from 'react';
import { Typography, Tabs, Input, Timeline as AntTimeline, Space, Button, Tag } from 'antd';
import { MessageOutlined, FileTextOutlined, HistoryOutlined, SafetyCertificateOutlined, FilePdfOutlined, DownloadOutlined, EyeOutlined, MailOutlined, BookOutlined, DatabaseOutlined, SyncOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { Panel } from './Panel';

const { Text } = Typography;
const { TextArea } = Input;
const { TabPane } = Tabs;

export const ActivityCenter = () => {
  return (
    <Panel bodyStyle={{ padding: 16, height: '100%', overflowY: 'auto' }}>
      <Tabs defaultActiveKey="1" size="small" tabBarStyle={{ color: '#6B7280' }}>
        
        <TabPane tab={<><MessageOutlined /> Discuss</>} key="1">
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <div style={{ flex: 1, marginBottom: 16, overflowY: 'auto' }}>
              <Text style={{ color: '#6B7280', fontSize: 12, display: 'block', textAlign: 'center', marginBottom: 16 }}>Oct 1 - Discovery Started</Text>
              <div style={{ marginBottom: 16 }}>
                <Text style={{ color: '#2563EB', fontSize: 12, fontWeight: 600 }}>General AI</Text>
                <Text style={{ fontSize: 12, display: 'block' }}>I have parsed the RFP and identified 3 key risks. Need human clarification on the Oracle licensing.</Text>
              </div>
              <div style={{ marginBottom: 16 }}>
                <Text style={{ color: '#6B7280', fontSize: 12, fontWeight: 600 }}>Current User</Text>
                <Text style={{ fontSize: 12, display: 'block' }}>We have enterprise BYOL. Please adjust budget.</Text>
              </div>
            </div>
            <TextArea placeholder="Reply to thread..." rows={2} style={{ background: '#FFFFFF', borderColor: '#E5E7EB' }} />
          </div>
        </TabPane>

        <TabPane tab={<><FileTextOutlined /> Docs</>} key="2">
          <Space direction="vertical" style={{ width: '100%' }}>
            {[
              { name: 'Original_RFP.pdf', type: 'RFP', ver: 'v1.0', owner: 'VNU', status: 'Parsed' },
              { name: 'Architecture.pdf', type: 'Architecture', ver: 'v2.1', owner: 'General AI', status: 'Active' },
              { name: 'RFQ_v2_Final.pdf', type: 'RFQ', ver: 'v2.0', owner: 'Current User', status: 'Approved' },
              { name: 'Proposal-Signed.pdf', type: 'Proposal', ver: 'v1.0', owner: 'Current User', status: 'Signed' }
            ].map(doc => (
              <div key={doc.name} style={{ borderBottom: '1px solid #f0f0f0', paddingBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <Space><FilePdfOutlined style={{ color: '#EF4444' }} /><Text style={{ fontSize: 12, fontWeight: 600 }}>{doc.name}</Text></Space>
                  <Tag color="blue">{doc.type}</Tag>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Space size="small">
                    <Text style={{ color: '#6B7280', fontSize: 10 }}>{doc.ver}</Text>
                    <Text style={{ color: '#6B7280', fontSize: 10 }}>{doc.owner}</Text>
                    <Text style={{ color: '#22C55E', fontSize: 10 }}>{doc.status}</Text>
                  </Space>
                  <Space>
                    <Button type="text" size="small" icon={<EyeOutlined />} style={{ color: '#2563EB' }} title="Preview" />
                    <Button type="text" size="small" icon={<DownloadOutlined />} style={{ color: '#6B7280' }} title="Download" />
                    <Button type="text" size="small" icon={<MailOutlined />} style={{ color: '#6B7280' }} title="Email" />
                    <Button type="text" size="small" icon={<HistoryOutlined />} style={{ color: '#6B7280' }} title="History / Rollback" />
                  </Space>
                </div>
              </div>
            ))}
          </Space>
        </TabPane>

        <TabPane tab={<><DatabaseOutlined /> Knowledge</>} key="3">
          <div style={{ borderBottom: '1px solid #f0f0f0', paddingBottom: 12, marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}><Text style={{ color: '#6B7280', fontSize: 12 }}>Processing Status</Text><Text style={{ color: '#22C55E', fontSize: 12 }}>Complete</Text></div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}><Text style={{ color: '#6B7280', fontSize: 12 }}>Processing Time</Text><Text style={{ fontSize: 12 }}>2.4s</Text></div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}><Text style={{ color: '#6B7280', fontSize: 12 }}>Embedding Model</Text><Text style={{ color: '#2563EB', fontSize: 12 }}>text-embedding-3-small</Text></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><Text style={{ color: '#6B7280', fontSize: 12 }}>Knowledge Size</Text><Text style={{ fontSize: 12 }}>14.2 MB</Text></div>
          </div>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><Text style={{ fontSize: 12 }}>Chunks</Text><Text style={{ color: '#2563EB', fontSize: 12 }}>4,102</Text></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><Text style={{ fontSize: 12 }}>Embeddings</Text><Text style={{ color: '#2563EB', fontSize: 12 }}>4,102</Text></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><Text style={{ fontSize: 12 }}>Entities</Text><Text style={{ color: '#2563EB', fontSize: 12 }}>128</Text></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><Text style={{ fontSize: 12 }}>Tables</Text><Text style={{ color: '#2563EB', fontSize: 12 }}>14</Text></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><Text style={{ fontSize: 12 }}>Images</Text><Text style={{ color: '#2563EB', fontSize: 12 }}>3</Text></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><Text style={{ fontSize: 12 }}>Pages</Text><Text style={{ color: '#2563EB', fontSize: 12 }}>45</Text></div>
          </Space>
        </TabPane>

        <TabPane tab={<><BookOutlined /> Memory</>} key="4">
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ borderBottom: '1px solid #f0f0f0', paddingBottom: 12 }}>
              <Text style={{ fontSize: 12, fontWeight: 600, display: 'block' }}>Customer Preferences</Text>
              <Text style={{ color: '#6B7280', fontSize: 12 }}>Prefers high-contingency budgeting and daily updates.</Text>
            </div>
            <div style={{ borderBottom: '1px solid #f0f0f0', paddingBottom: 12 }}>
              <Text style={{ fontSize: 12, fontWeight: 600, display: 'block' }}>Past Projects</Text>
              <Text style={{ color: '#6B7280', fontSize: 12 }}>2 successful projects (Cloud Migration, Active Directory).</Text>
            </div>
            <div style={{ borderBottom: '1px solid #f0f0f0', paddingBottom: 12 }}>
              <Text style={{ fontSize: 12, fontWeight: 600, display: 'block' }}>Negotiation History</Text>
              <Text style={{ color: '#6B7280', fontSize: 12 }}>Highly sensitive to recurring licensing costs.</Text>
            </div>
            <div style={{ borderBottom: '1px solid #f0f0f0', paddingBottom: 12 }}>
              <Text style={{ fontSize: 12, fontWeight: 600, display: 'block' }}>Compliance & Architecture</Text>
              <Text style={{ color: '#6B7280', fontSize: 12 }}>Requires SOC2 and BYOL (Bring Your Own License) for Oracle.</Text>
            </div>
            <div>
              <Text style={{ fontSize: 12, fontWeight: 600, display: 'block' }}>Lessons Learned / AI Notes</Text>
              <Text style={{ color: '#6B7280', fontSize: 12 }}>Ensure API limits are documented upfront.</Text>
            </div>
          </Space>
        </TabPane>

        <TabPane tab={<><MailOutlined /> Emails</>} key="5">
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ borderBottom: '1px solid #f0f0f0', paddingBottom: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text style={{ fontSize: 12, fontWeight: 600 }}>To: client@vnu.com</Text>
                <Tag color="green">Delivered</Tag>
              </div>
              <Text style={{ color: '#6B7280', fontSize: 10, display: 'block' }}>Template: Proposal Signature Request</Text>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
                <Text style={{ color: '#6B7280', fontSize: 10 }}>Opened: Yes</Text>
                <Text style={{ color: '#6B7280', fontSize: 10 }}>Clicked: Yes</Text>
                <Text style={{ color: '#6B7280', fontSize: 10 }}>Downloaded: Yes</Text>
              </div>
              <Text style={{ color: '#6B7280', fontSize: 10, display: 'block', marginTop: 4 }}>Oct 6, 14:00 PM</Text>
            </div>
          </Space>
        </TabPane>

        <TabPane tab={<><HistoryOutlined /> Timeline</>} key="6">
          <AntTimeline
            style={{ marginTop: 16 }}
            items={[
              { color: 'green', children: <><Text style={{ fontSize: 12, display: 'block' }}>Customer Created</Text><Text style={{ color: '#6B7280', fontSize: 10 }}>Oct 1</Text></> },
              { color: 'green', children: <><Text style={{ fontSize: 12, display: 'block' }}>Opportunity Created</Text><Text style={{ color: '#6B7280', fontSize: 10 }}>Oct 1</Text></> },
              { color: 'green', children: <><Text style={{ fontSize: 12, display: 'block' }}>RFP Uploaded</Text><Text style={{ color: '#6B7280', fontSize: 10 }}>Oct 2</Text></> },
              { color: 'green', children: <><Text style={{ fontSize: 12, display: 'block' }}>Discovery</Text><Text style={{ color: '#6B7280', fontSize: 10 }}>Oct 3</Text></> },
              { color: 'green', children: <><Text style={{ fontSize: 12, display: 'block' }}>RFQ</Text><Text style={{ color: '#6B7280', fontSize: 10 }}>Oct 4</Text></> },
              { color: 'blue', children: <><Text style={{ color: '#2563EB', fontSize: 12, display: 'block' }}>Proposal</Text><Text style={{ color: '#6B7280', fontSize: 10 }}>Oct 5</Text></> },
              { color: 'gray', children: <><Text style={{ color: '#6B7280', fontSize: 12, display: 'block' }}>Approval</Text><Text style={{ color: '#6B7280', fontSize: 10 }}>Pending</Text></> },
              { color: 'gray', children: <><Text style={{ color: '#6B7280', fontSize: 12, display: 'block' }}>Initialization</Text><Text style={{ color: '#6B7280', fontSize: 10 }}>Pending</Text></> },
              { color: 'gray', children: <><Text style={{ color: '#6B7280', fontSize: 12, display: 'block' }}>Project Created</Text><Text style={{ color: '#6B7280', fontSize: 10 }}>Pending</Text></> },
              { color: 'gray', children: <><Text style={{ color: '#6B7280', fontSize: 12, display: 'block' }}>Workspace Ready</Text><Text style={{ color: '#6B7280', fontSize: 10 }}>Pending</Text></> }
            ]}
          />
        </TabPane>

        <TabPane tab={<><SafetyCertificateOutlined /> Audit</>} key="7">
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ borderBottom: '1px solid #f0f0f0', paddingBottom: 8 }}>
              <Text style={{ fontSize: 12, display: 'block' }}>Generate RFQ (System)</Text>
              <Text style={{ color: '#6B7280', fontSize: 10 }}>Actor: General AI • Tokens: 12.4k • Cost: $0.14</Text>
            </div>
            <div style={{ borderBottom: '1px solid #f0f0f0', paddingBottom: 8 }}>
              <Text style={{ fontSize: 12, display: 'block' }}>Update Discovery (Human)</Text>
              <Text style={{ color: '#6B7280', fontSize: 10 }}>Actor: Current User • Artifacts Modified: 3</Text>
            </div>
          </Space>
        </TabPane>

      </Tabs>
    </Panel>
  );
};

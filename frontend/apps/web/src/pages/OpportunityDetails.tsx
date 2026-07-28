import React, { useState } from 'react';
import { Typography, Row, Col, Button, Space, Tag, Progress, Tabs, Card, Table, Avatar, Input, Tooltip, Divider, Form, message, List, Steps, Select, Timeline } from 'antd';
import { ArrowLeftOutlined, FileTextOutlined, InboxOutlined, RobotOutlined, CheckCircleOutlined, DesktopOutlined, PlusOutlined, SendOutlined, UserOutlined, BookOutlined, CalendarOutlined, DownloadOutlined, HistoryOutlined, CheckOutlined, CloseOutlined, WarningOutlined, FilePdfOutlined, InfoCircleOutlined, MessageOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { PageContainer } from '../components/ui/PageContainer';
import { Panel } from '../components/ui/Panel';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

export function OpportunityDetails() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState('overview');

  // Discovery items state
  const [requirements, setRequirements] = useState([
    { id: 'req-1', name: 'Oracle Spatial database conversion', category: 'Functional', status: 'Approved', desc: 'Convert legacy Oracle Spatial tables to PostGIS schema mappings.' },
    { id: 'req-2', name: 'Dual VPN replication tunnel latency', category: 'Non-Functional', status: 'Waiting', desc: 'Network latency must remain below 120ms during staging migration.' },
    { id: 'req-3', name: 'Database downtime window max 2 hours', category: 'Dependencies', status: 'Open', desc: 'Client demands zero write failures and maximum 2 hours absolute cutover downtime.' }
  ]);

  const [discussions, setDiscussions] = useState([
    { sender: 'Sarah Jenkins', role: 'Customer', text: 'Please ensure transaction isolation level remains serializable.', time: '10:30 AM' },
    { sender: 'General AI', role: 'Co-Pilot', text: 'Verification step: Serializable transaction level mapped. Database target instance configured.', time: '10:32 AM' }
  ]);
  const [chatInput, setChatInput] = useState('');

  const cardStyle = {
    background: '#FFFFFF',
    border: '1px solid #E2E8F0',
    borderRadius: 8,
    boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
  };

  const handleSendMessage = () => {
    if (!chatInput.trim()) return;
    setDiscussions(prev => [...prev, { sender: 'Current User', role: 'Sales', text: chatInput, time: new Date().toLocaleTimeString() }]);
    setChatInput('');
    message.success('Message synchronized to knowledge base.');
  };

  const handleUpdateStatus = (reqId: string, newStatus: string) => {
    setRequirements(prev => prev.map(r => r.id === reqId ? { ...r, status: newStatus } : r));
    message.success(`Status updated to: ${newStatus}`);
  };

  return (
    <PageContainer maxWidth={1600}>
      
      {/* HEADER SECTION */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <Space direction="vertical" size="small">
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate(`/projects`)} style={{ color: '#0F172A', padding: 0, fontWeight: 500 }}>
            Back to Project Details
          </Button>
          <Space align="center">
            <Title level={3} style={{ margin: 0, fontWeight: 700, color: '#0F172A' }}>VNU Database Modernization (MySQL to PostgreSQL)</Title>
            <Tag color="blue" style={{ fontWeight: 600 }}>Discovery Phase</Tag>
          </Space>
          <Space size="large" style={{ color: '#64748B', fontSize: 12 }}>
            <span>Stage: <b>Discovery</b></span>
            <span>Progress: <Progress percent={64} size="small" style={{ width: 80, display: 'inline-block' }} /></span>
            <span>Owner: <b>Sarah Jenkins</b></span>
            <span>Budget: <b>$57,385</b></span>
            <span>Timeline: <b>12 Wks Est</b></span>
          </Space>
        </Space>
        
        <Space>
          <Button icon={<DesktopOutlined />} onClick={() => navigate(`/projects/demo/workspace`)} style={{ fontWeight: 500 }}>Open Workspace</Button>
          <Button style={{ fontWeight: 500 }}>Generate RFQ</Button>
          <Button type="primary" style={{ background: '#2563EB', fontWeight: 600 }}>Generate Proposal</Button>
        </Space>
      </div>

      {/* HORIZONTAL TABS */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        type="card"
        tabBarStyle={{ marginBottom: 24 }}
        items={[
          {
            key: 'overview',
            label: 'Overview',
            children: (
              <Row gutter={[16, 16]}>
                {[
                  { title: 'Current Stage', value: 'Discovery & Extraction', desc: 'RFP completed, RFQ in review.' },
                  { title: 'Goal Progress', value: '64% Mapped', desc: 'Requirements catalog parsed.' },
                  { title: 'Opportunity Budget', value: '$57,385 USD', desc: 'Est: 450k tokens, $3.50 LLM costs.' },
                  { title: 'Risk Score Threshold', value: 'Low Risk', desc: '1 medium risk listed (Trigger conversion).' },
                  { title: 'Orchestrator Confidence', value: '94% Accuracy Index', desc: 'Calculated from standard PL/SQL maps.' },
                  { title: 'Recommended Next Action', value: 'Generate Proposal SOW', desc: 'Awaiting Sarah Jenkins sign-off.' }
                ].map((kpi, idx) => (
                  <Col span={8} key={idx}>
                    <Card style={cardStyle} bodyStyle={{ padding: 20 }}>
                      <Text style={{ fontSize: 9, fontWeight: 700, color: '#64748B', textTransform: 'uppercase', letterSpacing: 0.5, display: 'block', marginBottom: 8 }}>{kpi.title}</Text>
                      <div style={{ fontSize: 16, fontWeight: 700, color: '#0F172A', marginBottom: 4 }}>{kpi.value}</div>
                      <Text type="secondary" style={{ fontSize: 11 }}>{kpi.desc}</Text>
                    </Card>
                  </Col>
                ))}
              </Row>
            )
          },
          {
            key: 'rfp',
            label: 'RFP',
            children: (
              <Panel bodyStyle={{ padding: 24 }}>
                <Row gutter={24}>
                  <Col span={16}>
                    <Title level={5} style={{ marginBottom: 16 }}>Uploaded RFP Source Document</Title>
                    <Card style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', padding: 20 }}>
                      <Space>
                        <FilePdfOutlined style={{ fontSize: 32, color: '#EF4444' }} />
                        <div>
                          <Text strong style={{ fontSize: 13, display: 'block' }}>Legacy_Billing_RFP_v1.0.pdf</Text>
                          <Text type="secondary" style={{ fontSize: 11 }}>Size: 4.2 MB • Uploaded Oct 1 by VNU Customer</Text>
                        </div>
                      </Space>
                    </Card>
                    <Divider style={{ borderColor: '#E2E8F0' }} />
                    <Title level={5} style={{ marginBottom: 12 }}>RFP Version History</Title>
                    <List
                      size="small"
                      dataSource={[
                        { version: 'v1.0', date: 'Oct 1', desc: 'First upload of RFP specs.' }
                      ]}
                      renderItem={item => <div style={{ fontSize: 12, padding: '8px 0', borderBottom: '1px solid #E2E8F0' }}><b>{item.version}</b> - {item.date}: {item.desc}</div>}
                    />
                  </Col>
                  <Col span={8}>
                    <Card style={cardStyle} title="Vector Knowledge Imported" bodyStyle={{ padding: 16 }}>
                      <Progress percent={100} size="small" strokeColor="#16A34A" />
                      <Text style={{ display: 'block', fontSize: 11, color: '#475569', marginTop: 12 }}>
                        124 chunks vectorized and synced into primary agent context memory.
                      </Text>
                    </Card>
                  </Col>
                </Row>
              </Panel>
            )
          },
          {
            key: 'discovery',
            label: 'Discovery',
            children: (
              <div>
                {/* Discovery Actions */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                  <Text style={{ fontSize: 13, color: '#475569' }}>Perform technical discovery and resolve client requirements catalog.</Text>
                  <Space>
                    <Button icon={<PlusOutlined />}>Add Question</Button>
                    <Button>Request Client Input</Button>
                    <Button>Schedule Meeting</Button>
                    <Button type="primary" style={{ background: '#2563EB', fontWeight: 600 }}>Generate Summary</Button>
                  </Space>
                </div>

                <Row gutter={24}>
                  <Col span={14}>
                    <Text style={{ fontSize: 10, fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: 0.5, display: 'block', marginBottom: 12 }}>Opportunity Requirements Catalog</Text>
                    <List
                      dataSource={requirements}
                      renderItem={req => (
                        <Card style={{ ...cardStyle, marginBottom: 12 }} bodyStyle={{ padding: 16 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                            <Space>
                              <Tag color={req.category === 'Functional' ? 'blue' : 'purple'}>{req.category}</Tag>
                              <Text strong style={{ fontSize: 12 }}>{req.name}</Text>
                            </Space>
                            <Select 
                              value={req.status} 
                              size="small" 
                              style={{ width: 110 }} 
                              onChange={val => handleUpdateStatus(req.id, val)}
                            >
                              <Option value="Open">Open</Option>
                              <Option value="Waiting">Waiting</Option>
                              <Option value="Resolved">Resolved</Option>
                              <Option value="Approved">Approved</Option>
                            </Select>
                          </div>
                          <Paragraph style={{ color: '#475569', fontSize: 12, margin: 0 }}>{req.desc}</Paragraph>
                        </Card>
                      )}
                    />
                  </Col>

                  <Col span={10}>
                    <Text style={{ fontSize: 10, fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: 0.5, display: 'block', marginBottom: 12 }}>Client Alignment Discussions</Text>
                    <div style={{ background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: 8, padding: 16, display: 'flex', flexDirection: 'column', height: 400 }}>
                      <div style={{ flex: 1, overflowY: 'auto', marginBottom: 12 }} className="custom-scroll">
                        {discussions.map((msg, idx) => (
                          <div key={idx} style={{ marginBottom: 12 }}>
                            <Space>
                              <Text strong style={{ fontSize: 11 }}>{msg.sender}</Text>
                              <Tag style={{ fontSize: 8 }}>{msg.role}</Tag>
                              <Text type="secondary" style={{ fontSize: 10 }}>{msg.time}</Text>
                            </Space>
                            <Paragraph style={{ color: '#475569', fontSize: 12, marginTop: 4, background: '#F8FAFC', padding: 8, borderRadius: 6 }}>{msg.text}</Paragraph>
                          </div>
                        ))}
                      </div>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <Input 
                          placeholder="Reply to discussion..." 
                          value={chatInput} 
                          onChange={e => setChatInput(e.target.value)} 
                          onPressEnter={handleSendMessage}
                        />
                        <Button type="primary" icon={<SendOutlined />} onClick={handleSendMessage} style={{ background: '#2563EB' }} />
                      </div>
                    </div>
                  </Col>
                </Row>
              </div>
            )
          },
          {
            key: 'rfq',
            label: 'RFQ',
            children: (
              <Panel bodyStyle={{ padding: 24 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
                  <Text strong>Generated RFQ Document Preview</Text>
                  <Space>
                    <Button icon={<DownloadOutlined />}>Export PDF</Button>
                    <Button>Edit</Button>
                    <Button type="primary" style={{ background: '#16A34A', border: 'none' }} icon={<CheckOutlined />}>Approve RFQ</Button>
                  </Space>
                </div>
                <Card style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', padding: 24, fontFamily: 'serif' }}>
                  <Title level={4} style={{ textAlign: 'center', marginBottom: 24 }}>Request for Quote (RFQ) - DB Migration</Title>
                  <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 8 }}>1. Executive Summary</Text>
                  <Paragraph style={{ fontSize: 12, color: '#334155', lineHeight: 1.6 }}>
                    This RFQ defines the migration parameters, target timelines, and spatial conversion requirements for migrating 45 Oracle database tables to PostgreSQL staging replicas.
                  </Paragraph>
                  <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 8, marginTop: 16 }}>2. Deliverables & Commercial Terms</Text>
                  <Paragraph style={{ fontSize: 12, color: '#334155', lineHeight: 1.6 }}>
                    Milestone 1: Dynamic schema migration scripts. Milestone 2: KMS peeing network verification. Budget estimate locked at $57,385.00.
                  </Paragraph>
                </Card>
              </Panel>
            )
          },
          {
            key: 'proposal',
            label: 'Proposal',
            children: (
              <Panel bodyStyle={{ padding: 24 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
                  <Text strong>Executive Proposal SOW Preview</Text>
                  <Button icon={<DownloadOutlined />}>Export PDF</Button>
                </div>
                <Card style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', padding: 24 }}>
                  <Title level={4} style={{ textAlign: 'center', marginBottom: 24 }}>Commercial Statement of Work (SOW)</Title>
                  <Paragraph style={{ fontSize: 12, color: '#334155', lineHeight: 1.6 }}>
                    Recommended Target Architecture: Amazon RDS Multi-AZ Aurora PostgreSQL. Dual DirectConnect VPN paths mapped to local routing tables. Estimated migration duration: 12 Weeks.
                  </Paragraph>
                </Card>
              </Panel>
            )
          },
          {
            key: 'approvals',
            label: 'Approvals',
            children: (
              <Panel bodyStyle={{ padding: 24 }}>
                <Title level={5} style={{ marginBottom: 16 }}>Required Approval Workflows</Title>
                <Table
                  dataSource={[
                    { key: '1', request: 'Initial RFQ Document', requestedBy: 'General AI', date: 'Oct 3', status: 'Approved', approver: 'Sarah Jenkins' },
                    { key: '2', request: 'SOW Commercial Terms', requestedBy: 'Sarah Jenkins', date: 'Oct 6', status: 'Pending Sign-off', approver: 'Client Executive Board' }
                  ]}
                  size="middle"
                  pagination={false}
                  columns={[
                    { title: 'Request Name', dataIndex: 'request', key: 'request', render: t => <Text strong>{t}</Text> },
                    { title: 'Requested By', dataIndex: 'requestedBy', key: 'requestedBy' },
                    { title: 'Submission Date', dataIndex: 'date', key: 'date' },
                    { title: 'Assigned Approver', dataIndex: 'approver', key: 'approver' },
                    { title: 'Workflow Status', dataIndex: 'status', key: 'status', render: s => <Tag color={s === 'Approved' ? 'green' : 'orange'}>{s}</Tag> }
                  ]}
                />
              </Panel>
            )
          },
          {
            key: 'documents',
            label: 'Documents',
            children: (
              <Row gutter={[16, 16]}>
                {[
                  { name: 'Legacy_Billing_RFP_v1.0.pdf', category: 'RFP Source', size: '4.2 MB', date: 'Oct 1' },
                  { name: 'VNU_Schema_Mappings_RFQ.pdf', category: 'RFQ Documents', size: '320 KB', date: 'Oct 3' },
                  { name: 'Final_SOW_Proposal.pdf', category: 'Proposals', size: '1.4 MB', date: 'Oct 5' }
                ].map((doc, idx) => (
                  <Col span={8} key={idx}>
                    <Card style={cardStyle} bodyStyle={{ padding: 16 }}>
                      <Space style={{ marginBottom: 12 }}>
                        <FilePdfOutlined style={{ fontSize: 24, color: '#EF4444' }} />
                        <div>
                          <Text strong style={{ fontSize: 12, color: '#0F172A' }}>{doc.name}</Text>
                          <Text type="secondary" style={{ fontSize: 10, display: 'block' }}>Category: {doc.category} • {doc.size}</Text>
                        </div>
                      </Space>
                    </Card>
                  </Col>
                ))}
              </Row>
            )
          },
          {
            key: 'discussions',
            label: 'Discussions',
            children: (
              <Panel bodyStyle={{ padding: 24 }}>
                <Text style={{ fontSize: 13, color: '#475569', display: 'block', marginBottom: 16 }}>Slack-style collaborative channels synced to workspace intelligence.</Text>
                <div style={{ border: '1px solid #E2E8F0', borderRadius: 8, padding: 16 }}>
                  {discussions.map((msg, idx) => (
                    <div key={idx} style={{ marginBottom: 12 }}>
                      <Text strong style={{ fontSize: 12 }}>{msg.sender}</Text> <Tag style={{ fontSize: 9 }}>{msg.role}</Tag>
                      <Paragraph style={{ color: '#475569', fontSize: 12, margin: '4px 0' }}>{msg.text}</Paragraph>
                    </div>
                  ))}
                </div>
              </Panel>
            )
          },
          {
            key: 'timeline',
            label: 'Timeline',
            children: (
              <Panel bodyStyle={{ padding: 24 }}>
                <Timeline
                  items={[
                    { children: 'Opportunity Modernization registered (Oct 1)', color: 'blue' },
                    { children: 'RFP Source uploaded & vectorized (Oct 1)', color: 'blue' },
                    { children: 'RFQ draft generated by General AI (Oct 3)', color: 'blue' },
                    { children: 'Commercial SOW signed by VNU (Oct 6)', color: 'green' }
                  ]}
                />
              </Panel>
            )
          }
        ]}
      />

    </PageContainer>
  );
}

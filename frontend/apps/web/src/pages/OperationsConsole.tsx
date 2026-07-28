import React, { useEffect, useState } from 'react';
import { Typography, Row, Col, Card, Tag, List, Button, Input, Space, Badge, Spin, Result, Avatar, message } from 'antd';
import { RobotOutlined, WarningOutlined, ThunderboltOutlined, FileTextOutlined, CheckCircleOutlined, SendOutlined, UserOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { ApiClient } from '../api/client';
import { PageContainer } from '../components/ui/PageContainer';
import { Panel } from '../components/ui/Panel';

const { Title, Text, Paragraph } = Typography;

export function OperationsConsole() {
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [chatMessages, setChatMessages] = useState<any[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [queueItems, setQueueItems] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);

  const fetchSummary = async () => {
    try {
      const res = await ApiClient.get('/operations/summary');
      setData(res);
      const firstProj = res.projects[0];
      if (firstProj) {
        const workspaceData = await ApiClient.get(`/projects/${firstProj.key}/workspace`);
        setEvents(workspaceData.events || []);
      }
    } catch (e) {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const fetchQueue = async () => {
    try {
      const q = await ApiClient.get('/queue');
      setQueueItems(q.filter((item: any) => item.status === 'Pending'));
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchSummary();
    fetchQueue();
  }, []);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;
    const val = inputValue;
    setChatMessages(prev => [...prev, { sender: 'User', text: val, time: new Date().toLocaleTimeString() }]);
    setInputValue('');
    try {
      const targetProject = data?.projects?.[0];
      if (!targetProject) {
        message.warning('Create a project before sending workspace instructions.');
        return;
      }
      const res = await ApiClient.post(`/projects/${targetProject.key}/workspace/chat`, { message: val });
      setChatMessages(prev => [...prev, { sender: 'Chief of Staff', text: res.reply, time: new Date().toLocaleTimeString() }]);
      if (res.newEvent) setEvents(prev => [...prev, res.newEvent]);
      fetchSummary();
      fetchQueue();
    } catch (e) {
      message.error('Failed to communicate with Chief of Staff');
    }
  };

  const handleApprove = async (itemId: string) => {
    try {
      await ApiClient.post(`/queue/${itemId}/action`, { action: 'approve', comment: 'Approved via Executive Console' });
      message.success('Action authorized.');
      fetchSummary();
      fetchQueue();
    } catch (e) {
      message.error('Approval execution failed.');
    }
  };

  const handleReject = async (itemId: string) => {
    try {
      await ApiClient.post(`/queue/${itemId}/action`, { action: 'reject', comment: 'Rejected via Executive Console' });
      message.warning('Action rejected.');
      fetchSummary();
      fetchQueue();
    } catch (e) {
      message.error('Rejection execution failed.');
    }
  };

  if (loading) return <div style={{ height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', background: '#F8FAFC' }}><Spin size="large" /></div>;
  if (error || !data) return <Result status="error" title="System Offline" subTitle="Cannot connect to aegisOS Core." />;

  const sectionLabelStyle = {
    fontSize: 11,
    fontWeight: 600 as const,
    color: '#6B7280',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
    display: 'block',
    marginBottom: 12,
  };

  return (
    <PageContainer maxWidth={1600}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, paddingBottom: 16, borderBottom: '1px solid #E5E7EB' }}>
        <div>
          <Title level={3} style={{ margin: 0, fontWeight: 600, letterSpacing: -0.5, color: '#111827' }}>Operations Control Console</Title>
          <Text style={{ color: '#6B7280', fontSize: 13 }}>Real-time System Orchestration & Digital Employee Registry</Text>
        </div>
        <Button type="primary" style={{ background: '#2563EB', fontWeight: 500 }} onClick={() => navigate('/projects')}>Start New Goal</Button>
      </div>

      <Row gutter={[24, 24]}>
        {/* LEFT COLUMN */}
        <Col span={6}>
          <span style={sectionLabelStyle}>Organization Node</span>
          <Panel bodyStyle={{ padding: 16 }}>
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Text style={{ fontSize: 14, fontWeight: 600, color: '#111827' }}>aegisOS Enterprise Node</Text>
              <Text style={{ color: '#6B7280', fontSize: 12 }}>Domain: <Text style={{ color: '#2563EB' }}>aegisOS.internal</Text></Text>
              <Tag style={{ background: '#DCFCE7', color: '#15803D', border: 'none', fontWeight: 600 }}>License: Enterprise Demo</Tag>
            </Space>
          </Panel>

          <span style={sectionLabelStyle}>Active Goals</span>
          <Panel bodyStyle={{ padding: 0 }}>
            <List
              dataSource={data.projects}
              renderItem={(p: any) => (
                <div style={{ padding: '12px 16px', borderBottom: '1px solid #E5E7EB', cursor: 'pointer' }} onClick={() => navigate(`/projects/${p.key}/workspace`)}>
                  <Text style={{ fontWeight: 500, fontSize: 13, color: '#111827' }}>{p.project}</Text>
                  <br/>
                  <Badge status={p.status === 'Execution' ? 'processing' : 'default'} color={p.status === 'Execution' ? '#16A34A' : '#9CA3AF'} text={<span style={{ color: '#6B7280', fontSize: 11 }}>{p.status}</span>} />
                </div>
              )}
            />
          </Panel>

          <span style={sectionLabelStyle}>Digital Workers</span>
          <Panel bodyStyle={{ padding: 16 }}>
            <List
              dataSource={data.projects.map((p: any) => ({ name: p.ai || 'Validation Agent', status: p.status }))}
              renderItem={(w: any) => (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <Text style={{ color: '#4B5563', fontSize: 12, fontWeight: 500 }}>{w.name}</Text>
                  <Tag style={{ background: w.status === 'Execution' ? '#DCFCE7' : '#F3F4F6', color: w.status === 'Execution' ? '#15803D' : '#6B7280', border: 'none', fontWeight: 600, fontSize: 10 }}>{w.status === 'Execution' ? 'Running' : 'Idle'}</Tag>
                </div>
              )}
            />
          </Panel>
        </Col>

        {/* CENTER COLUMN */}
        <Col span={12}>
          <span style={sectionLabelStyle}>Chief of Staff Command Interface</span>
          <Panel bodyStyle={{ padding: 20 }}>
            <div style={{ height: 280, overflowY: 'auto', paddingRight: 8, marginBottom: 16 }} className="custom-scroll">
              {chatMessages.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 0', color: '#6B7280' }}>
                  <RobotOutlined style={{ fontSize: 32, color: '#2563EB', marginBottom: 12, opacity: 0.6 }} />
                  <br/>
                  <Text style={{ fontSize: 14, fontWeight: 600, color: '#111827' }}>Instruct Chief of Staff Node</Text>
                  <Paragraph style={{ color: '#6B7280', fontSize: 12, marginTop: 4 }}>Submit enterprise objectives to spawn workflow plans and workers.</Paragraph>
                </div>
              ) : (
                <List
                  dataSource={chatMessages}
                  renderItem={msg => (
                    <div style={{ marginBottom: 16, textAlign: msg.sender === 'User' ? 'right' : 'left' }}>
                      <div style={{
                        display: 'inline-block',
                        background: msg.sender === 'User' ? '#EEF2FF' : '#F8FAFC',
                        border: `1px solid ${msg.sender === 'User' ? '#C7D2FE' : '#E5E7EB'}`,
                        padding: '10px 14px',
                        borderRadius: 12,
                        maxWidth: '90%',
                        textAlign: 'left'
                      }}>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
                          <Avatar size="small" icon={msg.sender === 'User' ? <UserOutlined /> : <RobotOutlined />} style={{ background: msg.sender === 'User' ? '#E5E7EB' : '#EEF2FF', color: msg.sender === 'User' ? '#6B7280' : '#2563EB' }} />
                          <Text style={{ fontSize: 11, fontWeight: 600, color: '#111827' }}>{msg.sender}</Text>
                          <Text style={{ color: '#9CA3AF', fontSize: 9 }}>{msg.time}</Text>
                        </div>
                        <pre style={{ color: '#4B5563', fontSize: 12, lineHeight: 1.5, fontFamily: 'inherit', whiteSpace: 'pre-wrap', margin: 0 }}>{msg.text}</pre>
                      </div>
                    </div>
                  )}
                />
              )}
            </div>
            <Input.Search
              placeholder="Enter system instruction (e.g. Start Frappe Migration)..."
              enterButton={<SendOutlined />}
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              onSearch={handleSendMessage}
            />
          </Panel>

          <span style={sectionLabelStyle}>System Orchestration Timeline</span>
          <Panel bodyStyle={{ padding: 16 }}>
            <List
              dataSource={events.slice(-2)}
              renderItem={(ev: any) => (
                <div style={{ display: 'flex', gap: 12, marginBottom: 12, borderBottom: '1px solid #E5E7EB', paddingBottom: 8 }}>
                  <CheckCircleOutlined style={{ color: '#16A34A', fontSize: 14, marginTop: 2 }} />
                  <div>
                    <Text style={{ fontWeight: 500, fontSize: 13, color: '#111827' }}>{ev.agent} • {ev.title}</Text>
                    <Paragraph style={{ color: '#6B7280', fontSize: 11, margin: '2px 0 0 0' }}>{ev.desc}</Paragraph>
                  </div>
                </div>
              )}
            />
          </Panel>
        </Col>

        {/* RIGHT COLUMN */}
        <Col span={6}>
          <span style={sectionLabelStyle}>Approvals & Interventions</span>
          <Panel bodyStyle={{ padding: 16 }} style={{ borderColor: queueItems.length > 0 ? '#FCD34D' : '#E5E7EB', background: queueItems.length > 0 ? '#FFFBEB' : '#FFFFFF' }}>
            {queueItems.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '12px 0' }}>
                <CheckCircleOutlined style={{ fontSize: 18, color: '#16A34A', marginBottom: 6 }} />
                <br/><Text style={{ color: '#6B7280', fontSize: 12 }}>No pending approvals</Text>
              </div>
            ) : (
              <List
                dataSource={queueItems.slice(0, 1)}
                renderItem={(item: any) => (
                  <div>
                    <Text style={{ fontWeight: 500, fontSize: 12, display: 'block', marginBottom: 4, color: '#111827' }}>{item.reason}</Text>
                    <Space style={{ marginTop: 8 }}>
                      <Button type="primary" size="small" style={{ background: '#D97706', border: 'none', fontWeight: 600 }} onClick={() => handleApprove(item.id)}>Approve</Button>
                      <Button size="small" danger onClick={() => handleReject(item.id)}>Reject</Button>
                    </Space>
                  </div>
                )}
              />
            )}
          </Panel>

          <span style={sectionLabelStyle}>System Safety Risks</span>
          <Panel bodyStyle={{ padding: 12 }} style={{ borderColor: '#FCA5A5' }}>
            <pre style={{ margin: 0, fontSize: 10, color: '#DC2626', fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
              [SAFETY WARNING] External integration nodes detected with expired authorization headers. Review key connections.
            </pre>
          </Panel>

          <span style={sectionLabelStyle}>Notifications</span>
          <Panel bodyStyle={{ padding: 12 }}>
            <List
              size="small"
              dataSource={data.activities.slice(0, 2)}
              renderItem={(a: any) => (
                <div style={{ fontSize: 11, color: '#4B5563', marginBottom: 6 }}>
                  <ThunderboltOutlined style={{ color: '#2563EB', marginRight: 6 }} /> {a.text}
                </div>
              )}
            />
          </Panel>
        </Col>
      </Row>

      {/* BOTTOM ROW */}
      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col span={16}>
          <span style={sectionLabelStyle}>Live Execution Logs</span>
          <div style={{
            padding: 16,
            background: '#FFFFFF',
            border: '1px solid #E5E7EB',
            borderRadius: 12,
            fontFamily: 'monospace',
            fontSize: 11,
            color: '#16A34A',
            maxHeight: 180,
            overflowY: 'auto'
          }}>
            {(data.logs || []).map((log: string, idx: number) => (
              <div key={idx} style={{ marginBottom: 4 }}>&gt; {log}</div>
            ))}
          </div>
        </Col>
        <Col span={8}>
          <span style={sectionLabelStyle}>Generated Output Artifacts</span>
          <Panel bodyStyle={{ padding: 12 }}>
            <List
              size="small"
              dataSource={data.artifacts.slice(0, 3)}
              renderItem={(art: any) => (
                <div style={{ fontSize: 11, color: '#4B5563', display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                  <FileTextOutlined style={{ color: '#2563EB' }} /> {art.name.split('/').pop()}
                </div>
              )}
            />
          </Panel>
        </Col>
      </Row>
    </PageContainer>
  );
}

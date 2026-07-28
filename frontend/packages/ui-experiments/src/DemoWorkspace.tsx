import React, { useState, useEffect } from 'react';
import { Layout, Typography, Card, Row, Col, List, Avatar, Tag, Button, Input, Space, Badge, Progress, Collapse, Tree, Tabs } from 'antd';
import { RobotOutlined, UserOutlined, SendOutlined, CheckCircleOutlined, ExclamationCircleOutlined, SyncOutlined, DatabaseOutlined, ApartmentOutlined, WarningOutlined, ApiOutlined, PartitionOutlined, SearchOutlined, FileTextOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { ApiClient } from '../../api/client';

const { Content, Sider, Header } = Layout;
const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;
const { TabPane } = Tabs;

export const DemoWorkspace = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [chatMessages, setChatMessages] = useState<any[]>([]);
  const [inputValue, setInputValue] = useState('');

  // Simulated Master Agent Event Stream
  const [events, setEvents] = useState<any[]>([]);
  const [progress, setProgress] = useState(0);
  const [phase, setPhase] = useState('Discovery');
  
  useEffect(() => {
    ApiClient.get(`/projects/${id || 'demo'}/workspace`)
      .then(res => {
        setData(res);
        setPhase('Discovery');
        
        let timeouts = res.events.map((e: any) => setTimeout(() => {
          setEvents(prev => [e, ...prev]);
          if (e.phase) setPhase(e.phase);
          setProgress(p => Math.min(p + 15, 45));
        }, e.delay));

        return () => timeouts.forEach((t: any) => clearTimeout(t));
      })
      .catch(() => {});
  }, [id]);

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;
    const val = inputValue;
    setChatMessages([...chatMessages, { sender: 'User', text: val }]);
    setInputValue('');
    
    ApiClient.post(`/projects/${id || 'demo'}/workspace/chat`, { message: val })
      .then(res => {
        setChatMessages(prev => [...prev, { sender: 'Master Agent', text: res.reply }]);
        setEvents(prev => [res.newEvent, ...prev]);
        setProgress(res.newProgress);
        setPhase(res.newPhase);
      })
      .catch(() => {});
  };

  const getEventIcon = (type: string) => {
    if (type === 'alert') return <WarningOutlined style={{ color: 'red' }} />;
    if (type === 'create') return <ApiOutlined style={{ color: '#1677ff' }} />;
    if (type === 'human') return <UserOutlined style={{ color: 'orange' }} />;
    return <DatabaseOutlined style={{ color: 'green' }} />;
  };

  if (!data) return <div style={{ padding: 100, textAlign: 'center' }}>Loading workspace...</div>;

  return (
    <Layout style={{ height: '100%', display: 'flex', flexDirection: 'column', background: '#fafafa' }}>
      {/* OS PROJECT WORKSPACE TOP BAR */}
      <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', alignItems: 'center', gap: '32px', borderBottom: '1px solid #e8e8e8', height: 72 }}>
        <div><Text type="secondary" style={{ fontSize: 11 }}>Business Goal</Text><br/><Text strong style={{ fontSize: 14 }}>{data.goal}</Text></div>
        <div><Text type="secondary" style={{ fontSize: 11 }}>Overall Progress</Text><br/><Progress percent={progress} style={{ width: 120, margin: 0 }} size="small" /></div>
        <div><Text type="secondary" style={{ fontSize: 11 }}>Current Phase</Text><br/><Tag color="blue">{phase}</Tag></div>
        <div><Text type="secondary" style={{ fontSize: 11 }}>Workers</Text><br/><Badge status="processing" text="2 Running" /></div>
        <div><Text type="secondary" style={{ fontSize: 11 }}>Pending Approvals</Text><br/><Badge count={progress >= 45 && progress < 60 ? 1 : 0} style={{ backgroundColor: '#faad14' }} /></div>
        <div><Text type="secondary" style={{ fontSize: 11 }}>Current Risks</Text><br/><Text type="danger">1 Identified</Text></div>
        <div style={{ marginLeft: 'auto' }}><Button onClick={() => navigate('/projects')}>Close Workspace</Button></div>
      </Header>

      <Layout style={{ flex: 1, overflow: 'hidden' }}>
        {/* LEFT PANEL: GOAL TREE */}
        <Sider width={240} theme="light" style={{ borderRight: '1px solid #e8e8e8', padding: '16px 0', overflowY: 'auto' }}>
          <div style={{ padding: '0 16px', marginBottom: 12 }}><Text strong>Goal Tree</Text></div>
          <Tree
            defaultExpandAll
            treeData={[
              { title: <><Text strong>Migration Project</Text> <Tag color="green">Active</Tag></>, key: '0-0', children: [
                { title: 'Discovery', key: '0-0-0', icon: <CheckCircleOutlined style={{ color: 'green' }}/> },
                { title: 'Planning', key: '0-0-1', icon: <SyncOutlined spin style={{ color: '#1677ff' }}/> },
                { title: 'Approval', key: '0-0-2', icon: <ExclamationCircleOutlined style={{ color: 'orange' }}/> },
                { title: 'Execution', key: '0-0-3', icon: <PartitionOutlined style={{ color: 'gray' }}/> },
                { title: 'Validation', key: '0-0-4', icon: <PartitionOutlined style={{ color: 'gray' }}/> },
                { title: 'Deployment', key: '0-0-5', icon: <PartitionOutlined style={{ color: 'gray' }}/> }
              ]}
            ]}
          />
        </Sider>

        {/* CENTER PANEL: LIVE EXECUTION */}
        <Content style={{ padding: 24, display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
          <div style={{ marginBottom: 16 }}><Title level={4} style={{ margin: 0 }}><RobotOutlined /> Master Agent Console</Title></div>
          
          <div style={{ flex: 1, overflowY: 'auto', paddingRight: 16 }}>
            {events.map((ev, i) => (
              <Card key={i} size="small" style={{ marginBottom: 12, borderColor: ev.type === 'alert' ? '#ffccc7' : ev.type === 'human' ? '#ffe58f' : '#e8e8e8' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <Space>
                    {getEventIcon(ev.type)}
                    <Text strong>{ev.agent}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>[{ev.phase}]</Text>
                  </Space>
                  <Space>
                    <Tag color={ev.conf > 90 ? 'green' : 'orange'}>{ev.conf}% Conf</Tag>
                    <Text type="secondary" style={{ fontSize: 12 }}>{ev.dur}</Text>
                  </Space>
                </div>
                <Text strong>{ev.title}</Text>
                <Paragraph style={{ margin: '4px 0 0 0', fontSize: 13 }}>{ev.desc}</Paragraph>
                {ev.details && (
                  <Collapse size="small" ghost style={{ marginTop: 4 }}>
                    <Panel header="View Details & Reasoning" key="1">
                      <pre style={{ background: '#f5f5f5', padding: 8, borderRadius: 4, margin: 0, fontSize: 11 }}>{ev.details}</pre>
                    </Panel>
                  </Collapse>
                )}
                {ev.type === 'human' && (
                  <div style={{ marginTop: 12 }}>
                    <Space>
                      <Button size="small" type="primary">Approve</Button>
                      <Button size="small" danger>Reject</Button>
                      <Button size="small">Modify</Button>
                    </Space>
                  </div>
                )}
              </Card>
            ))}
          </div>
        </Content>

        {/* RIGHT PANEL: CHAT & QUEUE */}
        <Sider width={320} theme="light" style={{ borderLeft: '1px solid #e8e8e8', display: 'flex', flexDirection: 'column' }}>
          <Tabs defaultActiveKey="discussion" centered style={{ height: '100%', display: 'flex', flexDirection: 'column' }} items={[
            { key: 'discussion', label: 'Discussion', children: (
              <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 200px)' }}>
                <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
                  {chatMessages.length === 0 ? (
                    <div style={{ textAlign: 'center', color: '#999', marginTop: 40 }}>
                      <Text>Master Agent is listening.</Text>
                    </div>
                  ) : (
                    <List
                      dataSource={chatMessages}
                      renderItem={msg => (
                        <div style={{ marginBottom: 16, textAlign: msg.sender === 'User' ? 'right' : 'left' }}>
                          <div style={{ display: 'inline-block', background: msg.sender === 'User' ? '#1677ff' : '#f0f2f5', color: msg.sender === 'User' ? '#fff' : '#000', padding: '8px 12px', borderRadius: 8, maxWidth: '90%', textAlign: 'left' }}>
                            <Text style={{ color: 'inherit', fontSize: 12, display: 'block', marginBottom: 4 }}>{msg.sender}</Text>
                            <Text style={{ color: 'inherit', fontSize: 13 }}>{msg.text}</Text>
                          </div>
                        </div>
                      )}
                    />
                  )}
                </div>
                <div style={{ padding: 16, borderTop: '1px solid #e8e8e8' }}>
                  <Input.Search
                    placeholder="Provide direction..."
                    enterButton={<SendOutlined />}
                    value={inputValue}
                    onChange={e => setInputValue(e.target.value)}
                    onSearch={handleSendMessage}
                  />
                </div>
              </div>
            )},
            { key: 'approvals', label: 'Queue', children: (
               <div style={{ padding: 16 }}>
                 <Card size="small" title={<Text type="danger">High Priority</Text>} extra={<Tag color="orange">Pending</Tag>}>
                   <Text strong>Tax Mapping Rule</Text>
                   <p style={{ fontSize: 12 }}>Blocked Worker: Data Mapping Agent</p>
                   <Button type="primary" size="small" block>Review Decision</Button>
                 </Card>
               </div>
            )},
            { key: 'notifications', label: 'Alerts', children: <div style={{ padding: 16 }}><Text type="secondary">No new alerts</Text></div> }
          ]} />
        </Sider>
      </Layout>

      {/* BOTTOM PANEL: PROJECT ASSETS */}
      <div style={{ borderTop: '1px solid #e8e8e8', background: '#fff', padding: '0 16px', height: 250, overflowY: 'auto' }}>
        <Tabs defaultActiveKey="workers" size="small" items={[
          { key: 'workers', label: 'Workers', children: (
            <Row gutter={16}>
              {data.workers.map((w: any, idx: number) => (
                <Col span={6} key={idx}>
                  <Card size="small" title={w.name} extra={<Tag color={w.color || 'blue'}>{w.status}</Tag>}>
                    <Text type="secondary" style={{ fontSize: 12 }}>Task: {w.purpose}</Text>
                  </Card>
                </Col>
              ))}
            </Row>
          )},
          { key: 'artifacts', label: 'Artifacts', children: (
            <List size="small" dataSource={data.artifacts} renderItem={(i: any) => <List.Item><Button type="link" size="small"><FileTextOutlined /> {i}</Button></List.Item>} />
          )},
          { key: 'knowledge', label: 'Knowledge', children: <div style={{ padding: 8 }}>Loaded: {data.knowledge.join(', ')}</div> },
          { key: 'connectors', label: 'Connectors', children: <div style={{ padding: 8 }}>{data.connectors.join(', ')}</div> },
          { key: 'logs', label: 'Execution Logs', children: <div style={{ padding: 8, background: '#000', color: '#0f0', fontFamily: 'monospace' }}>{data.logs.map((l: string, i: number) => <div key={i}>{l}</div>)}</div> }
        ]} />
      </div>
    </Layout>
  );
};

import React, { useState, useEffect } from 'react';
import { Layout, Typography, Table, Tag, Button, Space, Modal, Input, message, Spin, Result } from 'antd';
import { CheckOutlined, CloseOutlined, CommentOutlined } from '@ant-design/icons';
import { ApiClient } from '../../api/client';
const { Content } = Layout;
const { Title, Text } = Typography;
const { TextArea } = Input;

export const DemoHumanQueue = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [activeItem, setActiveItem] = useState<any>(null);
  const [commentText, setCommentText] = useState('');

  const fetchQueue = () => {
    setLoading(true);
    ApiClient.get('/queue')
      .then(res => {
        setData(res);
        setLoading(false);
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Priority', dataIndex: 'priority', key: 'priority', render: (text: string) => <Tag color={text === 'High' ? 'orange' : 'red'}>{text}</Tag> },
    { title: 'Reason', dataIndex: 'reason', key: 'reason' },
    { title: 'AI Confidence', dataIndex: 'confidence', key: 'confidence', render: (c: number) => c > 0 ? <Text type={c > 80 ? 'success' : 'warning'}>{c}%</Text> : <Text type="secondary">N/A</Text> },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (text: string) => <Tag color="blue">{text}</Tag> },
    { title: 'Action', key: 'action', render: (_: any, record: any) => (
      <Space>
        <Button size="small" type="primary" icon={<CheckOutlined />} onClick={() => handleAction(record.id, 'approve')}>Approve</Button>
        <Button size="small" danger icon={<CloseOutlined />} onClick={() => handleAction(record.id, 'reject')}>Reject</Button>
        <Button size="small" icon={<CommentOutlined />} onClick={() => { setActiveItem(record); setModalVisible(true); }}>Comment</Button>
      </Space>
    )}
  ];

  const handleAction = (id: string, action: string, comment?: string) => {
    ApiClient.post(`/queue/${id}/action`, { action, comment })
      .then(() => {
        message.success(`Item ${action}d successfully.`);
        fetchQueue();
        setModalVisible(false);
        setCommentText('');
      })
      .catch(() => message.error(`Failed to ${action} item.`));
  };

  if (loading) return <div style={{ padding: 100, textAlign: 'center' }}><Spin size="large" /></div>;
  if (error) return <Result status="error" title="Failed to load queue" extra={<Button onClick={fetchQueue}>Retry</Button>} />;

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      
      <Content style={{ padding: '24px 48px' }}>
        <div style={{ background: '#fff', padding: 24, borderRadius: 8, boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
          <Title level={3}>Human Approval Queue</Title>
          <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>Manage tasks requiring human review due to low AI confidence or explicit business rules.</Text>
          <Table dataSource={data} columns={columns} rowKey="id" pagination={false} />
        </div>
      </Content>
      <Modal title="Add Comment" open={modalVisible} onOk={() => handleAction(activeItem?.id, 'comment', commentText)} onCancel={() => setModalVisible(false)}>
        <Text strong>{activeItem?.reason}</Text>
        <TextArea rows={4} style={{ marginTop: 16 }} placeholder="Enter your review notes..." value={commentText} onChange={e => setCommentText(e.target.value)} />
      </Modal>
    </Layout>
  );
};

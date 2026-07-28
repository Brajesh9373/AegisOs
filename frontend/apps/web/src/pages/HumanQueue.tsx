import React, { useEffect, useMemo, useState } from 'react';
import {
  Badge,
  Button,
  Drawer,
  Empty,
  Input,
  Progress,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd';
import {
  CheckOutlined,
  ClockCircleOutlined,
  CloseOutlined,
  CommentOutlined,
  ExclamationCircleOutlined,
  FilterOutlined,
  RobotOutlined,
  SearchOutlined,
  SendOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { PageContainer } from '../components/ui/PageContainer';
import { Panel } from '../components/ui/Panel';
import './HumanQueue.css';

const { Title, Text } = Typography;
const { TextArea } = Input;

type QueueStatus = 'Pending' | 'In Review' | 'Approved' | 'Rejected';
type QueuePriority = 'Critical' | 'High' | 'Medium' | 'Low';
type QueueType = 'Approval' | 'Escalation' | 'Review';

interface QueueItem {
  id: string;
  title: string;
  type: QueueType;
  priority: QueuePriority;
  reason: string;
  confidence: number;
  status: QueueStatus;
  agent: string;
  submittedAt: string;
  dueBy: string;
  comment?: string;
  project?: string;
}

const PRIORITY_META: Record<QueuePriority, { color: string; className: string }> = {
  Critical: { color: '#dc2626', className: 'queue-priority--critical' },
  High: { color: '#d97706', className: 'queue-priority--high' },
  Medium: { color: '#2563eb', className: 'queue-priority--medium' },
  Low: { color: '#64748b', className: 'queue-priority--low' },
};

const formatDueDate = (value: string) => {
  if (!value) return 'No due date';
  const due = new Date(value.length <= 10 ? value + 'T17:00:00' : value);
  const now = new Date();
  const hours = Math.round((due.getTime() - now.getTime()) / 3_600_000);

  if (hours < 0) return `${Math.abs(hours)}h overdue`;
  if (hours < 12) return `Due in ${hours}h`;
  if (hours < 36) return 'Due tomorrow';
  return due.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

const isOpen = (status: QueueStatus) => status === 'Pending' || status === 'In Review';

const formatSubmittedAt = (value: string) => {
  if (!value) return '';
  try {
    const d = new Date(value);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) + ' ' +
      d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  } catch { return value; }
};

export const HumanQueue = () => {
  const [data, setData] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeItem, setActiveItem] = useState<QueueItem | null>(null);
  const [search, setSearch] = useState('');
  const [priority, setPriority] = useState<QueuePriority | 'All'>('All');
  const [status, setStatus] = useState<QueueStatus | 'Open' | 'All'>('Open');
  const [commentText, setCommentText] = useState('');
  const [commentOpen, setCommentOpen] = useState(false);
  const [aiChatOpen, setAiChatOpen] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
    fetch('/queue', { headers })
      .then(res => res.json())
      .then((items: QueueItem[]) => { if (Array.isArray(items)) setData(items); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filteredData = useMemo(() => {
    const query = search.trim().toLowerCase();
    return data.filter(item => {
      const matchesSearch =
        !query ||
        item.id.toLowerCase().includes(query) ||
        item.title.toLowerCase().includes(query) ||
        item.agent.toLowerCase().includes(query);
      const matchesPriority = priority === 'All' || item.priority === priority;
      const matchesStatus =
        status === 'All' || (status === 'Open' ? isOpen(item.status) : item.status === status);

      return matchesSearch && matchesPriority && matchesStatus;
    });
  }, [data, priority, search, status]);

  const openCount = data.filter(item => isOpen(item.status)).length;
  const criticalCount = data.filter(item => isOpen(item.status) && item.priority === 'Critical').length;

  const selectItem = (record: QueueItem) => {
    setActiveItem(record);
    setCommentText(record.comment ?? '');
    setCommentOpen(Boolean(record.comment));
    setAiChatOpen(false);
  };

  const handleDecision = (decision: 'Approved' | 'Rejected') => {
    if (!activeItem) return;
    const updatedItem = { ...activeItem, status: decision };
    setData(previous => previous.map(item => (item.id === updatedItem.id ? updatedItem : item)));
    setActiveItem(updatedItem);
    const token = localStorage.getItem('auth_token');
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers.Authorization = `Bearer ${token}`;
    fetch(`/queue/${activeItem.id}/action`, {
      method: 'POST', headers,
      body: JSON.stringify({ action: decision.toLowerCase() }),
    }).catch(() => {});
  };

  const saveComment = () => {
    if (!activeItem) return;
    const updatedItem = { ...activeItem, comment: commentText.trim() };
    setData(previous => previous.map(item => (item.id === updatedItem.id ? updatedItem : item)));
    setActiveItem(updatedItem);
    setCommentOpen(false);
  };

  const columns = [
    {
      title: 'Request',
      key: 'request',
      render: (_: unknown, record: QueueItem) => (
        <div className="queue-request">
          <div className="queue-request__meta">
            <Text className="queue-ticket-id">{record.id}</Text>
            <span aria-hidden="true">·</span>
            <Text type="secondary">{record.type}</Text>
            {record.comment ? <CommentOutlined aria-label="Has reviewer note" /> : null}
          </div>
          <Text className="queue-request__title">{record.title}</Text>
          <Text className="queue-request__agent">{record.agent}</Text>
        </div>
      ),
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      width: 124,
      render: (value: QueuePriority) => (
        <Tag className={`queue-priority ${PRIORITY_META[value].className}`}>{value}</Tag>
      ),
    },
    {
      title: 'AI confidence',
      dataIndex: 'confidence',
      key: 'confidence',
      width: 150,
      render: (value: number) => (
        <div className="queue-confidence">
          <Progress
            percent={value}
            showInfo={false}
            size="small"
            strokeColor={value >= 80 ? '#16a34a' : value >= 50 ? '#d97706' : '#dc2626'}
          />
          <Text>{value}%</Text>
        </div>
      ),
    },
    {
      title: 'Due',
      dataIndex: 'dueBy',
      key: 'dueBy',
      width: 145,
      render: (value: string, record: QueueItem) => {
        const label = formatDueDate(value);
        const urgent = record.priority === 'Critical' && isOpen(record.status);
        return (
          <Space size={6} className={urgent ? 'queue-due queue-due--urgent' : 'queue-due'}>
            <ClockCircleOutlined />
            <Text>{label}</Text>
          </Space>
        );
      },
    },
  ];

  return (
    <PageContainer maxWidth={1480}>
      <header className="queue-header">
        <div>
          <div className="queue-eyebrow">Decision operations</div>
          <Title level={2}>Human approval queue</Title>
          <Text type="secondary">
            Review the exceptions that need judgment, context, or policy approval.
          </Text>
        </div>
        <div className="queue-summary" aria-label={`${openCount} open requests, ${criticalCount} critical`}>
          <div>
            <strong>{openCount}</strong>
            <span>Open</span>
          </div>
          <div className="queue-summary__critical">
            <strong>{criticalCount}</strong>
            <span>Critical</span>
          </div>
        </div>
      </header>

      <Panel bodyStyle={{ padding: 0 }} style={{ overflow: 'hidden' }}>
        <div className="queue-toolbar">
          <Input
            allowClear
            prefix={<SearchOutlined />}
            placeholder="Search ticket, request, or agent"
            value={search}
            onChange={event => setSearch(event.target.value)}
            className="queue-search"
            aria-label="Search approval queue"
          />
          <div className="queue-filters">
            <FilterOutlined className="queue-filter-icon" aria-hidden="true" />
            <Select
              value={priority}
              onChange={setPriority}
              aria-label="Filter by priority"
              options={['All', 'Critical', 'High', 'Medium', 'Low'].map(value => ({
                value,
                label: value === 'All' ? 'All priorities' : value,
              }))}
            />
            <Select
              value={status}
              onChange={setStatus}
              aria-label="Filter by status"
              options={[
                { value: 'Open', label: 'Open requests' },
                { value: 'All', label: 'All statuses' },
                { value: 'Approved', label: 'Approved' },
                { value: 'Rejected', label: 'Rejected' },
              ]}
            />
          </div>
        </div>

        <Table<QueueItem>
          className="queue-table"
          dataSource={filteredData}
          columns={columns}
          rowKey="id"
          pagination={false}
          size="middle"
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No requests match these filters" /> }}
          onRow={record => ({
            onClick: () => selectItem(record),
            onKeyDown: event => {
              if (event.key === 'Enter' || event.key === ' ') selectItem(record);
            },
            tabIndex: 0,
            role: 'button',
            'aria-label': `Review ${record.id}: ${record.title}`,
          })}
          rowClassName={record => (record.id === activeItem?.id ? 'queue-row--selected' : '')}
          scroll={{ x: 760 }}
        />
      </Panel>

      <Drawer
        className="queue-review-drawer"
        title={null}
        width={540}
        open={Boolean(activeItem)}
        onClose={() => setActiveItem(null)}
        destroyOnClose
      >
        {activeItem ? (
          <div className="queue-review">
            <div className="queue-review__topline">
              <Space size={8}>
                <Badge color={PRIORITY_META[activeItem.priority].color} />
                <Text className="queue-ticket-id">{activeItem.id}</Text>
                <Text type="secondary">{activeItem.type}</Text>
              </Space>
              <Tag className={`queue-priority ${PRIORITY_META[activeItem.priority].className}`}>
                {activeItem.priority}
              </Tag>
            </div>

            <Title level={3}>{activeItem.title}</Title>

            <div className="queue-review__due">
              <ClockCircleOutlined />
              <span>{formatDueDate(activeItem.dueBy)}</span>
              <span aria-hidden="true">·</span>
              <span>Submitted {formatSubmittedAt(activeItem.submittedAt)}</span>
            </div>

            <section className="queue-review__section">
              <div className="queue-section-label">
                <ExclamationCircleOutlined />
                Reason for escalation
              </div>
              <p>{activeItem.reason}</p>
            </section>

            <section className="queue-ai-card">
              <div className="queue-ai-card__header">
                <div>
                  <RobotOutlined />
                  <Text strong>{activeItem.agent}</Text>
                </div>
                <Text strong>{activeItem.confidence}% confidence</Text>
              </div>
              <Progress
                percent={activeItem.confidence}
                showInfo={false}
                strokeColor={activeItem.confidence >= 80 ? '#16a34a' : '#d97706'}
              />
              <Text type="secondary">
                This request was escalated because confidence is below the 80% automatic-decision threshold.
              </Text>
            </section>

            <section className="queue-review__section">
              <button
                type="button"
                className="queue-chat-toggle"
                onClick={() => setAiChatOpen(open => !open)}
                aria-expanded={aiChatOpen}
              >
                <span className="queue-chat-toggle__icon">
                  <RobotOutlined />
                </span>
                <span>
                  <strong>Chat with AI agent</strong>
                  <small>Ask for reasoning or supporting context</small>
                </span>
                <span className="queue-chat-toggle__action">{aiChatOpen ? 'Hide preview' : 'Open preview'}</span>
              </button>

              {aiChatOpen ? (
                <div className="queue-chat-preview">
                  <div className="queue-development-notice" role="note">
                    AI Agent Chat is in progress. Real-time conversations with escalation agents will be available in a future release.
                  </div>

                  <div className="queue-chat-preview__disabled" aria-disabled="true">
                    <div className="queue-chat-message queue-chat-message--agent">
                      <span className="queue-chat-avatar"><RobotOutlined /></span>
                      <div>
                        <Text strong>{activeItem.agent}</Text>
                        <p>
                          I escalated {activeItem.id} because the request conflicts with an approval rule and my confidence is {activeItem.confidence}%.
                          I can explain the evidence used in this assessment.
                        </p>
                      </div>
                    </div>
                    <div className="queue-chat-message queue-chat-message--user">
                      <span className="queue-chat-avatar"><UserOutlined /></span>
                      <div>
                        <Text strong>You</Text>
                        <p>Show me the policy and evidence behind this escalation.</p>
                      </div>
                    </div>
                    <div className="queue-chat-composer">
                      <Input value="Ask about this request…" readOnly />
                      <Button type="primary" icon={<SendOutlined />} aria-label="Send message" />
                    </div>
                  </div>
                </div>
              ) : null}
            </section>

            <section className="queue-review__section queue-review__metadata">
              <div>
                <span>Status</span>
                <strong>{activeItem.status}</strong>
              </div>
              <div>
                <span>Escalated by</span>
                <strong>{activeItem.agent}</strong>
              </div>
              <div>
                <span>Due date</span>
                <strong>{activeItem.dueBy ? formatSubmittedAt(activeItem.dueBy) : 'Not set'}</strong>
              </div>
            </section>

            <section className="queue-review__section">
              <div className="queue-development-notice" role="note" style={{ marginBottom: 12 }}>
                Reviewer notes are in progress. The ability to add context notes to escalation decisions will be available in a future release.
              </div>
              <div className="queue-chat-preview__disabled" aria-disabled="true">
              <button
                type="button"
                className="queue-note-toggle"
                aria-expanded={false}
              >
                <span>
                  <CommentOutlined />
                  Reviewer note
                </span>
                <span>{activeItem.comment ? 'Saved' : 'Add note'}</span>
              </button>
              {activeItem.comment ? (
                <p className="queue-saved-note">{activeItem.comment}</p>
              ) : null}
              </div>
            </section>

            <div className="queue-review__actions">
              {isOpen(activeItem.status) ? (
                <>
                  <Button
                    size="large"
                    icon={<CloseOutlined />}
                    onClick={() => handleDecision('Rejected')}
                    danger
                  >
                    Reject
                  </Button>
                  <Button
                    size="large"
                    type="primary"
                    icon={<CheckOutlined />}
                    onClick={() => handleDecision('Approved')}
                    className="queue-approve-button"
                  >
                    Approve request
                  </Button>
                </>
              ) : (
                <div className={`queue-decision queue-decision--${activeItem.status.toLowerCase()}`}>
                  {activeItem.status === 'Approved' ? <CheckOutlined /> : <CloseOutlined />}
                  Request {activeItem.status.toLowerCase()}
                </div>
              )}
            </div>
          </div>
        ) : null}
      </Drawer>
    </PageContainer>
  );
};

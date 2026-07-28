/* eslint-disable @typescript-eslint/no-explicit-any */
import React from 'react';
import { Card, Table, Tag, Typography, Progress } from 'antd';
import {
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

export interface TaskItem {
  id: string;
  title: string;
  description?: string;
  status: 'pending' | 'running' | 'done' | 'failed' | 'timed_out';
  result_preview?: string;
}

interface TaskProgressProps {
  tasks: TaskItem[];
  phase?: string;
}

export const TaskProgress: React.FC<TaskProgressProps> = ({ tasks, phase }) => {
  const phaseLabels: Record<string, string> = {
    understanding: 'Understanding request...',
    planning: 'Planning tasks...',
    executing: 'Executing tasks',
    compiling: 'Compiling results...',
  };

  if (tasks.length === 0 && !phase) return null;

  return (
    <Card
      size="small"
      title={
        <Text strong style={{ fontSize: 12 }}>
          {phase && phaseLabels[phase] ? phaseLabels[phase] : 'Execution Plan'}
        </Text>
      }
      style={{ marginBottom: 8, background: '#f8fafc', border: '1px solid #e2e8f0' }}
      bodyStyle={{ padding: tasks.length > 0 ? 8 : 16 }}
    >
      {phase && tasks.length === 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <LoadingOutlined style={{ color: '#2563eb' }} />
          <Text style={{ fontSize: 12, color: '#64748b' }}>{phaseLabels[phase]}</Text>
        </div>
      )}

      {tasks.length > 0 && (
        <Table<TaskItem>
          dataSource={tasks}
          rowKey="id"
          pagination={false}
          size="small"
          showHeader={false}
          columns={[
            {
              dataIndex: 'id',
              width: 30,
              render: (id: string) => <Text type="secondary" style={{ fontSize: 10 }}>#{id}</Text>,
            },
            {
              title: 'Task',
              dataIndex: 'title',
              render: (title: string, record: TaskItem) => (
                <div>
                  <Text style={{ fontSize: 12 }}>{title}</Text>
                  {record.result_preview && record.status === 'done' && (
                    <Text type="secondary" style={{ fontSize: 10, display: 'block', marginTop: 2 }} ellipsis>
                      {record.result_preview}
                    </Text>
                  )}
                </div>
              ),
            },
            {
              title: 'Status',
              dataIndex: 'status',
              width: 100,
              render: (status: string) => {
                const config: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
                  pending:   { color: 'default', icon: <ClockCircleOutlined />, label: 'Pending' },
                  running:   { color: 'processing', icon: <LoadingOutlined spin />, label: 'Running' },
                  done:      { color: 'success', icon: <CheckCircleOutlined />, label: 'Done' },
                  failed:    { color: 'error', icon: <CloseCircleOutlined />, label: 'Failed' },
                  timed_out: { color: 'warning', icon: <ClockCircleOutlined />, label: 'Timed Out' },
                };
                const c = config[status] || config.pending;
                return <Tag color={c.color} icon={c.icon} style={{ fontSize: 10, margin: 0 }}>{c.label}</Tag>;
              },
            },
          ]}
        />
      )}
    </Card>
  );
};

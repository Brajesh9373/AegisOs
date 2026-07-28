import React from 'react';
import { CheckCircleOutlined, ExperimentOutlined, WarningOutlined } from '@ant-design/icons';
import { Card, Progress, Space, Tag, Typography } from 'antd';

const { Text } = Typography;

interface EvalsTabProps {
  agentName: string;
}

const EVALS = [
  {
    name: 'Instruction following',
    score: 92,
    status: 'passing',
    detail: 'Maintains role scope and follows project guardrails during task execution.',
  },
  {
    name: 'Tool discipline',
    score: 86,
    status: 'passing',
    detail: 'Selects project connectors before attempting external actions.',
  },
  {
    name: 'Escalation clarity',
    score: 78,
    status: 'watch',
    detail: 'Requests human approval for sensitive changes, with room to tighten rationale.',
  },
];

const EvalsTab: React.FC<EvalsTabProps> = ({ agentName }) => (
  <div style={{ padding: '16px 0', display: 'flex', flexDirection: 'column', gap: 12 }}>
    <div>
      <Text style={{ fontSize: 13, fontWeight: 600, color: '#0f172a', display: 'block' }}>
        Evaluation snapshot
      </Text>
      <Text type="secondary" style={{ fontSize: 11 }}>
        Current quality gates for {agentName}
      </Text>
    </div>

    <Card
      size="small"
      style={{ borderRadius: 8, border: '1px solid #e2e8f0' }}
      bodyStyle={{ padding: 14 }}
    >
      <Space align="center" style={{ width: '100%', justifyContent: 'space-between' }}>
        <Space size={10}>
          <ExperimentOutlined style={{ color: '#2563eb', fontSize: 18 }} />
          <div>
            <Text strong style={{ fontSize: 12, display: 'block' }}>Overall readiness</Text>
            <Text type="secondary" style={{ fontSize: 10 }}>Weighted by recent run history</Text>
          </div>
        </Space>
        <Progress type="circle" percent={85} size={44} strokeColor="#2563eb" />
      </Space>
    </Card>

    {EVALS.map((item) => {
      const isPassing = item.status === 'passing';
      return (
        <Card
          key={item.name}
          size="small"
          style={{ borderRadius: 8, border: '1px solid #e2e8f0' }}
          bodyStyle={{ padding: 12 }}
        >
          <Space align="start" style={{ width: '100%', justifyContent: 'space-between' }}>
            <Space align="start" size={10}>
              {isPassing ? (
                <CheckCircleOutlined style={{ color: '#16a34a', marginTop: 3 }} />
              ) : (
                <WarningOutlined style={{ color: '#d97706', marginTop: 3 }} />
              )}
              <div>
                <Text strong style={{ fontSize: 12, display: 'block' }}>{item.name}</Text>
                <Text type="secondary" style={{ fontSize: 10, lineHeight: 1.5 }}>
                  {item.detail}
                </Text>
              </div>
            </Space>
            <Tag color={isPassing ? 'green' : 'orange'} style={{ margin: 0, fontSize: 10 }}>
              {item.score}%
            </Tag>
          </Space>
        </Card>
      );
    })}
  </div>
);

export default EvalsTab;

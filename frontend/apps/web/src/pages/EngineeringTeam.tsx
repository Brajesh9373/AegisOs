import React, { useState } from 'react';
import { Button, Card, Col, Input, Row, Select, Space, Spin, Tag, Typography } from 'antd';
import { RobotOutlined, SendOutlined, TeamOutlined } from '@ant-design/icons';
import {
  createTeam,
  deleteTeam,
  delegateTask,
  listTeams,
  sendMessage,
  type HierarchyAgentInfo,
  type HierarchyTeam
} from '../api/hierarchy';
import { useTeamStatus } from '../hooks/useHierarchy';
import { ApiClient } from '../api/client';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

interface ChatEntry {
  from: 'you' | 'agent';
  text: string;
  ms?: number;
}

const STATUS_COLOR: Record<string, string> = { idle: 'green', working: 'processing', dead: 'red' };

function AgentCard({
  teamId,
  agent,
  liveStatus
}: {
  teamId: string;
  agent: HierarchyAgentInfo;
  liveStatus?: string;
}) {
  const [draft, setDraft] = useState('');
  const [history, setHistory] = useState<ChatEntry[]>([]);
  const [sending, setSending] = useState(false);
  const status = liveStatus ?? agent.status;

  const send = async () => {
    const content = draft.trim();
    if (!content || sending) return;
    setDraft('');
    setSending(true);
    setHistory(h => [...h, { from: 'you', text: content }]);
    try {
      const res = await sendMessage(teamId, agent.agent_id, content);
      setHistory(h => [...h, { from: 'agent', text: res.response, ms: res.duration_ms }]);
    } catch (err) {
      ApiClient.handleError(err);
      setHistory(h => [...h, { from: 'agent', text: '(request failed — see notification)' }]);
    } finally {
      setSending(false);
    }
  };

  return (
    <Card
      title={
        <Space>
          <RobotOutlined />
          <Text strong>{agent.agent_id}</Text>
        </Space>
      }
      extra={<Tag color={STATUS_COLOR[status] ?? 'default'}>{status.toUpperCase()}</Tag>}
      style={{ height: '100%' }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="small">
        <Text type="secondary">{agent.profile_id} · {agent.role}</Text>
        <Text type="secondary" style={{ fontSize: 11 }}>session: {agent.session_id}</Text>
        <div style={{ maxHeight: 220, overflowY: 'auto', width: '100%' }}>
          {history.length === 0 && <Text type="secondary">No messages yet.</Text>}
          {history.map((m, i) => (
            <Paragraph
              key={i}
              style={{
                background: m.from === 'you' ? '#f0f5ff' : '#f6ffed',
                padding: '6px 10px',
                borderRadius: 6
              }}
            >
              <Text strong>{m.from === 'you' ? 'You' : agent.agent_id}: </Text>
              {m.text}
              {m.ms !== undefined && <Text type="secondary"> ({(m.ms / 1000).toFixed(1)}s)</Text>}
            </Paragraph>
          ))}
          {sending && <Spin size="small" tip="Agent is thinking…" />}
        </div>
        <Space.Compact style={{ width: '100%' }}>
          <Input
            value={draft}
            onChange={e => setDraft(e.target.value)}
            onPressEnter={send}
            placeholder={`Message ${agent.agent_id}…`}
            disabled={sending}
          />
          <Button type="primary" icon={<SendOutlined />} onClick={send} loading={sending} />
        </Space.Compact>
      </Space>
    </Card>
  );
}

export const EngineeringTeam = () => {
  const [team, setTeam] = useState<HierarchyTeam | null>(null);
  const [busy, setBusy] = useState(false);
  const [delegateTaskText, setDelegateTaskText] = useState('');
  const [delegateFrom, setDelegateFrom] = useState('');
  const [delegateTo, setDelegateTo] = useState('');
  const [delegateResult, setDelegateResult] = useState<string | null>(null);
  const [delegating, setDelegating] = useState(false);
  const { data: liveStatuses } = useTeamStatus(team?.team_id ?? null, 3000);

  const statusOf = (agentId: string) =>
    liveStatuses?.find(s => s.agent_id === agentId)?.status;

  const spawn = async () => {
    setBusy(true);
    try {
      const created = await createTeam();
      setTeam(created);
      setDelegateFrom(created.agents[0]?.agent_id ?? '');
      setDelegateTo(created.agents[1]?.agent_id ?? '');
    } catch (err) {
      ApiClient.handleError(err);
    } finally {
      setBusy(false);
    }
  };

  const refresh = async () => {
    try {
      const teams = await listTeams();
      if (teams.length > 0) setTeam(teams[teams.length - 1]);
    } catch (err) {
      ApiClient.handleError(err);
    }
  };

  const destroy = async () => {
    if (!team) return;
    setBusy(true);
    try {
      await deleteTeam(team.team_id);
      setTeam(null);
      setDelegateResult(null);
    } catch (err) {
      ApiClient.handleError(err);
    } finally {
      setBusy(false);
    }
  };

  const runDelegation = async () => {
    if (!team || !delegateFrom || !delegateTo || !delegateTaskText.trim()) return;
    setDelegating(true);
    setDelegateResult(null);
    try {
      const res = await delegateTask(team.team_id, delegateFrom, delegateTo, delegateTaskText.trim());
      setDelegateResult(res.response ?? '(no response — the child may have timed out)');
    } catch (err) {
      ApiClient.handleError(err);
    } finally {
      setDelegating(false);
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <Space style={{ width: '100%', justifyContent: 'space-between' }}>
        <Title level={3} style={{ margin: 0 }}>
          <TeamOutlined /> Engineering Team
        </Title>
        <Space>
          <Button onClick={refresh}>Refresh</Button>
          {team ? (
            <Button danger onClick={destroy} loading={busy}>
              Stop team
            </Button>
          ) : (
            <Button type="primary" onClick={spawn} loading={busy}>
              Spawn HOE team
            </Button>
          )}
        </Space>
      </Space>
      <Paragraph type="secondary">
        Live Head-of-Engineering team over persistent DSH sessions. Spawn takes ~2s warm;
        each reply typically lands in ~5s.
      </Paragraph>

      {!team && (
        <Card>
          <Text type="secondary">
            No live team. Spawn one to chat with the Head of Engineering and the senior
            Frontend / Backend engineers.
          </Text>
        </Card>
      )}

      {team && (
        <>
          <Row gutter={16}>
            {team.agents.map(agent => (
              <Col span={8} key={agent.agent_id}>
                <AgentCard teamId={team.team_id} agent={agent} liveStatus={statusOf(agent.agent_id)} />
              </Col>
            ))}
          </Row>

          <Card title="Delegate a task" style={{ marginTop: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <Select
                  value={delegateFrom}
                  onChange={setDelegateFrom}
                  style={{ width: 260 }}
                  options={team.agents.map(a => ({ value: a.agent_id, label: a.agent_id }))}
                />
                <Text>→</Text>
                <Select
                  value={delegateTo}
                  onChange={setDelegateTo}
                  style={{ width: 260 }}
                  options={team.agents.map(a => ({ value: a.agent_id, label: a.agent_id }))}
                />
                <Button type="primary" onClick={runDelegation} loading={delegating}>
                  Delegate
                </Button>
              </Space>
              <TextArea
                rows={2}
                value={delegateTaskText}
                onChange={e => setDelegateTaskText(e.target.value)}
                placeholder="Task for the child agent…"
              />
              {delegating && <Spin size="small" tip="Waiting for the child agent…" />}
              {delegateResult && (
                <Paragraph style={{ background: '#f6ffed', padding: '6px 10px', borderRadius: 6 }}>
                  <Text strong>Result: </Text>
                  {delegateResult}
                </Paragraph>
              )}
            </Space>
          </Card>
        </>
      )}
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { Typography, Row, Col, Button, Space, Tag, Progress, Table, Timeline, Avatar, Input, Tooltip, Divider, Modal, Form, message, List, Tabs, Card, ConfigProvider, Select, Upload } from 'antd';
import { ArrowLeftOutlined, FileTextOutlined, DeleteOutlined, BookOutlined, SafetyCertificateOutlined, FilePdfOutlined, DownloadOutlined, HistoryOutlined, SyncOutlined, SendOutlined, UserOutlined, RobotOutlined, BankOutlined, CrownOutlined, DesktopOutlined, FolderOpenOutlined, CalendarOutlined, TeamOutlined, BulbOutlined, PlusOutlined, FileExcelOutlined, FileZipOutlined, CheckOutlined, CloseOutlined, CodeOutlined, CheckCircleOutlined, PlayCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { Panel } from '../components/ui/Panel';
import { PageContainer } from '../components/ui/PageContainer';
import { ApiClient } from '../api/client';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

interface ProjectMeeting {
  id: string;
  date: string;
  participants: string[];
  agenda: string;
  notes: string;
  actionItems: string[];
  decisions: string[];
  attachments: string[];
}

interface TimelineEvent {
  color: string;
  type: string;
  title: string;
  time: string;
  owner: string;
  desc?: string;
}

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

interface MeetingData {
  time: string; title: string; participants: string[]; type: 'human' | 'agent' | 'both';
  past?: boolean; totalAttendees?: number; humanCount?: number; agentCount?: number;
  summary?: string; decisions?: string[]; recording?: string; duration?: string;
}

const SCHEDULED_MEETINGS: Record<string, MeetingData[]> = {
  '2026-07-07': [
    {
      time: '10:00 AM', title: 'Initial Requirement Gathering', participants: ['Current User', 'Sarah Jenkins', 'Business Analyst Agent'], type: 'both', past: true,
      totalAttendees: 3, humanCount: 2, agentCount: 1, duration: '48 min',
      summary: 'First meeting to discuss the migration from Adrenaline to Frappe HR. Client explained the current tech stack (PHP/Python/Node backends, React/Angular/Android frontends), database architecture (MySQL master with 450 tables, MongoDB staging), and GCP Pub/Sub pipeline. Identified 2000+ field employees as primary users. Discussed the need for real-time MySQL sync and mobile app rollout.',
      decisions: ['Migration target: Self-hosted Frappe HR on GCP', 'Scope: Full employee lifecycle (onboarding, attendance, leave, payroll)', 'Timeline: 3 months with phased rollout'],
      recording: 'initial-requirement-gathering-2026-07-07.mp4',
    },
  ],
  '2026-07-09': [
    {
      time: '02:00 PM', title: 'Technical Architecture Review', participants: ['Current User', 'Sarah Jenkins', 'Migration Orchestrator', 'Sync Pipeline Engineer'], type: 'both', past: true,
      totalAttendees: 4, humanCount: 2, agentCount: 2, duration: '1 hr 12 min',
      summary: 'Deep dive into the technical architecture for the migration. Reviewed Adrenaline database schema (150 master tables, 300 transaction tables). Discussed Frappe HR DocType mapping strategy. Evaluated GCP Pub/Sub topic structure for HR events. Reviewed MySQL sync latency requirements (< 2 seconds). Explored webhook integration for the Mongo monitoring tool.',
      decisions: ['Use GCP Pub/Sub with 3 topics: hr-events, sync-status, migration-progress', 'MySQL sync via idempotent writes with conflict resolution', 'Mongo monitoring tool receives webhook notifications only (no direct DB access)', 'Frappe HR mobile app replaces Android APK for field employees'],
      recording: 'technical-architecture-review-2026-07-09.mp4',
    },
  ],
  '2026-07-11': [
    {
      time: '09:00 AM', title: 'Adrenaline Schema Deep Dive', participants: ['Data Migration Specialist', 'Sync Pipeline Engineer', 'Migration Orchestrator'], type: 'agent', past: true,
      totalAttendees: 3, humanCount: 0, agentCount: 3, duration: '55 min',
      summary: 'Detailed analysis of Adrenaline database schema. Mapped all 150 master tables to Frappe HR DocTypes. Identified 47 fields requiring custom mapping (designation, location, status fields). Reviewed employee lifecycle data flow: onboarding → active → relieved. Analyzed dependencies between Adrenaline and MySQL for transaction blocking on relieved employees.',
      decisions: ['Priority mapping: employee_master, designation, location tables first', 'Custom field mapping for 47 fields documented in Frappe_HR_DocTypes_Map.xlsx', 'Employee status sync must propagate within 2 seconds to MySQL'],
      recording: 'adrenaline-schema-deep-dive-2026-07-11.mp4',
    },
    {
      time: '03:00 PM', title: 'Security & Compliance Review', participants: ['Current User', 'Sarah Jenkins', 'Migration Orchestrator'], type: 'both', past: true,
      totalAttendees: 3, humanCount: 2, agentCount: 1, duration: '40 min',
      summary: 'Reviewed security and compliance requirements for the migration. Discussed PII encryption (AES-256 at rest, TLS 1.3 in transit), RBAC for migration scripts (HR Admins only), and audit trail requirements. Covered SOC2 Type II controls and GDPR compliance for employee data. Reviewed data retention policies and right-to-deletion handling during migration.',
      decisions: ['All employee PII encrypted at rest and in transit', 'RBAC: only HR Admins can modify migration mappings', 'SOC2 Type II controls applied throughout migration', 'Adrenaline runs in read-only mode for 7 days post-cutover'],
      recording: 'security-compliance-review-2026-07-11.mp4',
    },
  ],
  '2026-07-14': [
    {
      time: '11:00 AM', title: 'Migration Plan Finalization', participants: ['Current User', 'Sarah Jenkins', 'Business Analyst Agent', 'Migration Orchestrator'], type: 'both', past: true,
      totalAttendees: 4, humanCount: 2, agentCount: 2, duration: '1 hr 25 min',
      summary: 'Finalized the 3-phase migration plan. Phase 1 (Month 1): Engineering department — set up Frappe HR instance, configure MySQL sync, migrate engineering employee data. Phase 2 (Month 2): Field operations — migrate field employee data, deploy mobile app, update Pub/Sub pipeline. Phase 3 (Month 3): Full cutover — complete migration, decommission Adrenaline, enable webhooks. Reviewed infrastructure requirements (GKE Autopilot, Cloud SQL, VPC peering).',
      decisions: ['Phase 1 starts July 15 with Engineering department', 'GKE Autopilot cluster (2-6 nodes) for Frappe HR', 'Cloud SQL PostgreSQL (HA) for Frappe HR database', 'Point-in-time recovery snapshots before each phase', 'Rollback procedure: automatic rollback within 15 minutes if validation fails'],
      recording: 'migration-plan-finalization-2026-07-14.mp4',
    },
  ],
  '2026-07-15': [
    { time: '10:00 AM', title: 'BA Requirement Finalization', participants: ['Current User', 'Business Analyst Agent'], type: 'agent' },
    { time: '02:00 PM', title: 'Migration Kickoff — Engineering', participants: ['Current User', 'Sarah Jenkins', 'Migration Orchestrator'], type: 'both' },
  ],
  '2026-07-16': [
    { time: '09:30 AM', title: 'Adrenaline Schema Review', participants: ['Data Migration Specialist', 'Sync Pipeline Engineer'], type: 'agent' },
    { time: '11:00 AM', title: 'Sprint Planning — Phase 1', participants: ['Current User', 'Sarah Jenkins'], type: 'human' },
  ],
  '2026-07-17': [
    { time: '10:00 AM', title: 'Frappe HR DocType Mapping', participants: ['Data Migration Specialist'], type: 'agent' },
  ],
  '2026-07-18': [
    { time: '03:00 PM', title: 'GCP Infra Review', participants: ['Current User', 'Sync Pipeline Engineer'], type: 'both' },
  ],
  '2026-07-21': [
    { time: '09:00 AM', title: 'Phase 1 Progress Review', participants: ['Current User', 'Sarah Jenkins', 'Migration Orchestrator'], type: 'both' },
    { time: '02:00 PM', title: 'MySQL Sync Validation', participants: ['Data Migration Specialist', 'Sync Pipeline Engineer'], type: 'agent' },
  ],
  '2026-07-22': [
    { time: '10:00 AM', title: 'Mobile App Demo', participants: ['Current User', 'Sarah Jenkins'], type: 'human' },
  ],
  '2026-07-23': [
    { time: '11:00 AM', title: 'Pub/Sub Pipeline Review', participants: ['Sync Pipeline Engineer', 'Migration Orchestrator'], type: 'agent' },
  ],
  '2026-07-25': [
    { time: '04:00 PM', title: 'Week 2 Retrospective', participants: ['Current User', 'Sarah Jenkins', 'Migration Orchestrator'], type: 'both' },
  ],
  '2026-07-28': [
    { time: '09:00 AM', title: 'Phase 2 Kickoff — Field Ops', participants: ['Current User', 'Sarah Jenkins', 'Migration Orchestrator', 'Data Migration Specialist'], type: 'both' },
  ],
  '2026-07-30': [
    { time: '10:00 AM', title: 'Frappe HR Mobile App Testing', participants: ['Current User', 'Data Migration Specialist'], type: 'both' },
  ],
};

// Inline recording player. A raw <video src> can't send the Bearer token, so we
// fetch the file as an authenticated blob and play it via an object URL.
function RecordingPlayer({ projectId, meetingId, name }: { projectId: string; meetingId: string; name?: string }) {
  const [url, setUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(false);
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`/api/projects/${projectId}/meetings/${meetingId}/recording`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error('fetch failed');
      const blob = await res.blob();
      setUrl(URL.createObjectURL(blob));
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Revoke the object URL on unmount to avoid leaks.
    return () => { if (url) URL.revokeObjectURL(url); };
  }, [url]);

  if (url) {
    return <video src={url} controls style={{ width: '100%', borderRadius: 8, background: '#000', maxHeight: 360 }} />;
  }

  return (
    <Card size="small" style={{ background: '#1e293b', borderRadius: 8, border: 'none' }} bodyStyle={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 16 }}>
      <div style={{ width: 48, height: 48, borderRadius: 8, background: '#334155', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <PlayCircleOutlined style={{ fontSize: 24, color: '#fff' }} />
      </div>
      <div style={{ flex: 1 }}>
        <Text style={{ fontSize: 12, color: '#fff', display: 'block' }}>{name || 'Recording'}</Text>
        <Text style={{ fontSize: 10, color: '#94a3b8' }}>{error ? 'Could not load recording' : 'Click play to load'}</Text>
      </div>
      <Button size="small" type="primary" icon={<PlayCircleOutlined />} loading={loading} onClick={load} style={{ background: '#2563eb' }}>Play</Button>
    </Card>
  );
}

function CalendarView({ meetings, onAddMeeting, isMigration, projectId, onDeleteMeeting }: { meetings: any[]; onAddMeeting: () => void; isMigration: boolean; projectId?: string; onDeleteMeeting?: (id: string) => void }) {
  const meetingsByDate: Record<string, MeetingData[]> = React.useMemo(() => {
    if (isMigration) return SCHEDULED_MEETINGS;
    const map: Record<string, MeetingData[]> = {};
    for (const m of meetings) {
      if (!m.date) continue;
      const parts: string[] = Array.isArray(m.participants) ? m.participants : [];
      const isAgent = (p: string) => /agent|specialist|engineer|orchestrator|analyst|lead|architect|manager|director/i.test(p);
      const agentCount = parts.filter(isAgent).length;
      const humanCount = parts.length - agentCount;
      const md: MeetingData = {
        time: m.time || 'All day',
        title: m.title,
        participants: parts,
        type: (m.type as 'human' | 'agent' | 'both') || 'both',
        past: !!m.past,
        totalAttendees: m.totalAttendees ?? parts.length,
        humanCount,
        agentCount,
        summary: m.summary,
        decisions: m.decisions || [],
        recording: m.recording || undefined,
        duration: m.duration || undefined,
      };
      (md as any).id = m.id;
      (md as any).hasRecording = m.hasRecording;
      (md as any).agenda = m.agenda;
      (md as any).source = m.source;
      (map[m.date] = map[m.date] || []).push(md);
    }
    return map;
  }, [isMigration, meetings]);

  const initialMonth = React.useMemo(() => {
    if (isMigration) return new Date(2026, 6, 1);
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1);
  }, [isMigration]);

  const [currentMonth, setCurrentMonth] = useState(initialMonth);
  const [selectedDate, setSelectedDate] = useState<string | null>(isMigration ? '2026-07-15' : null);
  const [selectedPastMeeting, setSelectedPastMeeting] = useState<MeetingData | null>(null);

  React.useEffect(() => {
    if (isMigration) return;
    const todayStr = new Date().toISOString().slice(0, 10);
    if (meetingsByDate[todayStr]) {
      setSelectedDate(todayStr);
    }
  }, [isMigration, meetings.length]);

  const year = currentMonth.getFullYear();
  const month = currentMonth.getMonth();
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const today = new Date().toISOString().slice(0, 10);

  const calendarDays: (number | null)[] = [];
  for (let i = 0; i < firstDay; i++) calendarDays.push(null);
  for (let d = 1; d <= daysInMonth; d++) calendarDays.push(d);

  const formatDate = (d: number) => `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;

  const selectedMeetings = selectedDate ? (meetingsByDate[selectedDate] || []) : [];

  const upcomingList = React.useMemo(() => {
    return Object.entries(meetingsByDate)
      .filter(([date]) => date >= today)
      .sort(([a], [b]) => a.localeCompare(b))
      .flatMap(([date, meets]) => meets.filter(m => !m.past).map(m => ({ ...m, date })))
      .slice(0, 5);
  }, [meetingsByDate, today]);

  const prevMonth = () => setCurrentMonth(new Date(year, month - 1, 1));
  const nextMonth = () => setCurrentMonth(new Date(year, month + 1, 1));

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Button size="small" onClick={prevMonth}>&lt;</Button>
          <Text strong style={{ fontSize: 16, color: '#0f172a', minWidth: 180, textAlign: 'center' }}>{MONTHS[month]} {year}</Text>
          <Button size="small" onClick={nextMonth}>&gt;</Button>
        </div>
        <Space>
          <Button size="small" onClick={() => setCurrentMonth(new Date())}>Today</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={onAddMeeting} style={{ background: '#2563EB' }}>Schedule Meeting</Button>
        </Space>
      </div>

      <Row gutter={20}>
        <Col span={16}>
          <div style={{ background: '#fff', borderRadius: 8, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
              {DAYS.map(d => (
                <div key={d} style={{ padding: '10px 8px', textAlign: 'center', fontSize: 11, fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>{d}</div>
              ))}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)' }}>
              {calendarDays.map((day, idx) => {
                if (!day) return <div key={idx} style={{ minHeight: 80, borderRight: '1px solid #f1f5f9', borderBottom: '1px solid #f1f5f9' }} />;
                const dateStr = formatDate(day);
                const dayMeetings = meetingsByDate[dateStr] || [];
                const isSelected = selectedDate === dateStr;
                const isToday = dateStr === today;

                return (
                  <div key={idx} onClick={() => setSelectedDate(dateStr)} style={{ minHeight: 80, padding: 6, cursor: 'pointer', borderRight: '1px solid #f1f5f9', borderBottom: '1px solid #f1f5f9', background: isSelected ? '#eff6ff' : isToday ? '#fef3c7' : '#fff', border: isSelected ? '2px solid #2563eb' : undefined }}>
                    <div style={{ fontSize: 12, fontWeight: isToday ? 700 : 500, color: isToday ? '#b45309' : '#334155', marginBottom: 4, textAlign: 'right', paddingRight: 4 }}>{day}</div>
                    {dayMeetings.slice(0, 2).map((m, i) => {
                      const isTBD = m.time === 'TBD';
                      return (
                        <div key={i} style={{ fontSize: 9, padding: '2px 4px', marginBottom: 2, borderRadius: 3, background: m.past ? '#e5e7eb' : isTBD ? '#fef3c7' : m.type === 'agent' ? '#dbeafe' : m.type === 'human' ? '#f3e8ff' : '#dcfce7', color: m.past ? '#6b7280' : isTBD ? '#92400e' : m.type === 'agent' ? '#1e40af' : m.type === 'human' ? '#6b21a8' : '#166534', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', textDecoration: m.past ? 'line-through' : 'none', border: isTBD ? '1px dashed #f59e0b' : 'none' }}>
                          {m.past ? '\u2713 ' : ''}{isTBD ? 'TBD' : m.time} {m.title}
                        </div>
                      );
                    })}
                    {dayMeetings.length > 2 && <div style={{ fontSize: 9, color: '#64748b', textAlign: 'center' }}>+{dayMeetings.length - 2} more</div>}
                  </div>
                );
              })}
            </div>
          </div>

          <div style={{ display: 'flex', gap: 16, marginTop: 12, fontSize: 11, flexWrap: 'wrap' }}>
            <Space size={4}><div style={{ width: 10, height: 10, borderRadius: 2, background: '#dbeafe' }} /><Text type="secondary">Agent Meeting</Text></Space>
            <Space size={4}><div style={{ width: 10, height: 10, borderRadius: 2, background: '#f3e8ff' }} /><Text type="secondary">Human Meeting</Text></Space>
            <Space size={4}><div style={{ width: 10, height: 10, borderRadius: 2, background: '#dcfce7' }} /><Text type="secondary">Joint Meeting</Text></Space>
            <Space size={4}><div style={{ width: 10, height: 10, borderRadius: 2, background: '#e5e7eb' }} /><Text type="secondary">Past Meeting</Text></Space>
            <Space size={4}><div style={{ width: 10, height: 10, borderRadius: 2, background: '#fef3c7', border: '1px dashed #f59e0b' }} /><Text type="secondary">Time TBD</Text></Space>
          </div>
        </Col>

        <Col span={8}>
          <Card size="small" style={{ borderRadius: 8, border: '1px solid #e2e8f0' }} bodyStyle={{ padding: 16 }}
            title={<Text strong style={{ fontSize: 13 }}>{selectedDate ? new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' }) : 'Select a date'}</Text>}
          >
            {selectedMeetings.length === 0 && (
              <div style={{ textAlign: 'center', padding: '20px 0', color: '#94a3b8' }}>
                <CalendarOutlined style={{ fontSize: 24, marginBottom: 8 }} />
                <div style={{ fontSize: 12 }}>No meetings scheduled</div>
                <Button size="small" type="link" onClick={onAddMeeting}>Schedule one</Button>
              </div>
            )}
            {selectedMeetings.map((m, i) => {
              const isTBD = m.time === 'TBD';
              const isPast = m.past;
              return (
                <div key={i} onClick={() => isPast && setSelectedPastMeeting(m)} style={{ marginBottom: 12, padding: 10, borderRadius: 6, cursor: isPast ? 'pointer' : 'default', background: isPast ? '#f3f4f6' : isTBD ? '#fffbeb' : m.type === 'agent' ? '#f0f9ff' : m.type === 'human' ? '#faf5ff' : '#f0fdf4', border: isTBD ? '2px dashed #f59e0b' : `1px solid ${isPast ? '#d1d5db' : m.type === 'agent' ? '#bfdbfe' : m.type === 'human' ? '#e9d5ff' : '#bbf7d0'}`, opacity: isPast ? 0.8 : 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <Text strong style={{ fontSize: 12, textDecoration: isPast ? 'line-through' : 'none', color: isPast ? '#6b7280' : '#0f172a' }}>{m.title}</Text>
                    <Space size={4}>
                      {isPast && <Tag color="default" style={{ fontSize: 9, margin: 0 }}>Completed</Tag>}
                      {isTBD && <Tag color="orange" style={{ fontSize: 9, margin: 0 }}><ClockCircleOutlined /> Time TBD</Tag>}
                      <Tag color={m.type === 'agent' ? 'blue' : m.type === 'human' ? 'purple' : 'green'} style={{ fontSize: 9, margin: 0 }}>{m.type}</Tag>
                    </Space>
                  </div>
                  <Text type="secondary" style={{ fontSize: 10, display: 'block', color: isTBD ? '#d97706' : undefined }}>
                    {isTBD ? 'Time TBD \u2014 awaiting confirmation' : m.time}{m.duration && !isTBD ? ` \u00b7 ${m.duration}` : ''}
                  </Text>
                  <div style={{ marginTop: 6 }}>
                    {m.participants.map((p, j) => (
                      <Tag key={j} style={{ fontSize: 9, marginBottom: 2, opacity: isPast ? 0.7 : 1 }}>{p}</Tag>
                    ))}
                  </div>
                  {isPast && <Text type="secondary" style={{ fontSize: 9, display: 'block', marginTop: 4, color: '#2563eb' }}>Click to view details \u2192</Text>}
                  {!isPast && onDeleteMeeting && (m as any).id && (
                    <Button size="small" danger type="text" icon={<DeleteOutlined />}
                      onClick={(e: any) => { e.stopPropagation(); onDeleteMeeting((m as any).id); }}
                      style={{ marginTop: 4, fontSize: 10 }}>Delete</Button>
                  )}
                </div>
              );
            })}
          </Card>

          <Card size="small" style={{ borderRadius: 8, border: '1px solid #e2e8f0', marginTop: 12 }} bodyStyle={{ padding: 12 }}
            title={<Text strong style={{ fontSize: 12 }}>Upcoming This Week</Text>}
          >
            {upcomingList.length === 0 && <Text type="secondary" style={{ fontSize: 11 }}>No upcoming meetings</Text>}
            {upcomingList.map((m: any, i: number) => {
              const isTBD = m.time === 'TBD';
              return (
                <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'flex-start' }}>
                  <div style={{ width: 4, height: 4, borderRadius: '50%', background: m.type === 'agent' ? '#2563eb' : m.type === 'human' ? '#7c3aed' : '#16a34a', marginTop: 5, flexShrink: 0 }} />
                  <div>
                    <Text style={{ fontSize: 11, display: 'block' }}>{m.title}</Text>
                    <Text type="secondary" style={{ fontSize: 9, color: isTBD ? '#d97706' : undefined }}>
                      {new Date(m.date + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })} \u00b7 {isTBD ? 'Time TBD' : m.time}
                    </Text>
                  </div>
                </div>
              );
            })}
          </Card>
        </Col>
      </Row>

      <Modal title={<Space><CheckCircleOutlined style={{ color: '#16a34a' }} /><span>{selectedPastMeeting?.title}</span><Tag color="default">Completed</Tag></Space>}
        open={!!selectedPastMeeting} onCancel={() => setSelectedPastMeeting(null)} width={700}
        footer={<Button onClick={() => setSelectedPastMeeting(null)}>Close</Button>}
      >
        {selectedPastMeeting && (
          <div>
            <div style={{ display: 'flex', gap: 16, marginBottom: 16, padding: '12px 16px', background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
              <div style={{ textAlign: 'center', flex: 1 }}><Text type="secondary" style={{ fontSize: 10, display: 'block' }}>TOTAL ATTENDEES</Text><Text strong style={{ fontSize: 20 }}>{selectedPastMeeting.totalAttendees}</Text></div>
              <div style={{ textAlign: 'center', flex: 1 }}><Text type="secondary" style={{ fontSize: 10, display: 'block' }}>HUMANS</Text><Text strong style={{ fontSize: 20, color: '#7c3aed' }}>{selectedPastMeeting.humanCount}</Text></div>
              <div style={{ textAlign: 'center', flex: 1 }}><Text type="secondary" style={{ fontSize: 10, display: 'block' }}>AGENTS</Text><Text strong style={{ fontSize: 20, color: '#2563eb' }}>{selectedPastMeeting.agentCount}</Text></div>
              <div style={{ textAlign: 'center', flex: 1 }}><Text type="secondary" style={{ fontSize: 10, display: 'block' }}>DURATION</Text><Text strong style={{ fontSize: 14 }}>{selectedPastMeeting.duration}</Text></div>
            </div>
            <Text strong style={{ fontSize: 11, display: 'block', marginBottom: 8, textTransform: 'uppercase', color: '#64748b' }}>Participants</Text>
            <div style={{ marginBottom: 16 }}>{selectedPastMeeting.participants.map((p, i) => (
              <Tag key={i} color={p.includes('Agent') || p.includes('Specialist') || p.includes('Engineer') || p.includes('Orchestrator') ? 'blue' : 'purple'} style={{ marginBottom: 4 }}>{p}</Tag>
            ))}</div>
            <Text strong style={{ fontSize: 11, display: 'block', marginBottom: 8, textTransform: 'uppercase', color: '#64748b' }}>Discussion Summary</Text>
            <div style={{ padding: '12px 16px', background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0', marginBottom: 16 }}>
              <Text style={{ fontSize: 12, color: '#374151', lineHeight: 1.7 }}>{selectedPastMeeting.summary}</Text>
            </div>
            <Text strong style={{ fontSize: 11, display: 'block', marginBottom: 8, textTransform: 'uppercase', color: '#64748b' }}>Key Decisions</Text>
            <div style={{ marginBottom: 16 }}>{(selectedPastMeeting.decisions || []).map((d, i) => (
              <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 6, padding: '8px 12px', background: '#f0fdf4', borderRadius: 6, border: '1px solid #bbf7d0' }}>
                <CheckCircleOutlined style={{ color: '#16a34a', fontSize: 12, marginTop: 2, flexShrink: 0 }} />
                <Text style={{ fontSize: 12, color: '#166534' }}>{d}</Text>
              </div>
            ))}</div>
            {selectedPastMeeting.recording && (
              <div>
                <Text strong style={{ fontSize: 11, display: 'block', marginBottom: 8, textTransform: 'uppercase', color: '#64748b' }}>Meeting Recording</Text>
                <RecordingPlayer projectId={projectId || ''} meetingId={(selectedPastMeeting as any).id || ''} name={selectedPastMeeting.recording} />
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}


export function ProjectDetails() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isMigration = id === 'migration-hr-001';
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState('opportunities');

  const projectTitle = isMigration ? 'Adrenaline to Frappe HR Migration' : 'VNU Database Modernization';

  // Multi-Opportunity Scope
  const opportunities = isMigration ? [
    { id: 'opp-m1', name: 'HR Data Migration (Adrenaline → Frappe)', stage: 'Execution', progress: 5, owner: 'Current User', budget: '$45,000.00' },
    { id: 'opp-m2', name: 'MySQL Real-Time Sync Setup', stage: 'Planning', progress: 0, owner: 'Current User', budget: '$12,000.00' },
    { id: 'opp-m3', name: 'Frappe HR Mobile App Rollout', stage: 'Discovery', progress: 0, owner: 'Current User', budget: '$8,500.00' },
  ] : [
    { id: 'opp-1', name: 'Database Modernization (MySQL to PostgreSQL)', stage: 'Execution', progress: 75, owner: 'Sarah Jenkins', budget: '$57,385.00' },
    { id: 'opp-2', name: 'API Sync Engine (AWS Gateway peer)', stage: 'Planning', progress: 20, owner: 'Sarah Jenkins', budget: '$18,500.00' },
    { id: 'opp-3', name: 'Analytics Message Broker (Kafka Cluster)', stage: 'Discovery', progress: 10, owner: 'David Miller', budget: '$12,400.00' }
  ];

  // Document Registry grouped by Opportunity
  const documentGroups = isMigration ? {
    'opp-m1': [
      { id: 1, name: 'Adrenaline_ERD_Schema.pdf', type: 'Architecture', icon: <FilePdfOutlined style={{ color: '#EF4444' }} />, version: 'v1.0', size: '3.8 MB', date: 'Jul 15' },
      { id: 2, name: 'Frappe_HR_DocTypes_Map.xlsx', type: 'Mapping', icon: <FileExcelOutlined style={{ color: '#10B981' }} />, version: 'v1.0', size: '520 KB', date: 'Jul 15' },
      { id: 3, name: 'Migration_Plan_Phases.docx', type: 'Plan', icon: <FileTextOutlined style={{ color: '#3B82F6' }} />, version: 'v1.0', size: '1.2 MB', date: 'Jul 15' },
    ],
    'opp-m2': [
      { id: 4, name: 'MySQL_Sync_Architecture.tf', type: 'Architecture', icon: <FileTextOutlined style={{ color: '#8B5CF6' }} />, version: 'v1.0', size: '64 KB', date: 'Jul 15' },
    ],
    'opp-m3': [
      { id: 5, name: 'Frappe_Mobile_App_Requirements.pdf', type: 'Requirements', icon: <FilePdfOutlined style={{ color: '#F59E0B' }} />, version: 'v1.0', size: '2.1 MB', date: 'Jul 15' },
    ],
  } : {
    'opp-1': [
      { id: 1, name: 'Original_Requirements.pdf', type: 'RFP', icon: <FilePdfOutlined style={{ color: '#EF4444' }} />, version: 'v1.0', size: '4.2 MB', date: 'Oct 1' },
      { id: 2, name: 'Scope_Draft.docx', type: 'RFQ', icon: <FileTextOutlined style={{ color: '#3B82F6' }} />, version: 'v1.2', size: '320 KB', date: 'Oct 3' },
      { id: 3, name: 'Final_Proposal.pdf', type: 'Proposal', icon: <SafetyCertificateOutlined style={{ color: '#10B981' }} />, version: 'v2.0', size: '1.4 MB', date: 'Oct 5' }
    ],
    'opp-2': [
      { id: 4, name: 'AWS_API_Gateway_Mapping.tf', type: 'Architecture', icon: <FileTextOutlined style={{ color: '#8B5CF6' }} />, version: 'v1.0', size: '48 KB', date: 'Oct 8' }
    ],
    'opp-3': [
      { id: 5, name: 'Kafka_Broker_Sizing.xlsx', type: 'Specs', icon: <FileExcelOutlined style={{ color: '#F59E0B' }} />, version: 'v1.0', size: '1.2 MB', date: 'Oct 10' }
    ]
  };


  // API-fetched meetings (real backend data for non-migration projects)
  const [apiMeetings, setApiMeetings] = useState<any[]>([]);

  const loadMeetings = React.useCallback(async () => {
    if (!id || isMigration) return;
    try {
      const res = await ApiClient.get(`/projects/${id}/meetings`);
      setApiMeetings(res.meetings || []);
    } catch (err) {
      console.error('Failed to load meetings:', err);
    }
  }, [id, isMigration]);

  React.useEffect(() => {
    loadMeetings();
  }, [loadMeetings]);

  const [meetings, setMeetings] = useState<ProjectMeeting[]>(isMigration ? [
    {
      id: 'meet-m1',
      date: 'Jul 15, 10:00 AM',
      participants: ['Current User', 'BA Agent', 'Migration Specialist'],
      agenda: 'Requirement Analysis — Adrenaline to Frappe HR Migration',
      notes: 'Reviewed client recording. Identified 450 MySQL tables (150 master), MongoDB staging DB, GCP Pub/Sub pipeline, and Adrenaline HR tool dependency. Migration target: self-hosted Frappe HR on GCP.',
      actionItems: ['Map Adrenaline tables to Frappe HR DocTypes (Migration Specialist)', 'Design MySQL real-time sync architecture (Data Pipeline Agent)', 'Plan phased rollout: Engineering → Field Ops → Full Cutover'],
      decisions: ['3-year historical data to be migrated', 'Phased migration over 3 months', 'Self-hosted Frappe HR on GCP'],
      attachments: ['Client_Requirement_Transcription.txt', 'Adrenaline_ERD_Schema.pdf']
    }
  ] : [
    {
      id: 'meet-1',
      date: 'Oct 2, 11:00 AM',
      participants: ['Sarah Jenkins', 'Current User', 'Tech Lead'],
      agenda: 'Discovery Workshop & Schema Overview',
      notes: 'Reviewed legacy Oracle DDL. Identified 12 complex PL/SQL packages containing transaction triggers.',
      actionItems: ['Extract schema definition scripts (Sarah Jenkins)', 'Configure initial PG target instance (DevOps)'],
      decisions: ['Use active-active replication during cutover', 'Establish 15% effort buffer for PL/SQL translations'],
      attachments: ['Oracle_DDL_Summary.pdf']
    }
  ]);

  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>(isMigration ? [
    { color: '#2563EB', type: 'MILESTONE', title: 'Workspace Activated', time: 'Jul 15 10:00', owner: 'System Orchestrator' },
    { color: '#2563EB', type: 'MILESTONE', title: 'Project Created via BA Agent', time: 'Jul 15 09:50', owner: 'Business Analyst Agent' },
    { color: '#16A34A', type: 'ANALYSIS', title: 'Requirement Recording Analyzed', time: 'Jul 15 09:30', owner: 'Business Analyst Agent' },
    { color: '#16A34A', type: 'ANALYSIS', title: 'Requirements Finalized', time: 'Jul 15 09:45', owner: 'Business Analyst Agent' },
    { color: '#F59E0B', type: 'INPUT', title: 'Client Recording Uploaded', time: 'Jul 15 09:15', owner: 'Current User' },
  ] : [
    { color: '#2563EB', type: 'MILESTONE', title: 'Workspace Activated', time: 'Oct 7 09:15', owner: 'System Orchestrator' },
    { color: '#2563EB', type: 'MILESTONE', title: 'Project Initialized', time: 'Oct 7 09:00', owner: 'System' },
    { color: '#16A34A', type: 'APPROVAL', title: 'Contract Signed & Counter-Signed', time: 'Oct 6 11:00', owner: 'VNU Exec Sign-off (Sarah Jenkins)' }
  ]);

  const handleLogMeetingSubmit = (values: any) => {
    const newMeeting: ProjectMeeting = {
      id: `meet-${Date.now()}`,
      date: values.date || new Date().toLocaleString(),
      participants: values.participants ? values.participants.split(',').map((p: string) => p.trim()) : [],
      agenda: values.agenda,
      notes: values.notes,
      actionItems: values.actionItems ? values.actionItems.split(',').map((a: string) => a.trim()) : [],
      decisions: values.decisions ? values.decisions.split(',').map((d: string) => d.trim()) : [],
      attachments: values.attachments ? values.attachments.split(',').map((att: string) => att.trim()) : []
    };

    setMeetings(prev => [newMeeting, ...prev]);
    message.success('Meeting notes completed and added to project timeline.');
    form.resetFields();
    setIsModalOpen(false);
  };

  const cardStyle = {
    background: '#FFFFFF',
    border: '1px solid #E2E8F0',
    borderRadius: 8,
    boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
    transition: 'all 0.2s'
  };

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#2563EB',
          colorBgContainer: '#FFFFFF',
          colorBgLayout: '#F8FAFC',
          colorBorder: '#E2E8F0',
          colorText: '#0F172A',
          colorTextSecondary: '#475569',
          borderRadius: 8
        }
      }}
    >
      <PageContainer maxWidth={1500}>
        
        {/* HEADER */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
          <Space direction="vertical" size="small">
            <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/projects')} style={{ color: '#0F172A', padding: 0, fontWeight: 500 }}>Back to Registry</Button>
            <Space align="center">
              <Title level={3} style={{ margin: 0, fontWeight: 700, color: '#0F172A' }}>{projectTitle}</Title>
              <Tag color="success" style={{ margin: 0, background: '#DCFCE7', color: '#16A34A', border: 'none', fontWeight: 600 }}>{isMigration ? 'Discovery Phase' : 'Active Execution'}</Tag>
            </Space>
            <Text style={{ color: '#64748B', fontSize: 13 }}>Project ID: {id || '542bc353-da01-4fd8-88ed-4975228ee92a'}</Text>
          </Space>
          
          <Space>
            <Button icon={<FileTextOutlined />} style={{ fontWeight: 500 }}>Generate Report</Button>
            <Button danger icon={<DeleteOutlined />} style={{ fontWeight: 500 }}>Archive Project</Button>
            <Button type="primary" icon={<DesktopOutlined />} onClick={() => navigate(`/projects/${id || 'demo'}/workspace`)} style={{ background: '#2563EB', fontWeight: 600 }}>
              Open OS Workspace
            </Button>
          </Space>
        </div>

        {/* METRICS ROW (Overview KPIs) */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          {(isMigration ? [
            { label: 'OPPORTUNITIES IN PROJECT', value: '3 Active Tracked', sub: 'Migration Scope' },
            { label: 'PROJECT HEALTH SCORE', value: 'On Track', sub: '85/100 Initial Assessment' },
            { label: 'COMBINED BUDGET', value: '$65,500.00', sub: '$0 Burned' },
            { label: 'RISK THRESHOLD', value: '2 Medium Risks', sub: '0 Fatal Blocks' }
          ] : [
            { label: 'OPPORTUNITIES IN PROJECT', value: '3 Active Tracked', sub: 'Single Workspace Context' },
            { label: 'PROJECT HEALTH SCORE', value: 'Excellent', sub: '92/100 Policy Matrix' },
            { label: 'COMBINED BUDGET', value: '$88,285.00', sub: '$4,120.50 Burned' },
            { label: 'RISK THRESHOLD', value: '1 Medium Risk', sub: '0 Fatal Blocks' }
          ]).map((kpi, idx) => (
            <Col span={6} key={idx}>
              <Card style={cardStyle} bodyStyle={{ padding: 20 }}>
                <Text style={{ fontSize: 9, fontWeight: 700, color: '#64748B', textTransform: 'uppercase', letterSpacing: 0.5, display: 'block', marginBottom: 8 }}>{kpi.label}</Text>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#0F172A', marginBottom: 4 }}>{kpi.value}</div>
                <Text style={{ color: '#475569', fontSize: 12 }}>{kpi.sub}</Text>
              </Card>
            </Col>
          ))}
        </Row>

        {/* SYSTEM TABS */}
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          type="card"
          tabBarStyle={{ marginBottom: 24 }}
          items={[
            {
              key: 'opportunities',
              label: 'Opportunities',
              children: (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                    <Text style={{ fontSize: 13, color: '#475569' }}>Opportunities represent target pipelines executing in the parent workspace scope.</Text>
                    <Button type="primary" icon={<PlusOutlined />} style={{ background: '#2563EB', fontWeight: 600 }} onClick={() => navigate('/opportunities/new')}>
                      Create Opportunity
                    </Button>
                  </div>
                  <Row gutter={[16, 16]}>
                    {opportunities.map(opp => (
                      <Col span={8} key={opp.id}>
                        <Card 
                          style={cardStyle} 
                          bodyStyle={{ padding: 24 }}
                          actions={[
                            <Button type="link" size="small" style={{ color: '#2563EB', fontWeight: 600 }} onClick={() => navigate(`/projects/${id || 'demo'}/workspace`)}>Workspace</Button>,
                            <Button type="text" size="small" onClick={() => navigate(`/opportunities/${opp.id}`)}>View Details</Button>
                          ]}
                        >
                          <Title level={5} style={{ margin: '0 0 12px 0', fontSize: 14, fontWeight: 700, color: '#0F172A', minHeight: 40 }}>{opp.name}</Title>
                          <Row gutter={12} style={{ marginBottom: 12 }}>
                            <Col span={12}>
                              <Text type="secondary" style={{ fontSize: 10, display: 'block' }}>STAGE</Text>
                              <Tag color={opp.stage === 'Execution' ? 'green' : 'blue'} style={{ marginTop: 4, margin: '4px 0 0 0' }}>{opp.stage}</Tag>
                            </Col>
                            <Col span={12}>
                              <Text type="secondary" style={{ fontSize: 10, display: 'block' }}>BUDGET</Text>
                              <Text strong style={{ fontSize: 12, display: 'block', marginTop: 4 }}>{opp.budget}</Text>
                            </Col>
                          </Row>
                          <div style={{ marginBottom: 12 }}>
                            <Text type="secondary" style={{ fontSize: 10, display: 'block', marginBottom: 4 }}>PROGRESS</Text>
                            <Progress percent={opp.progress} size="small" strokeColor="#2563EB" />
                          </div>
                          <Text type="secondary" style={{ fontSize: 11 }}>Owner: <b>{opp.owner}</b></Text>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </div>
              )
            },
            {
              key: 'meetings',
              label: 'Meetings',
              children: (
                <Panel bodyStyle={{ padding: 24 }}>
                  <CalendarView meetings={apiMeetings} onAddMeeting={() => setIsModalOpen(true)} isMigration={isMigration} projectId={id} onDeleteMeeting={loadMeetings} />
                </Panel>
              )
            },
            {
              key: 'knowledge',
              label: 'Knowledge',
              children: (
                <Panel bodyStyle={{ padding: 24 }}>
                  {/* Header with status */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                    <div>
                      <Text strong style={{ fontSize: 14, color: '#0F172A', display: 'block' }}>Project Knowledge Base</Text>
                      <Text style={{ fontSize: 12, color: '#475569' }}>All project documents, schemas, and vectorized knowledge for agent access.</Text>
                    </div>
                    <Space>
                      <Tag color="green">Synced & Active</Tag>
                      <Tag color="blue">text-embedding-3-small</Tag>
                      <Tag color="purple">1,245 Chunks</Tag>
                    </Space>
                  </div>

                  <Divider style={{ margin: '0 0 20px 0' }} />

                  {/* Documents by Opportunity */}
                  <Text strong style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, display: 'block', marginBottom: 16 }}>Project Documents</Text>
                  <Space direction="vertical" size="large" style={{ width: '100%' }}>
                    {opportunities.map(opp => {
                      const docs = documentGroups[opp.id as keyof typeof documentGroups] || [];
                      return (
                        <div key={opp.id}>
                          <Text strong style={{ fontSize: 12, color: '#475569', textTransform: 'uppercase', display: 'block', marginBottom: 12 }}>
                            {opp.name}
                          </Text>
                          <Row gutter={[16, 16]}>
                            {docs.map(doc => (
                              <Col span={6} key={doc.id}>
                                <Card style={cardStyle} bodyStyle={{ padding: 16 }}>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                                    <Avatar shape="square" size="large" icon={doc.icon} style={{ background: '#F8FAFC' }} />
                                    <div style={{ flex: 1, minWidth: 0 }}>
                                      <Text strong style={{ fontSize: 12, color: '#0F172A', display: 'block' }} ellipsis={{ tooltip: doc.name }}>{doc.name}</Text>
                                      <Text type="secondary" style={{ fontSize: 10 }}>{doc.size} • Version {doc.version}</Text>
                                    </div>
                                  </div>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <Tag color="blue" style={{ fontSize: 9 }}>{doc.type}</Tag>
                                    <Space>
                                      <Tooltip title="View Document"><Button size="small" type="text" icon={<FolderOpenOutlined style={{ color: '#2563EB' }} />} /></Tooltip>
                                      <Tooltip title="Download"><Button size="small" type="text" icon={<DownloadOutlined style={{ color: '#475569' }} />} /></Tooltip>
                                      <Tooltip title="Version History"><Button size="small" type="text" icon={<HistoryOutlined style={{ color: '#475569' }} />} /></Tooltip>
                                    </Space>
                                  </div>
                                </Card>
                              </Col>
                            ))}
                            {docs.length === 0 && (
                              <Col span={24}>
                                <Card style={{ ...cardStyle, background: '#F8FAFC', textAlign: 'center' }} bodyStyle={{ padding: 24 }}>
                                  <Text type="secondary">No documents uploaded for this opportunity context.</Text>
                                </Card>
                              </Col>
                            )}
                          </Row>
                        </div>
                      );
                    })}
                  </Space>

                  <Divider style={{ margin: '24px 0 20px 0' }} />

                  {/* Key Decisions */}
                  <Text strong style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, display: 'block', marginBottom: 16 }}>Key Decisions</Text>
                  <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                    {(isMigration ? [
                      { decision: 'Self-hosted Frappe HR on GCP', by: 'CTO', date: 'Jul 15', status: 'Approved' },
                      { decision: 'Phased migration: Engineering → Field Ops → Cutover', by: 'Engineering Lead', date: 'Jul 15', status: 'Approved' },
                      { decision: 'Real-time MySQL sync via GCP Pub/Sub', by: 'Architect', date: 'Jul 15', status: 'Approved' },
                      { decision: 'Frappe HR mobile app replaces Android APK', by: 'Product Owner', date: 'Jul 15', status: 'Approved' },
                      { decision: 'Mongo monitoring tool stays separate (webhook only)', by: 'Tech Lead', date: 'Jul 15', status: 'Approved' },
                      { decision: '3-year historical data migration scope', by: 'HR Director', date: 'Jul 15', status: 'Pending' },
                    ] : [
                      { decision: 'Use active-active replication during cutover', by: 'Sarah Jenkins', date: 'Oct 3', status: 'Approved' },
                      { decision: 'Target Aurora PostgreSQL 15.x on AWS', by: 'DevOps Lead', date: 'Oct 4', status: 'Approved' },
                      { decision: '15% effort buffer for PL/SQL translations', by: 'Tech Lead', date: 'Oct 5', status: 'Approved' },
                    ]).map((d, i) => (
                      <Col span={8} key={i}>
                        <Card size="small" style={{ ...cardStyle, borderLeft: `3px solid ${d.status === 'Approved' ? '#16a34a' : '#f59e0b'}` }} bodyStyle={{ padding: '10px 12px' }}>
                          <Text strong style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>{d.decision}</Text>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <Text type="secondary" style={{ fontSize: 9 }}>{d.by} · {d.date}</Text>
                            <Tag color={d.status === 'Approved' ? 'green' : 'orange'} style={{ fontSize: 9, margin: 0 }}>{d.status}</Tag>
                          </div>
                        </Card>
                      </Col>
                    ))}
                  </Row>

                  {/* Connected Repositories */}
                  <Text strong style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, display: 'block', marginBottom: 16 }}>Connected Repositories</Text>
                  <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                    {(isMigration ? [
                      { name: 'acme-corp/hr-migration-scripts', branch: 'main', lang: 'Python', status: 'Active' },
                      { name: 'acme-corp/frappe-hr-config', branch: 'develop', lang: 'Python', status: 'Active' },
                      { name: 'acme-corp/mysql-sync-service', branch: 'main', lang: 'Node.js', status: 'Active' },
                      { name: 'acme-corp/gcp-pubsub-pipeline', branch: 'main', lang: 'Python', status: 'Active' },
                      { name: 'acme-corp/mobile-app-hr', branch: 'feature/frappe', lang: 'Dart', status: 'Pending' },
                    ] : [
                      { name: 'acme-corp/oracle-to-pg', branch: 'main', lang: 'Python', status: 'Active' },
                      { name: 'acme-corp/terraform-infra', branch: 'main', lang: 'HCL', status: 'Active' },
                      { name: 'acme-corp/debezium-config', branch: 'main', lang: 'JSON', status: 'Active' },
                    ]).map((repo, i) => (
                      <Col span={8} key={i}>
                        <Card size="small" style={cardStyle} bodyStyle={{ padding: '10px 12px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                            <CodeOutlined style={{ fontSize: 14, color: '#0f172a' }} />
                            <Text strong style={{ fontSize: 11, color: '#0f172a' }}>{repo.name}</Text>
                          </div>
                          <Space size={4}>
                            <Tag style={{ fontSize: 9 }}>{repo.branch}</Tag>
                            <Tag style={{ fontSize: 9 }}>{repo.lang}</Tag>
                            <Tag color={repo.status === 'Active' ? 'green' : 'orange'} style={{ fontSize: 9 }}>{repo.status}</Tag>
                          </Space>
                        </Card>
                      </Col>
                    ))}
                  </Row>

                  {/* Connected Tools & Connectors */}
                  <Text strong style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, display: 'block', marginBottom: 16 }}>Connected Tools & Connectors</Text>
                  <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                    {(isMigration ? [
                      { name: 'MySQL', type: 'Database', status: 'Connected', detail: 'acme-prod-mysql.cloudsql:3306' },
                      { name: 'Frappe HR API', type: 'Application', status: 'Connected', detail: 'https://hr.acme-corp.com/api' },
                      { name: 'GCP Pub/Sub', type: 'Messaging', status: 'Connected', detail: 'acme-prod · 3 topics' },
                      { name: 'MongoDB', type: 'Database', status: 'Connected', detail: 'acme-staging-mongo:27017' },
                      { name: 'Adrenaline API', type: 'Application', status: 'Connected', detail: 'https://adrenaline.acme-corp.com/api' },
                      { name: 'Redis', type: 'Cache', status: 'Connected', detail: 'acme-redis.cloudmemorystore:6379' },
                    ] : [
                      { name: 'AWS RDS Aurora', type: 'Database', status: 'Connected', detail: 'acme-pg.cluster-xxx.us-east-1.rds' },
                      { name: 'Debezium CDC', type: 'Pipeline', status: 'Connected', detail: 'debezium-cluster.internal:8083' },
                      { name: 'Redis', type: 'Cache', status: 'Connected', detail: 'acme-redis.elasticache:6379' },
                    ]).map((tool, i) => (
                      <Col span={8} key={i}>
                        <Card size="small" style={cardStyle} bodyStyle={{ padding: '10px 12px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                            <Text strong style={{ fontSize: 11 }}>{tool.name}</Text>
                            <Tag color="green" style={{ fontSize: 9, margin: 0 }}>{tool.status}</Tag>
                          </div>
                          <Text type="secondary" style={{ fontSize: 9, display: 'block' }}>{tool.type}</Text>
                          <Text style={{ fontSize: 9, color: '#475569', fontFamily: 'monospace', marginTop: 4, display: 'block' }}>{tool.detail}</Text>
                        </Card>
                      </Col>
                    ))}
                  </Row>

                  {/* Important Terms */}
                  <Text strong style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, display: 'block', marginBottom: 16 }}>Important Terms</Text>
                  <Row gutter={[16, 16]}>
                    {(isMigration ? [
                      { term: 'DocType', definition: 'Frappe HR data model unit — equivalent to a database table with built-in forms, permissions, and API endpoints.' },
                      { term: 'Adrenaline', definition: 'Legacy HR tool managing employee lifecycle (onboarding, attendance, leave, payroll) for 2000+ field employees.' },
                      { term: 'Pub/Sub Pipeline', definition: 'GCP messaging backbone for HR data events — routes employee status changes to MySQL and downstream systems.' },
                      { term: 'MySQL Master DB', definition: 'Central database with 450 tables (150 master). Source of truth for all transactional data and reporting.' },
                      { term: 'Mongo Staging DB', definition: 'Intermediate database for data pipeline error handling. Tech ops use low-code tool to monitor/fix data issues.' },
                      { term: 'Bidirectional Sync', definition: 'Real-time data sync between Frappe HR and MySQL. Frappe wins on HR fields, MySQL wins on transaction fields.' },
                    ] : [
                      { term: 'PL/SQL Translation', definition: 'Converting Oracle stored procedures and triggers to PostgreSQL pgSQL functions.' },
                      { term: 'CDC Pipeline', definition: 'Change Data Capture using Debezium Kafka connector for real-time Oracle → PostgreSQL replication.' },
                      { term: 'PostGIS', definition: 'PostgreSQL spatial extension for handling Oracle Spatial data type conversions.' },
                    ]).map((t, i) => (
                      <Col span={8} key={i}>
                        <Card size="small" style={cardStyle} bodyStyle={{ padding: '10px 12px' }}>
                          <Text strong style={{ fontSize: 11, color: '#0f172a', display: 'block', marginBottom: 4 }}>{t.term}</Text>
                          <Text style={{ fontSize: 10, color: '#475569', lineHeight: 1.5 }}>{t.definition}</Text>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </Panel>
              )
            },
            {
              key: 'timeline',
              label: 'Timeline',
              children: (
                <Panel bodyStyle={{ padding: 24 }}>
                  <Timeline
                    items={timelineEvents.map((evt, idx) => ({
                      key: idx,
                      color: evt.color,
                      children: (
                        <div style={{ marginBottom: 12 }}>
                          <Tag color={evt.color === '#2563EB' ? 'blue' : (evt.color === '#16A34A' ? 'green' : 'purple')}>{evt.type}</Tag>
                          <Text strong style={{ display: 'block', color: '#0F172A', marginTop: 4 }}>{evt.title}</Text>
                          <Text style={{ color: '#64748B', fontSize: 11 }}>{evt.time} • {evt.owner}</Text>
                        </div>
                      )
                    }))}
                  />
                </Panel>
              )
            },
            {
              key: 'team',
              label: 'Team',
              children: (
                <Panel bodyStyle={{ padding: 24 }}>
                  <List
                    dataSource={[
                      { name: 'Sarah Jenkins', role: 'Lead Migration Architect', email: 'sarah.j@vnu.com' },
                      { name: 'David Miller', role: 'DevOps Coordinator', email: 'david.m@vnu.com' }
                    ]}
                    renderItem={user => (
                      <List.Item>
                        <Space>
                          <Avatar icon={<UserOutlined />} style={{ background: '#F1F5F9', color: '#0F172A' }} />
                          <div>
                            <Text strong style={{ fontSize: 12, color: '#0F172A' }}>{user.name}</Text>
                            <Text type="secondary" style={{ fontSize: 10, display: 'block' }}>{user.role} • {user.email}</Text>
                          </div>
                        </Space>
                      </List.Item>
                    )}
                  />
                </Panel>
              )
            },
            {
              key: 'reports',
              label: 'Reports',
              children: (
                <Panel bodyStyle={{ padding: 24 }}>
                  <Text strong style={{ fontSize: 12, color: '#475569', display: 'block', marginBottom: 16 }}>GENERATED EXECUTIVE REPORTS</Text>
                  <List
                    dataSource={[
                      { title: 'VNU Database Modernization RFP Report', date: 'Oct 3' },
                      { title: 'Commercial Proposal v2.0 Sign-off summary', date: 'Oct 5' }
                    ]}
                    renderItem={rep => (
                      <List.Item actions={[<Button size="small" icon={<DownloadOutlined />}>Download</Button>]}>
                        <Space><FileTextOutlined style={{ color: '#2563EB' }} /> <Text style={{ fontSize: 12 }}>{rep.title}</Text></Space>
                      </List.Item>
                    )}
                  />
                </Panel>
              )
            }
          ]}
        />

        {/* Log Meeting Modal */}
        <Modal
          title={<span style={{ color: '#0F172A', fontSize: 15, fontWeight: 600 }}>Log New Meeting Notes</span>}
          open={isModalOpen}
          onCancel={() => setIsModalOpen(false)}
          onOk={() => form.submit()}
          okText="Log & Sync Meeting"
          cancelText="Cancel"
        >
          <Form form={form} layout="vertical" onFinish={handleLogMeetingSubmit} style={{ marginTop: 16 }}>
            <Form.Item name="agenda" label="Meeting Agenda" rules={[{ required: true, message: 'Please enter meeting agenda' }]}>
              <Input placeholder="e.g. Schema Review & Cutover Strategy Alignment" />
            </Form.Item>
            <Form.Item name="date" label="Meeting Date/Time" initialValue={new Date().toLocaleString()}>
              <Input placeholder="e.g. Oct 8, 10:00 AM" />
            </Form.Item>
            <Form.Item name="participants" label="Participants (comma-separated)" initialValue="Sarah Jenkins, Current User">
              <Input placeholder="e.g. Sarah Jenkins, Current User, DevOps Lead" />
            </Form.Item>
            <Form.Item name="notes" label="Meeting Notes" rules={[{ required: true, message: 'Please enter meeting notes' }]}>
              <TextArea rows={4} placeholder="Summarize notes, legacy database mappings, security concerns..." />
            </Form.Item>
            <Form.Item name="actionItems" label="Action Items (comma-separated)">
              <Input placeholder="e.g. Finalize target AWS account access, Establish SSL tunnels" />
            </Form.Item>
            <Form.Item name="decisions" label="Decisions (comma-separated)">
              <Input placeholder="e.g. Route staging read load to PG immediately, Target Aurora Engine version 15" />
            </Form.Item>
            <Form.Item name="attachments" label="Attachments (comma-separated)">
              <Input placeholder="e.g. Target_VPC_Specs.pdf" />
            </Form.Item>
          </Form>
        </Modal>

      </PageContainer>
    </ConfigProvider>
  );
}

import React from 'react';
import { Button, Input, Modal, Select, message } from 'antd';
import { CalendarOutlined, LeftOutlined, PlusOutlined, RightOutlined } from '@ant-design/icons';
import { ApiClient } from '../api/client';
import './MeetingsCalendarDashboard.css';

export interface WorkspaceMeeting {
  id?: string;
  project_id?: string;
  title?: string;
  date?: string;
  time?: string | null;
  duration?: string | null;
  type?: 'agent' | 'human' | 'both' | string;
  status?: string;
  past?: boolean;
  participants?: string[];
  totalAttendees?: number;
  agenda?: string | null;
  notes?: string | null;
  summary?: string | null;
  decisions?: string[];
  actionItems?: string[];
  source?: string;
}

interface MeetingsCalendarDashboardProps {
  projectId?: string;
  meetings: WorkspaceMeeting[];
  onMeetingsChanged?: () => Promise<void> | void;
}

const WEEKDAYS = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];

const EVENT_STYLES = {
  agent: { label: 'Agent Meeting', className: 'mc-event--agent', bullet: '#2D6CDF' },
  human: { label: 'Human Meeting', className: 'mc-event--human', bullet: '#8B5CF6' },
  joint: { label: 'Joint Meeting', className: 'mc-event--joint', bullet: '#24A148' },
  past: { label: 'Past Meeting', className: 'mc-event--past', bullet: '#9AA4B2' },
  tbd: { label: 'Time TBD', className: 'mc-event--tbd', bullet: '#D97706' },
} as const;

type EventStyleKey = keyof typeof EVENT_STYLES;

function pad(value: number): string {
  return String(value).padStart(2, '0');
}

function todayIso(): string {
  const now = new Date();
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

function toIsoDate(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function parseIsoDate(value?: string | null): Date | null {
  if (!value) return null;
  const raw = String(value).split(' ')[0];
  const match = raw.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return null;
  const [, y, m, d] = match;
  const date = new Date(Number(y), Number(m) - 1, Number(d));
  return Number.isNaN(date.getTime()) ? null : date;
}

function addDays(date: Date, days: number): Date {
  const copy = new Date(date);
  copy.setDate(copy.getDate() + days);
  return copy;
}

function formatMonthTitle(date: Date): string {
  return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
}

function formatMeetingDate(value?: string | null): string {
  const date = parseIsoDate(value);
  if (!date) return '';
  return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

function formatSelectedDate(value?: string | null): string {
  const date = parseIsoDate(value);
  if (!date) return 'Choose a calendar day';
  return date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
}

function normalizeMeetingDate(meeting: WorkspaceMeeting): string {
  return String(meeting.date || '').split(' ')[0];
}

function isPastMeeting(meeting: WorkspaceMeeting, today: string): boolean {
  const date = normalizeMeetingDate(meeting);
  return Boolean(meeting.past || meeting.status === 'past' || (date && date < today));
}

function isTimeTbd(meeting: WorkspaceMeeting): boolean {
  const time = String(meeting.time || '').trim().toUpperCase();
  return !time || time === 'TBD' || time === 'TIME TBD';
}

function meetingType(meeting: WorkspaceMeeting): 'agent' | 'human' | 'both' {
  if (meeting.type === 'agent') return 'agent';
  if (meeting.type === 'human') return 'human';
  return 'both';
}

function eventStyleKey(meeting: WorkspaceMeeting, today: string): EventStyleKey {
  if (isPastMeeting(meeting, today)) return 'past';
  if (isTimeTbd(meeting)) return 'tbd';
  if (meetingType(meeting) === 'agent') return 'agent';
  if (meetingType(meeting) === 'human') return 'human';
  return 'joint';
}

function bulletColor(meeting: WorkspaceMeeting): string {
  const type = meetingType(meeting);
  if (type === 'agent') return EVENT_STYLES.agent.bullet;
  if (type === 'human') return EVENT_STYLES.human.bullet;
  return EVENT_STYLES.joint.bullet;
}

function displayTime(meeting: WorkspaceMeeting): string {
  return isTimeTbd(meeting) ? 'Time TBD' : String(meeting.time);
}

function cleanList(values?: string[]): string[] {
  return Array.isArray(values) ? values.filter(Boolean) : [];
}

function buildMonthCells(viewMonth: Date) {
  const year = viewMonth.getFullYear();
  const month = viewMonth.getMonth();
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const totalCells = Math.ceil((firstDay + daysInMonth) / 7) * 7;

  return Array.from({ length: totalCells }, (_, index) => {
    const day = index - firstDay + 1;
    const inMonth = day >= 1 && day <= daysInMonth;
    const date = inMonth ? new Date(year, month, day) : null;
    return {
      key: `${year}-${month}-${index}`,
      day: inMonth ? day : null,
      iso: date ? toIsoDate(date) : '',
      row: Math.floor(index / 7) + 1,
      column: (index % 7) + 1,
    };
  });
}

function eventsForMonth(meetings: WorkspaceMeeting[], viewMonth: Date, today: string) {
  const year = viewMonth.getFullYear();
  const month = viewMonth.getMonth();
  const firstDay = new Date(year, month, 1).getDay();
  const usedLanes: Record<string, number> = {};

  return meetings
    .map((meeting, index) => {
      const meetingDate = parseIsoDate(normalizeMeetingDate(meeting));
      if (!meetingDate) return null;

      let displayDate = meetingDate;
      let span = 1;
      const title = meeting.title || 'Project Meeting';
      const source = String(meeting.source || '');

      if (source === 'ba_discovery') {
        span = 2;
      } else if (isTimeTbd(meeting) && /kickoff/i.test(title)) {
        displayDate = addDays(meetingDate, -1);
        span = 2;
      }

      if (displayDate.getFullYear() !== year || displayDate.getMonth() !== month) return null;
      const day = displayDate.getDate();
      const cellIndex = firstDay + day - 1;
      const row = Math.floor(cellIndex / 7) + 1;
      const column = (cellIndex % 7) + 1;
      const clampedSpan = Math.max(1, Math.min(span, 8 - column));
      const laneKey = `${row}-${column}`;
      const lane = usedLanes[laneKey] || 0;
      usedLanes[laneKey] = lane + 1;

      return {
        meeting,
        key: meeting.id || `${title}-${index}`,
        row,
        column,
        span: clampedSpan,
        lane,
        styleKey: eventStyleKey(meeting, today),
      };
    })
    .filter(Boolean) as Array<{
      meeting: WorkspaceMeeting;
      key: string;
      row: number;
      column: number;
      span: number;
      lane: number;
      styleKey: EventStyleKey;
    }>;
}

export function CalendarHeader({
  title,
  onPrevious,
  onNext,
  onToday,
  onSchedule,
}: {
  title: string;
  onPrevious: () => void;
  onNext: () => void;
  onToday: () => void;
  onSchedule: () => void;
}) {
  return (
    <header className="mc-panel-header">
      <div className="mc-month-controls">
        <button type="button" className="mc-icon-button" onClick={onPrevious} aria-label="Previous month">
          <LeftOutlined />
        </button>
        <h2>{title}</h2>
        <button type="button" className="mc-icon-button" onClick={onNext} aria-label="Next month">
          <RightOutlined />
        </button>
      </div>
      <div className="mc-actions">
        <button type="button" className="mc-secondary-button" onClick={onToday}>Today</button>
        <button type="button" className="mc-primary-button" onClick={onSchedule}>
          <PlusOutlined />
          <span>Schedule Meeting</span>
        </button>
      </div>
    </header>
  );
}

export function CalendarEvent({
  meeting,
  styleKey,
  style,
  onClick,
}: {
  meeting: WorkspaceMeeting;
  styleKey: EventStyleKey;
  style: React.CSSProperties;
  onClick: () => void;
}) {
  const prefix = styleKey === 'past' ? '✓ All-day' : styleKey === 'tbd' ? 'TBD' : displayTime(meeting);
  return (
    <button
      type="button"
      className={`mc-calendar-event ${EVENT_STYLES[styleKey].className}`}
      style={style}
      onClick={onClick}
      title={meeting.title || 'Project Meeting'}
    >
      <span>{prefix} {meeting.title || 'Project Meeting'}</span>
    </button>
  );
}

export function MonthCalendar({
  viewMonth,
  meetings,
  selectedDate,
  today,
  onSelectDate,
  onSelectMeeting,
}: {
  viewMonth: Date;
  meetings: WorkspaceMeeting[];
  selectedDate: string;
  today: string;
  onSelectDate: (date: string) => void;
  onSelectMeeting: (meeting: WorkspaceMeeting) => void;
}) {
  const cells = React.useMemo(() => buildMonthCells(viewMonth), [viewMonth]);
  const displayEvents = React.useMemo(() => eventsForMonth(meetings, viewMonth, today), [meetings, today, viewMonth]);
  const rowCount = Math.max(5, Math.ceil(cells.length / 7));

  return (
    <section className="mc-calendar-card" aria-label={`${formatMonthTitle(viewMonth)} calendar`}>
      <div className="mc-weekdays" role="row">
        {WEEKDAYS.map((day) => (
          <div key={day} role="columnheader">{day}</div>
        ))}
      </div>
      <div className="mc-calendar-body" style={{ '--mc-row-count': String(rowCount) } as React.CSSProperties}>
        <div className="mc-date-grid" role="grid">
          {cells.map((cell) => {
            const isToday = cell.iso === today;
            const isSelected = cell.iso === selectedDate;
            return (
              <button
                key={cell.key}
                type="button"
                className={[
                  'mc-date-cell',
                  !cell.day ? 'mc-date-cell--empty' : '',
                  isToday ? 'mc-date-cell--today' : '',
                  isSelected ? 'mc-date-cell--selected' : '',
                ].filter(Boolean).join(' ')}
                disabled={!cell.day}
                onClick={() => cell.iso && onSelectDate(cell.iso)}
                aria-label={cell.iso || 'Empty calendar cell'}
              >
                {cell.day && <span>{cell.day}</span>}
              </button>
            );
          })}
        </div>
        <div className="mc-event-layer" aria-label="Meetings">
          {displayEvents.map((event) => (
            <CalendarEvent
              key={event.key}
              meeting={event.meeting}
              styleKey={event.styleKey}
              style={{
                gridColumn: `${event.column} / span ${event.span}`,
                gridRow: event.row,
                marginTop: 42 + event.lane * 24,
              }}
              onClick={() => {
                const date = normalizeMeetingDate(event.meeting);
                if (date) onSelectDate(date);
                onSelectMeeting(event.meeting);
              }}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

export function Legend() {
  return (
    <div className="mc-legend" aria-label="Calendar legend">
      {Object.entries(EVENT_STYLES).map(([key, item]) => (
        <div key={key} className="mc-legend-item">
          <span className={`mc-legend-square ${item.className}`} />
          <span>{item.label}</span>
        </div>
      ))}
    </div>
  );
}

export function EmptyStateCard({ onSchedule }: { onSchedule: () => void }) {
  return (
    <div className="mc-empty-state">
      <div className="mc-empty-icon" aria-hidden="true">
        <CalendarOutlined />
      </div>
      <p>No meetings scheduled</p>
      <button type="button" onClick={onSchedule}>Schedule one</button>
    </div>
  );
}

function MeetingDetailsList({
  selectedDate,
  meetings,
  selectedMeetingId,
  onSchedule,
}: {
  selectedDate: string;
  meetings: WorkspaceMeeting[];
  selectedMeetingId?: string;
  onSchedule: () => void;
}) {
  if (meetings.length === 0) {
    return <EmptyStateCard onSchedule={onSchedule} />;
  }

  const ordered = [...meetings].sort((a, b) => {
    if (a.id === selectedMeetingId) return -1;
    if (b.id === selectedMeetingId) return 1;
    return String(a.time || '').localeCompare(String(b.time || ''));
  });

  return (
    <div className="mc-selected-meetings">
      <p className="mc-selected-date">{formatSelectedDate(selectedDate)}</p>
      {ordered.map((meeting) => {
        const today = todayIso();
        const past = isPastMeeting(meeting, today);
        const decisions = cleanList(meeting.decisions);
        const actions = cleanList(meeting.actionItems);
        const participants = cleanList(meeting.participants);
        return (
          <article key={meeting.id || meeting.title} className={`mc-meeting-detail ${past ? 'mc-meeting-detail--past' : ''}`}>
            <div className="mc-meeting-detail-header">
              <div>
                <h4>{meeting.title || 'Project Meeting'}</h4>
                <p>{displayTime(meeting)}{meeting.duration ? ` · ${meeting.duration}` : ''}</p>
              </div>
              <span className={`mc-meeting-pill ${past ? 'mc-meeting-pill--past' : ''}`}>
                {past ? 'Completed' : isTimeTbd(meeting) ? 'Time TBD' : meetingType(meeting)}
              </span>
            </div>

            {meeting.agenda && (
              <div className="mc-detail-block">
                <span>Agenda</span>
                <p>{meeting.agenda}</p>
              </div>
            )}

            {past && (
              <div className="mc-detail-block">
                <span>Summary</span>
                <p>{meeting.summary || meeting.notes || 'No meeting summary has been recorded yet.'}</p>
              </div>
            )}

            {participants.length > 0 && (
              <div className="mc-chip-row" aria-label="Participants">
                {participants.map((participant) => (
                  <span key={participant}>{participant}</span>
                ))}
              </div>
            )}

            {decisions.length > 0 && (
              <div className="mc-detail-list">
                <span>Decisions</span>
                <ul>
                  {decisions.map((decision) => <li key={decision}>{decision}</li>)}
                </ul>
              </div>
            )}

            {actions.length > 0 && (
              <div className="mc-detail-list">
                <span>Action Items</span>
                <ul>
                  {actions.map((action) => <li key={action}>{action}</li>)}
                </ul>
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}

export function UpcomingMeetings({ meetings, today }: { meetings: WorkspaceMeeting[]; today: string }) {
  const upcoming = React.useMemo(() => (
    meetings
      .filter((meeting) => {
        const date = normalizeMeetingDate(meeting);
        return date && date >= today && !isPastMeeting(meeting, today);
      })
      .sort((a, b) => normalizeMeetingDate(a).localeCompare(normalizeMeetingDate(b)))
      .slice(0, 5)
  ), [meetings, today]);

  return (
    <section className="mc-side-card mc-upcoming-card" aria-label="Upcoming meetings">
      <h3>Upcoming This Week</h3>
      {upcoming.length === 0 ? (
        <p className="mc-muted">No upcoming meetings scheduled.</p>
      ) : (
        <ul>
          {upcoming.map((meeting) => (
            <li key={meeting.id || `${meeting.title}-${meeting.date}`}>
              <span className="mc-upcoming-bullet" style={{ background: bulletColor(meeting) }} />
              <div>
                <h4>{meeting.title || 'Project Meeting'}</h4>
                <p>{formatMeetingDate(meeting.date)} · {displayTime(meeting)}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function SelectedDatePanel({
  selectedDate,
  selectedMeetingId,
  meetings,
  onSchedule,
}: {
  selectedDate: string;
  selectedMeetingId?: string;
  meetings: WorkspaceMeeting[];
  onSchedule: () => void;
}) {
  return (
    <section className="mc-side-card mc-select-card" aria-label="Selected date details">
      <h3>Select a date</h3>
      <MeetingDetailsList
        selectedDate={selectedDate}
        selectedMeetingId={selectedMeetingId}
        meetings={meetings}
        onSchedule={onSchedule}
      />
    </section>
  );
}

function defaultScheduleDraft(selectedDate: string) {
  return {
    title: '',
    date: selectedDate || todayIso(),
    time: 'TBD',
    duration: '1 hour',
    type: 'both',
    participants: '',
    agenda: '',
  };
}

export function MeetingsCalendarDashboard({ projectId, meetings, onMeetingsChanged }: MeetingsCalendarDashboardProps) {
  const today = React.useMemo(() => todayIso(), []);
  const [viewMonth, setViewMonth] = React.useState(() => {
    const parsedToday = parseIsoDate(today) || new Date();
    return new Date(parsedToday.getFullYear(), parsedToday.getMonth(), 1);
  });
  const [selectedDate, setSelectedDate] = React.useState(today);
  const [selectedMeetingId, setSelectedMeetingId] = React.useState<string | undefined>();
  const [scheduleOpen, setScheduleOpen] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [draft, setDraft] = React.useState(defaultScheduleDraft(today));

  const meetingsByDate = React.useMemo(() => {
    return meetings.reduce((map: Record<string, WorkspaceMeeting[]>, meeting) => {
      const date = normalizeMeetingDate(meeting);
      if (!date) return map;
      map[date] = map[date] || [];
      map[date].push(meeting);
      return map;
    }, {});
  }, [meetings]);

  React.useEffect(() => {
    if (meetingsByDate[selectedDate]) return;
    const firstUpcoming = meetings
      .map((meeting) => normalizeMeetingDate(meeting))
      .filter((date) => date >= today)
      .sort()[0];
    if (firstUpcoming && !selectedDate) setSelectedDate(firstUpcoming);
  }, [meetings, meetingsByDate, selectedDate, today]);

  const selectedMeetings = meetingsByDate[selectedDate] || [];

  const openScheduleModal = () => {
    setDraft(defaultScheduleDraft(selectedDate || today));
    setScheduleOpen(true);
  };

  const submitSchedule = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!projectId) {
      message.error('Project id is missing.');
      return;
    }
    if (!draft.title.trim()) {
      message.warning('Meeting title is required.');
      return;
    }
    if (!draft.date) {
      message.warning('Meeting date is required.');
      return;
    }

    setSaving(true);
    try {
      const created = await ApiClient.post(`/projects/${projectId}/meetings`, {
        title: draft.title.trim(),
        date: draft.date,
        time: draft.time.trim() || 'TBD',
        duration: draft.duration.trim() || '1 hour',
        type: draft.type,
        status: draft.date < today ? 'past' : 'upcoming',
        participants: draft.participants.split(',').map((p) => p.trim()).filter(Boolean),
        agenda: draft.agenda.trim() || null,
      }) as WorkspaceMeeting;
      setScheduleOpen(false);
      setSelectedDate(draft.date);
      setSelectedMeetingId(created?.id);
      await onMeetingsChanged?.();
      message.success('Meeting scheduled.');
    } catch (err) {
      ApiClient.handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mc-dashboard">
      <main className="mc-panel">
        <CalendarHeader
          title={formatMonthTitle(viewMonth)}
          onPrevious={() => setViewMonth(new Date(viewMonth.getFullYear(), viewMonth.getMonth() - 1, 1))}
          onNext={() => setViewMonth(new Date(viewMonth.getFullYear(), viewMonth.getMonth() + 1, 1))}
          onToday={() => {
            const parsedToday = parseIsoDate(today) || new Date();
            setViewMonth(new Date(parsedToday.getFullYear(), parsedToday.getMonth(), 1));
            setSelectedDate(today);
          }}
          onSchedule={openScheduleModal}
        />

        <div className="mc-main-grid">
          <div className="mc-calendar-column">
            <MonthCalendar
              viewMonth={viewMonth}
              meetings={meetings}
              selectedDate={selectedDate}
              today={today}
              onSelectDate={(date) => {
                setSelectedDate(date);
                setSelectedMeetingId(undefined);
              }}
              onSelectMeeting={(meeting) => setSelectedMeetingId(meeting.id)}
            />
            <Legend />
          </div>

          <aside className="mc-sidebar">
            <SelectedDatePanel
              selectedDate={selectedDate}
              selectedMeetingId={selectedMeetingId}
              meetings={selectedMeetings}
              onSchedule={openScheduleModal}
            />
            <UpcomingMeetings meetings={meetings} today={today} />
          </aside>
        </div>
      </main>

      <Modal
        title="Schedule Meeting"
        open={scheduleOpen}
        onCancel={() => setScheduleOpen(false)}
        footer={null}
        width={620}
        destroyOnClose
      >
        <form className="mc-schedule-form" onSubmit={submitSchedule}>
          <label>
            <span>Title</span>
            <Input
              value={draft.title}
              onChange={(event) => setDraft((prev) => ({ ...prev, title: event.target.value }))}
              placeholder="Phase review, stakeholder sync, or discovery meeting"
            />
          </label>

          <div className="mc-form-grid">
            <label>
              <span>Date</span>
              <input
                type="date"
                value={draft.date}
                onChange={(event) => setDraft((prev) => ({ ...prev, date: event.target.value }))}
              />
            </label>
            <label>
              <span>Time</span>
              <Input
                value={draft.time}
                onChange={(event) => setDraft((prev) => ({ ...prev, time: event.target.value }))}
                placeholder="TBD or 10:30 AM"
              />
            </label>
          </div>

          <div className="mc-form-grid">
            <label>
              <span>Duration</span>
              <Input
                value={draft.duration}
                onChange={(event) => setDraft((prev) => ({ ...prev, duration: event.target.value }))}
                placeholder="1 hour"
              />
            </label>
            <label>
              <span>Meeting Type</span>
              <Select
                value={draft.type}
                onChange={(value) => setDraft((prev) => ({ ...prev, type: value }))}
                options={[
                  { value: 'both', label: 'Joint Meeting' },
                  { value: 'agent', label: 'Agent Meeting' },
                  { value: 'human', label: 'Human Meeting' },
                ]}
              />
            </label>
          </div>

          <label>
            <span>Participants</span>
            <Input
              value={draft.participants}
              onChange={(event) => setDraft((prev) => ({ ...prev, participants: event.target.value }))}
              placeholder="Comma-separated names"
            />
          </label>

          <label>
            <span>Agenda</span>
            <Input.TextArea
              value={draft.agenda}
              onChange={(event) => setDraft((prev) => ({ ...prev, agenda: event.target.value }))}
              placeholder="What should this meeting cover?"
              rows={4}
            />
          </label>

          <div className="mc-form-actions">
            <Button onClick={() => setScheduleOpen(false)}>Cancel</Button>
            <Button type="primary" htmlType="submit" loading={saving} icon={<PlusOutlined />}>Schedule Meeting</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

export default MeetingsCalendarDashboard;

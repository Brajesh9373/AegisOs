/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Input, Button, Spin, Tag, Space, Typography, Badge, Select, Upload } from 'antd';
import {
  SendOutlined,
  LoadingOutlined,
  RobotOutlined,
  UserOutlined,
  MessageOutlined,
  PlusOutlined,
  CloseOutlined,
  ThunderboltOutlined,
  BulbOutlined,
  PaperClipOutlined,
  CheckOutlined,
} from '@ant-design/icons';
import { TaskProgress, TaskItem } from './TaskProgress';

const { Text } = Typography;
const { TextArea } = Input;

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatSession {
  session_id: string;
  title: string;
  last_active: string;
  message_count: number;
}

interface ChatViewProps {
  workspaceId: string;
  onSessionsChange?: (sessions: ChatSession[]) => void;
  agentId?: string;
  hideTaskProgress?: boolean;
  onFinalize?: (answer: string) => void;
  attachedDoc?: { name: string; text: string } | null;
  onAttachedDocUsed?: () => void;
  initialMessages?: { role: 'user' | 'assistant'; content: string; timestamp: string }[];
}

const ANIMATION_STYLE = `
  @keyframes chatSlideIn {
    from { opacity: 0; transform: translateY(8px) scale(0.98); }
    to { opacity: 1; transform: translateY(0) scale(1); }
  }
  @keyframes chatPulse {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 0.8; }
  }
  @keyframes chatGlow {
    0%, 100% { box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.2); }
    50% { box-shadow: 0 0 0 6px rgba(37, 99, 235, 0); }
  }
  .chat-message-enter {
    animation: chatSlideIn 0.3s ease-out forwards;
  }
  .chat-typing-dot {
    display: inline-block; width: 6px; height: 6px; border-radius: 50%;
    background: #94a3b8; margin: 0 1px;
    animation: chatPulse 1.4s infinite;
  }
  .chat-typing-dot:nth-child(2) { animation-delay: 0.2s; }
  .chat-typing-dot:nth-child(3) { animation-delay: 0.4s; }
  .chat-send-btn:not(:disabled):hover {
    animation: chatGlow 1.5s infinite;
  }
  .chat-tab {
    transition: all 0.2s ease;
  }
  .chat-tab:hover {
    background: #f1f5f9 !important;
    color: #1d4ed8 !important;
  }
  .chat-scroll::-webkit-scrollbar { width: 5px; }
  .chat-scroll::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 10px; }
  .chat-scroll::-webkit-scrollbar-track { background: transparent; }
`;

export const ChatView: React.FC<ChatViewProps> = ({ workspaceId, onSessionsChange, agentId, hideTaskProgress, onFinalize, attachedDoc, onAttachedDocUsed, initialMessages }) => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [creatingSession, setCreatingSession] = useState(false);
  const [selectedModelId, setSelectedModelId] = useState<string>('');
  const [availableModels, setAvailableModels] = useState<any[]>([]);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [phase, setPhase] = useState<string>('');
  const [pendingFinalize, setPendingFinalize] = useState(false);
  const [finalizeAnswer, setFinalizeAnswer] = useState<string>('');
  const bottomRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => { scrollToBottom(); }, [messages]);

  const fetchSessions = useCallback(async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const [sessRes, modelsRes] = await Promise.all([
        fetch(`/api/v1/sessions?workspace_id=${workspaceId}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} }),
        fetch('/api/ai-models', { headers: token ? { Authorization: `Bearer ${token}` } : {} }),
      ]);
      if (sessRes.ok) {
        const data = await sessRes.json();
        const list = data.sessions || [];
        setSessions(list);
        onSessionsChange?.(list);
        if (!activeSessionId && list.length > 0) setActiveSessionId(list[0].session_id);
      }
      if (modelsRes.ok) {
        const models = await modelsRes.json();
        setAvailableModels(models || []);
        const dm = (models || []).find((m: any) => m.is_default === 1 || m.is_default === true);
        if (dm && !selectedModelId) setSelectedModelId(dm.id);
      }
    } catch { /* silent */ }
  }, [workspaceId, activeSessionId, onSessionsChange, selectedModelId]);

  useEffect(() => { fetchSessions(); }, [fetchSessions]);

  useEffect(() => {
    if (!activeSessionId) { setMessages([]); return; }
    const token = localStorage.getItem('auth_token');
    fetch(`/api/v1/sessions/${activeSessionId}/messages`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then((r) => r.json())
      .then((data) => { setMessages((data.messages || []).map((m: any) => ({ id: m.id, role: m.role, content: m.content || '', timestamp: m.created_at || new Date().toISOString() }))); })
      .catch(() => setMessages([]));
  }, [activeSessionId]);

  const createSession = async () => {
    setCreatingSession(true);
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch('/api/v1/sessions', { method: 'POST', headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }, body: JSON.stringify({ workspace_id: workspaceId }) });
      if (res.ok) { const data = await res.json(); setActiveSessionId(data.session_id); setMessages([]); fetchSessions(); }
    } catch { /* silent */ } finally { setCreatingSession(false); }
  };

  const deleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const token = localStorage.getItem('auth_token');
      await fetch(`/api/v1/sessions/${sessionId}`, { method: 'DELETE', headers: token ? { Authorization: `Bearer ${token}` } : {} });
      if (activeSessionId === sessionId) setActiveSessionId(null);
      fetchSessions();
    } catch { /* silent */ }
  };

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading || !activeSessionId) return;

    // Build prompt with attached document context
    let finalPrompt = trimmed;
    let docAttachment = null;
    if (attachedDoc) {
      docAttachment = { ...attachedDoc };
      finalPrompt = `[Attached document: ${attachedDoc.name}]\n\n${attachedDoc.text}\n\n---\n\nUser message: ${trimmed}`;
    }

    setMessages((prev) => [...prev, { id: `msg-${Date.now()}`, role: 'user', content: trimmed, timestamp: new Date().toISOString() }]);
    setInput(''); setLoading(true); setTasks([]); setPhase('understanding');
    if (docAttachment) { onAttachedDocUsed?.(); setInput(''); }
    try {
      const token = localStorage.getItem('auth_token');
      const chatBody: any = { prompt: finalPrompt, workspace_id: workspaceId };
      if (agentId) chatBody.agent_id = agentId;
      if (selectedModelId) {
        const model = availableModels.find((m) => m.id === selectedModelId);
        if (model) { chatBody.model = model.model_id; if (model.api_key) chatBody.model_api_key = model.api_key; if (model.base_url) chatBody.model_base_url = model.base_url; }
      }
      const res = await fetch(`/api/v1/sessions/${activeSessionId}/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }, body: JSON.stringify(chatBody) });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `Error ${res.status}`);
      const reader = res.body?.getReader();
      if (!reader) throw new Error('No stream');
      const decoder = new TextDecoder(); let buffer = ''; let finalAnswer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n'); buffer = lines.pop() || '';
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const event = JSON.parse(line.slice(6));
            const handlers: Record<string, () => void> = {
              status: () => setPhase(event.phase),
              plan: () => { setTasks(event.tasks.map((t: any) => ({ id: t.id, title: t.title, description: t.description, status: 'pending' as const }))); setPhase('executing'); },
              task_start: () => setTasks((prev) => prev.map((t) => t.id === event.id ? { ...t, status: 'running' as const } : t)),
              task_done: () => setTasks((prev) => prev.map((t) => t.id === event.id ? { ...t, status: 'done' as const, result_preview: event.result_preview } : t)),
              task_failed: () => setTasks((prev) => prev.map((t) => t.id === event.id ? { ...t, status: 'failed' as const } : t)),
              compiling: () => { setPhase('compiling'); setTasks([]); },
              answer: () => {
                finalAnswer = event.content;
                if (event.show_finalize) {
                  setPendingFinalize(true);
                  setFinalizeAnswer(event.content);
                }
              },
              error: () => { setLoading(false); setMessages((prev) => [...prev, { id: `msg-${Date.now()}`, role: 'assistant', content: `❌ ${event.message || 'Error'}`, timestamp: new Date().toISOString() }]); },
            };
            handlers[event.type]?.();
          } catch { /* skip */ }
        }
      }
      if (finalAnswer) setMessages((prev) => [...prev, { id: `msg-${Date.now()}`, role: 'assistant', content: finalAnswer, timestamp: new Date().toISOString() }]);
      setTasks([]); setPhase(''); setTimeout(fetchSessions, 500);
    } catch (e: any) {
      setMessages((prev) => [...prev, { id: `msg-${Date.now()}`, role: 'assistant', content: `❌ ${e.message || 'Failed'}`, timestamp: new Date().toISOString() }]);
    } finally { setLoading(false); setTasks([]); setPhase(''); }
  };

  const jsonBlockStyle: React.CSSProperties = {
    background: '#1e293b', color: '#e2e8f0', borderRadius: 8, padding: '12px 14px',
    fontSize: 12, lineHeight: 1.6, fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
    overflowX: 'auto', margin: '6px 0', whiteSpace: 'pre', wordBreak: 'break-word',
  };

  const renderJsonBlock = (jsonStr: string) => {
    let formatted: string;
    try { formatted = JSON.stringify(JSON.parse(jsonStr), null, 2); } catch { formatted = jsonStr; }
    return <pre style={jsonBlockStyle}>{formatted}</pre>;
  };

  const renderInline = (text: string) => {
    const parts = text.split(/\*\*/);
    return parts.map((part, i) => i % 2 === 1 ? <strong key={i}>{part}</strong> : part);
  };

  const renderTextBlock = (text: string) => {
    return text.split('\n').map((line, i, arr) => {
      const hMatch = line.match(/^(#{1,6})\s+(.*)/);
      if (hMatch) {
        const level = hMatch[1].length;
        const sizes: Record<number, number> = { 1: 18, 2: 16, 3: 15, 4: 14, 5: 13, 6: 13 };
        return <span key={i} style={{ display: 'block', fontWeight: 700, fontSize: sizes[level] || 13, marginTop: i > 0 ? 8 : 0, color: '#0f172a' }}>{renderInline(hMatch[2])}</span>;
      }
      return <span key={i}>{renderInline(line)}{i < arr.length - 1 && <br />}</span>;
    });
  };

  const renderContent = (content: string) => {
    const segments = content.split(/```/);
    return segments.map((seg, i) => {
      if (i % 2 === 1) {
        const nl = seg.indexOf('\n');
        const lang = nl > -1 ? seg.slice(0, nl).trim().toLowerCase() : seg.trim().toLowerCase();
        const code = nl > -1 ? seg.slice(nl + 1) : seg;
        if (lang === 'json') return <React.Fragment key={i}>{renderJsonBlock(code)}</React.Fragment>;
        return <pre key={i} style={{ ...jsonBlockStyle, background: '#334155' }}>{code}</pre>;
      }
      if (!seg) return null;
      return <React.Fragment key={i}>{renderTextBlock(seg)}</React.Fragment>;
    });
  };

  const getSessionTitle = (s: ChatSession) => (s.title && s.title !== 'Untitled' ? s.title : `Chat ${s.session_id?.slice(-4) || ''}`);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#fafbfc' }}>
      <style>{ANIMATION_STYLE}</style>

      {/* Tab Bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 1, padding: '8px 10px 0', background: '#fff', borderBottom: '1px solid #e5e7eb', overflowX: 'auto', whiteSpace: 'nowrap', minHeight: 42, flexShrink: 0 }}>
        {sessions.map((s) => (
          <div key={s.session_id} onClick={() => setActiveSessionId(s.session_id)} className="chat-tab"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '6px 14px', borderRadius: '8px 8px 0 0', fontSize: 12, cursor: 'pointer', background: activeSessionId === s.session_id ? '#fff' : 'transparent', border: activeSessionId === s.session_id ? '1px solid #e5e7eb' : '1px solid transparent', borderBottom: activeSessionId === s.session_id ? '1px solid #fff' : 'none', marginBottom: activeSessionId === s.session_id ? -1 : 0, color: activeSessionId === s.session_id ? '#111827' : '#6b7280', fontWeight: activeSessionId === s.session_id ? 600 : 400, position: 'relative', zIndex: activeSessionId === s.session_id ? 1 : 0 }}>
            <MessageOutlined style={{ fontSize: 11, opacity: 0.6 }} />
            <span style={{ maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis' }}>{getSessionTitle(s)}</span>
            {s.message_count > 0 && <span style={{ fontSize: 10, background: '#e5e7eb', color: '#6b7280', borderRadius: 10, padding: '0 6px', minWidth: 18, textAlign: 'center' }}>{s.message_count}</span>}
            <CloseOutlined style={{ fontSize: 9, color: '#9ca3af', padding: '2px 0', opacity: 0.6, transition: 'opacity 0.15s' }} onClick={(e) => deleteSession(s.session_id, e)}
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.opacity = '1'; (e.currentTarget as HTMLElement).style.color = '#ef4444'; }} onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.opacity = '0.6'; (e.currentTarget as HTMLElement).style.color = '#9ca3af'; }} />
          </div>
        ))}
        <Button type="text" size="small" icon={<PlusOutlined />} disabled style={{ color: '#d1d5db', flexShrink: 0, fontSize: 12, fontWeight: 500, opacity: 0.5, pointerEvents: 'none' }}>New Chat</Button>
      </div>

      {/* Messages Area */}
      <div className="chat-scroll" style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
        {messages.length === 0 && !activeSessionId && !initialMessages && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: 300, color: '#9ca3af' }}>
            <div style={{ width: 72, height: 72, borderRadius: '50%', background: '#f0fdf4', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20, border: '2px solid #bbf7d0' }}>
              <BulbOutlined style={{ fontSize: 32, color: '#4ade80' }} />
            </div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#374151', marginBottom: 6 }}>Start a Conversation</div>
            <div style={{ fontSize: 13, color: '#9ca3af', textAlign: 'center', maxWidth: 300, lineHeight: 1.5 }}>
              Click <strong style={{ color: '#6b7280' }}>+ New Chat</strong> to begin. Your AI agent will help you explore ideas, answer questions, and build.
            </div>
          </div>
        )}

        {messages.length === 0 && !activeSessionId && initialMessages && initialMessages.map((msg, idx) => (
          <div key={`init-${idx}`} className="chat-message-enter"
            style={{ display: 'flex', gap: 12, marginBottom: 20, justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start', animationDelay: `${idx * 0.05}s` }}>
            {msg.role === 'assistant' && (
              <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, #10b981, #059669)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, boxShadow: '0 2px 8px rgba(16, 185, 129, 0.2)' }}>
                <RobotOutlined style={{ fontSize: 14, color: '#fff' }} />
              </div>
            )}
            <div style={{ maxWidth: '75%', padding: '12px 16px', borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px', background: msg.role === 'user' ? '#2563eb' : '#fff', color: msg.role === 'user' ? '#fff' : '#1e293b', border: msg.role === 'user' ? 'none' : '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
              <div style={{ fontSize: 12, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{msg.content}</div>
              <div style={{ fontSize: 9, color: msg.role === 'user' ? '#93c5fd' : '#94a3b8', marginTop: 6, textAlign: 'right' }}>{msg.timestamp}</div>
            </div>
            {msg.role === 'user' && (
              <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, #3b82f6, #2563eb)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, boxShadow: '0 2px 8px rgba(37, 99, 235, 0.2)' }}>
                <UserOutlined style={{ fontSize: 14, color: '#fff' }} />
              </div>
            )}
          </div>
        ))}

        {messages.length === 0 && activeSessionId && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: 300 }}>
            <div style={{ width: 56, height: 56, borderRadius: '50%', background: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16, border: '2px solid #bfdbfe' }}>
              <ThunderboltOutlined style={{ fontSize: 24, color: '#3b82f6' }} />
            </div>
            <Text style={{ fontSize: 14, fontWeight: 600, color: '#374151' }}>New session ready</Text>
            <Text type="secondary" style={{ fontSize: 12, marginTop: 4 }}>Type your first message below</Text>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={msg.id} className="chat-message-enter"
            style={{ display: 'flex', gap: 12, marginBottom: 20, justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start', animationDelay: `${idx * 0.05}s` }}>
            {msg.role === 'assistant' && (
              <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, #10b981, #059669)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, boxShadow: '0 2px 8px rgba(16, 185, 129, 0.2)' }}>
                <RobotOutlined style={{ fontSize: 14, color: '#fff' }} />
              </div>
            )}
            <div style={{ maxWidth: '72%', padding: '12px 16px', borderRadius: 16, background: msg.role === 'user' ? '#2563eb' : '#fff', color: msg.role === 'user' ? '#fff' : '#1f2937', border: msg.role === 'assistant' ? '1px solid #e5e7eb' : 'none', fontSize: 13.5, lineHeight: 1.65, wordBreak: 'break-word', boxShadow: msg.role === 'user' ? '0 2px 12px rgba(37, 99, 235, 0.15)' : '0 1px 3px rgba(0,0,0,0.04)', borderBottomRightRadius: msg.role === 'user' ? 4 : 16, borderBottomLeftRadius: msg.role === 'assistant' ? 4 : 16 }}>
              {msg.role === 'assistant' ? renderContent(msg.content) : <span style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</span>}
              <div style={{ fontSize: 10, marginTop: 6, opacity: 0.4, textAlign: 'right', letterSpacing: '0.02em' }}>{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>

              {/* Show Finalize button if this is the last assistant message and pending */}
              {pendingFinalize && msg.role === 'assistant' && msg.id === messages[messages.length - 1]?.id && (
                <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid #e5e7eb', textAlign: 'center' }}>
                  <Button
                    type="primary"
                    size="small"
                    icon={<CheckOutlined />}
                    onClick={() => { setPendingFinalize(false); onFinalize?.(finalizeAnswer); }}
                    style={{ background: '#16a34a', border: 'none', borderRadius: 6 }}
                  >
                    Finalize Requirements
                  </Button>
                </div>
              )}
            </div>
            {msg.role === 'user' && (
              <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, #3b82f6, #2563eb)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, boxShadow: '0 2px 8px rgba(37, 99, 235, 0.2)' }}>
                <UserOutlined style={{ fontSize: 14, color: '#fff' }} />
              </div>
            )}
          </div>
        ))}

        {!hideTaskProgress && (tasks.length > 0 || phase) && (
          <div style={{ marginBottom: 12 }}><TaskProgress tasks={tasks} phase={phase} /></div>
        )}

        {loading && (hideTaskProgress || (tasks.length === 0 && !phase)) && (
          <div className="chat-message-enter" style={{ display: 'flex', gap: 12, marginBottom: 20, alignItems: 'center' }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, #10b981, #059669)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 2px 8px rgba(16, 185, 129, 0.2)' }}>
              <RobotOutlined style={{ fontSize: 14, color: '#fff' }} />
            </div>
            <div style={{ padding: '12px 18px', borderRadius: 16, background: '#fff', border: '1px solid #e5e7eb', fontSize: 13, color: '#9ca3af', borderBottomLeftRadius: 4 }}>
              <Space size={6}>
                <span className="chat-typing-dot" />
                <span className="chat-typing-dot" />
                <span className="chat-typing-dot" />
              </Space>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{ padding: '12px 16px 8px', background: '#fff', borderTop: '1px solid #e5e7eb', flexShrink: 0 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
          <TextArea value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
            placeholder={activeSessionId ? 'Type a message...' : 'Create a new chat to start...'} disabled={!activeSessionId || loading} autoSize={{ minRows: 1, maxRows: 5 }}
            style={{ flex: 1, borderRadius: 12, fontSize: 13.5, border: '1px solid #e5e7eb', background: '#f9fafb', padding: '10px 14px', resize: 'none' }} />
          <Upload
            accept=".pdf,.docx,.txt,.md"
            showUploadList={false}
            beforeUpload={(file: any) => { const reader = new FileReader(); reader.onload = () => console.log('Doc loaded:', file.name); reader.readAsText(file); return false; }}
          >
            <Button icon={<PaperClipOutlined />} type="text" style={{ color: '#9ca3af', fontSize: 18, padding: '8px 4px' }} />
          </Upload>
          <Button type="primary" icon={loading ? <LoadingOutlined /> : <SendOutlined />} disabled={!input.trim() || loading || !activeSessionId}
            onClick={sendMessage} className="chat-send-btn"
            style={{ background: '#2563eb', borderRadius: 12, width: 42, height: 42, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 2px 8px rgba(37, 99, 235, 0.25)' }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 4px 2px', fontSize: 10, color: '#9ca3af' }}>
          <Text type="secondary" style={{ fontSize: 10 }}>Enter to send · Shift+Enter for new line</Text>
          {availableModels.length > 0 && (
            <Select size="small" value={selectedModelId || undefined} onChange={setSelectedModelId} placeholder="Model" bordered={false}
              style={{ width: 160, fontSize: 10, color: '#9ca3af' }}
              dropdownStyle={{ fontSize: 11 }}>
              {availableModels.map((m: any) => (
                <Select.Option key={m.id} value={m.id} style={{ fontSize: 11 }}>{m.name} <Text type="secondary" style={{ fontSize: 10 }}>({m.model_id})</Text></Select.Option>
              ))}
            </Select>
          )}
        </div>
      </div>
    </div>
  );
};

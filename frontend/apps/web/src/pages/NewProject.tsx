/* eslint-disable @typescript-eslint/no-explicit-any, no-console */
import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkBreaks from 'remark-breaks';
import remarkGfm from 'remark-gfm';
import {
  Button, Input, Tag, Upload, message, Spin, Drawer, Tooltip, Typography,
} from 'antd';
import {
  ArrowLeftOutlined, RocketOutlined,
  AudioOutlined, FileTextOutlined, SafetyOutlined, ToolOutlined,
  BookOutlined, LinkOutlined, SendOutlined, UserOutlined, RobotOutlined,
  EditOutlined, PaperClipOutlined, ClockCircleOutlined, CheckCircleOutlined,
  BulbOutlined, CloseOutlined, EyeOutlined, ThunderboltOutlined, CloudServerOutlined, CalendarOutlined,
  SearchOutlined, SettingOutlined, ApiOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { ApiClient } from '../api/client';
import { CATEGORIES, PROVIDER_FIELDS } from '../components/CollaborationPanel';
import './NewProject.css';

const { Text } = Typography;

export type ProjectStep = 'upload' | 'transcribe' | 'discuss' | 'meeting_preferences' | 'finalize' | 'connectors';

const WORKFLOW_STEPS: Array<{
  key: ProjectStep;
  label: string;
  description: string;
}> = [
  { key: 'upload', label: 'Brief', description: 'Share the project context' },
  { key: 'transcribe', label: 'Analyze', description: 'Extract goals and constraints' },
  { key: 'discuss', label: 'Clarify', description: 'Resolve open questions' },
  { key: 'meeting_preferences', label: 'Meetings', description: 'Set your meeting cadence' },
  { key: 'finalize', label: 'Review', description: 'Approve the requirements' },
  { key: 'connectors', label: 'Connectors', description: 'Optional · Connect project tools' },
];

const UNIVERSAL_CONNECTORS = new Set(['Jira', 'Asana', 'Slack', 'Teams', 'Meet', 'AWS', 'GCP', 'Azure']);

const DEFAULT_CONNECTOR_FIELDS = [
  { label: 'Connection name', key: 'connection_name', type: 'text', placeholder: 'Name this project connection' },
  { label: 'Workspace or endpoint', key: 'endpoint', type: 'text', placeholder: 'https://example.com/workspace' },
];

interface RequirementSectionProps {
  title: string;
  icon: React.ReactNode;
  tone: 'blue' | 'violet' | 'teal' | 'green';
  items?: string[];
  tags?: string[];
}

interface DiscoveryMessage {
  id: number;
  role: 'user' | 'agent';
  content: string;
  timestamp: string;
  category?: string;
  categoryLabel?: string;
}

const RequirementSection: React.FC<RequirementSectionProps> = ({
  title,
  icon,
  tone,
  items = [],
  tags = [],
}) => (
  <section className={`np-requirement-section np-requirement-section--${tone}`}>
    <div className="np-requirement-section__header">
      <span className="np-requirement-section__icon">{icon}</span>
      <h3>{title}</h3>
      <span className="np-requirement-section__count">{items.length || tags.length}</span>
    </div>
    {items.length > 0 ? (
      <ol className="np-requirement-list">
        {items.map((item) => <li key={item}>{item}</li>)}
      </ol>
    ) : null}
    {tags.length > 0 ? (
      <div className="np-tag-list">
        {tags.map((tag, index) => <Tag key={`${tag}-${index}`}>{tag}</Tag>)}
      </div>
    ) : null}
  </section>
);

const MarkdownMessage: React.FC<{ content: string }> = ({ content }) => (
  <ReactMarkdown
    remarkPlugins={[remarkGfm, remarkBreaks]}
    components={{
      a: ({ node: _node, ...props }: any) => (
        <a {...props} target="_blank" rel="noreferrer" />
      ),
    }}
  >
    {content}
  </ReactMarkdown>
);

// ── Helpers ──────────────────────────────────────────────────────────────

function getToken(): string {
  return localStorage.getItem('auth_token') || '';
}

function timestamp(): string {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function isFinalizeIntent(input: string): boolean {
  const normalized = input
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ');

  if (!normalized) return false;

  const exactIntents = new Set([
    'create project',
    'create the project',
    'generate requirements',
    'generate the requirements',
    'finalize requirements',
    'finalise requirements',
    'finalize the requirements',
    'finalise the requirements',
    'create requirements package',
    'create the requirements package',
    'move forward',
    'go ahead',
    'proceed',
  ]);

  return exactIntents.has(normalized)
    || normalized.startsWith('please create project')
    || normalized.startsWith('please generate requirements')
    || normalized.startsWith('please finalize')
    || normalized.startsWith('please finalise');
}

// ── Component ────────────────────────────────────────────────────────────

export const NewProject: React.FC = () => {
  const navigate = useNavigate();
  const [projectName, setProjectName] = useState('');
  const [textInput, setTextInput] = useState('');
  const [fileAdded, setFileAdded] = useState(false);
  const [fileName, setFileName] = useState('');
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [inputSubmitted, setInputSubmitted] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [transcribed, setTranscribed] = useState(false);
  const [showTranscription, setShowTranscription] = useState(false);
  const [transcriptionText, setTranscriptionText] = useState('');
  const [messages, setMessages] = useState<DiscoveryMessage[]>([]);
  const [currentStep, setCurrentStep] = useState<ProjectStep>('upload');
  const [showRequirements, setShowRequirements] = useState(false);
  const [requirementsDrawerOpen, setRequirementsDrawerOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // ── Discovery session state ──
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [requirements, setRequirements] = useState<any>(null);
  const [generatingReqs, setGeneratingReqs] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisFailed, setAnalysisFailed] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [connectorSearch, setConnectorSearch] = useState('');
  const [connectorCategory, setConnectorCategory] = useState('all');
  const [selectedConnectors, setSelectedConnectors] = useState<Set<string>>(() => new Set());
  const [connectorDrawerOpen, setConnectorDrawerOpen] = useState(false);
  const [activeConnector, setActiveConnector] = useState<string | null>(null);
  const [connectorDrafts, setConnectorDrafts] = useState<Record<string, Record<string, string>>>({});

    // Meeting preferences state
    const [meetingFrequency, setMeetingFrequency] = useState<string>('weekly');
    const [customFrequency, setCustomFrequency] = useState('');
    const [preferredTime, setPreferredTime] = useState('');

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const [chatInput, setChatInput] = useState('');

  // ── STT (Speech-to-Text) state ──
  const [isListening, setIsListening] = useState(false);
  const [sttMode, setSttMode] = useState<'webspeech' | 'recording'>('webspeech');
  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const [isTranscribing, setIsTranscribing] = useState(false);

  useEffect(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SR && window.location.protocol !== 'file:') {
      const recognition = new SR();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event: any) => {
        let finalTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          }
        }
        if (finalTranscript) {
          setTextInput((prev) => (prev ? prev + ' ' : '') + finalTranscript);
        }
      };

      recognition.onend = () => setIsListening(false);

      recognition.onerror = (event: any) => {
        console.error('[STT] error:', event.error);
        setIsListening(false);
        if (event.error === 'network') {
          setSttMode('recording');
          message.info('Live speech unavailable. Switched to record mode.');
        } else if (event.error === 'not-allowed') {
          message.error('Microphone access denied.');
        }
      };

      recognitionRef.current = recognition;
      setSttMode('webspeech');
    } else {
      setSttMode('recording');
    }
  }, []);

  // ── Web Speech toggle ──
  const toggleWebSpeech = () => {
    if (!recognitionRef.current) return;
    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch {
        setSttMode('recording');
      }
    }
  };

  // ── MediaRecorder fallback (record → send to backend Whisper) ──
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        if (blob.size < 100) return; // too small, ignore

        setIsTranscribing(true);
        try {
          const formData = new FormData();
          formData.append('audio', blob, 'recording.webm');
          const token = localStorage.getItem('auth_token') || '';
          const res = await fetch('/api/discovery/transcribe', {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` },
            body: formData,
          });
          const data = await res.json();
          if (data.text) {
            setTextInput((prev) => (prev ? prev + ' ' : '') + data.text);
          } else {
            message.warning('Could not transcribe audio. Please try again or type your requirements.');
          }
        } catch (err) {
          console.error('[STT] transcription failed:', err);
          message.error('Transcription failed. Please type your requirements.');
        } finally {
          setIsTranscribing(false);
        }
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setIsListening(true);
    } catch (err) {
      console.error('[STT] mic access error:', err);
      message.error('Could not access microphone. Please allow mic permission.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    setIsListening(false);
  };

  const toggleRecording = () => {
    if (isListening) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // ── TTS (Text-to-Speech) for agent messages ──
  const [speakingMsgId, setSpeakingMsgId] = useState<number | null>(null);

  const toggleSpeak = (msgId: number, text: string) => {
    if (!text) return;
    if (speakingMsgId === msgId) {
      // Already speaking this message — stop it
      window.speechSynthesis.cancel();
      setSpeakingMsgId(null);
    } else {
      // Stop any current speech and start new one
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'en-US';
      utterance.rate = 1;
      utterance.onend = () => setSpeakingMsgId(null);
      utterance.onerror = () => setSpeakingMsgId(null);
      setSpeakingMsgId(msgId);
      window.speechSynthesis.speak(utterance);
    }
  };

  // ── 1. Submit input → create session + ingest ──────────────────────────

  const handleSubmitInput = async () => {
    const typed = textInput.trim();
    const hasFile = fileAdded && !!fileContent;

    if (!typed && !hasFile) {
      message.warning('Type your requirements or attach a document first.');
      return;
    }

    // Combine text + file content (like ChatGPT: typed text + attachment)
    let sourceText = '';
    if (typed && hasFile) {
      sourceText = `${typed}\n\n---\n\nAttached document (${fileName}):\n\n${fileContent}`;
    } else if (typed) {
      sourceText = typed;
    } else {
      sourceText = fileContent || '';
    }

    setIsSubmitting(true);
    try {
      // Create discovery session.
      const sessionRes = await ApiClient.post('/discovery/sessions', {});
      const sid = sessionRes.session_id;
      setSessionId(sid);

      // Ingest the combined source text.
      await ApiClient.post(`/discovery/${sid}/ingest`, {
        text: sourceText,
        file_name: hasFile ? fileName : undefined,
      });

      setTranscriptionText(sourceText);
      setInputSubmitted(true);
      setCurrentStep('transcribe');
      await handleAnalyze(sid, sourceText);
    } catch (err: any) {
      console.error('[NewProject] ingest failed:', err);
      message.error('Failed to submit requirements. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // ── 2. Analyze → run understand + clarify ──────────────────────────────

  const handleAnalyze = async (
    requestedSessionId: string | null = sessionId,
    sourceOverride?: string,
  ) => {
    setTranscribing(true);
    setShowTranscription(true);
    setCurrentStep('transcribe');
    setAnalysisFailed(false);

    let activeSessionId = requestedSessionId;
    if (!activeSessionId) {
      // No session (e.g. audio stub) — create one now with whatever text we have.
      try {
        const sourceText = sourceOverride || transcriptionText || textInput.trim() || 'No input provided';
        const sessionRes = await ApiClient.post('/discovery/sessions', {});
        const sid = sessionRes.session_id;
        setSessionId(sid);
        activeSessionId = sid;
        await ApiClient.post(`/discovery/${sid}/ingest`, { text: sourceText });
      } catch {
        message.error('Failed to initialize session.');
        setTranscribing(false);
        setAnalysisFailed(true);
        return;
      }
    }

    setIsAnalyzing(true);
    try {
      const res = await ApiClient.post(`/discovery/${activeSessionId}/analyze`, {});
      setTranscribed(true);

      // Build the conversation from the analyze response.
      const ts = timestamp();
      const newMessages: DiscoveryMessage[] = [];
      if (res.recap) {
        newMessages.push({ id: 0, role: 'agent', content: res.recap, timestamp: ts });
      }
      if (res.questions) {
        newMessages.push({
          id: 1,
          role: 'agent',
          content: res.questions,
          timestamp: ts,
          category: res.category,
          categoryLabel: res.category_label,
        });
      }
      setMessages(newMessages);
      setCurrentStep('discuss');
      setAnalysisFailed(false);
    } catch (err: any) {
      console.error('[NewProject] analyze failed:', err);
      message.error('Analysis failed. Please check your input and try again.');
      setAnalysisFailed(true);
    } finally {
      setTranscribing(false);
      setIsAnalyzing(false);
    }
  };

  // ── 3. Chat → send user message ────────────────────────────────────────

  const handleSendMessage = async () => {
    if (!chatInput.trim() || !sessionId) return;
    const userContent = chatInput.trim();
    const ts = timestamp();

    const userMsg: DiscoveryMessage = {
      id: messages.length,
      role: 'user',
      content: userContent,
      timestamp: ts,
    };
    setMessages((prev) => [...prev, userMsg]);
    setChatInput('');

    if (isFinalizeIntent(userContent)) {
      if (requirements) {
        const agentMsg: DiscoveryMessage = {
          id: messages.length + 1,
          role: 'agent',
          content: 'The working brief is ready. Choose any project connectors you want, or skip that optional step and create the workspace.',
          timestamp: timestamp(),
        };
        setMessages((prev) => [...prev, agentMsg]);
        setCurrentStep('connectors');
        setShowRequirements(true);
        return;
      }

      const nextStep: ProjectStep = requirements ? 'finalize' : 'meeting_preferences';
      const agentMsg: DiscoveryMessage = {
        id: messages.length + 1,
        role: 'agent',
        content: 'Understood. I have enough to move forward. Set the meeting cadence now, then generate the requirements package for review.',
        timestamp: timestamp(),
      };
      setMessages((prev) => [...prev, agentMsg]);
      setCurrentStep(nextStep);
      return;
    }

    setIsSending(true);

    try {
      const res = await ApiClient.post(`/discovery/${sessionId}/chat`, {
        message: userContent,
      });
      const agentMsg: DiscoveryMessage = {
        id: messages.length + 1,
        role: 'agent' as const,
        content: res.reply || 'Noted.',
        timestamp: timestamp(),
        category: res.category,
        categoryLabel: res.category_label,
      };
      setMessages((prev) => [...prev, agentMsg]);
      if (res.show_finalize) {
        setCurrentStep('meeting_preferences');
      }
    } catch (err: any) {
      console.error('[NewProject] chat failed:', err);
      const errMsg: DiscoveryMessage = {
        id: messages.length + 1,
        role: 'agent',
        content: 'Sorry, I encountered an error processing your message. Please try again.',
        timestamp: timestamp(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsSending(false);
    }
  };

  // ── 4. Generate requirements → finalize (renders the panel, stays put) ──

  const buildSummary = (r: any): string => {
    const lines: string[] = [];
    lines.push(`**Project: ${r.projectName || 'Untitled Project'}**`);
    if (r.objective) lines.push(`\n**Objective:** ${r.objective}`);
    if (r.functionalReqs?.length) {
      lines.push('\n**Functional Requirements:**');
      r.functionalReqs.forEach((fr: string) => lines.push(`- ${fr}`));
    }
    if (r.techStack?.length) {
      lines.push('\n**Technical Stack:**');
      lines.push(r.techStack.join(', '));
    }
    if (r.phases?.length) {
      lines.push('\n**Migration Strategy:**');
      r.phases.forEach((p: any) => lines.push(`- ${p.name} (${p.duration}): ${p.description}`));
    }
    if (r.risks?.length) {
      lines.push('\n**Risks:**');
      r.risks.forEach((rk: string) => lines.push(`- ${rk}`));
    }
    lines.push("\nI pulled the main decisions into the working brief. Give it a read, adjust anything that feels off, then create the project when it reflects what you mean.");
    return lines.join('\n');
  };

  const handleGenerateRequirements = async () => {
    if (!sessionId) {
      message.error('No active session. Please submit your requirements first.');
      return;
    }
    setGeneratingReqs(true);
    try {
      const effectiveFreq = meetingFrequency === 'custom' ? customFrequency : meetingFrequency;
      const finalizeRes = await ApiClient.post(`/discovery/${sessionId}/finalize`, {
        meeting_frequency: effectiveFreq || 'weekly',
        preferred_time: preferredTime || null,
      });
      const finalizedReqs = finalizeRes.requirements;
      if (!finalizedReqs) {
        message.error("We couldn't pull the brief together yet. Add a little more detail and try again.");
        return;
      }

      setRequirements(finalizedReqs);
      setShowRequirements(true);
      setCurrentStep('finalize');
      const recommended = new Set<string>();
      const requirementConnectors = Array.isArray(finalizedReqs.connectors) ? finalizedReqs.connectors : [];
      CATEGORIES.forEach((category) => {
        category.tools.forEach((tool) => {
          if (requirementConnectors.some((item: string) => item.toLowerCase().includes(tool.name.toLowerCase()))) {
            recommended.add(tool.name);
          }
        });
      });
      setSelectedConnectors(recommended);

      const summaryMsg: DiscoveryMessage = {
        id: messages.length,
        role: 'agent',
        content: buildSummary(finalizedReqs),
        timestamp: timestamp(),
      };
      setMessages((prev) => [...prev, summaryMsg]);
    } catch (err: any) {
      console.error('[NewProject] finalize failed:', err);
      message.error('Failed to generate requirements. Please try again.');
    } finally {
      setGeneratingReqs(false);
    }
  };

  // ── 5. Create project → uses the already-generated requirements ─────────

  const waitForWorkspaceReady = async (projectId: string): Promise<'ready' | 'team_failed' | 'timeout'> => {
    for (let attempt = 0; attempt < 10; attempt += 1) {
      const [team, workspace] = await Promise.all([
        ApiClient.get(`/discovery/projects/${projectId}/team`).catch(() => null),
        ApiClient.get(`/projects/${projectId}/workspace`).catch(() => null),
      ]);
      const positionsReady = Array.isArray(team?.positions) && team.positions.length > 0;
      const assignedAgentsReady = Array.isArray(team?.agents) && team.agents.length > 0;
      const teamReady = team?.team_status === 'ready' && (positionsReady || assignedAgentsReady);
      const docsReady = Array.isArray(workspace?.documents) && workspace.documents.length > 0;
      if (teamReady && docsReady) return 'ready';
      if (team?.team_status === 'failed') return 'team_failed';
      await new Promise((resolve) => setTimeout(resolve, 1500));
    }
    return 'timeout';
  };

  const handleCreateProject = async () => {
    if (!requirements) {
      message.error('Please generate the requirements package first.');
      return;
    }
    setCreating(true);
    message.loading({ key: 'create-project', content: 'Creating project workspace...', duration: 0 });
    try {
      const token = getToken();
      const res = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          name: projectName || requirements?.projectName || 'Untitled Project',
          businessGoal: requirements?.objective || '',
          priority: 'High',
          department: 'Engineering',
          requirements: {
            functionalReqs: requirements.functionalReqs || [],
            techStack: requirements.techStack || [],
            skills: requirements.skills || [],
            connectors: requirements.connectors || [],
            risks: requirements.risks || [],
            phases: requirements.phases || [],
            governance: requirements.governance || [],
            guardrails: requirements.guardrails || [],
            infrastructure: requirements.infrastructure || [],
          },
        }),
      });
      const data = await res.json();

      // Link discovery session to the created project
      if (sessionId && data.id) {
        try {
          // link-project persists the session→project link AND kicks off
          // agent-team design server-side (team_status='generating'). The
          // workspace polls team-status and swaps in the org chart when ready.
          await ApiClient.post(`/discovery/${sessionId}/link-project`, { project_id: data.id });
          message.loading({ key: 'create-project', content: 'Creating workers and knowledge documents...', duration: 0 });
          const readyState = await waitForWorkspaceReady(data.id);
          if (readyState === 'team_failed') {
            message.warning({ key: 'create-project', content: 'Workspace created. Team generation failed; regenerate it from the workspace.', duration: 3 });
          } else if (readyState === 'timeout') {
            message.info({ key: 'create-project', content: 'Workspace created. Team setup is still finishing in the background.', duration: 3 });
          }
        } catch (linkErr) {
          // Non-critical — project is already created
          console.error('[NewProject] Could not link discovery session to project', linkErr);
          throw linkErr;
        }
      }

      message.success({ key: 'create-project', content: 'Opening workspace', duration: 1 });
      navigate(`/projects/${data.id}/workspace`);
    } catch (err: any) {
      console.error('[NewProject] create project failed:', err);
      message.error({ key: 'create-project', content: 'Failed to create project. Please try again.' });
      setCreating(false);
    }
  };

  // ── File upload handler ────────────────────────────────────────────────

  const handleFileRead = (file: any) => {
    setFileAdded(true);
    setFileName(`${file.name} (${(file.size / 1024 / 1024).toFixed(1)}MB)`);

    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      setFileContent(text?.substring(0, 50000) || '');
    };
    reader.readAsText(file);
    return false; // prevent default upload
  };

  // ── Clear the current attachment ───────────────────────────────────────

  const handleClearAttachment = () => {
    setFileAdded(false);
    setFileName('');
    setFileContent(null);
  };

  const toggleConnector = (connectorName: string) => {
    setSelectedConnectors((current) => {
      const next = new Set(current);
      if (next.has(connectorName)) next.delete(connectorName);
      else next.add(connectorName);
      return next;
    });
  };

  const openConnectorConfiguration = (connectorName: string) => {
    setActiveConnector(connectorName);
    setConnectorDrawerOpen(true);
  };

  const updateConnectorDraft = (key: string, value: string) => {
    if (!activeConnector) return;
    setConnectorDrafts((current) => ({
      ...current,
      [activeConnector]: {
        ...(current[activeConnector] || {}),
        [key]: value,
      },
    }));
  };

  const saveConnectorDraft = () => {
    if (!activeConnector) return;
    setSelectedConnectors((current) => new Set(current).add(activeConnector));
    setConnectorDrawerOpen(false);
    message.success(`${activeConnector} connected for this setup`);
  };

  const currentStepIndex = WORKFLOW_STEPS.findIndex((step) => step.key === currentStep);
  const submittedPreview = textInput.trim() || (fileAdded ? fileName : '');
  const sourceLabel = fileAdded && textInput.trim()
    ? 'Brief + Document'
    : fileAdded
      ? 'Document'
      : 'Written brief';
  const requirementConnectorNames = Array.isArray(requirements?.connectors)
    ? requirements.connectors.map((item: string) => item.toLowerCase())
    : [];
  const activeConnectorFields = activeConnector
    ? (PROVIDER_FIELDS[activeConnector] || DEFAULT_CONNECTOR_FIELDS)
    : DEFAULT_CONNECTOR_FIELDS;
  const normalizedConnectorSearch = connectorSearch.trim().toLowerCase();
  const visibleConnectorCategories = CATEGORIES
    .filter((category) => connectorCategory === 'all' || category.key === connectorCategory)
    .map((category) => ({
      ...category,
      tools: category.tools.filter((tool) => (
        !normalizedConnectorSearch
        || tool.name.toLowerCase().includes(normalizedConnectorSearch)
        || category.title.toLowerCase().includes(normalizedConnectorSearch)
      )),
    }))
    .filter((category) => category.tools.length > 0);

  const connectorsPanel = (
    <div className="np-connectors">
      <section className="np-connectors__intro">
        <div className="np-connectors__intro-icon"><ApiOutlined /></div>
        <div>
          <span className="np-eyebrow">Optional setup</span>
          <h3>Connect the tools your project needs</h3>
          <p>Select shared organization tools or add draft details for a project connection. You can also do this later from the workspace.</p>
        </div>
        <Tag className="np-connectors__optional">Optional</Tag>
      </section>

      <div className="np-connectors__toolbar">
        <Input
          aria-label="Search connectors"
          prefix={<SearchOutlined />}
          placeholder="Search connectors"
          value={connectorSearch}
          onChange={(event) => setConnectorSearch(event.target.value)}
          allowClear
        />
        <div className="np-connectors__filters" role="group" aria-label="Connector categories">
          <Button
            size="small"
            type={connectorCategory === 'all' ? 'primary' : 'default'}
            onClick={() => setConnectorCategory('all')}
          >
            All
          </Button>
          {CATEGORIES.map((category) => (
            <Button
              size="small"
              type={connectorCategory === category.key ? 'primary' : 'default'}
              onClick={() => setConnectorCategory(category.key)}
              key={category.key}
            >
              {category.title}
            </Button>
          ))}
        </div>
      </div>

      {visibleConnectorCategories.length > 0 ? (
        <div className="np-connector-groups">
          {visibleConnectorCategories.map((category) => (
            <section className="np-connector-group" key={category.key}>
              <div className="np-connector-group__header">
                <span>{category.icon}</span>
                <h4>{category.title}</h4>
                <span>{category.tools.length}</span>
              </div>
              <div className="np-connector-grid">
                {category.tools.map((tool) => {
                  const isUniversal = UNIVERSAL_CONNECTORS.has(tool.name);
                  const isSelected = selectedConnectors.has(tool.name);
                  const isRecommended = requirementConnectorNames.some((name: string) => name.includes(tool.name.toLowerCase()));
                  const hasDraft = Object.keys(connectorDrafts[tool.name] || {}).length > 0;
                  return (
                    <article
                      className={`np-connector-card ${isSelected ? 'np-connector-card--selected' : ''}`}
                      key={tool.name}
                    >
                      <div className="np-connector-card__top">
                        <div className="np-connector-card__logo">
                          <img src={tool.logo} alt="" loading="lazy" />
                        </div>
                        <div className="np-connector-card__identity">
                          <strong>{tool.name}</strong>
                          <span>{category.title}</span>
                        </div>
                        {isRecommended ? <Tag color="blue">Recommended</Tag> : null}
                      </div>
                      <div className="np-connector-card__meta">
                        <Tag color={isUniversal ? 'cyan' : 'gold'}>
                          {isUniversal ? 'Universal' : 'Project'}
                        </Tag>
                        <span>
                          {isUniversal
                            ? 'Shared organization connection'
                            : hasDraft ? 'Connection details added' : 'Private to this project'}
                        </span>
                      </div>
                      <div className="np-connector-card__action">
                        {isUniversal ? (
                          <Button
                            block
                            type={isSelected ? 'primary' : 'default'}
                            icon={isSelected ? <CheckCircleOutlined /> : <LinkOutlined />}
                            onClick={() => toggleConnector(tool.name)}
                          >
                            {isSelected ? 'Selected' : 'Select'}
                          </Button>
                        ) : (
                          <>
                            <Button
                              block
                              type={isSelected ? 'primary' : 'default'}
                              icon={isSelected ? <CheckCircleOutlined /> : <SettingOutlined />}
                              onClick={() => openConnectorConfiguration(tool.name)}
                            >
                              {isSelected ? 'Edit connection' : 'Configure'}
                            </Button>
                            {isSelected ? (
                              <Button
                                type="text"
                                aria-label={`Remove ${tool.name}`}
                                onClick={() => toggleConnector(tool.name)}
                              >
                                Remove
                              </Button>
                            ) : null}
                          </>
                        )}
                      </div>
                    </article>
                  );
                })}
              </div>
            </section>
          ))}
        </div>
      ) : (
        <div className="np-connectors__empty">
          <SearchOutlined />
          <strong>No connectors found</strong>
          <span>Try another search or category.</span>
        </div>
      )}
    </div>
  );

  const requirementsPanel = requirements ? (
    <div className="np-requirements">
      <div className="np-requirements__header">
        <div>
          <span className="np-eyebrow">Working brief</span>
          <h2>{requirements.projectName || projectName || 'Untitled project'}</h2>
        </div>
        <div className="np-requirements__status">
          <CheckCircleOutlined />
          Looks ready to review
        </div>
      </div>

      {requirements.objective ? (
        <div className="np-objective">
          <BulbOutlined />
          <div>
            <span>What this project is for</span>
            <p>{requirements.objective}</p>
          </div>
        </div>
      ) : null}

      <RequirementSection
        title="Functional requirements"
        icon={<FileTextOutlined />}
        tone="blue"
        items={requirements.functionalReqs || []}
      />
      <RequirementSection
        title="Skills required"
        icon={<ToolOutlined />}
        tone="violet"
        tags={requirements.skills || []}
      />
      <RequirementSection
        title="Connectors"
        icon={<LinkOutlined />}
        tone="teal"
        tags={requirements.connectors || []}
      />
      <RequirementSection
        title="Technology"
        icon={<BookOutlined />}
        tone="green"
        tags={requirements.techStack || []}
      />

      {requirements.risks?.length > 0 ? (
        <section className="np-detail-section np-detail-section--risk">
          <div className="np-detail-section__header">
            <SafetyOutlined />
            <h3>Delivery risks</h3>
            <span>{requirements.risks.length}</span>
          </div>
          <ul>
            {requirements.risks.map((risk: string) => <li key={risk}>{risk}</li>)}
          </ul>
        </section>
      ) : null}

      {requirements.phases?.length > 0 ? (
        <section className="np-detail-section np-detail-section--phases">
          <div className="np-detail-section__header">
            <ClockCircleOutlined />
            <h3>Delivery phases</h3>
            <span>{requirements.phases.length}</span>
          </div>
          <div className="np-phase-list">
            {requirements.phases.map((phase: any, index: number) => (
              <div className="np-phase" key={`${phase.name}-${index}`}>
                <div className="np-phase__marker">{index + 1}</div>
                <div>
                  <div className="np-phase__title">
                    <strong>{phase.name}</strong>
                    {phase.duration ? <Tag>{phase.duration}</Tag> : null}
                  </div>
                  <p>{phase.description}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {[
        { title: 'Governance', icon: <SafetyOutlined />, items: requirements.governance },
        { title: 'Guardrails', icon: <ThunderboltOutlined />, items: requirements.guardrails },
        { title: 'Infrastructure', icon: <CloudServerOutlined />, items: requirements.infrastructure },
      ].map((group) => group.items?.length ? (
        <section className="np-detail-section" key={group.title}>
          <div className="np-detail-section__header">
            {group.icon}
            <h3>{group.title}</h3>
            <span>{group.items.length}</span>
          </div>
          <div className="np-control-list">
            {group.items.map((item: any, index: number) => (
              <div key={`${typeof item === 'string' ? item : item.label}-${index}`}>
                <strong>{typeof item === 'string' ? item : item.label}</strong>
                {typeof item === 'string' ? null : <p>{item.detail}</p>}
              </div>
            ))}
          </div>
        </section>
      ) : null)}
    </div>
  ) : null;

  return (
    <div className={`np-shell ${showRequirements ? 'np-shell--with-requirements' : ''}`}>
      <header className="np-header">
        <div className="np-header__identity">
          <Tooltip title="Back to projects">
            <Button
              aria-label="Back to projects"
              className="np-icon-button"
              icon={<ArrowLeftOutlined />}
              type="text"
              onClick={() => navigate('/projects')}
            />
          </Tooltip>
          <div className="np-brand-mark"><RocketOutlined /></div>
          <div>
            <span className="np-eyebrow">Project workspace</span>
            <h1>New project</h1>
          </div>
        </div>

        <div className="np-project-name">
          <label htmlFor="new-project-name">Project name</label>
          <Input
            id="new-project-name"
            placeholder="Name this initiative"
            value={projectName}
            onChange={(event) => setProjectName(event.target.value)}
            variant="borderless"
          />
        </div>

        <div className="np-header__actions">
          {requirements ? (
            <>
              <Button
                className="np-mobile-review"
                icon={<EyeOutlined />}
                onClick={() => setRequirementsDrawerOpen(true)}
              >
                Review
              </Button>
              <Button
                type="primary"
                className="np-create-button"
                icon={currentStep === 'connectors' ? <RocketOutlined /> : <LinkOutlined />}
                onClick={currentStep === 'connectors'
                  ? handleCreateProject
                  : () => setCurrentStep('connectors')}
                loading={creating}
              >
                {currentStep === 'connectors' ? 'Create project' : 'Continue to connectors'}
              </Button>
            </>
          ) : (
            <Button
              type="primary"
              icon={<FileTextOutlined />}
              onClick={() => setCurrentStep('meeting_preferences')}
              disabled={!sessionId || messages.length === 0 || generatingReqs}
              loading={generatingReqs}
            >
              Set meeting preferences
            </Button>
          )}
        </div>
      </header>

      <div className="np-workspace">
        <aside className="np-workflow">
          <div className="np-agent">
            <div className="np-agent__avatar"><RobotOutlined /></div>
            <div>
              <strong>Project partner</strong>
              <span><i /> Here to help you think it through</span>
            </div>
          </div>

          <nav className="np-steps" aria-label="Project setup progress">
            {WORKFLOW_STEPS.map((step, index) => {
              const isComplete = index < currentStepIndex;
              const isCurrent = index === currentStepIndex;
              return (
                <div
                  className={`np-step ${isComplete ? 'np-step--complete' : ''} ${isCurrent ? 'np-step--current' : ''}`}
                  key={step.key}
                >
                  <div className="np-step__marker">
                    {isComplete ? <CheckCircleOutlined /> : index + 1}
                  </div>
                  <div>
                    <strong>{step.label}</strong>
                    <span>{step.description}</span>
                  </div>
                </div>
              );
            })}
          </nav>

          <div className="np-privacy-note">
            <SafetyOutlined />
            <div>
              <strong>Just for this project</strong>
              <span>Your notes and source material stay with this workspace.</span>
            </div>
          </div>
        </aside>

        <main className="np-conversation">
          <div className="np-conversation__header">
            <div>
              <span className="np-eyebrow">{currentStep === 'connectors' ? 'Project setup' : 'Working session'}</span>
              <h2>{currentStep === 'connectors' ? 'Choose your connectors' : 'Let’s get the shape of this right'}</h2>
            </div>
            <div className={`np-session-state ${transcribed || currentStep === 'connectors' ? 'np-session-state--ready' : ''}`}>
              <span />
              {currentStep === 'connectors'
                ? `${selectedConnectors.size} selected`
                : transcribed ? 'Ready to review' : inputSubmitted ? 'Got it' : 'Ready when you are'}
            </div>
          </div>

          <div className="np-conversation__body">
            {currentStep === 'connectors' ? connectorsPanel : null}

            {currentStep !== 'connectors' && !inputSubmitted ? (
              <div className="np-welcome">
                <div className="np-welcome__icon"><BulbOutlined /></div>
                <span className="np-eyebrow">A good place to start</span>
                <h2>What are you trying to change?</h2>
                <p>
                  Tell us what is happening today, what needs to improve, and who this work is for.
                  Rough notes are fine. We’ll help turn them into something the team can act on.
                </p>
                <div className="np-prompt-grid">
                  <div>
                    <strong>What prompted this?</strong>
                    <span>What problem or opportunity started the conversation?</span>
                  </div>
                  <div>
                    <strong>What are we working with?</strong>
                    <span>Which systems, people, and dependencies are involved?</span>
                  </div>
                  <div>
                    <strong>What would good look like?</strong>
                    <span>What should be different when this is finished?</span>
                  </div>
                </div>
              </div>
            ) : null}

            {currentStep !== 'connectors' && inputSubmitted && messages.length === 0 ? (
              <div className="np-analysis-ready">
                <div className="np-analysis-ready__source">
                  <div className="np-source-icon">
                    {fileAdded ? <FileTextOutlined /> : <EditOutlined />}
                  </div>
                  <div>
                    <span>{sourceLabel}</span>
                    <strong>Project context submitted</strong>
                  </div>
                  <CheckCircleOutlined className="np-analysis-ready__check" />
                </div>
                {submittedPreview ? (
                  <p className="np-analysis-ready__preview">{submittedPreview}</p>
                ) : null}
                <div className="np-analysis-ready__action">
                  <div>
                    <strong>{analysisFailed ? 'That first pass didn’t finish' : 'Taking a first pass'}</strong>
                    <span>
                      {analysisFailed
                        ? 'Your brief is saved. Try the analysis again when you’re ready.'
                        : 'Pulling out the goals, dependencies, risks, and questions worth discussing.'}
                    </span>
                  </div>
                  {analysisFailed ? (
                    <Button
                      type="primary"
                      icon={<ThunderboltOutlined />}
                      onClick={() => handleAnalyze()}
                      loading={isAnalyzing || transcribing}
                    >
                      Try again
                    </Button>
                  ) : (
                    <div className="np-analysis-progress">
                      <Spin size="small" />
                      Looking through the details
                    </div>
                  )}
                </div>
              </div>
            ) : null}

            {currentStep !== 'connectors' && showTranscription ? (
              <div className="np-transcription">
                <div className="np-transcription__header">
                  <FileTextOutlined />
                  <strong>From your source</strong>
                  <Tag>Original note</Tag>
                </div>
                <p>{transcriptionText}</p>
              </div>
            ) : null}

            {currentStep !== 'connectors' && messages.length > 0 ? (
              <div className="np-message-list">
                {messages.map((msg) => (
                  <div className={`np-message np-message--${msg.role}`} key={msg.id}>
                    <div className="np-message__avatar">
                      {msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
                    </div>
                    <div className="np-message__content">
                      {msg.role === 'agent' && msg.categoryLabel ? (
                        <div className={`np-message__category np-message__category--${msg.category}`}>
                          <span className="np-message__category-marker" aria-hidden="true" />
                          <span>{msg.categoryLabel}</span>
                        </div>
                      ) : null}
                      <div className="np-message__meta">
                        <strong>{msg.role === 'user' ? 'You' : 'Project partner'}</strong>
                        <span>{msg.timestamp}</span>
                        {msg.role === 'agent' && (
                          <Tooltip title={speakingMsgId === msg.id ? 'Stop speaking' : 'Read aloud'}>
                            <Button
                              type="text"
                              size="small"
                              icon={<AudioOutlined />}
                              onClick={() => toggleSpeak(msg.id, msg.content)}
                              style={{
                                padding: '0 4px',
                                fontSize: 11,
                                color: speakingMsgId === msg.id ? '#ef4444' : '#94a3b8',
                              }}
                            />
                          </Tooltip>
                        )}
                      </div>
                      <div className="np-message__text">
                        <MarkdownMessage content={msg.content} />
                      </div>
                    </div>
                  </div>
                ))}
                {isSending ? (
                  <div className="np-message np-message--agent">
                    <div className="np-message__avatar"><RobotOutlined /></div>
                    <div className="np-typing">
                      <Spin size="small" />
                      Thinking through that
                    </div>
                  </div>
                ) : null}
              </div>
            ) : null}

            <div ref={chatEndRef} />
          </div>

          <footer className="np-composer">
            {currentStep === 'connectors' ? (
              <div className="np-connectors__footer">
                <div>
                  <strong>{selectedConnectors.size} connector{selectedConnectors.size === 1 ? '' : 's'} selected</strong>
                  <span>Connector setup is optional and can be changed later.</span>
                </div>
                <div className="np-connectors__footer-actions">
                  <Button onClick={() => setCurrentStep('finalize')} disabled={creating}>
                    Back to requirements
                  </Button>
                  <Button onClick={handleCreateProject} loading={creating}>
                    Skip for now
                  </Button>
                  <Button type="primary" icon={<RocketOutlined />} onClick={handleCreateProject} loading={creating}>
                    Create project
                  </Button>
                </div>
              </div>
            ) : !inputSubmitted ? (
              <div className="np-composer__box">
                <Input.TextArea
                  aria-label="Project requirements"
                  placeholder={isListening ? 'Listening... speak now' : 'Describe the problem, desired outcome, users, systems, constraints, and timeline...'}
                  value={textInput}
                  onChange={(event) => setTextInput(event.target.value)}
                  autoSize={{ minRows: 3, maxRows: 8 }}
                  variant="borderless"
                  style={isListening ? { borderLeft: '3px solid #ef4444', background: '#fef2f2' } : undefined}
                />
                {fileAdded ? (
                  <div className="np-attachment">
                    <FileTextOutlined />
                    <span>{fileName}</span>
                    <Tooltip title="Remove attachment">
                      <Button
                        aria-label="Remove attachment"
                        icon={<CloseOutlined />}
                        type="text"
                        size="small"
                        onClick={handleClearAttachment}
                      />
                    </Tooltip>
                  </div>
                ) : null}
                <div className="np-composer__toolbar">
                  <div className="np-source-options" aria-label="Input source">
                    <Upload
                      accept=".txt,.md,.csv,.json,.xml"
                      showUploadList={false}
                      beforeUpload={handleFileRead}
                    >
                      <Tooltip title={fileAdded ? fileName : 'Attach document'}>
                        <Button
                          type={fileAdded ? 'primary' : 'text'}
                          icon={<PaperClipOutlined />}
                          style={{ fontSize: 18, width: 40, height: 40, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                        />
                      </Tooltip>
                    </Upload>
                    <Tooltip title={isListening ? 'Stop recording' : 'Speak'}>
                      <Button
                        type={isListening ? 'primary' : 'text'}
                        danger={isListening}
                        icon={<AudioOutlined />}
                        onClick={sttMode === 'webspeech' ? toggleWebSpeech : toggleRecording}
                        loading={isTranscribing}
                        style={{
                          fontSize: 18, width: 40, height: 40,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          ...(isListening ? { animation: 'pulse 1.5s infinite', color: '#fff' } : {}),
                        }}
                      />
                    </Tooltip>
                  </div>
                  <Button
                    type="primary"
                    icon={<SendOutlined />}
                    onClick={handleSubmitInput}
                    disabled={!textInput.trim() && !fileAdded && !isListening && !isTranscribing}
                    loading={isSubmitting}
                  >
                    Send
                  </Button>
                </div>
              </div>
            ) : currentStep !== 'meeting_preferences' && messages.length > 0 ? (
              <div className="np-chat-composer">
                <Input.TextArea
                  aria-label="Message the business analyst"
                  placeholder="Answer a question or add a constraint..."
                  value={chatInput}
                  onChange={(event) => setChatInput(event.target.value)}
                  onPressEnter={(event) => {
                    if (!event.shiftKey) {
                      event.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  autoSize={{ minRows: 1, maxRows: 5 }}
                  disabled={isSending || creating || generatingReqs}
                />
                <Tooltip title="Send message">
                  <Button
                    aria-label="Send message"
                    type="primary"
                    icon={<SendOutlined />}
                    onClick={handleSendMessage}
                    disabled={!chatInput.trim() || isSending || creating || generatingReqs}
                  />
                </Tooltip>
              </div>
            ) : currentStep === 'meeting_preferences' ? (
              <div style={{ padding: '16px 20px', background: '#f8fafc', borderTop: '1px solid #e2e8f0' }}>
                <div style={{ marginBottom: 12 }}>
                  <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 4 }}>Meeting Frequency</Text>
                  <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 8 }}>How often should the team meet to review progress?</Text>
                  <select
                    value={meetingFrequency}
                    onChange={(e) => setMeetingFrequency(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid #d9d9d9', fontSize: 12 }}
                  >
                    <option value="daily">Daily</option>
                    <option value="every2days">Every 2 Days</option>
                    <option value="weekly">Weekly</option>
                    <option value="biweekly">Bi-weekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="custom">Custom</option>
                  </select>
                </div>
                {meetingFrequency === 'custom' && (
                  <div style={{ marginBottom: 12 }}>
                    <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>Custom Frequency</Text>
                    <Input
                      placeholder="e.g., Every 3 days, Twice a week"
                      value={customFrequency}
                      onChange={(e) => setCustomFrequency(e.target.value)}
                      style={{ fontSize: 12 }}
                    />
                  </div>
                )}
                <div style={{ marginBottom: 12 }}>
                  <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 4 }}>Preferred Meeting Time</Text>
                  <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 8 }}>Leave empty — the agent will ask you to confirm the time before each meeting.</Text>
                  <Input
                    placeholder="e.g., 10:00 AM (optional)"
                    value={preferredTime}
                    onChange={(e) => setPreferredTime(e.target.value)}
                    style={{ fontSize: 12 }}
                    prefix={<ClockCircleOutlined style={{ color: '#94a3b8' }} />}
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                  <Button onClick={() => setCurrentStep('discuss')} disabled={generatingReqs}>
                    Back to questions
                  </Button>
                  <Button
                    type="primary"
                    icon={<FileTextOutlined />}
                    onClick={handleGenerateRequirements}
                    loading={generatingReqs}
                    disabled={!sessionId}
                  >
                    Generate requirements
                  </Button>
                </div>
              </div>
            ) : (
              <div className="np-composer__hint">
                {analysisFailed ? <ThunderboltOutlined /> : <Spin size="small" />}
                {analysisFailed
                  ? 'The brief is safe. Retry the first pass above.'
                  : 'Pulling together the first questions now.'}
              </div>
            )}
          </footer>
        </main>

        {showRequirements && requirements ? (
          <aside className="np-requirements-panel">{requirementsPanel}</aside>
        ) : null}
      </div>

      <Drawer
        className="np-requirements-drawer"
        title="Working brief"
        width={420}
        open={requirementsDrawerOpen}
        onClose={() => setRequirementsDrawerOpen(false)}
      >
        {requirementsPanel}
      </Drawer>

      <Drawer
        className="np-connector-drawer"
        title={activeConnector ? `Configure ${activeConnector}` : 'Configure connector'}
        width={440}
        open={connectorDrawerOpen}
        onClose={() => setConnectorDrawerOpen(false)}
        extra={<Tag color="gold">Project connector</Tag>}
      >
        <div className="np-connector-config">
          <div className="np-connector-config__notice">
            <SettingOutlined />
            <div>
              <strong>Project connection</strong>
              <span>These details stay in this setup screen for now and are not sent to the backend.</span>
            </div>
          </div>
          {activeConnectorFields.map((field) => (
            <label className="np-connector-config__field" key={field.key}>
              <span>{field.label}</span>
              {field.type === 'password' ? (
                <Input.Password
                  placeholder={field.placeholder}
                  value={activeConnector ? connectorDrafts[activeConnector]?.[field.key] || '' : ''}
                  onChange={(event) => updateConnectorDraft(field.key, event.target.value)}
                />
              ) : (
                <Input
                  placeholder={field.placeholder}
                  value={activeConnector ? connectorDrafts[activeConnector]?.[field.key] || '' : ''}
                  onChange={(event) => updateConnectorDraft(field.key, event.target.value)}
                />
              )}
            </label>
          ))}
          <div className="np-connector-config__actions">
            <Button onClick={() => setConnectorDrawerOpen(false)}>Cancel</Button>
            <Button type="primary" icon={<LinkOutlined />} onClick={saveConnectorDraft}>Connect</Button>
          </div>
        </div>
      </Drawer>
    </div>
  );
};

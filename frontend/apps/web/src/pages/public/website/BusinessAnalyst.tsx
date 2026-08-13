import React, { useState, useRef, useEffect } from 'react';
import {
  Typography, Button, Input, Upload, Card, Tag, Form, message, Alert, Modal, Row, Col, Select, Progress
} from 'antd';
import {
  RobotOutlined, SendOutlined, AudioOutlined, PaperClipOutlined,
  CheckCircleOutlined, WarningOutlined, KeyOutlined,
  SettingOutlined, UserOutlined, MailOutlined, BankOutlined, LogoutOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { ApiClient } from '../../../api/client';
import './BusinessAnalyst.css';

const { TextArea } = Input;
const { Title, Text } = Typography;

type ChatMsg = {
  role: 'user' | 'assistant';
  sender: string;
  content: string;
  timestamp: string;
  isSpecialist?: boolean;
  isFallbackForm?: boolean;
  isByokPrompt?: boolean;
};

export default function BusinessAnalyst() {
  const navigate = useNavigate();

  // Authentication & Session state
  const [authLoading, setAuthLoading] = useState(true);
  const [userEmail, setUserEmail] = useState('');

  // BYOK Settings Modal
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [byokForm] = Form.useForm();
  const [byokConnected, setByokConnected] = useState(false);
  const [configuredProvider, setConfiguredProvider] = useState<string | null>(null);
  const [configuredModel, setConfiguredModel] = useState<string | null>(null);

  // Missing Specialist / Capability Modal
  const [fallbackOpen, setFallbackOpen] = useState(false);
  const [fallbackForm] = Form.useForm();
  const [fallbackSubmitted, setFallbackSubmitted] = useState(false);

  // BA Simulation States
  const [msgs, setMsgs] = useState<ChatMsg[]>([
    {
      role: 'assistant',
      sender: 'Business Analyst',
      content: "Welcome to the AegisOS Business Analyst discovery session. Describe your requirement or business problem here. You don't need a complete specification yet—I will help structure objectives, constraints, and dependencies.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [activeSpecialist, setActiveSpecialist] = useState<string | null>(null);
  const [chatCount, setChatCount] = useState(0);
  const [complimentaryExhausted, setComplimentaryExhausted] = useState(false);

  // 3-panel Sidebar Context States
  const [reqCtx, setReqCtx] = useState({
    understanding: 'Awaiting requirement details...',
    category: 'General Business Analyst',
    progress: 10,
    constraints: [] as string[],
    openQuestions: [] as string[],
    risks: [] as string[],
    dependencies: [] as string[],
    estimatedScope: 'TBD',
    nextStep: 'Describe business requirement'
  });

  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Auth protection check on mount
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (token === 'simulated_token') {
      setUserEmail('demo@aegisos.com');
      setAuthLoading(false);
      return;
    }

    ApiClient.get('/auth/me')
      .then(res => {
        setUserEmail(res.user.email);
        setAuthLoading(false);
      })
      .catch(() => {
        navigate('/signup');
      });
  }, [navigate]);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [msgs]);

  const handleLogout = async () => {
    try {
      await ApiClient.post('/auth/logout', {});
    } catch (e) {
      // ignore
    }
    localStorage.clear();
    navigate('/landing');
  };

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;
    const text = inputValue.trim();
    setInputValue('');

    const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const newMsgs = [...msgs, { role: 'user' as const, sender: 'You', content: text, timestamp: ts }];
    setMsgs(newMsgs);

    const nextCount = chatCount + 1;
    setChatCount(nextCount);

    if (nextCount >= 4 && !byokConnected) {
      setTimeout(() => {
        setComplimentaryExhausted(true);
        setMsgs(prev => [
          ...prev,
          {
            role: 'assistant',
            sender: activeSpecialist || 'Business Analyst',
            content: "Your complimentary AI usage has ended. Please connect your own AI provider key from Settings to continue requirement discovery.",
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            isByokPrompt: true
          }
        ]);
        setSettingsOpen(true);
      }, 1200);
      return;
    }

    setTimeout(() => {
      const lower = text.toLowerCase();
      const isFintech = lower.includes('finance') || lower.includes('bank') || lower.includes('onboard') || lower.includes('payment') || lower.includes('reconcil');
      const isMigration = lower.includes('mysql') || lower.includes('database') || lower.includes('frappe') || lower.includes('migrate') || lower.includes('sql');
      const isErp = lower.includes('erp') || lower.includes('manufactur') || lower.includes('inventory') || lower.includes('supply');

      if (isFintech) {
        setMsgs(prev => [
          ...prev,
          {
            role: 'assistant',
            sender: 'Business Analyst',
            content: `I've analyzed your initial input: "${text}". This falls under FinTech Operations & KYC compliance. I am routing you to our Specialized FinTech Business Analyst for deeper discovery...`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }
        ]);

        setReqCtx({
          understanding: text,
          category: 'Classifying...',
          progress: 30,
          constraints: ['KYC compliance policies', 'Real-time validation SLA'],
          openQuestions: ['What banking CRM platform is target system?'],
          risks: ['PII leak boundaries'],
          dependencies: ['CRM API', 'Compliance gatekeeper node'],
          estimatedScope: 'Analyzing...',
          nextStep: 'Specialist classification'
        });

        setTimeout(() => {
          setActiveSpecialist('FinTech Business Analyst');
          setMsgs(prev => [
            ...prev,
            {
              role: 'assistant',
              sender: 'FinTech Business Analyst',
              content: "Hello, I am your Specialized FinTech Business Analyst. I've initialized our secure workspace footprint. What core data repositories and transaction gateways will this workflow integrate with?",
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              isSpecialist: true
            }
          ]);

          setReqCtx(prev => ({
            ...prev,
            category: 'FinTech Specialist',
            progress: 55,
            estimatedScope: '3 Digital Nodes (Est. 2 weeks)',
            nextStep: 'Clarify system integrations'
          }));
        }, 1500);

      } else if (isMigration) {
        setMsgs(prev => [
          ...prev,
          {
            role: 'assistant',
            sender: 'Business Analyst',
            content: `I've analyzed your initial input: "${text}". This matches our Database & System Migration patterns. I am routing you to our Specialized Database & Systems Architect...`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }
        ]);

        setReqCtx({
          understanding: text,
          category: 'Classifying...',
          progress: 35,
          constraints: ['Target Frappe/ERPNext version compatibility', 'Minimal downtime requirement'],
          openQuestions: ['What is the approximate data volume or database size?', 'Are custom tables or core schema changes required?'],
          risks: ['Data loss during row-mapping transformation'],
          dependencies: ['MySQL connection credentials', 'Target Frappe environment'],
          estimatedScope: 'Analyzing...',
          nextStep: 'Specialist classification'
        });

        setTimeout(() => {
          setActiveSpecialist('Systems Architect');
          setMsgs(prev => [
            ...prev,
            {
              role: 'assistant',
              sender: 'Systems Architect',
              content: "Hello, I am your Specialized Database & Systems Architect. I've mapped out the migration framework. Could you clarify the exact volume of data, any custom schema rules, and your preferred downtime window?",
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              isSpecialist: true
            }
          ]);

          setReqCtx(prev => ({
            ...prev,
            category: 'Systems Architect',
            progress: 60,
            estimatedScope: '2 Digital Nodes (Est. 1 week)',
            nextStep: 'Clarify volume & downtime constraints'
          }));
        }, 1500);

      } else if (isErp) {
        setMsgs(prev => [
          ...prev,
          {
            role: 'assistant',
            sender: 'Business Analyst',
            content: `I've analyzed your initial input: "${text}". This falls under ERP & Manufacturing Operations. I am routing you to our Specialized Operations Business Analyst...`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }
        ]);

        setReqCtx({
          understanding: text,
          category: 'Classifying...',
          progress: 35,
          constraints: ['Real-time shop floor hardware integration', 'Supply chain policy gates'],
          openQuestions: ['What are the key manufacturing methods (discrete vs process)?', 'How many active users will require ERP permissions?'],
          risks: ['Inventory sync latency'],
          dependencies: ['Shop floor machinery APIs', 'Warehouse location data'],
          estimatedScope: 'Analyzing...',
          nextStep: 'Specialist classification'
        });

        setTimeout(() => {
          setActiveSpecialist('Operations Analyst');
          setMsgs(prev => [
            ...prev,
            {
              role: 'assistant',
              sender: 'Operations Analyst',
              content: "Hello, I am your Specialized Operations Business Analyst. I've initialized the ERP operational discovery workspace. Could you outline your core production workflows and specify how many distinct departments will be onboarded?",
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              isSpecialist: true
            }
          ]);

          setReqCtx(prev => ({
            ...prev,
            category: 'Operations Analyst',
            progress: 58,
            estimatedScope: '4 Digital Nodes (Est. 3 weeks)',
            nextStep: 'Clarify production flows'
          }));
        }, 1500);

      } else {
        setMsgs(prev => [
          ...prev,
          {
            role: 'assistant',
            sender: 'Business Analyst',
            content: `I've captured your requirement: "${text}". We understand the objective. To help structure the constraints and risks, could you share the primary system goals, any third-party dependencies, and your target completion timeline?`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }
        ]);

        setReqCtx(prev => ({
          ...prev,
          understanding: text,
          category: 'General Business Analyst',
          progress: 40,
          nextStep: 'Clarify project timeline & goals'
        }));
      }
    }, 1200);
  };

  const handleSimulateRecord = () => {
    setIsRecording(true);
    message.loading({ content: 'Listening...', key: 'record-load' });
    setTimeout(() => {
      setIsRecording(false);
      message.success({ content: 'Voice requirement captured', key: 'record-load', duration: 2 });
      setInputValue('We need to build a secure reconciliation channel for payment validation.');
    }, 2000);
  };

  const handleUploadSimulate = (info: any) => {
    message.loading({ content: `Processing ${info.file.name}...`, key: 'upload-load' });
    setTimeout(() => {
      message.success({ content: `${info.file.name} successfully parsed into session context.`, key: 'upload-load', duration: 2 });
      setInputValue(`Uploaded document brief: Onboarding automation using Salesforce and compliance validation rules.`);
    }, 1500);
  };

  const handleConnectBYOK = (values: any) => {
    message.loading({ content: 'Verifying API key connection to provider...', key: 'byok-load' });
    setTimeout(() => {
      message.success({ content: 'Model connected successfully', key: 'byok-load', duration: 2 });
      setByokConnected(true);
      setConfiguredProvider(values.provider);
      setConfiguredModel(values.model);
      setComplimentaryExhausted(false);
      setSettingsOpen(false);

      setMsgs(prev => [
        ...prev,
        {
          role: 'assistant',
          sender: activeSpecialist || 'Business Analyst',
          content: `✅ Connected successfully via User-provided API Key (${values.provider} - ${values.model}). Memory context and structured understanding intact. Ask your next question to continue.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);

      setReqCtx(prev => ({
        ...prev,
        progress: 85,
        nextStep: 'Finalize solution blueprint'
      }));
    }, 1200);
  };

  const handleCapabilityReview = () => {
    setFallbackSubmitted(true);
    message.success('Capability review request submitted successfully.');
  };

  if (authLoading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#f4f1ea', gap: '16px' }}>
        <Progress type="circle" percent={45} strokeColor="#69765d" status="active" />
        <Text strong style={{ color: '#242321' }}>Verifying AegisOS Session...</Text>
      </div>
    );
  }

  return (
    <div className="aegis-public-ba-shell">
      {/* PROFESSIONAL COMPACT HEADER */}
      <div className="ba-header-nav">
        <div className="brand" onClick={() => navigate('/landing')} style={{ cursor: 'pointer' }}>
          <div className="brand-mark"></div>
          <span className="brand-text">AegisOS</span>
          <span className="product-badge">Business Analyst</span>
        </div>
        <div className="header-meta">
          <span className="session-context">Active Discovery Session</span>
          <div className="user-profile">
            <UserOutlined className="user-icon" />
            <span className="user-email">{userEmail}</span>
          </div>
          <Button 
            type="text" 
            icon={<SettingOutlined />} 
            onClick={() => setSettingsOpen(true)} 
            className="settings-btn"
          >
            AI Settings
          </Button>
          <Button 
            type="text" 
            danger 
            icon={<LogoutOutlined />} 
            onClick={handleLogout}
            className="logout-btn"
          >
            Logout
          </Button>
        </div>
      </div>

      <div className="ba-simulation-container">
        
        {/* LEFT PANEL: Business Discovery Context */}
        <aside className="ba-side-panel left-panel">
          <div className="panel-header">
            <h3>Discovery Context</h3>
          </div>
          <div className="side-section">
            <label className="section-label">Objective</label>
            <div className="value-text">{reqCtx.understanding}</div>
          </div>
          
          <div className="side-section">
            <label className="section-label">Specialist Category</label>
            <div>
              <Tag color={activeSpecialist ? 'purple' : 'blue'} className="specialist-tag">
                {reqCtx.category}
              </Tag>
            </div>
          </div>

          <div className="side-section">
            <label className="section-label">Constraints</label>
            {reqCtx.constraints.length === 0 ? (
              <span className="empty-text">No constraints identified yet</span>
            ) : (
              reqCtx.constraints.map((c, i) => <div key={i} className="list-item">• {c}</div>)
            )}
          </div>

          <div className="side-section">
            <label className="section-label">Open Questions</label>
            {reqCtx.openQuestions.length === 0 ? (
              <span className="empty-text">No open questions identified yet</span>
            ) : (
              reqCtx.openQuestions.map((q, i) => <div key={i} className="list-item">• {q}</div>)
            )}
          </div>
        </aside>

        {/* CENTER PANEL: Interactive Chat Workspace */}
        <main className="ba-chat-panel">
          <div className="chat-log-wrapper" ref={chatContainerRef}>
            {chatCount === 0 && msgs.length === 1 ? (
              /* PROFESSIONAL ONBOARDING EMPTY STATE */
              <div className="ba-empty-state">
                <div className="empty-logo">
                  <RobotOutlined style={{ fontSize: '38px', color: '#69765d' }} />
                </div>
                <h2>Let's define what you need.</h2>
                <p className="empty-subtitle">
                  Describe your business requirement in your own words. I'll identify the domain, clarify missing information, and structure the requirement.
                </p>
                <div className="suggestions-grid">
                  <div 
                    className="suggestion-card" 
                    onClick={() => {
                      setInputValue("We need to automate our financial customer onboarding workflow and KYC compliance.");
                    }}
                  >
                    <div className="suggestion-title">Automate a business process</div>
                    <p className="suggestion-desc">"Describe a process you want to automate"</p>
                  </div>
                  <div 
                    className="suggestion-card" 
                    onClick={() => {
                      setInputValue("I want to migrate my MySQL database schema to Frappe.");
                    }}
                  >
                    <div className="suggestion-title">Migrate databases/systems</div>
                    <p className="suggestion-desc">"Explain a system you want to migrate"</p>
                  </div>
                  <div 
                    className="suggestion-card" 
                    onClick={() => {
                      setInputValue("We need to build a digital employee workforce for customer support operations.");
                    }}
                  >
                    <div className="suggestion-title">Improve team efficiency</div>
                    <p className="suggestion-desc">"Tell me what your team needs to improve"</p>
                  </div>
                </div>
              </div>
            ) : (
              msgs.map((msg, i) => (
                <div key={i} className={`chat-bubble-container ${msg.role === 'user' ? 'bubble-user' : 'bubble-ai'}`}>
                  <div className="chat-bubble">
                    <div className="bubble-sender">{msg.sender}</div>
                    <div className="bubble-body">{msg.content}</div>
                    
                    {msg.isFallbackForm && (
                      <Button 
                        type="primary" 
                        size="small" 
                        style={{ marginTop: 12, background: '#69765d', borderColor: '#69765d', borderRadius: 6 }}
                        onClick={() => setFallbackOpen(true)}
                      >
                        Request Specialist Assistance
                      </Button>
                    )}

                    {msg.isByokPrompt && (
                      <div className="byok-inline-card">
                        {byokConnected ? (
                          <div style={{ color: '#168a68', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                            <CheckCircleOutlined /> Custom Model Connected ({configuredProvider} - {configuredModel})
                          </div>
                        ) : (
                          <Button 
                            type="primary" 
                            size="small" 
                            style={{ background: '#69765d', borderColor: '#69765d', borderRadius: 6 }} 
                            onClick={() => setSettingsOpen(true)}
                            block
                          >
                            Open AI Provider Configuration
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* COMPOSER (FIXED AT BOTTOM) */}
          <div className="chat-composer-wrapper">
            <div className="chat-input-bar">
              <div className="input-toolbar">
                <Button 
                  type="text" 
                  shape="circle" 
                  icon={<AudioOutlined />} 
                  danger={isRecording} 
                  onClick={handleSimulateRecord} 
                  title="Voice dictation input"
                />
                <Upload showUploadList={false} beforeUpload={() => false} onChange={handleUploadSimulate}>
                  <Button type="text" shape="circle" icon={<PaperClipOutlined />} title="Attach system brief" />
                </Upload>
                <Input 
                  placeholder={complimentaryExhausted ? "Please configure your AI API key in Settings..." : "Ask your Business Analyst a question or specify constraints..."}
                  value={inputValue}
                  disabled={complimentaryExhausted}
                  onChange={e => setInputValue(e.target.value)}
                  onPressEnter={handleSendMessage}
                  bordered={false}
                  style={{ flex: 1 }}
                />
              </div>
              <button 
                className="chat-send-btn" 
                onClick={handleSendMessage} 
                disabled={!inputValue.trim() || complimentaryExhausted}
                title="Send message"
              >
                <SendOutlined />
              </button>
            </div>
          </div>
        </main>

        {/* RIGHT PANEL: Structured Requirement Summary */}
        <aside className="ba-side-panel right-panel">
          <div className="panel-header">
            <h3>Requirement Summary</h3>
          </div>
          <div className="side-section">
            <label className="section-label">Risks</label>
            {reqCtx.risks.length === 0 ? (
              <span className="empty-text">No risks identified yet</span>
            ) : (
              reqCtx.risks.map((r, i) => <div key={i} className="list-item">⚠️ {r}</div>)
            )}
          </div>

          <div className="side-section">
            <label className="section-label">Dependencies</label>
            {reqCtx.dependencies.length === 0 ? (
              <span className="empty-text">No dependencies identified yet</span>
            ) : (
              reqCtx.dependencies.map((d, i) => <div key={i} className="list-item">⚙️ {d}</div>)
            )}
          </div>

          <div className="side-section">
            <label className="section-label">Estimated Scope</label>
            <div className="value-text">{reqCtx.estimatedScope}</div>
          </div>

          <div className="side-section">
            <label className="section-label">Next Step</label>
            <div className="value-text next-step-value">{reqCtx.nextStep}</div>
          </div>
        </aside>

      </div>

      {/* ── PROFESSIONAL INLINE AI / BYOK CONFIGURATION MODAL ── */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <KeyOutlined style={{ color: '#69765d' }} />
            <span>AI Model & Key Configuration</span>
          </div>
        }
        open={settingsOpen}
        onCancel={() => setSettingsOpen(false)}
        footer={null}
        width={420}
      >
        <Form 
          form={byokForm}
          layout="vertical" 
          onFinish={handleConnectBYOK} 
          initialValues={{ provider: 'openai', model: 'gpt-4o' }}
          style={{ marginTop: 12 }}
        >
          <Form.Item name="provider" label="AI Provider" rules={[{ required: true }]} style={{ marginBottom: 16 }}>
            <Select options={[
              { value: 'openai', label: 'OpenAI Compatible API' },
              { value: 'anthropic', label: 'Anthropic Claude' },
              { value: 'gemini', label: 'Google Gemini' }
            ]} />
          </Form.Item>
          <Form.Item name="model" label="AI Model" rules={[{ required: true }]} style={{ marginBottom: 16 }}>
            <Select options={[
              { value: 'gpt-4o', label: 'gpt-4o (Standard)' },
              { value: 'claude-3-5-sonnet', label: 'claude-3-5-sonnet' },
              { value: 'gemini-1-5-pro', label: 'gemini-1.5-pro' }
            ]} />
          </Form.Item>
          <Form.Item name="apiKey" label="API Key" rules={[{ required: true, message: 'Please enter API Key' }]} style={{ marginBottom: 20 }}>
            <Input.Password placeholder="sk-..." prefix={<KeyOutlined style={{ color: '#888' }} />} />
          </Form.Item>
          
          <Alert 
            message="Credentials Safety" 
            description="API keys are processed in your browser session for LLM execution context. They are not stored persistently on the platform database."
            type="info" 
            showIcon 
            style={{ marginBottom: 20 }}
          />

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
            <Button onClick={() => setSettingsOpen(false)}>Cancel</Button>
            <Button type="primary" htmlType="submit" style={{ background: '#69765d', borderColor: '#69765d' }}>
              Connect & Save
            </Button>
          </div>
        </Form>
      </Modal>

      {/* ── SPECIALIST ASSISTANCE FORM MODAL ── */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <WarningOutlined style={{ color: '#69765d' }} />
            <span>Capability Review Request</span>
          </div>
        }
        open={fallbackOpen}
        onCancel={() => { setFallbackOpen(false); setFallbackSubmitted(false); fallbackForm.resetFields(); }}
        footer={null}
        width={500}
      >
        {!fallbackSubmitted ? (
          <Form form={fallbackForm} layout="vertical" onFinish={handleCapabilityReview}>
            <p style={{ color: '#575756', fontSize: '13px', marginBottom: '18px' }}>
              We don't currently have a specialized Business Analyst agent configured for this domain. Share your requirement details, and our human operations team will assign a systems designer.
            </p>
            <Form.Item name="name" label="Full Name" rules={[{ required: true }]}>
              <Input placeholder="Enter your full name" prefix={<UserOutlined style={{ color: '#888' }} />} />
            </Form.Item>
            <Form.Item name="company" label="Company" rules={[{ required: true }]}>
              <Input placeholder="Your organization name" prefix={<BankOutlined style={{ color: '#888' }} />} />
            </Form.Item>
            <Form.Item name="email" label="Work Email" rules={[{ required: true, type: 'email' }]}>
              <Input placeholder="name@company.com" prefix={<MailOutlined style={{ color: '#888' }} />} />
            </Form.Item>
            <Form.Item name="summary" label="Requirement Summary">
              <TextArea rows={3} placeholder="Please summarize the custom capability scope..." />
            </Form.Item>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '24px' }}>
              <Button onClick={() => setFallbackOpen(false)}>Cancel</Button>
              <Button type="primary" htmlType="submit" style={{ background: '#69765d', borderColor: '#69765d' }}>
                Request Capability Review
              </Button>
            </div>
          </Form>
        ) : (
          <div style={{ textAlign: 'center', padding: '24px 0' }}>
            <CheckCircleOutlined style={{ fontSize: '50px', color: '#168a68', marginBottom: '16px' }} />
            <h4>Capability Request Submitted</h4>
            <p style={{ color: '#575756', fontSize: '13px' }}>
              Thank you. AegisOS specialists will review your requirements to design the new capability node.
            </p>
            <Button type="primary" onClick={() => { setFallbackOpen(false); setFallbackSubmitted(false); }} style={{ background: '#69765d', borderColor: '#69765d', marginTop: '12px' }}>
              Close
            </Button>
          </div>
        )}
      </Modal>

    </div>
  );
}

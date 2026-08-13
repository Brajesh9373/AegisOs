import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ApiClient } from '../../../api/client';
import './Landing.css';

export default function Landing() {
  const navigate = useNavigate();

  const handleStartDiscovery = async (e: React.MouseEvent) => {
    e.preventDefault();
    const token = localStorage.getItem('auth_token');
    if (token) {
      try {
        await ApiClient.get('/auth/me');
        navigate('/business-analyst');
        return;
      } catch (err) {
        localStorage.removeItem('auth_token');
      }
    }
    navigate('/signup');
  };

  // Mobile menu control
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Mount scroll reset, reveal, tilt, and scroll toggling effects from home.html
  useEffect(() => {
    if ('scrollRestoration' in history) {
      history.scrollRestoration = 'manual';
    }
    window.scrollTo(0, 0);
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;

    document.title = 'AegisOS \u2014 AI Workforce Operating System';
    const meta = document.querySelector('meta[name="description"]');
    if (meta) {
      meta.setAttribute('content', 'AegisOS turns business requirements into governed AI execution.');
    }

    // IntersectionObserver for scroll-reveal animations
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );

    const animatedElements = document.querySelectorAll(
      '.aegis-landing-page section, .aegis-landing-page .trust, .aegis-landing-page .cta, .aegis-landing-page .footer, .aegis-landing-page .steps'
    );
    animatedElements.forEach((el) => observer.observe(el));

    // Scroll header hide/show toggling
    let lastY = window.scrollY;
    const handleScroll = () => {
      const navEl = document.querySelector('.aegis-landing-page .nav');
      if (!navEl) return;
      const y = window.scrollY;
      if (y > lastY && y > 120) {
        navEl.classList.add('nav-hidden');
      } else {
        navEl.classList.remove('nav-hidden');
      }
      lastY = y;
    };
    window.addEventListener('scroll', handleScroll, { passive: true });

    // Pointermove tilt effects
    const tiltElements = document.querySelectorAll(
      '.aegis-landing-page .workflow, .aegis-landing-page .arch-diagram, .aegis-landing-page .workspace, .aegis-landing-page .employee'
    );

    const handlePointerMove = (e: Event) => {
      const el = e.currentTarget as HTMLElement;
      const rect = el.getBoundingClientRect();
      const pointerEvent = e as PointerEvent;
      const x = (pointerEvent.clientX - rect.left) / rect.width - 0.5;
      const y = (pointerEvent.clientY - rect.top) / rect.height - 0.5;
      el.style.transform = `perspective(900px) rotateX(${y * -2.2}deg) rotateY(${x * 2.2}deg) translateY(-3px)`;
    };

    const handlePointerLeave = (e: Event) => {
      const el = e.currentTarget as HTMLElement;
      el.style.transform = '';
    };

    tiltElements.forEach((el) => {
      el.addEventListener('pointermove', handlePointerMove);
      el.addEventListener('pointerleave', handlePointerLeave);
    });

    return () => {
      observer.disconnect();
      window.removeEventListener('scroll', handleScroll);
      tiltElements.forEach((el) => {
        el.removeEventListener('pointermove', handlePointerMove);
        el.removeEventListener('pointerleave', handlePointerLeave);
      });
    };
  }, []);

  const handleNavClick = (anchor: string) => {
    const el = document.querySelector(anchor);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
    setMobileMenuOpen(false);
  };

  return (
    <div className="aegis-landing-page">

      {/* 1. HEADER */}
      <nav className="nav">
        <div className="wrap nav-inner">
          <a className="brand" href="/landing" onClick={(e) => { e.preventDefault(); navigate('/landing'); window.scrollTo({ top: 0, behavior: 'smooth' }); }}>
            <span className="brand-mark"></span>AegisOS
          </a>
          <div className="nav-links">
            <a href="#platform" onClick={(e) => { e.preventDefault(); handleNavClick('#platform'); }}>Platform</a>
            <a href="/business-analyst" onClick={handleStartDiscovery}>Business Analyst</a>
            <a href="#ai-workforce" onClick={(e) => { e.preventDefault(); handleNavClick('#ai-workforce'); }}>AI Workforce</a>
            <a href="#how-it-works" onClick={(e) => { e.preventDefault(); handleNavClick('#how-it-works'); }}>How It Works</a>
            <a href="#enterprise" onClick={(e) => { e.preventDefault(); handleNavClick('#enterprise'); }}>Enterprise</a>
          </div>
          <div className="nav-actions">
            <a className="signin" href="/login" onClick={(e) => { e.preventDefault(); navigate('/login'); }}>Sign In</a>
            <a className="btn primary" href="/business-analyst" onClick={handleStartDiscovery}>Start with Business Analyst</a>
          </div>
          <button className="mobile-toggle" aria-label="Open menu" onClick={() => setMobileMenuOpen(true)}>☰</button>
        </div>
      </nav>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="mobile-menu-overlay open" onClick={() => setMobileMenuOpen(false)}>
          <div className="mobile-menu" onClick={(e) => e.stopPropagation()}>
            <button
              className="mobile-close"
              onClick={() => setMobileMenuOpen(false)}
              aria-label="Close menu"
            >
              ✕
            </button>
            <div className="mobile-menu-content">
              <a href="#platform" onClick={(e) => { e.preventDefault(); handleNavClick('#platform'); }} className="mobile-link">Platform</a>
              <a href="/business-analyst" onClick={handleStartDiscovery} className="mobile-link">Business Analyst</a>
              <a href="#ai-workforce" onClick={(e) => { e.preventDefault(); handleNavClick('#ai-workforce'); }} className="mobile-link">AI Workforce</a>
              <a href="#how-it-works" onClick={(e) => { e.preventDefault(); handleNavClick('#how-it-works'); }} className="mobile-link">How It Works</a>
              <a href="#enterprise" onClick={(e) => { e.preventDefault(); handleNavClick('#enterprise'); }} className="mobile-link">Enterprise</a>
              <hr style={{ margin: '16px 0', border: 'none', borderTop: '1px solid var(--line)' }} />
              <a href="/login" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); navigate('/login'); }} className="mobile-link">Sign In</a>
              <button className="btn primary" style={{ width: '100%', marginTop: '8px' }} onClick={(e) => { setMobileMenuOpen(false); handleStartDiscovery(e); }}>
                Start with Business Analyst
              </button>
            </div>
          </div>
        </div>
      )}

      <main id="top">

        {/* 2. HERO */}
        <section className="hero">
          <div className="wrap hero-grid">
            <div>
              <div className="eyebrow">AI Workforce Operating System</div>
              <h1>Turn business requirements into governed AI execution.</h1>
              <p className="hero-copy">AegisOS connects business understanding, enterprise context, and a governed digital workforce into one continuous execution system.</p>
              <div className="hero-actions">
                <a className="btn primary" href="/business-analyst" onClick={handleStartDiscovery}>Start with Business Analyst ↗</a>
                <a className="btn ghost" href="#platform" onClick={(e) => { e.preventDefault(); handleNavClick('#platform'); }}>Explore AegisOS</a>
              </div>
              <div className="micro">
                <span className="pulse"></span>Operational layer for enterprise work
              </div>
            </div>

            {/* Hero Visual Flowchart */}
            <div className="workflow">
              <div className="system-orbit" aria-hidden="true">
                <span className="orbit-ring ring-1"></span>
                <span className="orbit-ring ring-2"></span>
                <span className="orbit-ring ring-3"></span>
                <span className="orbit-core">AEGIS<br /><small>OS</small></span>
                <i className="orbit-node node-a">MEMORY</i>
                <i className="orbit-node node-b">POLICY</i>
                <i className="orbit-node node-c">TOOLS</i>
                <i className="orbit-node node-d">MODELS</i>
              </div>
              <div className="system-rail"><span>LIVE SYSTEM MAP</span><b>01</b><b>02</b><b>03</b><b>04</b><b>05</b></div>
              <div className="flow-title">
                <strong>Requirement → outcome</strong>
                <span className="status">● SYSTEM READY</span>
              </div>
              <div className="flow-stack">
                <div className="flow-node">
                  <span className="node-dot"></span>
                  <div><b>Business Requirement</b><small>Customer onboarding automation</small></div>
                </div>
                <div className="flow-node">
                  <span className="node-dot"></span>
                  <div><b>AI Business Analyst</b><small>Clarifying objectives, constraints & systems</small></div>
                </div>
                <div className="flow-node">
                  <span className="node-dot"></span>
                  <div><b>Requirements & Understanding</b><small>Acceptance criteria synthesized</small></div>
                </div>
                <div className="flow-node">
                  <span className="node-dot"></span>
                  <div><b>AI Workforce</b><small>Configured digital employees</small></div>
                </div>
                <div className="flow-node">
                  <span className="node-dot"></span>
                  <div><b>Governed Execution</b><small>Policy check · approval · audit</small></div>
                </div>
                <div className="flow-node">
                  <span className="node-dot"></span>
                  <div><b>Business Outcome</b><small>Traceable work, measurable result</small></div>
                </div>
              </div>
              <div className="telemetry">
                <span>Context <b>14 sources</b></span>
                <span>Policy <b>v2.4</b></span>
                <span>Latency <b>280ms</b></span>
              </div>
            </div>
          </div>
        </section>

        {/* 3. TRUST */}
        <section className="trust">
          <div className="wrap trust-row">
            <div className="trust-intro">Built for work that cannot live in a chat window.</div>
            <div className="trust-item"><b>Memory</b>Persistent organizational memory</div>
            <div className="trust-item"><b>Control</b>Governed AI execution</div>
            <div className="trust-item"><b>Context</b>Enterprise context</div>
            <div className="trust-item"><b>Review</b>Human approvals</div>
            <div className="trust-item"><b>Proof</b>Traceable outcomes</div>
          </div>
        </section>

        {/* 4. SECTION 01 / PLATFORM */}
        <section className="section architecture" id="platform">
          <div className="wrap arch-grid">
            <div className="arch-copy">
              <div className="eyebrow">01 / Platform</div>
              <div className="section-head">
                <h2>One system from requirement to execution.</h2>
                <p>AegisOS is an operating layer for coordinated AI work. It connects understanding, context, workforce, governance, systems and outcomes without losing the thread.</p>
              </div>
              <div className="pill-list">
                <span className="pill">Knowledge</span>
                <span className="pill">Memory</span>
                <span className="pill">Policies</span>
                <span className="pill">Approvals</span>
                <span className="pill">Connectors</span>
                <span className="pill">Models</span>
                <span className="pill">Audit</span>
              </div>
            </div>
            <div className="arch-diagram">
              <div className="arch-main">
                <div className="arch-step">Business Requirements</div>
                <div className="arch-arrow">↓</div>
                <div className="arch-step">Business Analyst</div>
                <div className="arch-arrow">↓</div>
                <div className="arch-step">Context & Knowledge</div>
                <div className="arch-arrow">↓</div>
                <div className="arch-step">AI Workforce</div>
                <div className="arch-arrow">↓</div>
                <div className="arch-step">Governance → Enterprise Systems → Execution → Outcome</div>
              </div>
              <div className="arch-side">
                <b>Operating memory</b>Decisions, documents and project knowledge persist beyond a single interaction.
              </div>
              <div className="arch-side">
                <b>Control plane</b>Permissions, approvals and auditability remain part of the workflow.
              </div>
            </div>
          </div>
        </section>

        {/* 5. SECTION 02 / BUSINESS ANALYST (INFORMATIONAL ONLY) */}
        <section className="section" id="business-analyst">
          <div className="wrap">
            <div className="section-head">
              <div className="eyebrow">02 / Business Analyst</div>
              <h2>Start with the requirement. Not the technology.</h2>
              <p>The AI Business Analyst helps people articulate the work before asking them to configure the system. Write, speak or bring the source document.</p>
            </div>
            <div className="split">
              {/* Static Chat Panel Mockup */}
              <div className="panel chat">
                <div className="kicker">Business Analyst session · New discovery</div>
                <div className="chat-msg chat-user">We need to automate customer onboarding across sales, compliance and operations.</div>
                <div className="chat-msg chat-ai">
                  <b>I understand the objective.</b>
                  <ul>
                    <li>Clarify the target customer journey</li>
                    <li>Identify stakeholders and systems</li>
                    <li>Surface constraints, risks and dependencies</li>
                    <li>Define measurable acceptance criteria</li>
                  </ul>
                </div>
                <div className="inputbar">
                  Write a requirement, speak, or upload a document… <span style={{ float: 'right', color: '#245eea' }}>＋</span>
                </div>
              </div>

              {/* Static details side mockup */}
              <div className="panel">
                <h3>Business understanding</h3>
                <p className="muted" style={{ fontSize: '13px' }}>A structured brief emerges from the conversation, ready for review and execution planning.</p>
                <div className="understanding">
                  <div className="data-cell"><b>Requirements</b>Automate intake, validation and handoff</div>
                  <div className="data-cell"><b>Constraints</b>Data boundaries and approval checkpoints</div>
                  <div className="data-cell"><b>Risks</b>Incomplete customer records</div>
                  <div className="data-cell"><b>Dependencies</b>CRM, compliance and operations</div>
                  <div className="data-cell"><b>Open questions</b>Escalation path and service levels</div>
                  <div className="data-cell"><b>Acceptance criteria</b>Traceable onboarding status</div>
                </div>
                <div className="pill-list">
                  <span className="pill">Write</span>
                  <span className="pill">Speak</span>
                  <span className="pill">PDF</span>
                  <span className="pill">DOC/DOCX</span>
                  <span className="pill">Audio</span>
                </div>
                <a className="btn primary" href="/business-analyst" onClick={handleStartDiscovery} style={{ marginTop: '22px' }}>
                  Start with Business Analyst ↗
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* 6. SECTION 03 / SPECIALIZED BUSINESS ANALYSTS */}
        <section className="section">
          <div className="wrap">
            <div className="section-head">
              <div className="eyebrow">03 / Specialized Business Analysts</div>
              <h2>The right Business Analyst for the problem.</h2>
              <p>AegisOS starts with a General Business Analyst. Based on the requirement, it can route discovery toward specialized capabilities.</p>
            </div>
            <div className="route">
              <div className="route-box">General BA</div>
              <div className="route-arrow">→</div>
              <div className="route-box">Requirement Classification</div>
              <div className="route-arrow">→</div>
              <div className="route-box">Specialized BA</div>
              <div className="route-arrow">→</div>
              <div className="route-box">Deeper Discovery</div>
            </div>
            <div className="specialists">
              <span>Finance</span>
              <span>Healthcare</span>
              <span>Manufacturing</span>
              <span>Retail</span>
              <span>Technology</span>
              <span>Operations</span>
              <span>Security</span>
              <span>Compliance</span>
            </div>
            <div className="request">
              <b>Enterprise capability request</b><br />
              <span className="muted">Your requirement requires a specialized capability that is not currently available in AegisOS.</span>{' '}
              <a href="/business-analyst" onClick={(e) => { e.preventDefault(); navigate('/business-analyst'); }} style={{ color: 'var(--blue)', fontWeight: 700 }}>Contact the team →</a>
            </div>
          </div>
        </section>

        {/* 7. SECTION 04 / CONTEXT + ORGANIZATIONAL MEMORY */}
        <section className="section" style={{ background: '#fbfdff' }}>
          <div className="wrap">
            <div className="section-head">
              <div className="eyebrow">04 / Context + Organizational Memory</div>
              <h2>AI that remembers the work.</h2>
              <p>Requirements, documents, decisions, discussions, approvals and project knowledge should not disappear after a chat session.</p>
            </div>
            <div className="memory">
              <div className="memory-column">
                <div className="memory-item">Documents</div>
                <div className="memory-item">Conversations</div>
                <div className="memory-item">Decisions</div>
              </div>
              <div className="memory-core">
                <strong>Organizational<br />Knowledge & Memory</strong>
                <small>Context for today · learning for tomorrow</small>
              </div>
              <div className="memory-column">
                <div className="memory-item">Projects</div>
                <div className="memory-item">Systems</div>
                <div className="memory-item">Approvals</div>
              </div>
            </div>
            <div className="split" style={{ marginTop: '55px' }}>
              <div>
                <div className="eyebrow">Context</div>
                <p className="muted">What the AI needs for this task: relevant documents, system state, policies, roles and current decisions.</p>
              </div>
              <div>
                <div className="eyebrow">Memory</div>
                <p className="muted">What the organization has learned over time: patterns, outcomes, precedent and institutional knowledge.</p>
              </div>
            </div>
          </div>
        </section>

        {/* 8. SECTION 05 / AI WORKFORCE */}
        <section className="section" id="ai-workforce">
          <div className="wrap">
            <div className="section-head">
              <div className="eyebrow">05 / AI Workforce</div>
              <h2>From one AI assistant to an entire digital workforce.</h2>
              <p>Organize AI work like an enterprise: from general intelligence to departments, teams and accountable digital employees.</p>
            </div>
            <div className="hierarchy">
              <span className="level">AegisOS</span>
              <i>→</i>
              <span className="level">General AI</span>
              <i>→</i>
              <span className="level">Departments</span>
              <i>→</i>
              <span className="level" style={{ background: '#eff5ff', color: '#245eea' }}>Digital Employees</span>
            </div>
            <div className="dept-grid">
              <div className="dept">Engineering</div>
              <div className="dept">Product</div>
              <div className="dept">Finance</div>
              <div className="dept">Operations</div>
              <div className="dept">Sales</div>
              <div className="dept">Support</div>
              <div className="dept">Security</div>
            </div>
            <div className="employee">
              <div className="employee-profile">
                <div className="avatar">CO</div>
                <h3>Customer Operations Lead</h3>
                <small>Digital employee · Active</small>
                <p className="muted" style={{ fontSize: '12px' }}>Coordinates onboarding tasks across systems, escalating exceptions to the right human owner.</p>
              </div>
              <div className="employee-grid">
                <div className="spec"><b>Mission</b>Reduce onboarding friction</div>
                <div className="spec"><b>Skills</b>Case triage, routing</div>
                <div className="spec"><b>Tools</b>CRM, ticketing</div>
                <div className="spec"><b>Model</b>Approved model set</div>
                <div className="spec"><b>Policies</b>Customer data boundary</div>
                <div className="spec"><b>Manager</b>Operations team</div>
                <div className="spec"><b>Status</b><span style={{ color: '#168a68' }}>● On duty</span></div>
              </div>
            </div>
          </div>
        </section>

        {/* 9. SECTION 06 / DIGITAL EMPLOYEE CAPABILITIES */}
        <section className="section">
          <div className="wrap">
            <div className="section-head">
              <div className="eyebrow">06 / Digital Employee Capabilities</div>
              <h2>Digital employees built for real work.</h2>
            </div>
            <div className="bento">
              <div className="bento-card wide">
                <div className="mini-visual">
                  <i style={{ height: '10px' }}></i>
                  <i style={{ height: '16px' }}></i>
                  <i style={{ height: '22px' }}></i>
                  <i style={{ height: '14px' }}></i>
                </div>
                <h3>Mission & Objectives</h3>
                <p>Every worker has a clear purpose, outcomes and operating boundaries.</p>
              </div>
              <div className="bento-card">
                <div className="kicker">↗</div>
                <h3>Skills</h3>
                <p>Capabilities matched to the work.</p>
              </div>
              <div className="bento-card">
                <div className="kicker">⌘</div>
                <h3>Tools & Connectors</h3>
                <p>Permissioned access to enterprise systems.</p>
              </div>
              <div className="bento-card">
                <div className="kicker">◌</div>
                <h3>Knowledge</h3>
                <p>Relevant organizational context.</p>
              </div>
              <div className="bento-card">
                <div className="kicker">◉</div>
                <h3>Memory</h3>
                <p>Learning that persists across work.</p>
              </div>
              <div className="bento-card wide">
                <div className="mini-visual">
                  <i style={{ height: '22px' }}></i>
                  <i style={{ height: '12px' }}></i>
                  <i style={{ height: '18px' }}></i>
                  <i style={{ height: '8px' }}></i>
                  <i style={{ height: '20px' }}></i>
                </div>
                <h3>Governance, scheduling & notifications</h3>
                <p>Operate with policies, dependencies, triggers and human escalation.</p>
              </div>
              <div className="bento-card">
                <div className="kicker">▣</div>
                <h3>Outputs & Artifacts</h3>
                <p>Useful work products, not just responses.</p>
              </div>
              <div className="bento-card">
                <div className="kicker">⌁</div>
                <h3>Analytics</h3>
                <p>Understand throughput, quality and cost.</p>
              </div>
            </div>
          </div>
        </section>

        {/* 10. SECTION 07 / GOVERNED EXECUTION */}
        <section className="section" style={{ background: '#f8fbff' }}>
          <div className="wrap">
            <div className="section-head">
              <div className="eyebrow">07 / Governed Execution</div>
              <h2>AI execution with controls built in.</h2>
              <p>Enterprise-controlled AI means the policy check, approval and audit trail are part of the workflow—not an afterthought.</p>
            </div>
            <div className="governance">
              <div className="control-flow">
                <div className="control-step">Task</div>
                <div className="control-step">Context</div>
                <div className="control-step accent">AI Worker</div>
                <div className="control-step">Policy Check</div>
                <div className="control-step accent">Approval</div>
                <div className="control-step">Enterprise Tool</div>
                <div className="control-step accent">Execution</div>
                <div className="control-step">Audit</div>
              </div>
              <div className="controls">
                <div className="control-card"><b>Permissions</b>Role-based access for every action.</div>
                <div className="control-card"><b>Approval rules</b>Escalate sensitive decisions.</div>
                <div className="control-card"><b>Security policies</b>Keep data within defined boundaries.</div>
                <div className="control-card"><b>Human oversight</b>Intervene, approve or redirect.</div>
                <div className="control-card"><b>Audit trail</b>Trace what happened and why.</div>
                <div className="control-card"><b>Version history</b>Reproduce the operating state.</div>
              </div>
            </div>
          </div>
        </section>

        {/* 11. SECTION 08 / ENTERPRISE INTEGRATIONS */}
        <section className="section" id="enterprise">
          <div className="wrap">
            <div className="section-head">
              <div className="eyebrow">08 / Enterprise Integrations</div>
              <h2>Connect AI to the systems your organization already uses.</h2>
              <p>Use integration categories as the starting point for a governed enterprise connection model. Specific availability depends on configuration.</p>
            </div>
            <div className="integrations">
              <div>
                <div className="integration-grid">
                  <div className="integration"><b>CRM</b>Customer systems</div>
                  <div className="integration"><b>ERP</b>Resource planning</div>
                  <div className="integration"><b>PM</b>Project management</div>
                  <div className="integration"><b>◫</b>Communication</div>
                  <div className="integration"><b>⌘</b>Code repositories</div>
                  <div className="integration"><b>▤</b>Documents</div>
                  <div className="integration"><b>◈</b>Databases</div>
                  <div className="integration"><b>☁</b>Cloud infrastructure</div>
                  <div className="integration"><b>↗</b>APIs</div>
                </div>
              </div>
              <div className="panel">
                <h3>Integration control surface</h3>
                <p className="muted" style={{ fontSize: '13px' }}>Connectors are governed by capability, policy and auditability.</p>
                <div className="permissions">
                  <span>READ</span>
                  <span>WRITE</span>
                  <span>EXECUTE</span>
                  <span>AUDIT</span>
                </div>
                <div className="request" style={{ marginTop: '24px' }}>
                  References may include systems such as Slack, Jira, GitHub, CRM, ERP or SAP. Production readiness is configured and verified per organization.
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 12. SECTION 09 / HOW IT WORKS */}
        <section className="section" id="how-it-works">
          <div className="wrap">
            <div className="section-head">
              <div className="eyebrow">09 / How It Works</div>
              <h2>From idea to execution in one continuous workflow.</h2>
            </div>
            <div className="steps">
              <div className="step">
                <div className="step-num">01</div>
                <h3>Describe the requirement</h3>
                <p>Bring the business problem in your own words.</p>
              </div>
              <div className="step">
                <div className="step-num">02</div>
                <h3>Understand and clarify</h3>
                <p>The Business Analyst surfaces the shape of the work.</p>
              </div>
              <div className="step">
                <div className="step-num">03</div>
                <h3>Build the plan</h3>
                <p>AegisOS structures requirements and execution paths.</p>
              </div>
              <div className="step">
                <div className="step-num">04</div>
                <h3>Configure the workforce</h3>
                <p>Assign digital employees, tools and policies.</p>
              </div>
              <div className="step">
                <div className="step-num">05</div>
                <h3>Begin governed execution</h3>
                <p>AI acts with review, control and traceability.</p>
              </div>
            </div>
          </div>
        </section>

        {/* 13. SECTION 10 / PRODUCT EXPERIENCE */}
        <section className="section">
          <div className="wrap">
            <div className="section-head">
              <div className="eyebrow">10 / Product Experience</div>
              <h2>A workspace for the work behind the work.</h2>
              <p>Move from requirements to coordinated execution without losing the business context.</p>
            </div>
            <div className="workspace">
              <div className="workspace-top">
                <span><b>AegisOS</b> / Customer onboarding</span>
                <span style={{ color: '#168a68' }}>● Workspace synced</span>
              </div>
              <div className="workspace-body">
                <aside className="workspace-side">
                  <strong>Customer</strong>
                  <span className="active">Business Understanding</span>
                  <span>Requirements</span>
                  <span>Digital Workforce</span>
                  <span>Timeline</span>
                  <span>Documents</span>
                  <span>Knowledge</span>
                  <span>Memory</span>
                  <span>Execution</span>
                  <span>Analytics</span>
                  <span>Sustainability</span>
                </aside>
                <div className="workspace-main">
                  <div className="crumb">Project / Customer / Opportunity</div>
                  <h3>Business Understanding</h3>
                  <div className="workspace-cells">
                    <div className="workspace-cell">
                      <strong>Execution readiness</strong>
                      <div className="bar"><i style={{ width: '82%' }}></i></div>
                      <span className="muted">82% structured</span>
                      <div className="bar"><i style={{ width: '64%' }}></i></div>
                      <span className="muted">64% approved</span>
                    </div>
                    <div className="workspace-cell">
                      <strong>Active workforce</strong>
                      <p>Customer Operations Lead</p>
                      <p>Compliance Reviewer</p>
                      <p>Data Quality Worker</p>
                    </div>
                    <div className="workspace-cell">
                      <strong>Next checkpoint</strong>
                      <p>Review exception policy</p>
                      <p className="muted">Owner · Operations</p>
                      <p className="muted">Due · Today</p>
                    </div>
                  </div>
                  <div className="workspace-cell" style={{ marginTop: '10px' }}>
                    <strong>Requirement trace</strong>
                    <span className="muted">Customer intake → validation → risk review → system handoff → status notification</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 14. SECTION 11 / AI + HUMAN COLLABORATION */}
        <section className="section" style={{ background: '#fbfdff' }}>
          <div className="wrap">
            <div className="section-head">
              <div className="eyebrow">11 / AI + Human Collaboration</div>
              <h2>AI executes. Humans stay in control.</h2>
            </div>
            <div className="collab">
              <div className="collab-flow">
                <div className="collab-step">AI discovers</div>
                <div className="collab-step">AI analyzes</div>
                <div className="collab-step">AI recommends</div>
                <div className="collab-step">Human reviews</div>
                <div className="collab-step">Human approves</div>
                <div className="collab-step">AI executes</div>
                <div className="collab-step">System audits</div>
              </div>
              <div className="collab-list">
                <div>
                  <b>Human approval</b><br />
                  <span className="muted">Require explicit sign-off where the organization decides.</span>
                </div>
                <div>
                  <b>Decision history</b><br />
                  <span className="muted">Keep the reasoning and operating context connected.</span>
                </div>
                <div>
                  <b>Intervention & exception handling</b><br />
                  <span className="muted">Pause, redirect or escalate when the work changes.</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 15. SECTION 12 / SUSTAINABILITY + AI TELEMETRY */}
        <section className="section">
          <div className="wrap">
            <div className="section-head">
              <div className="eyebrow">12 / Sustainability + AI Telemetry</div>
              <h2>Know what every AI workflow costs.</h2>
              <p>Operational telemetry gives teams visibility into usage and resource measurements. Metrics shown are interface examples, not claims about production performance.</p>
            </div>
            <div className="telemetry-ui">
              <div className="metric-grid">
                <div className="metric">
                  <label>Tokens</label>
                  <strong>1.28M</strong>
                  <em>+8.4% this week</em>
                </div>
                <div className="metric">
                  <label>AI cost</label>
                  <strong>$42.18</strong>
                  <em>per workflow set</em>
                </div>
                <div className="metric">
                  <label>CO₂</label>
                  <strong>0.84 kg</strong>
                  <em>operational estimate</em>
                </div>
                <div className="metric">
                  <label>Energy</label>
                  <strong>6.2 kWh</strong>
                  <em>operational estimate</em>
                </div>
                <div className="metric">
                  <label>Water</label>
                  <strong>0.9 L</strong>
                  <em>operational estimate</em>
                </div>
                <div className="metric">
                  <label>Trees / equivalent</label>
                  <strong>0.03</strong>
                  <em>reference metric</em>
                </div>
              </div>
              <div className="meter">
                <div className="kicker">Workflow efficiency index</div>
                <div className="meter-ring"></div>
                <p className="muted" style={{ textAlign: 'center', fontSize: '12px' }}>Track usage, cost and resource signals alongside business outcomes.</p>
              </div>
            </div>
          </div>
        </section>

        {/* 16. SECTION 13 / SECURITY + GOVERNANCE */}
        <section className="section" style={{ background: '#f8fbff' }}>
          <div className="wrap">
            <div className="section-head">
              <div className="eyebrow">13 / Security + Governance</div>
              <h2>Enterprise AI needs more than intelligence.</h2>
              <p>Design the control plane around identity, access, policy, data boundaries and a clear record of action.</p>
            </div>
            <div className="security">
              <div className="security-grid">
                <div className="security-item">Identity</div>
                <div className="security-item">Access Control</div>
                <div className="security-item">RBAC</div>
                <div className="security-item">Policies</div>
                <div className="security-item">Secrets</div>
                <div className="security-item">Audit Logs</div>
                <div className="security-item">Approvals</div>
                <div className="security-item">Model Governance</div>
                <div className="security-item">Data Boundaries</div>
              </div>
              <div className="panel">
                <div className="kicker">Governance architecture</div>
                <div className="arch-main" style={{ marginTop: '20px' }}>
                  <div className="arch-step">Identity & roles</div>
                  <div className="arch-arrow">↓</div>
                  <div className="arch-step">Policy evaluation</div>
                  <div className="arch-arrow">↓</div>
                  <div className="arch-step">Approved model + data boundary</div>
                  <div className="arch-arrow">↓</div>
                  <div className="arch-step">Human decision point</div>
                  <div className="arch-arrow">↓</div>
                  <div className="arch-step">Audited enterprise action</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 17. SECTION 14 / WHO AEGISOS IS FOR */}
        <section className="section">
          <div className="wrap">
            <div className="section-head">
              <div className="eyebrow">14 / Who AegisOS Is For</div>
              <h2>Build an operating model for AI across the organization.</h2>
            </div>
            <div className="audience">
              <article>
                <div className="eyebrow">Business leaders</div>
                <h3>Make the work executable.</h3>
                <p>Turn business goals into executable work.</p>
              </article>
              <article>
                <div className="eyebrow">Technology leaders</div>
                <h3>Connect without losing control.</h3>
                <p>Connect AI to enterprise systems with governance.</p>
              </article>
              <article>
                <div className="eyebrow">Engineering / Operations</div>
                <h3>Operate the digital workforce.</h3>
                <p>Deploy and operate a coordinated digital workforce.</p>
              </article>
            </div>
          </div>
        </section>

        {/* 18. SECTION 15 / WHY AEGISOS */}
        <section className="section" style={{ background: '#fbfdff' }}>
          <div className="wrap">
            <div className="section-head">
              <div className="eyebrow">15 / Why AegisOS</div>
              <h2>Beyond AI assistants.</h2>
              <p>AegisOS expands the unit of work from a single answer to a governed, connected operating system.</p>
            </div>
            <div className="comparison">
              <div className="compare-row head">
                <div>Capability</div>
                <div>Traditional AI assistant</div>
                <div>AegisOS</div>
              </div>
              <div className="compare-row">
                <div>Requirement understanding</div>
                <div>Prompt-led</div>
                <div>Business Analyst-led</div>
              </div>
              <div className="compare-row">
                <div>Persistent memory</div>
                <div>Conversation-bound</div>
                <div>Organizational</div>
              </div>
              <div className="compare-row">
                <div>Enterprise context</div>
                <div>Added manually</div>
                <div>Connected context</div>
              </div>
              <div className="compare-row">
                <div>Digital workforce</div>
                <div>Single assistant</div>
                <div>Coordinated employees</div>
              </div>
              <div className="compare-row">
                <div>Governance</div>
                <div>Separate controls</div>
                <div>Built into execution</div>
              </div>
              <div className="compare-row">
                <div>Human approvals</div>
                <div>Optional</div>
                <div>Policy-driven</div>
              </div>
              <div className="compare-row">
                <div>Enterprise integrations</div>
                <div>Tool calls</div>
                <div>Permissioned connectors</div>
              </div>
              <div className="compare-row">
                <div>Execution & auditability</div>
                <div>Response output</div>
                <div>Traceable action</div>
              </div>
            </div>
          </div>
        </section>

        {/* 19. FINAL CTA */}
        <section className="cta" id="final-cta">
          <div className="wrap">
            <div className="eyebrow">Start with the requirement</div>
            <h2>Bring the business problem. Find what should happen next.</h2>
            <p>AegisOS will help you understand it, structure it and determine the next governed step.</p>
            <div className="hero-actions" style={{ justifyContent: 'center', marginBottom: 0 }}>
              <a className="btn primary" href="/business-analyst" onClick={handleStartDiscovery}>Start with Business Analyst ↗</a>
              <a className="btn ghost" href="/login" onClick={(e) => { e.preventDefault(); navigate('/login'); }}>Talk to AegisOS</a>
            </div>
          </div>
        </section>

      </main>

      {/* 20. FOOTER */}
      <footer className="footer" id="footer">
        <div className="wrap">
          <div className="footer-grid">
            <div className="footer-brand">
              <a className="brand" href="/landing" onClick={(e) => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); }}>
                <span className="brand-mark"></span>AegisOS
              </a>
              <p>AI Workforce Operating System. From business requirements to governed AI execution.</p>
            </div>
            
            <div>
              <h4>Product</h4>
              <a href="#platform" onClick={(e) => { e.preventDefault(); handleNavClick('#platform'); }}>Platform</a>
              <a href="/business-analyst" onClick={handleStartDiscovery}>Business Analyst</a>
              <a href="#ai-workforce" onClick={(e) => { e.preventDefault(); handleNavClick('#ai-workforce'); }}>AI Workforce</a>
              <a href="#how-it-works" onClick={(e) => { e.preventDefault(); handleNavClick('#how-it-works'); }}>How It Works</a>
              <a href="#enterprise" onClick={(e) => { e.preventDefault(); handleNavClick('#enterprise'); }}>Enterprise</a>
            </div>
            <div>
              <h4>Resources</h4>
              <a href="#platform" onClick={(e) => { e.preventDefault(); handleNavClick('#platform'); }}>Documentation</a>
              <a href="#platform" onClick={(e) => { e.preventDefault(); handleNavClick('#platform'); }}>Architecture</a>
              <a href="#enterprise" onClick={(e) => { e.preventDefault(); handleNavClick('#enterprise'); }}>Security</a>
              <a href="#" onClick={(e) => e.preventDefault()}>Blog</a>
            </div>
            <div>
              <h4>Company</h4>
              <a href="#" onClick={(e) => e.preventDefault()}>About</a>
              <a href="#" onClick={(e) => e.preventDefault()}>Contact</a>
              <a href="#" onClick={(e) => e.preventDefault()}>Careers</a>
            </div>
            <div>
              <h4>Legal</h4>
              <a href="#" onClick={(e) => e.preventDefault()}>Privacy</a>
              <a href="#" onClick={(e) => e.preventDefault()}>Terms</a>
              <a href="#" onClick={(e) => e.preventDefault()}>Security Policy</a>
            </div>
          </div>

          <div className="footer-bottom">
            <span>AegisOS · AI Workforce Operating System</span>
            <span>© AegisOS · Designed for governed enterprise work</span>
          </div>
        </div>
      </footer>

    </div>
  );
}

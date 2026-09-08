import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import { AgentFactory } from '@aegisos/agent';
import { createProvider, UserRepository, ProjectRepository, OrganizationRepository, SessionRepository, AuditRepository } from '@aegisos/database';
import { ExecutionEngine, ExecutionState, StepExecutor } from '@aegisos/execution-runtime';
import { GeminiProvider, OpenAIProvider } from '@aegisos/provider-openai';
import { eventBus } from '@aegisos/shared';
import { WorkflowFactory, WorkflowGraph, WorkflowNodeType } from '@aegisos/workflow';
import { registerEcmsRoutes } from './routes/ecms.js';

const app = express();
app.use(cors());
app.use(express.json());

const db = createProvider();
const userRepo = new UserRepository(db);
const projectRepo = new ProjectRepository(db);
const orgRepo = new OrganizationRepository(db);
const sessionRepo = new SessionRepository(db);
const auditRepo = new AuditRepository(db);

// Subscribe to global events
eventBus.subscribe('*', async (event: any) => {
  if (event.type !== 'HUMAN_QUEUE_ACTION' && event.type !== 'USER_LOGGED_IN' && event.type !== 'WORKSPACE_CHAT_MESSAGE') {
    await auditRepo.log(event.type, 'system', `Event Triggered: ${event.type}`);
  }
});

eventBus.subscribe('WORKSPACE_CHAT_MESSAGE', (event: any) => {
  console.log(`[Timeline] New chat message for project ${event.payload.projectId}: ${event.payload.message}`);
});

eventBus.subscribe('HUMAN_QUEUE_ACTION', (event: any) => {
  console.log(`[Human Queue] Action ${event.payload.action} taken on task ${event.payload.id}`);
});

const asyncHandler =
  (fn: (...args: any[]) => any) => (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };

// Define requireAuth middleware early so it can be used by logout and others
const requireAuth = asyncHandler(async (req: Request, res: Response, next: NextFunction) => {
  const authHeader = req.headers.authorization;
  if (!authHeader) throw new ApiError(401, 'AUTH-4011', 'Missing token');
  const token = authHeader.split(' ')[1];
  const session = await sessionRepo.getByToken(token);

  if (!session || parseInt(session.expiresAt as string) < Date.now()) {
    if (session) await sessionRepo.deleteByToken(token);
    throw new ApiError(401, 'AUTH-4012', 'Invalid session');
  }

  (req as any).user = { id: session.userId };
  next();
});

// ECMS-owned surfaces (discovery, live hierarchy, workspace): explicit routes
// registered ahead of the legacy mocks below so Express matches them first.
registerEcmsRoutes(app, requireAuth, asyncHandler);

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Custom Error Class
import { ApiError } from './errors.js';
export { ApiError };



app.post(
  '/api/install',
  asyncHandler(async (req: Request, res: Response) => {
    const org = await orgRepo.get();
    if (org && org.setupComplete) {
      throw new ApiError(
        403,
        'INSTALL-4031',
        'Installation locked',
        'The platform has already been installed.',
      );
    }

    const { orgName, adminEmail, adminPassword, aiProvider, aiApiKey, aiModel } = req.body;
    if (!orgName || !adminEmail || !adminPassword || !aiProvider || !aiModel) {
      throw new ApiError(
        400,
        'VAL-4001',
        'Validation Error',
        'Missing required fields for installation.',
      );
    }
    if (['openai', 'gemini', 'anthropic'].includes(aiProvider) && !aiApiKey) {
      throw new ApiError(400, 'VAL-4002', 'Validation Error', 'API Key is required for this provider.');
    }

    const domain = orgName.toLowerCase().replace(/\s+/g, '') + '.com';
    const license = 'Demo';

    await orgRepo.clear();
    await orgRepo.create({
      id: 'org-1',
      name: orgName,
      domain,
      licenseKey: license,
      aiProvider,
      aiApiKey,
      aiModel,
      storage: 'local',
      database: 'sqlite'
    });

    await userRepo.create({
      email: adminEmail,
      passwordHash: adminPassword,
      role: 'Super Admin',
      department: 'General',
    });

    await seedDatabase(db);

    await auditRepo.log('Installation Completed', 'system', 'Platform initialized');

    eventBus.publish('INSTALLATION_COMPLETED', { orgName, aiProvider });

    res.json({ success: true });
  }),
);

app.post(
  '/api/auth/login',
  asyncHandler(async (req: Request, res: Response) => {
    const { email, password } = req.body;
    if (!email || !password) throw new ApiError(400, 'VAL-4002', 'Email and password required');

    const user = await userRepo.getByEmail(email);
    if (!user || user.passwordHash !== password || !user.active) {
      throw new ApiError(401, 'AUTH-4011', 'Invalid credentials');
    }

    const token = 'sess_' + Date.now();
    await sessionRepo.create(Date.now().toString(), user.id as string, token, (Date.now() + 86400000).toString());

    await auditRepo.log('User Login', user.id as string, 'Successful login');
    eventBus.publish('USER_LOGGED_IN', { userId: user.id });

    res.json({ token, user: { id: user.id, email: user.email, role: user.role } });
  }),
);

app.get(
  '/api/auth/me',
  asyncHandler(async (req: Request, res: Response) => {
    const authHeader = req.headers.authorization;
    if (!authHeader) throw new ApiError(401, 'AUTH-4012', 'Missing token');

    const token = authHeader.split(' ')[1];
    const session = await sessionRepo.getByToken(token);

    if (!session || parseInt(session.expiresAt as string) < Date.now()) {
      if (session) await sessionRepo.deleteByToken(token);
      throw new ApiError(401, 'AUTH-4013', 'Invalid or expired session');
    }

    const user = await userRepo.getById(session.userId as string);
    res.json({ user: { id: user.id, email: user.email, role: user.role } });
  }),
);

app.post(
  '/api/auth/logout',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    const token = req.headers.authorization?.split(' ')[1];
    if (token) {
      await sessionRepo.deleteByToken(token);
    }
    eventBus.publish('USER_LOGGED_OUT', { userId: (req as any).user?.id });
    res.json({ success: true });
  }),
);

app.get(
  '/api/users',
  asyncHandler(async (req: Request, res: Response) => {
    const users = await userRepo.getAll();
    res.json(users.map((u) => ({ id: u.id, email: u.email, role: u.role, active: u.active })));
  }),
);

app.post(
  '/api/users',
  asyncHandler(async (req: Request, res: Response) => {
    const { email, password, role, department } = req.body;
    const user = await userRepo.create({
      email,
      passwordHash: password || 'password123',
      role: role || 'Viewer',
      department: department || 'General',
      active: 1
    });
    res.json({ success: true, user });
  })
);

app.put(
  '/api/users/:id/active',
  asyncHandler(async (req: Request, res: Response) => {
    await userRepo.update(req.params.id, { active: req.body.active ? 1 : 0 });
    res.json({ success: true });
  }),
);

app.post(
  '/api/rbac/evaluate',
  asyncHandler(async (req: Request, res: Response) => {
    const { role, resource } = req.body;
    const hierarchy = ['Viewer', 'Analyst', 'Developer', 'Manager', 'Org Admin', 'Super Admin'];
    let required = 'Viewer';
    if (resource === 'users') required = 'Org Admin';
    if (resource === 'installation') required = 'Super Admin';

    const hasAccess = hierarchy.indexOf(role) >= hierarchy.indexOf(required);
    res.json({ allowed: hasAccess });
  }),
);

app.get(
  '/api/installation/status',
  asyncHandler(async (req: Request, res: Response) => {
    const org = await orgRepo.get();
    res.json({ locked: org ? org.setupComplete === 1 : false });
  }),
);

app.post(
  '/api/install/test/:service',
  asyncHandler(async (req: Request, res: Response) => {
    res.json({ success: true });
  }),
);

app.get(
  '/api/install/health',
  asyncHandler(async (req: Request, res: Response) => {
    res.json({ status: 'healthy', db: true, storage: true, ai: true });
  }),
);

// --- Project Routes ---

app.post(
  '/api/projects',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    const { name, businessGoal } = req.body;
    if (!name || !businessGoal)
      throw new ApiError(400, 'VAL-4001', 'Name and Business Goal are required');
    const project = await projectRepo.create(req.body, (req as any).user.id);
    res.json(project);
  }),
);

app.get(
  '/api/projects',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    const projects = await projectRepo.getAll();
    res.json(projects);
  }),
);

app.get(
  '/api/projects/:id',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    const project = await projectRepo.getById(req.params.id);
    if (!project) throw new ApiError(404, 'NOT-FOUND', 'Project not found');
    res.json(project);
  }),
);

app.put(
  '/api/projects/:id',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    await projectRepo.update(req.params.id, req.body, (req as any).user.id);
    res.json({ success: true });
  }),
);

app.delete(
  '/api/projects/:id',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    await projectRepo.delete(req.params.id, (req as any).user.id);
    res.json({ success: true });
  }),
);

app.post(
  '/api/projects/:id/analyze',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    const project = await projectRepo.getById(req.params.id);
    if (!project) throw new ApiError(404, 'NOT-FOUND', 'Project not found');

    const goal = (project.businessGoal as string).toLowerCase();

    // Simulated AI Reasoning Engine response based on the business goal.
    // In production, this proxies to the selected AI Provider (e.g., GPT-4o, Claude 3.5).
    let domain = 'Operations';
    let complexity = 'Low';
    let skills = ['Process Mapping'];
    let knowledge = ['Internal Policies'];
    let connectors = ['Internal Database'];
    let risks = ['Scope creep', 'Unclear metrics'];
    let missing = ['Success criteria', 'Timeline'];
    let questions = ['What is the expected ROI?', 'Who are the key stakeholders?'];

    if (goal.includes('migrate') || goal.includes('mysql') || goal.includes('frappe')) {
      domain = 'Migration & Integration';
      complexity = 'Medium';
      skills = ['Schema Analysis', 'Data Mapping', 'Validation', 'Migration Strategy'];
      knowledge = ['MySQL', 'Frappe Documentation', 'Migration Policies'];
      connectors = ['MySQL', 'GitHub', 'Frappe'];
      risks = ['Data loss during transfer', 'Downtime exceeding window', 'Schema mismatch'];
      missing = ['Downtime allowed', 'Data volume metrics'];
      questions = ['What Frappe version?', 'How many records?', 'Are there any custom fields?'];
    } else if (goal.includes('invoice') || goal.includes('automate')) {
      domain = 'Financial Automation';
      complexity = 'High';
      skills = ['OCR Processing', 'Data Extraction', 'Approval Workflow Routing'];
      knowledge = ['Accounting Principles', 'Vendor Contracts'];
      connectors = ['ERP System', 'Email Inbox', 'Cloud Storage'];
      risks = ['OCR inaccuracies', 'Compliance violations', 'Fraud detection failure'];
      missing = ['Sample invoices', 'Approval hierarchy matrix'];
      questions = ['What formats do invoices arrive in?', 'Is PO matching required?'];
    }

    const analysis = {
      businessDomain: domain,
      businessType: 'Transformation',
      estimatedComplexity: complexity,
      requiredSkills: skills,
      requiredKnowledge: knowledge,
      requiredConnectors: connectors,
      potentialRisks: risks,
      missingInformation: missing,
      questionsForUser: questions,
    };

    // Audit event
    await auditRepo.log('Business Goal Analyzed', (req as any).user.id, `Analyzed goal for project: ${project.id}`);

    res.json({ success: true, analysis });
  }),
);

app.post(
  '/api/projects/:id/recommend',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    const project = await projectRepo.getById(req.params.id);
    if (!project) throw new ApiError(404, 'NOT-FOUND', 'Project not found');

    const orgs = await db.query<Record<string, any>>('SELECT * FROM organization');
    const org = orgs[0];

    if (!org || !org.aiProvider || org.aiProvider === 'none') {
      throw new ApiError(
        400,
        'AI-001',
        'AI Provider Not Configured',
        'Configure an AI Provider to generate recommendations.',
      );
    }

      let aiResponseText = '';
    try {
      let apiKey = process.env.AI_API_KEY || org.aiApiKey || 'dummy_key_to_trigger_real_network_request';

      // Support OpenAI, Gemini, Ollama, Azure OpenAI (mapped to their standard endpoints)
      let baseUrl = 'https://api.openai.com/v1/chat/completions';
      let headers: Record<string, string> = {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`,
      };

      if (org.aiProvider === 'gemini') {
        baseUrl = `https://generativelanguage.googleapis.com/v1beta/models/${org.aiModel || 'gemini-pro'}:generateContent?key=${apiKey}`;
        headers = { 'Content-Type': 'application/json' };
      } else if (org.aiProvider === 'ollama') {
        baseUrl = 'http://localhost:11434/api/generate';
      }

      const systemPrompt = `Analyze the business goal: ${project.businessGoal}.
You must strictly return a valid JSON object matching this schema exactly:
{
  "recommendedEmployees": [{"name": "string", "role": "string", "purpose": "string", "reason": "string", "confidence": "number"}],
  "recommendedSkills": [{"name": "string", "reason": "string"}],
  "recommendedKnowledge": [{"name": "string", "reason": "string"}],
  "recommendedMemory": [{"name": "string", "type": "Working|Session|Semantic|Long-term", "reason": "string"}],
  "recommendedConnectors": [{"name": "string", "reason": "string"}],
  "recommendedWorkflow": [{"stage": "string", "description": "string"}],
  "assumptions": ["string"],
  "questions": ["string"],
  "risks": ["string"]
}
Do NOT return anything except the JSON object. No markdown formatting.`;

      const body = JSON.stringify({
        model: 'gpt-4o',
        messages: [{ role: 'user', content: systemPrompt }],
      });

      const aiReq = await fetch(baseUrl, { method: 'POST', headers, body });

      if (!aiReq.ok) {
        const errBody = await aiReq.text();
        throw new ApiError(
          502,
          'AI-502',
          'AI Provider Error',
          `Provider Error: ${aiReq.statusText}`,
        );
      }

      const aiData = await aiReq.json();
      aiResponseText =
        aiData.choices?.[0]?.message?.content || aiData.response || JSON.stringify(aiData);
    } catch (error: any) {
      if (error instanceof ApiError) throw error;
      throw new ApiError(500, 'AI-500', 'AI Connection Failed', error.message);
    }

    // Parse and strictly validate JSON Schema
    let parsedRecommendations: any = {};
    try {
      const rawStr = aiResponseText
        .replace(/```json/g, '')
        .replace(/```/g, '')
        .trim();
      parsedRecommendations = JSON.parse(rawStr);
    } catch {
      throw new ApiError(
        500,
        'AI-501',
        'AI Provider Error',
        'AI failed to return valid structured JSON',
      );
    }

    // Ensure default arrays exist for all keys
    const schema = {
      recommendedEmployees: parsedRecommendations.recommendedEmployees || [],
      recommendedSkills: parsedRecommendations.recommendedSkills || [],
      recommendedKnowledge: parsedRecommendations.recommendedKnowledge || [],
      recommendedMemory: parsedRecommendations.recommendedMemory || [],
      recommendedConnectors: parsedRecommendations.recommendedConnectors || [],
      recommendedWorkflow: parsedRecommendations.recommendedWorkflow || [],
      assumptions: parsedRecommendations.assumptions || [],
      questions: parsedRecommendations.questions || [],
      risks: parsedRecommendations.risks || [],
    };

    await auditRepo.log('Recommendation Generated', (req as any).user.id, `Generated structured recommendations for project: ${project.id}`);

    res.json({ success: true, payload: schema });
  }),
);

app.post(
  '/api/projects/:id/recommendations/audit',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    const { action, detail } = req.body;
    await auditRepo.log(action, (req as any).user.id, detail);
    res.json({ success: true });
  }),
);

app.get(
  '/api/queue',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    const queue = await db.query<any>('SELECT * FROM human_queue WHERE status = ?', ['Pending']);
    res.json(queue.map((q: any) => ({
      id: q.id,
      priority: 'High',
      reason: q.reason,
      confidence: 50,
      assigned: q.assignedTo,
      status: q.status,
      project: q.projectId
    })));
  })
);

app.post(
  '/api/queue/:id/action',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    const { id } = req.params;
    const { action, comment } = req.body;

    let resolution = comment || action;
    const status = action === 'approve' ? 'Approved' : action === 'reject' ? 'Rejected' : 'Pending';

    if (action === 'approve' || action === 'reject') {
      await db.execute('UPDATE human_queue SET status = ?, resolution = ? WHERE id = ?', [status, resolution, id]);

      const item = await db.query<any>('SELECT * FROM human_queue WHERE id = ?', [id]);
      if (item[0] && item[0].agentId) {
         // Update the blocked execution node if agent exists
         await db.execute("UPDATE execution_nodes SET state = 'Completed', reasoning = ? WHERE agentId = ? AND state = 'Blocked'", [
           `Human intervened: ${action}. ${resolution}`,
           item[0].agentId
         ]);
         await db.execute("UPDATE project_agents SET status = 'Running' WHERE id = ?", [item[0].agentId]);

         if (action === 'approve') {
            await db.execute(
              'INSERT INTO artifacts (id, projectId, type, storagePath, versionHistory) VALUES (?, ?, ?, ?, ?)',
              ['art-mapping-' + Date.now(), item[0].projectId, 'SQL Script', 'data/artifacts/Schema_Mapping_Validation.sql', '{}']
            );
         }
      }
    }

    eventBus.publish('HUMAN_QUEUE_ACTION', { id, action, comment, user: (req as any).user?.id });
    res.json({ success: true });
  })
);

app.get(
  '/api/projects/:id/workspace',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    const projectId = req.params.id;

    let targetId = projectId === 'demo' ? (await db.query<any>('SELECT id FROM business_projects LIMIT 1'))[0]?.id : projectId;

    if (!targetId) return res.json({ error: 'No project found' });

    let project = (await db.query<any>('SELECT * FROM business_projects WHERE id = ?', [targetId]))[0];
    let finalId = targetId;
    if (!project) {
      project = (await db.query<any>('SELECT * FROM business_projects LIMIT 1'))[0];
      if (!project) return res.json({ error: 'No project found' });
      finalId = project.id;
    }

    const agents = await db.query<any>('SELECT * FROM project_agents WHERE projectId = ?', [finalId]);
    const artifacts = await db.query<any>('SELECT * FROM artifacts WHERE projectId = ?', [finalId]);
    const executionNodes = await db.query<any>('SELECT * FROM execution_nodes WHERE projectId = ?', [finalId]);

    // Build simulated "events" based on execution nodes for the UI timeline
    const events = executionNodes.map((node: any, idx: number) => ({
      delay: 0,
      agent: agents.find((a: any) => a.id === node.agentId)?.name || 'General AI',
      type: node.state === 'Blocked' ? 'human' : 'info',
      phase: 'Execution',
      title: `Node ${node.state}`,
      desc: node.reasoning,
      conf: 95,
      dur: '0.1s'
    }));

    res.json({
      goal: project.businessGoal,
      workers: agents.map((a: any) => {
        let parsedConfig = {
          manager: 'General AI',
          humanOwner: 'Admin User',
          skills: [],
          knowledge: [],
          memory: [],
          connectors: [],
          discussion: []
        };
        try {
          if (a.config) {
            parsedConfig = { ...parsedConfig, ...JSON.parse(a.config) };
          }
        } catch (e) {}
        return {
          id: a.id,
          name: a.name,
          status: a.status,
          purpose: a.systemPrompt,
          config: parsedConfig
        };
      }),
      artifacts: artifacts.map((a: any) => a.storagePath),
      registries: {
        skills: ['Data Mapping', 'SQL Query Generation', 'OCR Text Extraction', 'Anomaly Detection', 'Compliance Verification'],
        knowledge: ['State Tax Regulation Manual v4', 'Company Invoice Standard Operating Procedure', 'Frappe ERPNext Schema Documentation', 'GDPR Data Compliance Rules'],
        memory: ['Semantic Vector Storage', 'Working Memory Cache', 'Semantic Long-term Log'],
        connectors: ['Postgres ERP Connector', 'Local SQLite Database', 'Hubspot CRM Webhook', 'Slack Alert Gateway']
      },
      logs: executionNodes.map((n: any) => `[SYS] Node transitioned to ${n.state}`),
      events: events.length > 0 ? events : [
        { delay: 0, agent: 'General AI', type: 'info', phase: 'Planning', title: 'Goal Analysis & Project Plan Created', desc: 'Project initialized based on business goal.', conf: 99, dur: '0s' }
      ]
    });
  })
);

app.put(
  '/api/projects/:projectId/workers/:workerId',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    const { config, purpose } = req.body;
    await db.execute(
      'UPDATE project_agents SET config = ?, systemPrompt = ? WHERE id = ?',
      [JSON.stringify(config), purpose, req.params.workerId]
    );
    res.json({ success: true });
  })
);

app.post(
  '/api/projects/:projectId/workers',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    const { name, purpose, status, config } = req.body;
    const workerId = Math.random().toString();
    await db.execute(
      'INSERT INTO project_agents (id, projectId, name, status, config, systemPrompt) VALUES (?, ?, ?, ?, ?, ?)',
      [workerId, req.params.projectId, name, status || 'Running', JSON.stringify(config || {}), purpose || '']
    );
    res.json({ success: true, workerId });
  })
);

app.delete(
  '/api/projects/:projectId/workers/:workerId',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    await db.execute('DELETE FROM project_agents WHERE id = ?', [req.params.workerId]);
    res.json({ success: true });
  })
);

app.post(
  '/api/projects/:projectId/workers/:workerId/status',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    const { status } = req.body;
    await db.execute('UPDATE project_agents SET status = ? WHERE id = ?', [status, req.params.workerId]);
    res.json({ success: true });
  })
);

app.post(
  '/api/projects/:id/workspace/chat',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    const { message } = req.body;
    const projectId = req.params.id;
    let targetId = projectId === 'demo' ? (await db.query<any>('SELECT id FROM business_projects LIMIT 1'))[0]?.id : projectId;

    if (!targetId) return res.json({ error: 'No project found' });

    let project = (await db.query<any>('SELECT * FROM business_projects WHERE id = ?', [targetId]))[0];
    if (!project) {
      project = (await db.query<any>('SELECT * FROM business_projects LIMIT 1'))[0];
      if (!project) return res.json({ error: 'No project found' });
    }

    // Structured sections for UI rendering
    const understanding = `Initiating migration protocol for target enterprise objective: "${message}".`;
    const reasoning = `Frappe ERPNext requires strict database schema alignment and validation mappings from MySQL tables to prevent downstream serialization failures.`;
    const decision = `Provisioning validation employee and mapping node targets. Launching safety sandbox.`;
    const planUpdate = `Workflow graph expanded. Phase 1: Schema Mapping initialized. Phase 2: Interoperability Token Verification queued.`;
    const workerActions = `Provisioned agent "Validation Orchestrator" (ID: val-node-1) with prompt target definitions.`;
    const requiredApprovals = `aegisOS Policy requires explicit Human-in-the-loop authorization to bind integration keys. Queue item registered.`;
    const expectedOutcome = `Successful migration of core tables with zero record loss and verified API interoperability.`;

    const reply = `[Chief of Staff Analysis]
• Understanding: ${understanding}
• Reasoning: ${reasoning}
• Decision: ${decision}
• Plan Update: ${planUpdate}
• Worker Actions: ${workerActions}
• Required Approvals: ${requiredApprovals}
• Expected Outcome: ${expectedOutcome}`;

    // Clear old nodes & create new execution graph in SQLite
    await db.execute('DELETE FROM execution_nodes WHERE projectId = ?', [targetId]);
    await db.execute('DELETE FROM project_agents WHERE projectId = ?', [targetId]);
    await db.execute('DELETE FROM artifacts WHERE projectId = ?', [targetId]);
    await db.execute('DELETE FROM human_queue WHERE projectId = ?', [targetId]);

    // Insert structured execution graph nodes
    const node1Id = 'node-plan-' + Date.now();
    await db.execute(
      'INSERT INTO execution_nodes (id, projectId, agentId, state, dependencies, outputs, reasoning) VALUES (?, ?, ?, ?, ?, ?, ?)',
      [node1Id, targetId, 'val-node-1', 'Completed', '[]', '["Migration Blueprint"]', 'Planning and analysis phase complete. Strategy locked.']
    );

    const node2Id = 'node-run-' + Date.now();
    await db.execute(
      'INSERT INTO execution_nodes (id, projectId, agentId, state, dependencies, outputs, reasoning) VALUES (?, ?, ?, ?, ?, ?, ?)',
      [node2Id, targetId, 'val-node-1', 'Running', `["${node1Id}"]`, '["Data Validation Report"]', 'Active schema validation running. Analyzing columns.']
    );

    const node3Id = 'node-block-' + Date.now();
    await db.execute(
      'INSERT INTO execution_nodes (id, projectId, agentId, state, dependencies, outputs, reasoning) VALUES (?, ?, ?, ?, ?, ?, ?)',
      [node3Id, targetId, 'val-node-1', 'Blocked', `["${node2Id}"]`, '[]', 'Intervention required: Authorize connection token to access live environment.']
    );

    // Create workers
    await db.execute(
      'INSERT INTO project_agents (id, projectId, name, status, config, systemPrompt) VALUES (?, ?, ?, ?, ?, ?)',
      ['val-node-1', targetId, 'Validation Orchestrator', 'Running', JSON.stringify({
        manager: 'General AI',
        humanOwner: 'Admin User',
        skills: ['Data Mapping', 'SQL Query Generation'],
        knowledge: ['Frappe ERPNext Schema Documentation'],
        memory: ['Working Memory Cache'],
        connectors: ['Local SQLite Database'],
        discussion: []
      }), 'Performs schema validation and checks API contract alignments.']
    );

    // Create artifacts
    await db.execute(
      'INSERT INTO artifacts (id, projectId, type, storagePath, versionHistory) VALUES (?, ?, ?, ?, ?)',
      ['art-blueprint-' + Date.now(), targetId, 'Blueprint', 'data/artifacts/Migration_Blueprint.pdf', '{}']
    );
    await db.execute(
      'INSERT INTO artifacts (id, projectId, type, storagePath, versionHistory) VALUES (?, ?, ?, ?, ?)',
      ['art-validation-' + Date.now(), targetId, 'Report', 'data/artifacts/Validation_Report.json', '{}']
    );

    // Create Approval
    await db.execute(
      'INSERT INTO human_queue (id, projectId, agentId, reason, status, resolution, assignedTo) VALUES (?, ?, ?, ?, ?, ?, ?)',
      ['q-auth-' + Date.now(), targetId, 'val-node-1', `${project.name || 'ERP Migration'} Core Connection Authorization`, 'Pending', null, (req as any).user?.id || 'admin']
    );

    await db.execute(
      "UPDATE business_projects SET status = 'Execution', updatedAt = ? WHERE id = ?",
      [new Date().toISOString(), targetId]
    );

    res.json({
      success: true,
      reply,
      understanding,
      reasoning,
      decision,
      planUpdate,
      workerActions,
      requiredApprovals,
      expectedOutcome,
      newEvent: { delay: 0, agent: 'General AI', type: 'info', phase: 'Execution', title: 'Plan Deployed', desc: reply, conf: 99, dur: '0.1s' },
      newProgress: 45,
      newPhase: 'Execution'
    });
  })
);

app.get(
  '/api/operations/summary',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    const projects = await db.query<any>('SELECT * FROM business_projects ORDER BY updatedAt DESC LIMIT 5');
    const runningProjectsCount = (await db.query<any>("SELECT count(1) as c FROM business_projects WHERE status = 'Execution'"))[0]?.c || 0;
    const activeEmployeesCount = (await db.query<any>("SELECT count(1) as c FROM users WHERE active = 1"))[0]?.c || 0;
    const pendingApprovalsCount = (await db.query<any>("SELECT count(1) as c FROM human_queue WHERE status = 'Pending'"))[0]?.c || 0;

    const activities = await db.query<any>('SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 5');
    const artifacts = await db.query<any>('SELECT * FROM artifacts ORDER BY id DESC LIMIT 5');

    const summary = {
      health: { status: 'Optimal', cpu: '12%', ram: '2.1GB' },
      stats: { runningProjects: runningProjectsCount, activeEmployees: activeEmployeesCount, pendingApprovals: pendingApprovalsCount },
      projects: projects.map(p => ({
        key: p.id,
        project: p.name,
        status: p.status,
        phase: p.status,
        ai: 'General AI',
        updated: p.updatedAt
      })),
      providers: [
        { name: 'OpenAI GPT-4o', type: 'LLM Gateway', status: 'Healthy' },
        { name: 'Local SQLite', type: 'Platform DB', status: 'Healthy' }
      ],
      sources: [
        { name: 'Core DB', type: 'Internal Data', status: 'Connected' }
      ],
      activities: activities.map(a => ({
        text: a.action + (a.details ? ': ' + a.details : ''),
        time: a.timestamp
      })),
      artifacts: artifacts.map(a => ({
        name: a.storagePath,
        type: a.type
      }))
    };

    res.json(summary);
  })
);

// Global Error Handler
app.use((err: any, req: Request, res: Response, next: NextFunction) => {
  console.error(err);

  const traceId = 'req-' + Date.now();
  let statusCode = 500;
  let code = 'SYS-5000';
  let message = 'An unexpected internal error occurred.';
  let details = err.message || String(err);

  if (err instanceof ApiError) {
    statusCode = err.statusCode;
    code = err.code;
    message = err.message;
    details = err.details;
  } else if (err.message && err.message.includes('NOT NULL constraint')) {
    statusCode = 400;
    code = 'DB-4001';
    message = 'Database constraint violation';
  } else if (err.message && err.message.includes('UNIQUE constraint')) {
    statusCode = 409;
    code = 'DB-4091';
    message = 'Resource already exists';
  }

  res.status(statusCode).json({
    success: false,
    error: {
      code,
      message,
      details,
      traceId,
    },
  });
});

import { seedDatabase } from './seeder.js';

async function start() {
  await db.connect();
  await seedDatabase(db);
  app.listen(3001, () => {
    console.log('API running on http://localhost:3001');
  });
}

start().catch(console.error);

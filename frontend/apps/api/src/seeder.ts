import crypto from 'crypto';
const uuidv4 = () => crypto.randomUUID();

export async function seedDatabase(db: any) {
  const users = (await db.query('SELECT * FROM users')) as any[];
  if (users.length === 0) return; // Wait for install

  const projects = (await db.query('SELECT * FROM business_projects')) as any[];
  if (projects.length > 0) return; // Already seeded

  const adminId = users[0].id;
  const orgId = 'org-1';

  // Seed Departments
  const devDeptId = uuidv4();
  await db.execute('INSERT INTO departments (id, name, ownerId) VALUES (?, ?, ?)', [devDeptId, 'Engineering', adminId]);
  
  const finDeptId = uuidv4();
  await db.execute('INSERT INTO departments (id, name, ownerId) VALUES (?, ?, ?)', [finDeptId, 'Finance', adminId]);

  // Seed Projects (Goals)
  const proj1 = uuidv4();
  await db.execute(
    'INSERT INTO business_projects (id, name, description, businessGoal, ownerId, department, status, priority, tags, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
    [proj1, 'ERP Data Migration', 'Migrate legacy MySQL to Frappe ERPNext', 'Migrate MySQL to Frappe ERPNext', adminId, devDeptId, 'Execution', 'High', JSON.stringify(['Migration', 'Data']), new Date().toISOString(), new Date().toISOString()]
  );

  const proj2 = uuidv4();
  await db.execute(
    'INSERT INTO business_projects (id, name, description, businessGoal, ownerId, department, status, priority, tags, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
    [proj2, 'Invoice Automation', 'Automate vendor invoice processing', 'Automate invoice OCR and approval routing', adminId, finDeptId, 'Planning', 'Medium', JSON.stringify(['Finance', 'AI']), new Date().toISOString(), new Date().toISOString()]
  );

  // Seed Agents (Workers)
  const agent1 = uuidv4();
  await db.execute(
    'INSERT INTO project_agents (id, projectId, name, status, config, systemPrompt) VALUES (?, ?, ?, ?, ?, ?)',
    [agent1, proj1, 'Master Orchestrator', 'Running', '{}', 'You are the chief agent...']
  );

  const agent2 = uuidv4();
  await db.execute(
    'INSERT INTO project_agents (id, projectId, name, status, config, systemPrompt) VALUES (?, ?, ?, ?, ?, ?)',
    [agent2, proj1, 'Schema Discovery Agent', 'Archived', '{}', 'Analyze schemas...']
  );

  const agent3 = uuidv4();
  await db.execute(
    'INSERT INTO project_agents (id, projectId, name, status, config, systemPrompt) VALUES (?, ?, ?, ?, ?, ?)',
    [agent3, proj1, 'Data Mapping Agent', 'Blocked', '{}', 'Map data...']
  );

  // Seed Human Queue
  await db.execute(
    'INSERT INTO human_queue (id, projectId, agentId, reason, status, resolution, assignedTo) VALUES (?, ?, ?, ?, ?, ?, ?)',
    [uuidv4(), proj1, agent3, 'Tax Mapping Rule - Requires Human Approval', 'Pending', null, adminId]
  );
  
  await db.execute(
    'INSERT INTO human_queue (id, projectId, agentId, reason, status, resolution, assignedTo) VALUES (?, ?, ?, ?, ?, ?, ?)',
    [uuidv4(), proj2, null, 'Budget Approval for Invoice OCR API', 'Pending', null, adminId]
  );

  // Seed Artifacts
  await db.execute(
    'INSERT INTO artifacts (id, projectId, type, storagePath, versionHistory) VALUES (?, ?, ?, ?, ?)',
    [uuidv4(), proj1, 'Architecture Document', '/docs/migration_plan.md', '[]']
  );
  
  await db.execute(
    'INSERT INTO artifacts (id, projectId, type, storagePath, versionHistory) VALUES (?, ?, ?, ?, ?)',
    [uuidv4(), proj1, 'Data Mapping JSON', '/data/mapping_rules.json', '[]']
  );

  // Seed Execution Nodes (Execution Graph)
  await db.execute(
    'INSERT INTO execution_nodes (id, projectId, agentId, state, dependencies, outputs, reasoning) VALUES (?, ?, ?, ?, ?, ?, ?)',
    [uuidv4(), proj1, agent2, 'Completed', '[]', '["schema.json"]', 'Discovered 45 legacy tables.']
  );
  await db.execute(
    'INSERT INTO execution_nodes (id, projectId, agentId, state, dependencies, outputs, reasoning) VALUES (?, ?, ?, ?, ?, ?, ?)',
    [uuidv4(), proj1, agent3, 'Blocked', '["Schema Discovery"]', '[]', 'Awaiting human input on legacy_taxes table.']
  );

  console.log('Database seeded with realistic organization data.');
}

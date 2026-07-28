import { SQLiteProvider, UserRepository } from '../packages/database/src';

async function seed() {
  console.log('Starting Enterprise Database Seed...');
  const db = new SQLiteProvider();
  await db.connect();

  const userRepo = new UserRepository(db);

  // 1. Organization
  await db.execute('DELETE FROM organization');
  await db.execute(
    'INSERT INTO organization (id, name, domain, setupComplete, licenseKey) VALUES (?, ?, ?, ?, ?)',
    ['org-1', 'aegisOS Enterprise', 'aegisos.com', 1, 'SEED-LICENSE-123'],
  );
  console.log('Seeded Organization.');

  // 2. Department & Roles (Simplified in Users for now)
  // 3. Super Admin
  const adminExists = await userRepo.getByEmail('admin@aegisos.com');
  if (!adminExists) {
    await userRepo.create({
      email: 'admin@aegisos.com',
      passwordHash: 'admin123', // In production, this is hashed
      role: 'Super Admin',
      department: 'System Administration',
    });
    console.log('Seeded default Super Admin.');
  }

  // 4. Permissions (Initial setup for RBAC audit)
  await db.execute(
    'CREATE TABLE IF NOT EXISTS permissions (id TEXT PRIMARY KEY, role TEXT, resource TEXT, action TEXT)',
  );
  await db.execute('DELETE FROM permissions');
  await db.execute('INSERT INTO permissions (id, role, resource, action) VALUES (?, ?, ?, ?)', [
    'p1',
    'Super Admin',
    '*',
    '*',
  ]);
  console.log('Seeded Permissions.');

  await db.execute(`CREATE TABLE IF NOT EXISTS digital_employees (
    id TEXT PRIMARY KEY,
    name TEXT,
    role TEXT,
    purpose TEXT,
    description TEXT,
    manager TEXT,
    humanOwner TEXT,
    department TEXT,
    projectId TEXT,
    skills TEXT,
    knowledge TEXT,
    memory TEXT,
    status TEXT,
    createdAt TEXT
  )`);
  await db.execute(`CREATE TABLE IF NOT EXISTS skills_registry (
    id TEXT PRIMARY KEY,
    name TEXT,
    description TEXT,
    category TEXT,
    version TEXT,
    owner TEXT,
    status TEXT,
    dependencies TEXT,
    inputSchema TEXT,
    outputSchema TEXT,
    configuration TEXT,
    tags TEXT,
    isBuiltIn INTEGER,
    createdAt TEXT
  )`);

  // Seed a default skill
  await db.execute('DELETE FROM skills_registry');
  await db.execute(
    `INSERT INTO skills_registry (id, name, description, category, version, owner, status, dependencies, inputSchema, outputSchema, configuration, tags, isBuiltIn, createdAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      'skill-base-1',
      'Data Extraction',
      'Extracts structured data from unstructured text.',
      'Built-in',
      '1.0.0',
      'System',
      'Active',
      '[]',
      '{"type": "string"}',
      '{"type": "object"}',
      '{}',
      '["extraction", "nlp"]',
      1,
      new Date().toISOString(),
    ],
  );
  console.log('Seeded Skills Registry.');
  await db.execute(`CREATE TABLE IF NOT EXISTS knowledge_registry (
    id TEXT PRIMARY KEY,
    title TEXT,
    description TEXT,
    type TEXT,
    source TEXT,
    version TEXT,
    owner TEXT,
    status TEXT,
    tags TEXT,
    metadata TEXT,
    isBuiltIn INTEGER,
    createdAt TEXT
  )`);

  // Seed a default knowledge item
  await db.execute('DELETE FROM knowledge_registry');
  await db.execute(
    `INSERT INTO knowledge_registry (id, title, description, type, source, version, owner, status, tags, metadata, isBuiltIn, createdAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      'knowledge-base-1',
      'aegisOS Blueprint v3.2',
      'The architectural standard for all digital employee operations.',
      'Documentation',
      'Internal System',
      '1.0.0',
      'System',
      'Active',
      '["architecture", "blueprint"]',
      '{}',
      1,
      new Date().toISOString(),
    ],
  );
  console.log('Seeded Knowledge Registry.');
  await db.execute(`CREATE TABLE IF NOT EXISTS graph_nodes (
    id TEXT PRIMARY KEY,
    type TEXT,
    label TEXT,
    data TEXT,
    createdAt TEXT
  )`);

  await db.execute(`CREATE TABLE IF NOT EXISTS graph_edges (
    id TEXT PRIMARY KEY,
    source TEXT,
    target TEXT,
    relationship TEXT,
    properties TEXT,
    createdAt TEXT
  )`);

  // Seed basic graph structure
  await db.execute('DELETE FROM graph_nodes');
  await db.execute('DELETE FROM graph_edges');

  const rootId = 'node-project-1';
  await db.execute(
    `INSERT INTO graph_nodes (id, type, label, data, createdAt) VALUES (?, ?, ?, ?, ?)`,
    [rootId, 'Project', 'Automate Invoicing', '{}', new Date().toISOString()],
  );
  console.log('Seeded Knowledge Graph.');
  await db.execute(`CREATE TABLE IF NOT EXISTS connectors_execution (
    id TEXT PRIMARY KEY,
    name TEXT,
    type TEXT,
    category TEXT,
    status TEXT,
    config TEXT,
    schemaData TEXT,
    createdAt TEXT
  )`);

  await db.execute('DELETE FROM connectors_execution');
  await db.execute(
    `INSERT INTO connectors_execution (id, name, type, category, status, config, schemaData, createdAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      'conn-1',
      'Legacy MySQL DB',
      'MySQL',
      'Source',
      'Configured',
      '{}',
      '{}',
      new Date().toISOString(),
    ],
  );
  console.log('Seeded Connectors Execution Registry.');
  console.log('Database Seed Completed Successfully.');
}

seed().catch(console.error);

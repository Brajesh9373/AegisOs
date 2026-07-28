const fs = require('fs');
const path = require('path');
const initSqlJs = require('sql.js');

async function runTest() {
  const adminEmail = 'admin@aegisos.com';
  const adminPassword = 'admin123';
  const baseUrl = 'http://localhost:3001/api';

  console.log('1. Attempting login...');
  const loginRes = await fetch(`${baseUrl}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: adminEmail, password: adminPassword })
  });
  if (!loginRes.ok) {
    console.error('Login failed:', await loginRes.text());
    return;
  }
  const { token } = await loginRes.json();
  console.log('Login Succeeded, Token:', token);

  console.log('\n2. Attempting to create project...');
  const payload = {
    name: 'Automate Tax Mapping',
    businessGoal: 'Auto map incoming transaction lines to state specific sales tax rules',
    department: 'Finance',
    priority: 'High'
  };
  console.log('Request Payload:', payload);
  const projRes = await fetch(`${baseUrl}/projects`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });
  console.log('Response Status:', projRes.status);
  const bodyText = await projRes.text();
  console.log('Response Body:', bodyText);

  if (!projRes.ok) {
    console.error('Project creation failed.');
    return;
  }
  const project = JSON.parse(bodyText);
  const projectId = project.id;
  console.log('Project created successfully with ID:', projectId);

  console.log('\n3. Sending AI chat message to workspace...');
  const chatPayload = { message: 'Start mapping setup' };
  const chatRes = await fetch(`${baseUrl}/projects/${projectId}/workspace/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(chatPayload)
  });
  console.log('Chat Status:', chatRes.status);
  console.log('Chat Body:', await chatRes.text());

  console.log('\n4. Verifying database state via sql.js...');
  const SQL = await initSqlJs();
  const dbPath = path.join(process.cwd(), 'data', 'aegis.db');
  if (!fs.existsSync(dbPath)) {
    console.log('Database not found at', dbPath);
    return;
  }
  const filebuffer = fs.readFileSync(dbPath);
  const db = new SQL.Database(filebuffer);

  const stmt = db.prepare('SELECT id, name, department, priority, status FROM projects WHERE id = ?;', [projectId]);
  console.log('Project in DB:');
  while (stmt.step()) {
    console.log(stmt.getAsObject());
  }
  stmt.free();

  const stmt2 = db.prepare('SELECT id, projectId, state, reasoning FROM execution_nodes WHERE projectId = ?;', [projectId]);
  console.log('Execution Nodes in DB:');
  while (stmt2.step()) {
    console.log(stmt2.getAsObject());
  }
  stmt2.free();
}

runTest().catch(console.error);

const { Pool } = require('/app/node_modules/.pnpm/pg@8.22.0/node_modules/pg');
const p = new Pool({ connectionString: 'postgresql://ecms:ecms@postgres:5432/ecms' });
p.query('DROP TABLE IF EXISTS organization, users, departments, audit_logs, auth_sessions, business_projects, invitations, project_agents, execution_nodes, artifacts, human_queue, agent_memory, general_ai_sessions CASCADE')
  .then(() => { console.log('All tables dropped'); p.end(); })
  .catch(e => { console.error(e.message); p.end(); });

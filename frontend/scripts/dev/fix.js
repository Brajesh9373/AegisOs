const fs = require('fs');
const path = require('path');

const files = [
  'apps/web/src/pages/Connectors.tsx',
  'apps/web/src/pages/Dashboard.tsx',
  'apps/web/src/pages/Implementation.tsx',
  'apps/web/src/pages/Knowledge.tsx',
  'apps/web/src/pages/Workspace.tsx'
];

for (const file of files) {
  let content = fs.readFileSync(file, 'utf8');

  // Fix mockIdentity
  content = content.replace(
    /const mockIdentity: IdentityContext = \{\s*id: 'user-1',\s*roles: \['admin', 'manager'\],\s*permissions: \[\],\s*attributes: \{\},\s*\};/g,
    `const mockIdentity: IdentityContext = {
  userId: 'user-1',
  token: 'mock-token',
  claims: { role: 'admin' },
};`
  );

  // Fix Dashboard.tsx Action Timeline
  content = content.replace(/e\.timestamp/g, 'e.createdAt');
  
  // Fix Workspace.tsx
  content = content.replace(/k\.metadata/g, 'k.properties');
  content = content.replace(/m\.type/g, 'm.tier');

  // Fix Task description usage
  content = content.replace(/t\.description/g, 't.skillId');
  content = content.replace(/j\.description/g, 'j.skillId');
  content = content.replace(/r\.description/g, 'r.skillId');
  content = content.replace(/s\.description/g, 's.skillId');
  content = content.replace(/job\.description/g, 'job.skillId');
  content = content.replace(/task\.description/g, 'task.skillId');

  fs.writeFileSync(file, content);
}
console.log('Fixed pages.');

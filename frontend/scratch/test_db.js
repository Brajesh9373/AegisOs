const fs = require('fs');
const path = require('path');
const initSqlJs = require('sql.js');

async function test() {
  try {
    const SQL = await initSqlJs();
    let dbPath = path.join('apps', 'api', 'data', 'aegis.db');
    if (!fs.existsSync(dbPath)) {
      dbPath = path.join('data', 'aegis.db');
    }
    if (!fs.existsSync(dbPath)) {
      dbPath = path.join(process.cwd(), 'data', 'aegis.db');
    }
    if (!fs.existsSync(dbPath)) {
      console.log('Database file does not exist at current cwd paths');
      return;
    }
    const filebuffer = fs.readFileSync(dbPath);
    const db = new SQL.Database(filebuffer);
    
    const stmt = db.prepare('SELECT id, name, department, priority, status FROM projects;');
    console.log('=== Projects in Database ===');
    while (stmt.step()) {
      console.log(stmt.getAsObject());
    }
    stmt.free();
    
    const stmt2 = db.prepare('SELECT id, projectId, reason, status FROM human_queue;');
    console.log('=== Human Queue items ===');
    while (stmt2.step()) {
      console.log(stmt2.getAsObject());
    }
    stmt2.free();
  } catch (e) {
    console.error('Error querying database:', e);
  }
}
test();

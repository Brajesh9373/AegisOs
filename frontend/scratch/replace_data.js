import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const directoryPath = 'd:/experiments/aegisOS/apps/web/src';

const replacements = [
  { search: /Acme Corp/g, replace: 'VNU' },
  { search: /Acme/g, replace: 'VNU' },
  { search: /GlobalInc/g, replace: 'VNU' },
  { search: /Jane Doe/g, replace: 'Current User' },
  { search: /John Smith/g, replace: 'Sarah Jenkins' },
  { search: /jane@acme\.com/g, replace: 'sarah@vnu.com' },
  { search: /john@acme\.com/g, replace: 'sarah@vnu.com' },
  { search: /client@acme\.com/g, replace: 'client@vnu.com' },
  { search: /admin@acme\.com/g, replace: 'admin@vnu.com' },
];

function processDirectory(dir) {
  const files = fs.readdirSync(dir);

  for (const file of files) {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);

    if (stat.isDirectory()) {
      processDirectory(filePath);
    } else if (filePath.endsWith('.tsx') || filePath.endsWith('.ts')) {
      let content = fs.readFileSync(filePath, 'utf8');
      let changed = false;

      for (const rep of replacements) {
        if (rep.search.test(content)) {
          content = content.replace(rep.search, rep.replace);
          changed = true;
        }
      }

      if (changed) {
        fs.writeFileSync(filePath, content, 'utf8');
        console.log(`Replaced in: ${filePath}`);
      }
    }
  }
}

processDirectory(directoryPath);
console.log('Finished replacing data.');

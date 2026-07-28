const fs = require('fs');
const path = require('path');
const dir = 'src/pages';

function processFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let original = content;

  // Remove ConfigProvider opening tags with any attributes
  content = content.replace(/<ConfigProvider[^>]*>/g, '');
  // Remove ConfigProvider closing tags
  content = content.replace(/<\/ConfigProvider>/g, '');

  if (content !== original) {
    fs.writeFileSync(filePath, content);
    console.log('Removed ConfigProvider from: ' + filePath);
  }
}

function walk(dir) {
  const list = fs.readdirSync(dir);
  for (const file of list) {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      walk(fullPath);
    } else if (fullPath.endsWith('.tsx') || fullPath.endsWith('.ts')) {
      processFile(fullPath);
    }
  }
}

walk(dir);

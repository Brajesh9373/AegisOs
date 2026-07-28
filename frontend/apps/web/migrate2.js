const fs = require('fs');
const path = require('path');
const dir = 'src';

function processFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let original = content;

  // Replace stray rgba borders and backgrounds
  content = content.replace(/rgba\(255,255,255,0\.0[12458]\)/g, 'rgba(0,0,0,0.04)');
  content = content.replace(/rgba\(255,255,255,0\.15?\)/g, 'rgba(0,0,0,0.1)');
  content = content.replace(/rgba\(255,255,255,0\.2\)/g, 'rgba(0,0,0,0.15)');
  content = content.replace(/rgba\(255,255,255,0\.3\)/g, 'rgba(0,0,0,0.25)');
  
  // Specific fallback for default prop in ExecutiveCard.tsx
  content = content.replace(/bg = 'rgba\(0,0,0,0.04\)', borderColor = 'rgba\(0,0,0,0.04\)'/g, 'bg = \'#fff\', borderColor = \'#f0f0f0\'');

  if (content !== original) {
    fs.writeFileSync(filePath, content);
    console.log('Updated: ' + filePath);
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

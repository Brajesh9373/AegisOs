const fs = require('fs');
const path = require('path');
const dir = 'src/pages';
const compDir = 'src/components/ui';
const layoutDir = 'src/layout';

function processFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let original = content;

  // Backgrounds and colors
  content = content.replace(/['"]#f5f7fa['"]/ig, "'#F8FAFC'");
  content = content.replace(/['"]#fff['"]/ig, "'#FFFFFF'");
  content = content.replace(/['"]#f0f0f0['"]/ig, "'#E5E7EB'");
  content = content.replace(/['"]rgba\(0, 0, 0, 0.45\)['"]/ig, "'#6B7280'");
  content = content.replace(/['"]rgba\(0, 0, 0, 0.88\)['"]/ig, "'#111827'");
  content = content.replace(/['"]#000['"]/ig, "'#111827'");
  content = content.replace(/['"]#1677ff['"]/ig, "'#2563EB'");

  // Typography
  content = content.replace(/fontWeight:\s*700/ig, "fontWeight: 600");
  content = content.replace(/fontWeight:\s*['"]bold['"]/ig, "fontWeight: 600");

  // Remove aggressive box shadows
  content = content.replace(/boxShadow:\s*['"][^'"]+['"],?\s*/ig, "");

  // Remove redundant border radii (ConfigProvider handles it)
  // Let's only remove standard ones like 4, 6, 8 so we don't break complex shapes
  content = content.replace(/borderRadius:\s*[468],?\s*/ig, "");

  // Spacing (increase padding in root layouts if applicable)
  // Replaced in AppLayout instead

  if (content !== original) {
    fs.writeFileSync(filePath, content);
    console.log('Standardized: ' + filePath);
  }
}

function walk(directory) {
  const list = fs.readdirSync(directory);
  for (const file of list) {
    const fullPath = path.join(directory, file);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      walk(fullPath);
    } else if (fullPath.endsWith('.tsx') || fullPath.endsWith('.ts')) {
      processFile(fullPath);
    }
  }
}

walk(dir);
walk(compDir);
walk(layoutDir);

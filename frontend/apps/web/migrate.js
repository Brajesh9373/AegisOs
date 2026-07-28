const fs = require('fs');
const path = require('path');
const dir = 'src';

function processFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let original = content;

  // ConfigProvider replacements
  content = content.replace(/algorithm:\s*theme\.darkAlgorithm,?\s*/g, '');
  content = content.replace(/colorPrimary:\s*['"]#00D9FF['"]/ig, 'colorPrimary: \'#1677ff\'');
  content = content.replace(/colorPrimary:\s*['"]#00f0ff['"]/ig, 'colorPrimary: \'#1677ff\'');
  content = content.replace(/colorBgContainer:\s*['"]#(09090[bB]|111113|121214)['"]/ig, 'colorBgContainer: \'#fff\'');
  content = content.replace(/colorBorder:\s*['"]rgba\(255,255,255,0\.\d+['"]/ig, 'colorBorder: \'#f0f0f0\'');

  // Backgrounds
  content = content.replace(/background:\s*['"]#(09090[bB]|121214)['"]/ig, 'background: \'#f5f7fa\'');
  content = content.replace(/background:\s*['"]#111113['"]/ig, 'background: \'#fff\'');
  content = content.replace(/background:\s*['"]rgba\(255,\s*255,\s*255,\s*0\.0[2458]\)['"]/ig, 'background: \'#fafafa\'');
  content = content.replace(/backgroundColor:\s*['"]#(09090[bB]|121214|111113)['"]/ig, 'backgroundColor: \'#f5f7fa\'');

  // Borders
  content = content.replace(/border(Bottom|Top|Right|Left)?:\s*['"]1px solid rgba\(255,\s*255,\s*255,\s*0\.\d+\)['"]/ig, 'border$1: \'1px solid #f0f0f0\'');
  content = content.replace(/border:\s*['"]1px dashed rgba\(255,\s*255,\s*255,\s*0\.\d+\)['"]/ig, 'border: \'1px dashed #d9d9d9\'');
  content = content.replace(/borderColor:\s*['"]rgba\(255,\s*255,\s*255,\s*0\.\d+\)['"]/ig, 'borderColor: \'#f0f0f0\'');
  content = content.replace(/border:\s*['"]none['"],?/ig, '');

  // Typography colors
  content = content.replace(/color:\s*['"]#(a1a1aa|71717a|d4d4d8)['"]/ig, 'color: \'rgba(0, 0, 0, 0.45)\'');
  
  // Replace color: '#fff' safely
  content = content.replace(/,\s*color:\s*['"]#(fff|FFFFFF)['"]/ig, '');
  content = content.replace(/color:\s*['"]#(fff|FFFFFF)['"],\s*/ig, '');
  content = content.replace(/\{\{\s*color:\s*['"]#(fff|FFFFFF)['"]\s*\}\}/ig, '{{}}');
  
  // Specific fix for color: '#fff' in remaining cases
  content = content.replace(/color:\s*['"]#(fff|FFFFFF)['"]/ig, 'color: \'rgba(0, 0, 0, 0.88)\'');

  // Fix valueColor="#fff" for ExecutiveCard
  content = content.replace(/valueColor=["']#(fff|FFFFFF)["']/ig, 'valueColor="#000"');
  
  // Fix valueColor="#a1a1aa" for ExecutiveCard
  content = content.replace(/valueColor=["']#(a1a1aa|71717a)["']/ig, 'valueColor="rgba(0, 0, 0, 0.45)"');

  // Dashboard dark mode fixes for cards
  content = content.replace(/glassCard\s*=\s*\{[\s\S]*?\};/g, 'glassCard = { background: \'#fff\', border: \'1px solid #f0f0f0\', borderRadius: 6, marginBottom: 16 };');

  // Theme ConfigProvider overrides that were left over
  content = content.replace(/<ConfigProvider theme=\{\{\s*algorithm:\s*theme\.darkAlgorithm\s*\}\}>/g, '<ConfigProvider theme={{ token: { colorPrimary: \'#1677ff\', borderRadius: 4, colorBgContainer: \'#fff\' } }}>');

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

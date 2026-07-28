const fs = require('fs');
const file = 'd:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.3.md';
let txt = fs.readFileSync(file, 'utf8');

const industryPacks = `###  Industry Packs\r\nIndustry Packs serve as comprehensive, vertical-specific asset bundles that customize implementations for highly specialized markets without requiring any modification to the underlying platform architecture.\r\n\r\n**Examples of Industry Packs:**\r\n- Healthcare\r\n- Manufacturing\r\n- Finance\r\n- Retail\r\n- Logistics\r\n- Education\r\n- Government\r\n\r\n**Industry Packs include:**\r\n- Knowledge\r\n- Policies\r\n- Templates\r\n- Skills\r\n- Validation Rules\r\n- Compliance Rules\r\n- Assessment Rules\r\n- Discovery Rules\r\n\r\n`;

txt = txt.replace(/(###\s+Experience Library[\s\S]*?)(?=##\s+Universal Implementation Lifecycle)/, `$1\r\n${industryPacks}`);

fs.writeFileSync(file, txt);
console.log('Industry Packs added.');

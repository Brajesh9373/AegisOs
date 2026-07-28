const fs = require('fs');
const file = 'd:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.3.md';
let txt = fs.readFileSync(file, 'utf8');

const successCriteria = `##  Success Criteria\r\n\r\nEvery Implementation Project mandates the definition of explicitly measurable success. The platform fundamentally distances itself from measuring completion purely by task volume or agent execution cycles; instead, it measures completion strictly against these predefined Success Criteria.\r\n\r\nWhen these structural thresholds are met, the Success Criteria become the official, cryptographic completion signal for the project, triggering validation and deployment phases.\r\n\r\nExamples of strictly defined Success Criteria include:\r\n- System deployed\r\n- Users migrated\r\n- Zero validation errors\r\n- Compliance passed\r\n- Performance targets achieved\r\n- Rollback not required\r\n- Business acceptance completed\r\n\r\n`;

txt = txt.replace(/(##\s+Business Goal Model[\s\S]*?)(?=##\s+Digital Workforce)/, `$1\r\n${successCriteria}`);

fs.writeFileSync(file, txt);
console.log('Success Criteria added.');

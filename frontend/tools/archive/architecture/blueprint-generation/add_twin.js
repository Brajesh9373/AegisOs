const fs = require('fs');
const file = 'd:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.3.md';
let txt = fs.readFileSync(file, 'utf8');

const digitalTwin = `###  Digital Twin\r\n- **Purpose**: Create a virtual representation of customer environments before execution.\r\n- **Composition**: The Digital Twin may contain Applications, Users, Infrastructure, Servers, Policies, Configurations, Permissions, Data Models, and Dependencies.\r\n- **Lifecycle**: The Discovery Engine continuously updates the Digital Twin to maintain parity with the live environment.\r\n- **Consumers**: Planning, Simulation, and Validation execution phases operate strictly against the Digital Twin to verify safety and correctness before ever touching live production targets.\r\n\r\n`;

txt = txt.replace(/(###\s+Environment[\s\S]*?)(?=###\s+Asset Inventory)/, `$1\r\n${digitalTwin}`);

fs.writeFileSync(file, txt);
console.log('Digital Twin added.');

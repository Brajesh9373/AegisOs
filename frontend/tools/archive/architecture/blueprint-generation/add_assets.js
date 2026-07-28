const fs = require('fs');
const oldFile = 'd:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.4.md';
let txt = fs.readFileSync(oldFile, 'utf8');

// 1. Version Bump
txt = txt.replace(/Version: 2\.4\.0/g, 'Version: 2.5.0');
txt = txt.replace(/#  aegisOS Platform Blueprint v2\.4/g, '#  aegisOS Platform Blueprint v2.5');

// 2. Add to Canonical Platform Definitions
const canonicalAssets = `###  Assets\r\nAssets represent everything discovered inside a customer environment (Servers, VMs, Containers, Databases, Users, etc.). They are the fundamental structural inventory against which Digital Teams execute.\r\n\r\n`;
txt = txt.replace(/(##\s+Canonical Platform Definitions\r?\n\r?\n)/, `$1${canonicalAssets}`);

// 3. Add to Platform Capability Map
const capabilityAssets = `###  Assets\r\n- **Purpose**: Represent everything discovered inside a customer environment.\r\n- **Responsibilities**: Cataloging Servers, VMs, Containers, Clusters, Applications, Databases, Users, Groups, Domains, Certificates, Secrets References, Networks, Load Balancers, Buckets, Queues, Storage Accounts, Mailboxes, and Licenses.\r\n- **Owner**: Platform Data.\r\n- **Consumers**: Assessment Engine, Planning Engine, Digital Teams.\r\n- **Dependencies**: Produced by the Discovery Engine.\r\n- **Lifecycle**: Discovered, Validated, Mutated, Re-discovered.\r\n- **Future Evolution**: Real-time continuous streaming asset synchronization.\r\n\r\n`;
txt = txt.replace(/(##\s+Platform Capability Map\r?\n\r?\n)/, `$1${capabilityAssets}`);

// 4. Add to Bounded Context Map
const boundedAssets = `###  Assets Context\r\n- **Purpose**: System of record for discovered environment inventory.\r\n- **Ownership**: Platform Data.\r\n- **Responsibilities**: Tracking the lifecycle and state of discovered assets.\r\n- **Public interfaces**: \`getAsset\`, \`registerAsset\`, \`updateAssetState\`.\r\n- **Upstream contexts**: Discovery Engine.\r\n- **Downstream contexts**: Storage Context.\r\n- **Communication rules**: Synchronous queries, asynchronous ingestion.\r\n- **Isolation rules**: Never stores raw unencrypted secrets; only stores references.\r\n- **Shared kernel rules**: Shares abstract \`Asset\` models.\r\n- **Context boundaries**: Stops strictly at inventory management; does not orchestrate deployment.\r\n\r\n`;
txt = txt.replace(/(##\s+Bounded Context Map\r?\n\r?\n)/, `$1${boundedAssets}`);

// 5. Add to Package Dependency Matrix (Table)
const packageAssets = `| \`@aegis/assets\` | \`contracts\`, \`storage\` | Core Logic | Assessment, Planning | Platform Data | Logic | Discovered inventory management |\r\n`;
txt = txt.replace(/(\| \`@aegis\/agents\`)/, `${packageAssets}$1`);

// 6. Add to the numeric list of packages
txt = txt.replace(/20\. \`@aegis\/web\`/, "20. `@aegis/web`\r\n21. `@aegis/assets`");

fs.writeFileSync('d:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.5.md', txt);
fs.unlinkSync(oldFile);
console.log('Update complete.');

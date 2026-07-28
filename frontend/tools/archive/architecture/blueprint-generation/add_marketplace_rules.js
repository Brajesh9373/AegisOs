const fs = require('fs');
const oldFile = 'd:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.10.md';
let txt = fs.readFileSync(oldFile, 'utf8');

// 1. Version Bump
txt = txt.replace(/Version: 2\.10\.0/g, 'Version: 2.11.0');
txt = txt.replace(/#  aegisOS Platform Blueprint v2\.10/g, '#  aegisOS Platform Blueprint v2.11');

// 2. Expand Marketplace Architecture
const newMarketplace = `##  Marketplace\r\n\r\nThe Marketplace serves as the centralized distribution repository for reusable implementation assets. It strictly adheres to the platform's self-hosted philosophy: customers download and install Marketplace assets directly into their own isolated, self-hosted environments. The Marketplace never executes customer workloads and never accesses customer data; it is exclusively a distribution hub for signed packages.\r\n\r\n###  Marketplace Assets\r\nMarketplace assets fundamentally expand platform capabilities without requiring architectural modification. Supported assets include:\r\n- **Implementation Templates**\r\n- **Digital Teams**\r\n- **Skills**\r\n- **Connectors**\r\n- **Policies**\r\n- **Knowledge Packs**\r\n- **Compliance Packs**\r\n- **Industry Packs**\r\n- **Validation Packs**\r\n- **Playbooks**\r\n\r\n###  Purpose\r\nTo radically accelerate Implementation Projects by allowing customers to install pre-built, domain-specific intelligence, workflows, and policies rather than building them from scratch.\r\n\r\n###  Responsibilities\r\n- Indexing and cataloging available assets.\r\n- Serving immutable, cryptographically signed package binaries.\r\n- Distributing updates and patches for installed assets.\r\n- Maintaining strict dependency resolution between interrelated packs.\r\n\r\n###  Security\r\nOperates under a zero-trust model. Because it is purely a distribution mechanism, it has zero inbound connectivity to customer self-hosted instances. Customers always pull assets outwardly; the Marketplace cannot push or execute code remotely.\r\n\r\n###  Signing\r\nEvery asset published to the Marketplace must be cryptographically signed by its author. The self-hosted Guardian explicitly verifies this cryptographic signature before permitting the installation of any asset, ensuring absolute supply chain integrity.\r\n\r\n###  Versioning\r\nAssets adhere strictly to Semantic Versioning (SemVer). Breaking changes to structural contracts require major version increments. Deprecation of an asset version triggers proactive impact analysis for downstream consumers before the asset is sunset.\r\n\r\n###  Future Evolution\r\nPrivate, federated Marketplaces deployed strictly within Air-Gapped environments to allow isolated enterprise subsidiaries to share verified assets internally without connecting to the global ecosystem.\r\n\r\n`;

// Replace existing Marketplace section
txt = txt.replace(/##\s+Marketplace[\s\S]*?(?=##\s+Execution Modes)/, newMarketplace);

fs.writeFileSync('d:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.11.md', txt);
fs.unlinkSync(oldFile);
console.log('Update complete.');

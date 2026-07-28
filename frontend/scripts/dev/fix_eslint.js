const fs = require('fs');
const path = require('path');

function replaceInFile(filePath, searchRegex, replaceWith) {
    if (!fs.existsSync(filePath)) return;
    let content = fs.readFileSync(filePath, 'utf8');
    content = content.replace(searchRegex, replaceWith);
    fs.writeFileSync(filePath, content);
}

// Copy .eslintrc.js to connector-framework and digital-employee-workspace
try {
    fs.copyFileSync('packages/contracts/.eslintrc.js', 'packages/connector-framework/.eslintrc.js');
} catch(e) {}

// packages/knowledge/src/graph/store.ts
replaceInFile('packages/knowledge/src/graph/store.ts',
    /getNeighborhood\(nodeId: string, depth: number\) \{/,
    'getNeighborhood(nodeId: string, depth: number) {\n        void depth;'
);
replaceInFile('packages/knowledge/src/graph/store.ts',
    /search\(query: string, filters: Record<string, unknown>\) \{/,
    'search(query: string, filters: Record<string, unknown>) {\n        void query;'
);

// packages/knowledge/src/pipeline/extraction.ts
replaceInFile('packages/knowledge/src/pipeline/extraction.ts',
    /extractEntities\(text: string\) \{/,
    'extractEntities(text: string) {\n        void text;'
);
replaceInFile('packages/knowledge/src/pipeline/extraction.ts',
    /extractRelationships\(text: string\) \{/,
    'extractRelationships(text: string) {\n        void text;'
);

// packages/knowledge/src/pipeline/processor.ts
replaceInFile('packages/knowledge/src/pipeline/processor.ts',
    /content: any/,
    'content: unknown'
);

// packages/marketplace/src/v3/adapter.ts
replaceInFile('packages/marketplace/src/v3/adapter.ts',
    /getPlugin\(id: string, identity: string\) \{/,
    'getPlugin(id: string, identity: string) {\n        void identity;'
);

// packages/memory/src/hierarchy/coordinator.ts
replaceInFile('packages/memory/src/hierarchy/coordinator.ts',
    /flush\(agentId: string\) \{/,
    'flush(agentId: string) {\n        void agentId;'
);

// packages/memory/src/policies/lifecycle.ts
replaceInFile('packages/memory/src/policies/lifecycle.ts',
    /promote\(snapshotId: string, currentTier: string\) \{/,
    'promote(snapshotId: string, currentTier: string) {\n        void snapshotId;\n        void currentTier;'
);
replaceInFile('packages/memory/src/policies/lifecycle.ts',
    /evict\(sessionId: string\) \{/,
    'evict(sessionId: string) {\n        void sessionId;'
);

// packages/memory/src/security_adapter.ts
replaceInFile('packages/memory/src/security_adapter.ts',
    /data: any/,
    'data: unknown'
);

// packages/workflow/src/v3/adapter.ts
replaceInFile('packages/workflow/src/v3/adapter.ts',
    /import \{ ExecutionContext, TraceabilityContext, AuditLedger \} from '@aegisos\/contracts';/,
    "import { ExecutionContext } from '@aegisos/contracts';"
);


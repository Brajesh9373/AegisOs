# Business Analyst (BA) Agent Configuration

**Date:** 2026-09-03
**Status:** Documented from AegisOS codebase

## Overview

The Business Analyst (BA) agent is a digital worker that orchestrates project discovery, requirements gathering, and team design for software delivery projects in AegisOS.

## Core Configuration

### Identity
- **Key:** `business-analyst`
- **Name:** Business Analyst
- **Designation:** Requirements Custodian
- **Role:** `business_analyst`
- **Department:** `documentation`
- **Reports To:** Delivery Manager (project-dependent)

### Purpose & Goals
- **Goal:** "Hold requirements custody and acceptance criteria throughout delivery."
- **Instructions:** "Keep the finalized requirements authoritative. Translate client answers into acceptance criteria for each pod."

### Skills
- Requirements elicitation
- Acceptance criteria definition

### Model
- **Primary:** `gpt-4o`
- **Fallback:** Deterministic fallback when BA model not configured

### Tools
- `read_file` - Read project documents
- `search_memory` - Search knowledge base
- `note` - Document findings

## Knowledge Base

### Knowledge Categories
1. **universal_pattern** - BA methodology, how to think
2. **domain_pattern** - Industry/domain knowledge
3. **anti_pattern** - Red flags, common mistakes
4. **compliance** - Regulatory frameworks
5. **correction** - Fix a BA mistake
6. **project_context** - Specific project intel
7. **architecture_pattern** - Technical patterns
8. **success_pattern** - What worked well

### Knowledge Sources
- **Seeds Directory:** `backend/ecms/agent/ba/knowledge/seeds/`
- **Files:**
  - `universal_patterns.json` - 28 BA methodology patterns
  - `compliance_frameworks.json` - GDPR, HIPAA, SOC2 frameworks
  - `domain_patterns.json` - Domain-specific knowledge
  - `architecture_patterns.json` - Technical architecture patterns

### Sample Universal Patterns
- "Always probe rollback strategy before discussing cutover."
- "When a client says 'real-time sync', never accept it at face value."
- "The #1 cause of migration project failure is underestimating data quality issues."
- "Stakeholder analysis is not optional."
- "Non-functional requirements are where projects fail."

## Certifications

### BA-Specific Certifications
1. **Entry Certificate in Business Analysis (ECBA)**
   - Issuer: IIBA
   - URL: https://www.iiba.org/business-analysis-certifications/ecba/

2. **Certification of Capability in Business Analysis (CCBA)**
   - Issuer: IIBA
   - URL: https://www.iiba.org/business-analysis-certifications/ccba/

3. **PMI Professional in Business Analysis (PMI-PBA)**
   - Issuer: Project Management Institute
   - URL: https://www.pmi.org/certifications/business-analysis-pba

## Tool Policy

### Allowed Tools
```json
{
  "allowed_tools": ["read_file", "search_memory", "note"],
  "blocked_tools": []
}
```

### Workspace Scope
- Global reusable agent pool (not project-specific)
- Access to knowledge base for retrieval-augmented generation

## System Behavior

### Staged LLM Generations

The BA agent performs **four staged LLM generations**:

#### Stage 1: Understand
- **Input:** Project source text
- **Output:** "What I understood" recap message (Markdown)
- **Purpose:** Demonstrate comprehension before proceeding

#### Stage 2: Clarify
- **Input:** Project source text + knowledge context
- **Output:** Category-specific question batch
- **Categories:**
  - `assumptions` - Assumptions to validate
  - `scope` - Scope boundaries
  - `risks` - Risk identification
  - `governance` - Governance requirements
  - `technical` - Technical constraints
  - `phasing` - Phasing and timeline

#### Stage 3: Finalize
- **Input:** Source text + conversation + knowledge context
- **Output:** `FinalizedRequirements` object
- **Structure:**
  - Project name
  - Objective
  - Functional requirements
  - Tech stack
  - Skills required
  - Connectors
  - Risks
  - Phases (Discovery → Integration → Workflow → Launch)
  - Governance items
  - Guardrails
  - Infrastructure requirements

#### Stage 4: Design Team
- **Input:** Requirements + conversation + model catalog + tool catalog
- **Output:** `AgentTeam` object (org chart)
- **Structure:**
  - Flat list of agents with `reports_to` references
  - One root (reports_to = None)
  - No cycles
  - All models/tools from live catalogs

### Knowledge Retrieval

The BA agent uses **hybrid search** (text + semantic) to retrieve relevant knowledge:
1. Full-text search using PostgreSQL tsvector
2. Semantic search using embeddings (cosine similarity)
3. Deduplication and score fusion

### Fallback Behavior

When no BA model is configured, the agent uses a **deterministic fallback**:
- Derives content from source text and user answers
- Keeps fixed frontend schema
- Avoids pretending an LLM reviewed the project

## Automation & Features

### Default Automation Settings
```json
{
  "autoRetry": true,
  "maxRetries": 3,
  "retryDelaySeconds": 30,
  "escalateOnFailure": true,
  "heartbeatIntervalSeconds": 60
}
```

### Default Features
```json
{
  "memoryRetentionDays": 30,
  "dataQueryAccess": "read",
  "maxConcurrentTasks": 5,
  "rateLimitPerMinute": 60,
  "streamingEnabled": true,
  "auditLogging": true,
  "piiMasking": false
}
```

## Validation & Repair

The BA agent includes a **validate/repair loop**:
1. If emitted object fails schema validation
2. Re-ask once with the validation error
3. Attempt correction before giving up

## Integration Points

### API Endpoints
- REST API: `/api/ba/*` (understand, clarify, finalize, design-team)
- WebSocket: Real-time conversation streaming

### LLM Client
- `BaLlmClient` with timeout, retry, circuit breaker
- Temperature: 0.0 (deterministic)
- Max tokens: 1600-6000 depending on stage

### Catalog Integration
- **Model Catalog:** Validates model IDs against allowed models
- **Tool Catalog:** Validates tool names against allowed tools
- **Org Roster:** Maps positions to organization members

## Example Team Design

From `team_exemplar.py` - Golden exemplar for HR migration project:

```json
{
  "key": "business-analyst",
  "name": "Business Analyst",
  "designation": "Requirements Custodian",
  "role": "business_analyst",
  "department": "documentation",
  "reports_to": "delivery-manager",
  "goal": "Hold requirements custody and acceptance criteria throughout delivery.",
  "instructions": "Keep the finalized requirements authoritative. Translate client answers into acceptance criteria for each pod.",
  "skills": ["requirements elicitation", "acceptance criteria"],
  "model": "gpt-4o",
  "tools": ["read_file", "search_memory", "note"]
}
```

## File Locations

### Core Agent Code
- Agent implementation: `backend/ecms/agent/ba/agent.py`
- Team schema: `backend/ecms/agent/ba/team_schema.py`
- LLM client: `backend/ecms/agent/ba/llm_client.py`
- Prompts: `backend/ecms/agent/ba/prompts.py`

### Knowledge System
- Knowledge store: `backend/ecms/agent/ba/knowledge/store.py`
- Retrieval: `backend/ecms/agent/ba/knowledge/retrieval.py`
- Embeddings: `backend/ecms/agent/ba/knowledge/embeddings.py`
- Seed knowledge: `backend/ecms/agent/ba/knowledge/seed_knowledge.py`

### Certifications
- Certification rules: `backend/ecms/shared/certifications.py`

## Comparison Points for DSH Replication

When replicating in DSH, ensure:

1. **Same role/designation:** `business_analyst` / "Requirements Custodian"
2. **Same skills:** requirements elicitation, acceptance criteria
3. **Same tools:** read_file, search_memory, note (or DSH equivalents)
4. **Same model:** gpt-4o (or equivalent capability)
5. **Same knowledge:** Universal BA patterns loaded into context
6. **Same certifications:** ECBA, CCBA, PMI-PBA
7. **Same staged workflow:** understand → clarify → finalize → design-team
8. **Same validation:** Schema validation with repair loop

---

**Next Step:** Create DSH profile in `packages/dsh-integration/profiles/business-analyst/`

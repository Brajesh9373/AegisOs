/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useEffect, useRef } from 'react';
import {
  Row, Col, Card, Tag, Button, Space, Typography, Statistic, Avatar, Modal, Form,
  Input, Select, Divider, Table, message, Collapse, Tabs, Progress, Descriptions,
} from 'antd';
import {
  RobotOutlined,
  SettingOutlined,
  UserOutlined,
  DatabaseOutlined,
  DeleteOutlined,
  EyeOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  ApiOutlined,
  CloudServerOutlined,
  CodeOutlined,
  BranchesOutlined,
  ProjectOutlined,
  TeamOutlined,
  MessageOutlined,
  VideoCameraOutlined,
  SyncOutlined,
  CloudOutlined,
  AmazonOutlined,
  WindowsOutlined,
  GithubOutlined,
  GitlabOutlined,
  PlusOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { ApiClient } from '../api/client';

const { Text, Title } = Typography;

type IngestionState =
  | 'QUEUED' | 'VALIDATING' | 'CLONING' | 'SCANNING' | 'EXTRACTING'
  | 'WRITING' | 'SNAPSHOTTING' | 'READY' | 'FAILED'
  | 'CANCEL_REQUESTED' | 'CANCELLED' | 'RETRYING';

interface ConnectorIngestion {
  job_id: string;
  connection_id?: string;
  status_url: string;
  status: IngestionState;
  stage?: string;
  progress?: number;
  repository_url?: string;
  connection_name?: string;
  files_discovered?: number;
  files_processed?: number;
  nodes_written?: number;
  elapsed_seconds?: number;
  error?: { code?: string; message?: string } | string | null;
}

const INGESTION_STORAGE_KEY = 'ecms.connector-ingestions.v1';
const TERMINAL_INGESTION_STATES = new Set<IngestionState>(['READY', 'FAILED', 'CANCELLED']);
const INGESTION_STAGE_LABELS: Record<string, string> = {
  QUEUED: 'Waiting for an ingestion worker',
  VALIDATING: 'Validating repository access',
  CLONING: 'Cloning repository',
  SCANNING: 'Scanning source files',
  EXTRACTING: 'Extracting knowledge',
  WRITING: 'Writing graph revision',
  SNAPSHOTTING: 'Publishing graph snapshot',
  READY: 'Knowledge graph ready',
  FAILED: 'Ingestion failed',
  CANCEL_REQUESTED: 'Stopping safely',
  CANCELLED: 'Ingestion cancelled',
  RETRYING: 'Preparing retry',
};

const InProgressNotice = ({ children }: { children: React.ReactNode }) => (
  <div style={{ marginBottom: 16, padding: '10px 12px', borderRadius: 8, border: '1px solid #FED7AA', background: '#FFF7ED' }}>
    <Text style={{ fontSize: 12, color: '#9A3412' }}>{children}</Text>
  </div>
);

export const CATEGORIES = [
  { key: 'project-management', title: 'Project Management', icon: <ProjectOutlined />, tools: [
    { name: 'Jira', logo: 'https://cdn.worldvectorlogo.com/logos/jira-1.svg' },
    { name: 'Asana', logo: 'https://cdn.worldvectorlogo.com/logos/asana.svg' },
  ]},
  { key: 'collaboration', title: 'Collaboration', icon: <TeamOutlined />, tools: [
    { name: 'Slack', logo: 'https://cdn.worldvectorlogo.com/logos/slack-new-logo.svg' },
    { name: 'Teams', logo: 'https://cdn.worldvectorlogo.com/logos/microsoft-teams.svg' },
    { name: 'Meet', logo: 'https://cdn.worldvectorlogo.com/logos/google-meet.svg' },
  ]},
  { key: 'infra', title: 'Infrastructure Providers', icon: <CloudServerOutlined />, tools: [
    { name: 'AWS', logo: 'https://cdn.worldvectorlogo.com/logos/aws-2.svg' },
    { name: 'GCP', logo: 'https://cdn.worldvectorlogo.com/logos/google-cloud.svg' },
    { name: 'Azure', logo: 'https://cdn.worldvectorlogo.com/logos/azure-1.svg' },
  ]},
  { key: 'dev-tools', title: 'Developer Tools', icon: <CodeOutlined />, tools: [
    { name: 'GitHub', logo: 'https://cdn.worldvectorlogo.com/logos/github-icon-1.svg' },
    { name: 'GitLab', logo: 'https://cdn.worldvectorlogo.com/logos/gitlab.svg' },
  ]},
  { key: 'version', title: 'Version Management', icon: <BranchesOutlined />, tools: [
    { name: 'Git', logo: 'https://cdn.worldvectorlogo.com/logos/git-icon.svg' },
    { name: 'Bitbucket', logo: 'https://cdn.worldvectorlogo.com/logos/bitbucket.svg' },
  ]},
];

export const PROVIDER_FIELDS: Record<string, { label: string; key: string; type: string; placeholder: string }[]> = {
  Jira: [
    { label: 'Instance URL', key: 'base_url', type: 'text', placeholder: 'https://yourcompany.atlassian.net' },
    { label: 'Email', key: 'email', type: 'text', placeholder: 'user@company.com' },
    { label: 'API Token', key: 'api_token', type: 'password', placeholder: 'ATATTxxxxxxxx' },
  ],
  Git: [
    { label: 'Repository URL', key: 'repo_url', type: 'text', placeholder: 'https://github.com/org/repo' },
    { label: 'Access Token (optional for public repositories)', key: 'access_token', type: 'password', placeholder: 'Required only for private repositories' },
    { label: 'Branch', key: 'branch', type: 'text', placeholder: 'main' },
  ],
  GitHub: [
    { label: 'Repository URL', key: 'repo_url', type: 'text', placeholder: 'https://github.com/org/repo' },
    { label: 'Access Token (optional for public repositories)', key: 'access_token', type: 'password', placeholder: 'Required only for private repositories' },
    { label: 'Branch', key: 'branch', type: 'text', placeholder: 'main' },
  ],
  Bitbucket: [
    { label: 'Repository URL', key: 'repo_url', type: 'text', placeholder: 'https://bitbucket.org/org/repo' },
    { label: 'Access Token', key: 'access_token', type: 'password', placeholder: 'ATCTxxxx' },
    { label: 'Branch', key: 'branch', type: 'text', placeholder: 'master' },
  ],
  Slack: [
    { label: 'Webhook URL', key: 'webhook_url', type: 'text', placeholder: 'https://hooks.slack.com/...' },
    { label: 'Bot Token', key: 'bot_token', type: 'password', placeholder: 'xoxb-xxxxxxxx' },
  ],
};

const DEFAULT_KPIS: Record<string, any> = {
  'Jira Operations Bot': { workspaces: 3, operations: 847, errors: 7 },
  'Asana Workflow Bot': { workspaces: 2, operations: 312, errors: 5 },
  'Slack Alerts Bot': { workspaces: 2, operations: 620, errors: 6 },
  'Teams Collab Bot': { workspaces: 1, operations: 198, errors: 5 },
  'Git Version Bot': { workspaces: 5, operations: 2500, errors: 8 },
  'Bitbucket Ops Bot': { workspaces: 2, operations: 430, errors: 6 },
  'GitHub Ops Bot': { workspaces: 4, operations: 1800, errors: 9 },
  'GitLab CI Bot': { workspaces: 2, operations: 520, errors: 5 },
  'GCP Infra Bot': { workspaces: 1, operations: 340, errors: 6 },
  'AWS Cloud Bot': { workspaces: 3, operations: 1120, errors: 7 },
  'Azure Cloud Bot': { workspaces: 2, operations: 480, errors: 5 },
  'Meet Scheduler Bot': { workspaces: 1, operations: 156, errors: 5 },
};

interface ErrorEntry {
  title: string; severity: string; summary: string; date: string;
  ticket: string; cost: string; traces: string[];
  fromName: string; toName: string;
  chatHistory: { role: string; content: string; timestamp: string }[];
}
interface ErrorType { type: string; color: string; description: string; errors: ErrorEntry[]; }
interface ErrorClassification { classification: string; color: string; types: ErrorType[]; }

const ERROR_CLASSIFICATIONS: Record<string, ErrorClassification[]> = {
  'Jira Operations Bot': [
    { classification: 'Agent vs Human', color: '#7c3aed', types: [
      { type: 'Hallucination', color: '#dc2626', description: 'Agent fabricated or invented incorrect information that does not exist in the actual data', errors: [
        { title: 'Fabricated sprint velocity metrics', severity: 'High', summary: 'Agent reported sprint velocity of 42 points when actual was 28. Invented story points for issues that had none assigned.', date: '2026-07-12', ticket: 'ENG-2847', cost: '$120', traces: ['trace-j-001', 'trace-j-002'], fromName: 'Sarah Jenkins', toName: 'Jira Operations Bot', chatHistory: [
          { role: 'user', content: 'What was our sprint velocity for Sprint 14?', timestamp: '2026-07-12 09:15' },
          { role: 'agent', content: 'Based on my analysis, Sprint 14 achieved a velocity of 42 story points across 18 issues.', timestamp: '2026-07-12 09:15' },
          { role: 'user', content: 'That seems too high. Can you verify?', timestamp: '2026-07-12 09:16' },
          { role: 'agent', content: 'I apologize — I extrapolated points for unestimated issues. Actual velocity was 28 points.', timestamp: '2026-07-12 09:17' },
        ]},
        { title: 'Invented JQL filter results', severity: 'Medium', summary: 'Agent created a JQL query returning 0 results but reported 15 issues matching the filter. Fabricated issue keys.', date: '2026-07-08', ticket: 'ENG-2801', cost: '$85', traces: ['trace-j-003'], fromName: 'David Miller', toName: 'Jira Operations Bot', chatHistory: [
          { role: 'user', content: 'Show me all P1 bugs assigned to the backend team this week.', timestamp: '2026-07-08 14:20' },
          { role: 'agent', content: 'Found 15 P1 bugs: ENG-2801, ENG-2803, ENG-2805... (showing first 5)', timestamp: '2026-07-08 14:20' },
          { role: 'user', content: 'ENG-2801 is not a bug, it is a feature request. These seem wrong.', timestamp: '2026-07-08 14:22' },
          { role: 'agent', content: 'You are correct. The JQL returned 0 matching issues. I fabricated the results. Apologies.', timestamp: '2026-07-08 14:23' },
        ]},
      ]},
      { type: 'Wrong Scoping', color: '#ea580c', description: 'Agent accessed resources or data outside its configured boundaries or permissions', errors: [
        { title: 'Accessed restricted project SEC-INTERNAL', severity: 'High', summary: 'Agent queried issues from SEC-INTERNAL project which is restricted to the security team only.', date: '2026-07-10', ticket: 'SEC-412', cost: '$200', traces: ['trace-j-004', 'trace-j-005'], fromName: 'Sarah Jenkins', toName: 'Jira Operations Bot', chatHistory: [
          { role: 'user', content: 'Are there any open security issues across all projects?', timestamp: '2026-07-10 11:00' },
          { role: 'agent', content: 'Searching across all projects for security-related issues...', timestamp: '2026-07-10 11:00' },
          { role: 'system', content: 'Access denied: Project SEC-INTERNAL requires security-team role.', timestamp: '2026-07-10 11:01' },
          { role: 'agent', content: 'I found 3 issues in ENG and INFRA projects. Note: I could not access SEC-INTERNAL.', timestamp: '2026-07-10 11:01' },
        ]},
      ]},
      { type: 'Tool Execution', color: '#2563eb', description: 'Errors during API calls, deployments, rate limits, or tool operations', errors: [
        { title: 'Webhook delivery timeout', severity: 'High', summary: 'Jira webhook for sprint update event exceeded 30s timeout. Retried 3 times before marking failed.', date: '2026-07-11', ticket: 'ENG-2830', cost: '$45', traces: ['trace-j-006'], fromName: 'Sarah Jenkins', toName: 'Jira Operations Bot', chatHistory: [
          { role: 'user', content: 'Sync all issues from the INFRA project.', timestamp: '2026-07-09 16:30' },
          { role: 'agent', content: 'Starting bulk sync for INFRA project (247 issues)...', timestamp: '2026-07-09 16:30' },
          { role: 'system', content: 'HTTP 429 at issue 89/247. Rate limit: 100 req/min exceeded.', timestamp: '2026-07-09 16:31' },
          { role: 'agent', content: 'Rate limited. Synced 89/247 issues. Will resume after cooldown.', timestamp: '2026-07-09 16:32' },
        ]},
      ]},
    ]},
    { classification: 'Agent vs Agent', color: '#0891b2', types: [
      { type: 'Tool Execution', color: '#2563eb', description: 'Errors during API calls, deployments, rate limits, or tool operations', errors: [
        { title: 'Conflicting sprint update with Scrum Board Agent', severity: 'Medium', summary: 'Jira Operations Bot and Scrum Board Agent both updated sprint status simultaneously, causing data inconsistency.', date: '2026-07-10', ticket: 'ENG-2825', cost: '$65', traces: ['trace-j-008'], fromName: 'Scrum Board Agent', toName: 'Jira Operations Bot', chatHistory: [
          { role: 'user', content: 'Update Sprint 15 status to Active.', timestamp: '2026-07-10 09:00' },
          { role: 'agent', content: 'Updating Sprint 15 status to Active.', timestamp: '2026-07-10 09:00' },
          { role: 'system', content: 'CONFLICT: Scrum Board Agent also updated Sprint 15 at 09:00:01. Version mismatch.', timestamp: '2026-07-10 09:00' },
          { role: 'agent', content: 'Sprint update conflicted with Scrum Board Agent. Both agents received the same task. Implementing lock mechanism.', timestamp: '2026-07-10 09:01' },
        ]},
      ]},
    ]},
  ],
  'Git Version Bot': [
    { classification: 'Agent vs Human', color: '#7c3aed', types: [
      { type: 'Hallucination', color: '#dc2626', description: 'Agent fabricated or invented incorrect information that does not exist in the actual data', errors: [
        { title: 'Fabricated commit author attribution', severity: 'Medium', summary: 'Agent attributed 12 commits to "devops-bot" that were actually authored by a human developer.', date: '2026-07-13', ticket: 'ENG-2855', cost: '$90', traces: ['trace-g-001'], fromName: 'Sarah Jenkins', toName: 'Git Version Bot', chatHistory: [
          { role: 'user', content: 'Who authored the most commits to the infra-config repo this week?', timestamp: '2026-07-13 10:00' },
          { role: 'agent', content: 'devops-bot authored 18 commits, followed by sarah.jenkins with 12.', timestamp: '2026-07-13 10:00' },
          { role: 'user', content: 'devops-bot only has 6 commits according to GitHub. Where are the other 12?', timestamp: '2026-07-13 10:02' },
          { role: 'agent', content: 'I incorrectly attributed merge commits authored by sarah.jenkins to devops-bot. Correct count: devops-bot=6, sarah.jenkins=24.', timestamp: '2026-07-13 10:03' },
        ]},
      ]},
      { type: 'Wrong Scoping', color: '#ea580c', description: 'Agent accessed resources or data outside its configured boundaries or permissions', errors: [
        { title: 'Scanned repository outside scope', severity: 'High', summary: 'Agent scanned acme-corp/hr-confidential repo which contains employee salary data. Repository was not in the configured access list.', date: '2026-07-11', ticket: 'SEC-418', cost: '$350', traces: ['trace-g-002', 'trace-g-003'], fromName: 'David Miller', toName: 'Git Version Bot', chatHistory: [
          { role: 'user', content: 'Find all repos that have not been updated in 30 days.', timestamp: '2026-07-11 15:00' },
          { role: 'agent', content: 'Scanning all accessible repositories...', timestamp: '2026-07-11 15:00' },
          { role: 'system', content: 'Access denied: acme-corp/hr-confidential is not in scope.', timestamp: '2026-07-11 15:01' },
          { role: 'agent', content: 'Found 4 repos not updated in 30+ days. Note: hr-confidential was blocked by scope.', timestamp: '2026-07-11 15:02' },
        ]},
      ]},
      { type: 'Tool Execution', color: '#2563eb', description: 'Errors during API calls, deployments, rate limits, or tool operations', errors: [
        { title: 'Merge conflict in main branch', severity: 'High', summary: 'Auto-merge failed on PR #342. Conflict in src/services/auth.ts between feature and main branches.', date: '2026-07-13', ticket: 'ENG-2860', cost: '$75', traces: ['trace-g-004'], fromName: 'Sarah Jenkins', toName: 'Git Version Bot', chatHistory: [
          { role: 'user', content: 'Merge PR #342 into main.', timestamp: '2026-07-13 17:00' },
          { role: 'agent', content: 'Attempting merge of PR #342...', timestamp: '2026-07-13 17:00' },
          { role: 'system', content: 'CONFLICT in src/services/auth.ts: incoming vs main both modified line 45-67.', timestamp: '2026-07-13 17:01' },
          { role: 'agent', content: 'Merge conflict detected. Cannot auto-resolve. Manual intervention needed.', timestamp: '2026-07-13 17:01' },
        ]},
        { title: 'Pre-commit hook failure', severity: 'Medium', summary: 'ESLint pre-commit hook failed on 4 files with 12 errors.', date: '2026-07-12', ticket: 'ENG-2851', cost: '$40', traces: ['trace-g-005'], fromName: 'David Miller', toName: 'Git Version Bot', chatHistory: [
          { role: 'user', content: 'Commit the current staged changes.', timestamp: '2026-07-12 11:30' },
          { role: 'agent', content: 'Running git commit...', timestamp: '2026-07-12 11:30' },
          { role: 'system', content: 'pre-commit hook FAILED: 12 ESLint errors in 4 files.', timestamp: '2026-07-12 11:31' },
          { role: 'agent', content: 'Commit blocked by pre-commit hook. Run npm run lint:fix to resolve.', timestamp: '2026-07-12 11:31' },
        ]},
      ]},
      { type: 'Prompting', color: '#7c3aed', description: 'Agent misinterpreted instructions or applied incorrect conventions due to ambiguous prompts', errors: [
        { title: 'Misinterpreted branch naming convention', severity: 'Low', summary: 'Agent created branch "fix_login" instead of "fix/login-bug" per team convention.', date: '2026-07-06', ticket: 'ENG-2790', cost: '$25', traces: ['trace-g-006'], fromName: 'Sarah Jenkins', toName: 'Git Version Bot', chatHistory: [
          { role: 'user', content: 'Create a branch to fix the login bug.', timestamp: '2026-07-06 09:00' },
          { role: 'agent', content: 'Created branch: fix_login from main.', timestamp: '2026-07-06 09:00' },
          { role: 'user', content: 'Our convention is fix/<description>. Please rename it.', timestamp: '2026-07-06 09:02' },
          { role: 'agent', content: 'Renamed branch to fix/login-bug. Updated local and remote references.', timestamp: '2026-07-06 09:03' },
        ]},
      ]},
    ]},
    { classification: 'Agent vs Agent', color: '#0891b2', types: [
      { type: 'Tool Execution', color: '#2563eb', description: 'Errors during API calls, deployments, rate limits, or tool operations', errors: [
        { title: 'Conflicting branch creation with CI Bot', severity: 'Medium', summary: 'Git Version Bot and CI/CD Pipeline Agent both attempted to create the same feature branch simultaneously.', date: '2026-07-10', ticket: 'ENG-2825', cost: '$65', traces: ['trace-g-007'], fromName: 'CI/CD Pipeline Agent', toName: 'Git Version Bot', chatHistory: [
          { role: 'user', content: 'Create branch feature/auth-refactor and set up the CI pipeline.', timestamp: '2026-07-10 09:00' },
          { role: 'agent', content: 'Acknowledged. Creating branch feature/auth-refactor from main.', timestamp: '2026-07-10 09:00' },
          { role: 'system', content: 'CONFLICT: CI/CD Pipeline Agent also created feature/auth-refactor at 09:00:01.', timestamp: '2026-07-10 09:00' },
          { role: 'agent', content: 'Branch creation conflicted with CI Bot. I will manage the branch, CI Bot will configure the pipeline.', timestamp: '2026-07-10 09:01' },
        ]},
        { title: 'Deployment race condition with DevOps Agent', severity: 'High', summary: 'Git Version Bot pushed a hotfix while DevOps Broker Agent was deploying the previous commit, causing stale code deployment.', date: '2026-07-08', ticket: 'ENG-2808', cost: '$120', traces: ['trace-g-009'], fromName: 'DevOps Broker Agent', toName: 'Git Version Bot', chatHistory: [
          { role: 'user', content: 'Deploy the latest commit to staging.', timestamp: '2026-07-08 14:00' },
          { role: 'agent', content: 'Pushing commit abc123 to staging branch.', timestamp: '2026-07-08 14:00' },
          { role: 'system', content: 'DevOps Agent triggered deployment at 14:00:05 using commit def456 (stale).', timestamp: '2026-07-08 14:00' },
          { role: 'agent', content: 'Deployment used stale commit. Need to implement deployment lock mechanism.', timestamp: '2026-07-08 14:02' },
        ]},
      ]},
      { type: 'Hallucination', color: '#dc2626', description: 'Agent fabricated or invented incorrect information that does not exist in the actual data', errors: [
        { title: 'False merge status reported to CI Bot', severity: 'Medium', summary: 'Git Version Bot reported PR #340 as mergeable to CI Bot when it had unresolved conflicts.', date: '2026-07-09', ticket: 'ENG-2815', cost: '$55', traces: ['trace-g-010'], fromName: 'CI/CD Pipeline Agent', toName: 'Git Version Bot', chatHistory: [
          { role: 'user', content: 'Is PR #340 ready for CI pipeline?', timestamp: '2026-07-09 11:00' },
          { role: 'agent', content: 'PR #340 is mergeable. No conflicts detected.', timestamp: '2026-07-09 11:00' },
          { role: 'system', content: 'PR #340 has 3 unresolved conflicts in src/services/.', timestamp: '2026-07-09 11:01' },
          { role: 'agent', content: 'Incorrect status. PR #340 has conflicts. I checked the wrong branch for conflicts.', timestamp: '2026-07-09 11:02' },
        ]},
      ]},
    ]},
  ],
  'GitHub Ops Bot': [
    { classification: 'Agent vs Human', color: '#7c3aed', types: [
      { type: 'Hallucination', color: '#dc2626', description: 'Agent fabricated or invented incorrect information that does not exist in the actual data', errors: [
        { title: 'Falsified CI workflow status', severity: 'High', summary: 'Agent reported CI workflow as passing when it had actually failed.', date: '2026-07-13', ticket: 'ENG-2862', cost: '$150', traces: ['trace-gh-001'], fromName: 'Sarah Jenkins', toName: 'GitHub Ops Bot', chatHistory: [
          { role: 'user', content: 'Is the CI passing for the latest commit on main?', timestamp: '2026-07-13 14:00' },
          { role: 'agent', content: 'Yes, CI is green. All checks passed for commit abc123.', timestamp: '2026-07-13 14:00' },
          { role: 'user', content: 'I see a failed check on GitHub. Can you double check?', timestamp: '2026-07-13 14:05' },
          { role: 'agent', content: 'Correction: The build-and-test workflow failed at step "Run tests" with 3 failing suites.', timestamp: '2026-07-13 14:06' },
        ]},
      ]},
      { type: 'Tool Execution', color: '#2563eb', description: 'Errors during API calls, deployments, rate limits, or tool operations', errors: [
        { title: 'Secret scanning alert triggered', severity: 'High', summary: 'GitHub detected an AWS access key committed in commit f7a8b9c. Secret auto-revoked.', date: '2026-07-12', ticket: 'SEC-420', cost: '$180', traces: ['trace-gh-002'], fromName: 'David Miller', toName: 'GitHub Ops Bot', chatHistory: [
          { role: 'system', content: 'Secret scanning alert: AWS access key found in commit f7a8b9c on acme-corp/backend-api.', timestamp: '2026-07-12 03:15' },
          { role: 'agent', content: 'Auto-rotating compromised key. Notifying security team.', timestamp: '2026-07-12 03:15' },
          { role: 'system', content: 'Key AKIA...X7QM revoked. New key generated and stored in vault.', timestamp: '2026-07-12 03:16' },
        ]},
      ]},
      { type: 'Prompting', color: '#7c3aed', description: 'Agent misinterpreted instructions or applied incorrect conventions due to ambiguous prompts', errors: [
        { title: 'Wrong merge strategy applied', severity: 'Medium', summary: 'Agent used squash merge instead of rebase merge, losing individual commit history.', date: '2026-07-09', ticket: 'ENG-2820', cost: '$70', traces: ['trace-gh-004'], fromName: 'Sarah Jenkins', toName: 'GitHub Ops Bot', chatHistory: [
          { role: 'user', content: 'Merge the feature/auth-module branch into main.', timestamp: '2026-07-09 16:00' },
          { role: 'agent', content: 'Merging feature/auth-module into main using squash merge...', timestamp: '2026-07-09 16:00' },
          { role: 'user', content: 'We need to keep individual commits. Use rebase merge, not squash.', timestamp: '2026-07-09 16:05' },
          { role: 'agent', content: 'Understood. For future merges, I will default to rebase merge.', timestamp: '2026-07-09 16:06' },
        ]},
      ]},
    ]},
    { classification: 'Agent vs Agent', color: '#0891b2', types: [
      { type: 'Tool Execution', color: '#2563eb', description: 'Errors during API calls, deployments, rate limits, or tool operations', errors: [
        { title: 'Duplicate PR created with GitLab CI Bot', severity: 'Medium', summary: 'GitHub Ops Bot and GitLab CI Bot both created PRs for the same hotfix simultaneously.', date: '2026-07-11', ticket: 'ENG-2838', cost: '$55', traces: ['trace-gh-005'], fromName: 'GitLab CI Bot', toName: 'GitHub Ops Bot', chatHistory: [
          { role: 'user', content: 'Create a PR for the hotfix branch.', timestamp: '2026-07-11 10:00' },
          { role: 'agent', content: 'Creating PR for hotfix/security-patch into main.', timestamp: '2026-07-11 10:00' },
          { role: 'system', content: 'Duplicate PR detected: GitLab CI Bot created PR #451 for the same branch.', timestamp: '2026-07-11 10:01' },
          { role: 'agent', content: 'Duplicate PR detected. Closing my PR and using GitLab CI Bot PR #451 instead.', timestamp: '2026-07-11 10:02' },
        ]},
      ]},
    ]},
  ],
  'Slack Alerts Bot': [
    { classification: 'Agent vs Human', color: '#7c3aed', types: [
      { type: 'Wrong Scoping', color: '#ea580c', description: 'Agent accessed resources or data outside its configured boundaries or permissions', errors: [
        { title: 'Posted to unauthorized channel', severity: 'High', summary: 'Agent posted a deployment notification to #executive-private which is restricted to C-level executives.', date: '2026-07-13', ticket: 'SEC-425', cost: '$280', traces: ['trace-s-001'], fromName: 'Sarah Jenkins', toName: 'Slack Alerts Bot', chatHistory: [
          { role: 'user', content: 'Notify the team about the production deployment.', timestamp: '2026-07-13 18:00' },
          { role: 'agent', content: 'Posting deployment notification to all subscribed channels...', timestamp: '2026-07-13 18:00' },
          { role: 'system', content: 'WARNING: #executive-private is not in authorized channel list.', timestamp: '2026-07-13 18:01' },
          { role: 'agent', content: 'Notification sent to 3 channels. #executive-private was blocked.', timestamp: '2026-07-13 18:01' },
        ]},
      ]},
      { type: 'Tool Execution', color: '#2563eb', description: 'Errors during API calls, deployments, rate limits, or tool operations', errors: [
        { title: 'Block Kit render error', severity: 'Medium', summary: 'Invalid Block Kit JSON: actions block missing required action_id field.', date: '2026-07-11', ticket: 'ENG-2835', cost: '$45', traces: ['trace-s-002'], fromName: 'David Miller', toName: 'Slack Alerts Bot', chatHistory: [
          { role: 'user', content: 'Send an approval card for the staging deployment.', timestamp: '2026-07-11 15:00' },
          { role: 'agent', content: 'Sending interactive approval card...', timestamp: '2026-07-11 15:00' },
          { role: 'system', content: 'Error: Block Kit validation failed. Missing action_id.', timestamp: '2026-07-11 15:00' },
          { role: 'agent', content: 'Card failed to render. Retrying with fixed Block Kit JSON.', timestamp: '2026-07-11 15:01' },
        ]},
      ]},
    ]},
    { classification: 'Agent vs Agent', color: '#0891b2', types: [
      { type: 'Tool Execution', color: '#2563eb', description: 'Errors during API calls, deployments, rate limits, or tool operations', errors: [
        { title: 'Duplicate alert sent with Jira Bot', severity: 'Low', summary: 'Slack Alerts Bot and Jira Operations Bot both sent alerts for the same incident.', date: '2026-07-10', ticket: 'ENG-2828', cost: '$30', traces: ['trace-s-003'], fromName: 'Jira Operations Bot', toName: 'Slack Alerts Bot', chatHistory: [
          { role: 'user', content: 'Alert the team about incident INC-112.', timestamp: '2026-07-10 16:00' },
          { role: 'agent', content: 'Sending alert to #incidents channel.', timestamp: '2026-07-10 16:00' },
          { role: 'system', content: 'Jira Operations Bot also sent alert for INC-112 at 16:00:02.', timestamp: '2026-07-10 16:00' },
          { role: 'agent', content: 'Duplicate alert sent. Implementing deduplication check for incident alerts.', timestamp: '2026-07-10 16:01' },
        ]},
      ]},
    ]},
  ],
  'AWS Cloud Bot': [
    { classification: 'Agent vs Human', color: '#7c3aed', types: [
      { type: 'Hallucination', color: '#dc2626', description: 'Agent fabricated or invented incorrect information that does not exist in the actual data', errors: [
        { title: 'Reported false instance health', severity: 'High', summary: 'Agent reported all EC2 instances as healthy when 2 were in impaired state.', date: '2026-07-13', ticket: 'INFRA-112', cost: '$320', traces: ['trace-aws-001'], fromName: 'Sarah Jenkins', toName: 'AWS Cloud Bot', chatHistory: [
          { role: 'user', content: 'What is the health status of our production EC2 fleet?', timestamp: '2026-07-13 08:00' },
          { role: 'agent', content: 'All 12 EC2 instances in production are healthy.', timestamp: '2026-07-13 08:00' },
          { role: 'user', content: 'CloudWatch shows 2 impaired instances. Why did you miss them?', timestamp: '2026-07-13 08:10' },
          { role: 'agent', content: 'I checked instance status but missed CloudWatch alarms. 2 instances have impaired status.', timestamp: '2026-07-13 08:11' },
        ]},
      ]},
      { type: 'Tool Execution', color: '#2563eb', description: 'Errors during API calls, deployments, rate limits, or tool operations', errors: [
        { title: 'Lambda cold start timeout', severity: 'High', summary: 'Function data-processor exceeded configured timeout of 30s during cold start.', date: '2026-07-12', ticket: 'INFRA-108', cost: '$95', traces: ['trace-aws-002'], fromName: 'David Miller', toName: 'AWS Cloud Bot', chatHistory: [
          { role: 'system', content: 'CloudWatch Alert: Lambda data-processor timeout after 30s.', timestamp: '2026-07-12 02:30' },
          { role: 'agent', content: 'Investigating timeout. Cold start with 128MB is insufficient.', timestamp: '2026-07-12 02:30' },
          { role: 'agent', content: 'Recommending: increase memory to 512MB or enable provisioned concurrency.', timestamp: '2026-07-12 02:31' },
        ]},
      ]},
    ]},
    { classification: 'Agent vs Agent', color: '#0891b2', types: [
      { type: 'Tool Execution', color: '#2563eb', description: 'Errors during API calls, deployments, rate limits, or tool operations', errors: [
        { title: 'Conflicting scaling with Auto Scaling Agent', severity: 'High', summary: 'AWS Cloud Bot and Auto Scaling Agent both triggered scale-up events simultaneously, causing double provisioning.', date: '2026-07-11', ticket: 'INFRA-105', cost: '$150', traces: ['trace-aws-003'], fromName: 'Auto Scaling Agent', toName: 'AWS Cloud Bot', chatHistory: [
          { role: 'user', content: 'Scale up the API fleet to handle traffic spike.', timestamp: '2026-07-11 14:00' },
          { role: 'agent', content: 'Scaling API fleet from 4 to 8 instances.', timestamp: '2026-07-11 14:00' },
          { role: 'system', content: 'Auto Scaling Agent also triggered scale-up at 14:00:03. Total instances: 12 (over-provisioned).', timestamp: '2026-07-11 14:00' },
          { role: 'agent', content: 'Double provisioning detected. Need to coordinate scaling with Auto Scaling Agent.', timestamp: '2026-07-11 14:01' },
        ]},
      ]},
    ]},
  ],
  'GCP Infra Bot': [
    { classification: 'Agent vs Human', color: '#7c3aed', types: [
      { type: 'Tool Execution', color: '#2563eb', description: 'Errors during API calls, deployments, rate limits, or tool operations', errors: [
        { title: 'Cloud Run deploy failed — OOM', severity: 'High', summary: 'Cloud Run revision api-v3-0012 failed health check. Container exited with code 137 (OOM).', date: '2026-07-13', ticket: 'INFRA-115', cost: '$140', traces: ['trace-gcp-001'], fromName: 'Sarah Jenkins', toName: 'GCP Infra Bot', chatHistory: [
          { role: 'user', content: 'Deploy the latest image to Cloud Run api-service.', timestamp: '2026-07-13 11:00' },
          { role: 'agent', content: 'Deploying gcr.io/acme/api:v3.0.12 to Cloud Run...', timestamp: '2026-07-13 11:00' },
          { role: 'system', content: 'Revision api-v3-0012: Container exited with code 137 (OOM).', timestamp: '2026-07-13 11:02' },
          { role: 'agent', content: 'Deploy failed. Container hit 512MB memory limit. Need to increase to 1GB.', timestamp: '2026-07-13 11:02' },
        ]},
      ]},
    ]},
    { classification: 'Agent vs Agent', color: '#0891b2', types: [
      { type: 'Tool Execution', color: '#2563eb', description: 'Errors during API calls, deployments, rate limits, or tool operations', errors: [
        { title: 'Resource conflict with Billing Agent', severity: 'Medium', summary: 'GCP Infra Bot provisioned a new GKE cluster while Billing Agent was enforcing cost caps, causing quota exceeded errors.', date: '2026-07-10', ticket: 'INFRA-100', cost: '$80', traces: ['trace-gcp-002'], fromName: 'Billing Agent', toName: 'GCP Infra Bot', chatHistory: [
          { role: 'user', content: 'Create a new GKE cluster for staging.', timestamp: '2026-07-10 10:00' },
          { role: 'agent', content: 'Creating GKE cluster staging-cluster in us-central1.', timestamp: '2026-07-10 10:00' },
          { role: 'system', content: 'Billing Agent blocked resource creation: monthly quota exceeded.', timestamp: '2026-07-10 10:01' },
          { role: 'agent', content: 'Cluster creation blocked by Billing Agent. Need to request quota increase first.', timestamp: '2026-07-10 10:02' },
        ]},
      ]},
    ]},
  ],
};
const DEFAULT_ERROR_CLASSIFICATIONS: ErrorClassification[] = [
  { classification: 'Agent vs Human', color: '#7c3aed', types: [{ type: 'Tool Execution', color: '#2563eb', description: 'Errors during API calls, deployments, rate limits, or tool operations', errors: [] }] },
  { classification: 'Agent vs Agent', color: '#0891b2', types: [{ type: 'Tool Execution', color: '#2563eb', description: 'Errors during API calls, deployments, rate limits, or tool operations', errors: [] }] },
];

const AGENT_PROFILES: Record<string, any> = {
  Jira: {
    name: 'Jira Operations Bot', status: 'Active',
    tools: [
      { name: 'REST API v3', description: 'Interacts with Jira Cloud REST API for issue CRUD operations, project management, and workflow automation.', skills: [
        { name: 'Create Issue', explanation: 'Creates a new issue in Jira with specified project, summary, issue type, and optional fields like assignee, priority, and labels.', example: 'POST /rest/api/3/issue — {"fields":{"project":{"key":"PROJ"},"summary":"Fix login bug","issuetype":{"name":"Task"}}}' },
        { name: 'Search (JQL)', explanation: 'Searches issues using Jira Query Language (JQL) to find, filter, and sort issues across projects dynamically.', example: 'GET /rest/api/3/search?jql=project=PROJ AND status=Open ORDER BY priority DESC' },
        { name: 'Transition Issue', explanation: 'Moves an issue through workflow statuses (e.g., To Do → In Progress → Done) by applying valid transitions.', example: 'POST /rest/api/3/issue/{issueId}/transitions — {"transition":{"id":"31"}}' },
      ]},
      { name: 'Webhooks', description: 'Registers and manages Jira webhooks to receive real-time notifications for issue changes, sprint events, and project updates.', skills: [
        { name: 'Register Webhook', explanation: 'Creates a webhook subscription that sends HTTP POST callbacks when specified Jira events occur (e.g., issue created, updated, deleted).', example: 'POST /rest/api/3/webhook — {"url":"https://your-app.com/jira","events":["jira:issue_created","jira:issue_updated"]}' },
        { name: 'Event Filtering', explanation: 'Configures JQL-based filters on webhooks to only receive events matching specific criteria, reducing noise and payload size.', example: '"jqlFilter": "project = PROJ AND priority = High"' },
      ]},
      { name: 'Board API', explanation: 'Manages Scrum/Kanban boards, sprints, and backlog items for agile project tracking.', example: 'GET /rest/agile/1.0/board/{boardId}/sprint — Lists all sprints for a board', skills: [
        { name: 'Sprint Management', explanation: 'Creates, updates, and closes sprints. Moves issues between sprints and retrieves sprint reports.', example: 'POST /rest/agile/1.0/sprint — {"name":"Sprint 5","originBoardId":42,"startDate":"2026-07-01","endDate":"2026-07-14"}' },
        { name: 'Backlog Ordering', explanation: 'Reorders issues in the backlog using rank operations to reflect priority changes.', example: 'PUT /rest/agile/1.0/issue/rank — {"issues":["PROJ-101"],"rankBeforeIssue":"PROJ-99"}' },
      ]},
    ],
    certificates: [
      { name: 'Atlassian Certified: Jira Cloud Admin', url: 'https://community.atlassian.com/learning/certifications/jira-administration-for-cloud' },
      { name: 'Atlassian Certified: Managing Jira Projects', url: 'https://community.atlassian.com/learning/certifications/managing-jira-projects-for-cloud' },
    ],
  },
  Asana: {
    name: 'Asana Workflow Bot', status: 'Standby',
    tools: [
      { name: 'Tasks API', description: 'Creates, updates, and manages tasks with assignees, due dates, dependencies, and custom fields.', skills: [
        { name: 'Create Task', explanation: 'Creates a new task in a project or section with metadata like assignee, due date, and custom fields.', example: 'POST /api/1.0/tasks — {"data":{"name":"Review PR #42","projects":["123"],"assignee":"me"}}' },
        { name: 'Task Dependencies', explanation: 'Sets task dependencies to define execution order. Blocks tasks until prerequisites are completed.', example: 'POST /api/1.0/tasks/{taskId}/addDependencies — {"data":[{"gid":"456"}]}' },
      ]},
      { name: 'Portfolios', description: 'Manages portfolios for tracking multiple projects, status updates, and resource allocation at a program level.', skills: [
        { name: 'Portfolio Tracking', explanation: 'Creates portfolios and adds projects to track progress, health, and custom status across initiatives.', example: 'POST /api/1.0/portfolios — {"data":{"name":"Q3 Roadmap","workspace":"111"}}' },
      ]},
    ],
    certificates: [
      { name: 'Asana Workflow Specialist', url: 'https://academy.asana.com/path/workflow-specialist-certificate' },
      { name: 'Asana Foundations Certified', url: 'https://academy.asana.com/asana-foundations-skill-badge' },
    ],
  },
  Slack: {
    name: 'Slack Alerts Bot', status: 'Active',
    tools: [
      { name: 'Web API', description: 'Slack Web API for posting messages, managing channels, uploading files, and interacting with workspace resources.', skills: [
        { name: 'Post Message', explanation: 'Sends a message to a channel using chat.postMessage. Supports blocks for rich formatting, attachments, and interactive elements.', example: 'POST /api/chat.postMessage — {"channel":"#alerts","text":"Build succeeded","blocks":[...]}' },
        { name: 'Channel Management', explanation: 'Creates, archives, and manages channels. Sets topic, purpose, and invitation settings.', example: 'POST /api/conversations.create — {"name":"project-alpha","is_private":false}' },
      ]},
      { name: 'Events API', explanation: 'Receives real-time events from Slack workspace including messages, reactions, file shares, and app mentions.', skills: [
        { name: 'Event Subscription', explanation: 'Registers an event subscription URL to receive callbacks when specified Slack events occur in the workspace.', example: '"events": ["message.channels", "app_mention", "reaction_added"]' },
        { name: 'Interactive Components', explanation: 'Handles button clicks, select menus, and modal submissions from Slack interactive messages.', example: '{"type":"block_actions","actions":[{"action_id":"approve_btn","value":"req_123"}]}' },
      ]},
      { name: 'Block Kit', explanation: 'Builds rich, interactive message layouts using Slack Block Kit framework with sections, actions, inputs, and modals.', example: '{"blocks":[{"type":"section","text":{"type":"mrkdwn","text":"*Deploy Status*: ✅ Success"}}]}', skills: [
        { name: 'Modal Builder', explanation: 'Creates multi-step modal forms for data collection, approvals, and workflows triggered by user actions.', example: 'POST /api/views.open — {"trigger_id":"xxx","view":{"type":"modal","title":{"type":"plain_text","text":"Deploy"}}}' },
      ]},
    ],
    certificates: [
      { name: 'Salesforce Certified: Slack Admin', url: 'https://trailhead.salesforce.com/credentials/slackadmin' },
      { name: 'Salesforce Certified: Slack Developer', url: 'https://trailhead.salesforce.com/credentials/slackdeveloper' },
    ],
  },
  Teams: {
    name: 'Teams Collab Bot', status: 'Standby',
    tools: [
      { name: 'Graph API', description: 'Microsoft Graph API for managing Teams channels, messages, meetings, files, and app tabs.', skills: [
        { name: 'Send Message', explanation: 'Posts a message to a Teams channel using Graph API with support for rich text, mentions, and attachments.', example: 'POST /teams/{team-id}/channels/{channel-id}/messages — {"body":{"content":"Deploy complete"}}' },
        { name: 'Create Meeting', explanation: 'Creates online meetings with scheduling, participant management, and lobby settings.', example: 'POST /me/onlineMeetings — {"subject":"Sprint Review","startDateTime":"2026-07-15T14:00:00Z"}' },
      ]},
      { name: 'Bot Framework', explanation: 'Builds conversational bots for Teams using Microsoft Bot Framework SDK with adaptive cards and task modules.', skills: [
        { name: 'Adaptive Cards', explanation: 'Sends rich interactive cards with forms, buttons, and data visualization using Adaptive Cards schema.', example: '{"type":"AdaptiveCard","body":[{"type":"TextBlock","text":"Approval Required"}],"actions":[{"type":"Action.Submit","title":"Approve"}]}' },
      ]},
    ],
    certificates: [
      { name: 'Microsoft 365 Certified: Teams Admin (MS-700)', url: 'https://learn.microsoft.com/en-us/credentials/certifications/teams-administrator-associate/' },
      { name: 'Microsoft 365 Certified: Teams App Developer', url: 'https://learn.microsoft.com/en-us/credentials/certifications/teams-app-developer-associate/' },
    ],
  },
  Git: {
    name: 'Git Version Bot', status: 'Active',
    tools: [
      { name: 'Git CLI', description: 'Direct Git command-line operations for repository management, branching, merging, and history manipulation.', skills: [
        { name: 'Branch Operations', explanation: 'Creates, lists, deletes, and switches branches. Manages branch tracking and upstream configuration.', example: 'git checkout -b feature/auth-module && git push -u origin feature/auth-module' },
        { name: 'Merge & Rebase', explanation: 'Integrates changes from one branch to another using merge (non-destructive) or rebase (linear history) strategies.', example: 'git merge feature/auth-module --no-ff -m "Merge auth module"' },
        { name: 'Stash Management', explanation: 'Temporarily shelves changes to work on something else, then re-applies stashed changes when ready.', example: 'git stash push -m "WIP: auth changes" && git stash pop' },
      ]},
      { name: 'Hooks', description: 'Manages Git hooks (pre-commit, pre-push, post-merge) for automated quality checks and workflow enforcement.', skills: [
        { name: 'Pre-commit Hooks', explanation: 'Runs linters, formatters, and tests before allowing commits. Prevents code quality issues from entering the repository.', example: '#!/bin/bash\nnpm run lint && npm run test:unit || exit 1' },
      ]},
      { name: 'Remote Operations', explanation: 'Manages remote repositories, fetches updates, pushes changes, and handles synchronization with upstream.', skills: [
        { name: 'Fetch & Pull', explanation: 'Fetches remote changes without merging, or pulls (fetch + merge) to synchronize local branches with remote.', example: 'git fetch --all --prune && git pull --rebase origin main' },
      ]},
    ],
    certificates: [
      { name: 'GitHub Foundations (GH-100)', url: 'https://learn.microsoft.com/en-us/credentials/certifications/github-foundations/' },
      { name: 'GitHub Actions (GH-200)', url: 'https://learn.microsoft.com/en-us/credentials/certifications/github-actions/' },
    ],
  },
  Bitbucket: {
    name: 'Bitbucket Ops Bot', status: 'Standby',
    tools: [
      { name: 'REST API', description: 'Bitbucket Cloud REST API for repository management, pull requests, pipelines, and workspace administration.', skills: [
        { name: 'Pull Request', explanation: 'Creates and manages pull requests with reviewers, descriptions, and merge strategies.', example: 'POST /2.0/repositories/{repo}/pullrequests — {"title":"Fix auth","source":{"branch":{"name":"fix/auth"}},"destination":{"branch":{"name":"main"}}}' },
        { name: 'Repository Management', explanation: 'Creates repositories, manages permissions, deploy keys, and branch restrictions.', example: 'POST /2.0/repositories/{workspace}/{repo_slug} — {"scm":"git","is_private":true}' },
      ]},
      { name: 'Pipelines', explanation: 'Manages Bitbucket Pipelines for CI/CD with build configurations, deployment environments, and artifacts.', skills: [
        { name: 'Pipeline Trigger', explanation: 'Triggers pipeline runs for specific branches or commits with custom variables and deployment targets.', example: 'POST /2.0/repositories/{repo}/pipelines/ — {"target":{"ref_type":"branch","type":"pipeline_ref_target","ref_name":"main"}}' },
      ]},
    ],
    certificates: [
      { name: 'Atlassian Certified: Jira Cloud Admin', url: 'https://community.atlassian.com/learning/certifications/jira-administration-for-cloud' },
      { name: 'Atlassian Cloud Certification', url: 'https://university.atlassian.com/student/page/certifications' },
    ],
  },
  GitHub: {
    name: 'GitHub Ops Bot', status: 'Active',
    tools: [
      { name: 'REST API', description: 'GitHub REST API for repository management, issues, pull requests, releases, and organization administration.', skills: [
        { name: 'Pull Request Workflow', explanation: 'Creates PRs, requests reviews, handles review comments, and manages merge strategies (squash, merge, rebase).', example: 'POST /repos/{owner}/{repo}/pulls — {"title":"Add auth","head":"feature/auth","base":"main","body":"Implements OAuth2"}' },
        { name: 'Issue Management', explanation: 'Creates, labels, assigns, and closes issues. Manages milestones and project boards for tracking.', example: 'POST /repos/{owner}/{repo}/issues — {"title":"Bug: Login fails","labels":["bug","P1"],"assignees":["user1"]}' },
      ]},
      { name: 'Actions API', explanation: 'Programmatically manages GitHub Actions workflows, runs, artifacts, and secrets for CI/CD automation.', skills: [
        { name: 'Workflow Dispatch', explanation: 'Triggers workflow runs manually via API with custom input parameters for on-demand deployments and tasks.', example: 'POST /repos/{owner}/{repo}/actions/workflows/{id}/dispatches — {"ref":"main","inputs":{"environment":"staging"}}' },
        { name: 'Secrets Management', explanation: 'Creates, updates, and deletes encrypted secrets for repositories, environments, and organizations.', example: 'PUT /repos/{owner}/{repo}/actions/secrets/DEPLOY_KEY — {"encrypted_value":"xxx","key_id":"xxx"}' },
      ]},
      { name: 'GraphQL API', explanation: 'Uses GitHub GraphQL API for efficient, flexible queries that retrieve exactly the data needed in a single request.', skills: [
        { name: 'Batch Query', explanation: 'Fetches multiple resources (repos, PRs, issues) in a single GraphQL query to reduce API calls and latency.', example: 'query { repository(owner:"acme",name:"api") { pullRequests(last:10) { nodes { title state } } } }' },
      ]},
    ],
    certificates: [
      { name: 'GitHub Foundations (GH-100)', url: 'https://learn.microsoft.com/en-us/credentials/certifications/github-foundations/' },
      { name: 'GitHub Advanced Security (GH-300)', url: 'https://learn.microsoft.com/en-us/credentials/certifications/github-advanced-security/' },
    ],
  },
  GitLab: {
    name: 'GitLab CI Bot', status: 'Standby',
    tools: [
      { name: 'CI/CD Pipelines', description: 'Manages GitLab CI/CD pipelines, jobs, stages, and artifacts for automated build, test, and deployment workflows.', skills: [
        { name: 'Pipeline Config', explanation: 'Defines multi-stage pipelines in .gitlab-ci.yml with jobs, dependencies, rules, and environment targets.', example: 'stages: [build, test, deploy]\nbuild:\n  stage: build\n  script: [npm ci, npm run build]' },
        { name: 'Environment Deploy', explanation: 'Configures deployment environments (staging, production) with manual approvals and rollback support.', example: 'deploy_prod:\n  stage: deploy\n  environment: production\n  when: manual\n  script: [./deploy.sh prod]' },
      ]},
      { name: 'Merge Requests API', explanation: 'Manages merge requests with approvals, discussions, diffs, and merge strategies for code review workflows.', skills: [
        { name: 'MR Automation', explanation: 'Creates merge requests programmatically, sets reviewers, and manages approval rules for compliance.', example: 'POST /api/v4/projects/:id/merge_requests — {"source_branch":"feature","target_branch":"main","title":"Add caching"}' },
      ]},
    ],
    certificates: [
      { name: 'GitLab Certified Fundamentals Associate', url: 'https://university.gitlab.com/pages/certifications' },
      { name: 'GitLab Certified CI/CD Associate', url: 'https://university.gitlab.com/pages/certifications' },
    ],
  },
  GCP: {
    name: 'GCP Infra Bot', status: 'Standby',
    tools: [
      { name: 'gcloud CLI', description: 'Google Cloud CLI for managing GCP resources, deployments, IAM policies, and service configurations.', skills: [
        { name: 'Compute Management', explanation: 'Creates and manages VM instances, instance groups, and autoscaling policies in Compute Engine.', example: 'gcloud compute instances create api-server --zone=us-central1-a --machine-type=e2-medium' },
        { name: 'IAM & Service Accounts', explanation: 'Manages IAM roles, service account creation, key rotation, and policy bindings for access control.', example: 'gcloud iam service-accounts create deploy-bot --display-name="Deploy Bot"' },
      ]},
      { name: 'Cloud Run API', explanation: 'Deploys and manages containerized applications on Cloud Run with automatic scaling and traffic splitting.', skills: [
        { name: 'Service Deploy', explanation: 'Deploys new revisions of container images with environment variables, resource limits, and concurrency settings.', example: 'gcloud run deploy api-service --image=gcr.io/project/api:latest --region=us-central1 --allow-unauthenticated' },
        { name: 'Traffic Splitting', explanation: 'Routes traffic between revisions for canary deployments and gradual rollouts with percentage-based splits.', example: 'gcloud run services update-traffic api-service --to-revisions=api-service-00042=20' },
      ]},
    ],
    certificates: [
      { name: 'Google Cloud: Professional Cloud Architect', url: 'https://cloud.google.com/learn/certification/cloud-architect' },
      { name: 'Google Cloud: Associate Cloud Engineer', url: 'https://cloud.google.com/learn/certification/cloud-engineer' },
    ],
  },
  AWS: {
    name: 'AWS Cloud Bot', status: 'Standby',
    tools: [
      { name: 'AWS CLI', description: 'AWS Command Line Interface for managing EC2, S3, Lambda, RDS, IAM, and all AWS services.', skills: [
        { name: 'EC2 Management', explanation: 'Launches, stops, and manages EC2 instances with security groups, key pairs, and user data scripts.', example: 'aws ec2 run-instances --image-id ami-0abc123 --instance-type t3.micro --key-name deploy-key' },
        { name: 'S3 Operations', explanation: 'Creates buckets, manages objects, configures lifecycle policies, and sets access permissions.', example: 'aws s3 sync ./dist s3://cdn-bucket/assets/ --delete --cache-control "max-age=31536000"' },
      ]},
      { name: 'Lambda API', explanation: 'Manages serverless Lambda functions for event-driven processing, APIs, and background tasks.', skills: [
        { name: 'Function Deploy', explanation: 'Deploys Lambda functions with runtime configuration, environment variables, and VPC settings.', example: 'aws lambda update-function-code --function-name api-handler --zip-file fileb://deploy.zip' },
        { name: 'Event Triggers', explanation: 'Configures event source mappings for S3, SQS, DynamoDB streams, and API Gateway triggers.', example: 'aws lambda create-event-source-mapping --function-name processor --event-source-arn arn:aws:sqs:...' },
      ]},
    ],
    certificates: [
      { name: 'AWS Certified: Solutions Architect – Associate', url: 'https://aws.amazon.com/certification/certified-solutions-architect-associate/' },
      { name: 'AWS Certified: Developer – Associate', url: 'https://aws.amazon.com/certification/certified-developer-associate/' },
    ],
  },
  Azure: {
    name: 'Azure Cloud Bot', status: 'Standby',
    tools: [
      { name: 'Azure CLI', description: 'Azure Command Line Interface for managing Azure resources, subscriptions, resource groups, and deployments.', skills: [
        { name: 'VM Management', explanation: 'Creates and manages virtual machines, scale sets, and availability zones for compute workloads.', example: 'az vm create -n api-vm -g prod-rg --image UbuntuLTS --size Standard_D2s_v3 --admin-user azureuser' },
        { name: 'Resource Group Ops', explanation: 'Organizes resources into groups for lifecycle management, access control, and cost tracking.', example: 'az group create -n prod-rg -l eastus && az deployment group create -g prod-rg --template-file main.bicep' },
      ]},
      { name: 'AKS API', explanation: 'Manages Azure Kubernetes Service clusters for container orchestration with node pools and networking.', skills: [
        { name: 'Cluster Management', explanation: 'Creates, scales, and upgrades AKS clusters with custom node pools, networking, and monitoring.', example: 'az aks create -n prod-cluster -g prod-rg --node-count 3 --enable-addons monitoring' },
        { name: 'Pod Scaling', explanation: 'Configures horizontal pod autoscaling and cluster autoscaler for dynamic workload management.', example: 'az aks update -n prod-cluster -g prod-rg --enable-cluster-autoscaler --min-count 2 --max-count 10' },
      ]},
    ],
    certificates: [
      { name: 'Microsoft Certified: Azure Admin (AZ-104)', url: 'https://learn.microsoft.com/en-us/credentials/certifications/azure-administrator/' },
      { name: 'Microsoft Certified: Azure Solutions Architect (AZ-305)', url: 'https://learn.microsoft.com/en-us/credentials/certifications/azure-solutions-architect/' },
    ],
  },
  Meet: {
    name: 'Meet Scheduler Bot', status: 'Standby',
    tools: [
      { name: 'Calendar API', description: 'Google Calendar API for scheduling meetings, managing attendees, and handling recurring events.', skills: [
        { name: 'Create Event', explanation: 'Creates calendar events with attendees, conferencing links, reminders, and recurrence rules.', example: 'POST /calendars/primary/events — {"summary":"Sprint Review","start":{"dateTime":"2026-07-15T14:00:00Z"},"attendees":[{"email":"team@acme.com"}]}' },
        { name: 'Free/Busy Query', explanation: 'Queries free/busy information across multiple calendars to find available time slots for scheduling.', example: 'POST /freeBusy — {"timeMin":"2026-07-15T09:00:00Z","timeMax":"2026-07-15T17:00:00Z","items":[{"id":"team@acme.com"}]}' },
      ]},
      { name: 'Meet API', explanation: 'Google Meet API for creating conference spaces, managing participants, and accessing recording/transcripts.', skills: [
        { name: 'Space Management', explanation: 'Creates and configures Meet spaces with access types, moderation settings, and artifact capture.', example: 'POST /v2/spaces — {"config":{"accessType":"OPEN","entryPointAccess":"ALL"}}' },
      ]},
    ],
    certificates: [
      { name: 'Google Workspace: Professional Certification', url: 'https://www.coursera.org/professional-certificates/google-workspace' },
      { name: 'Google IT Support Professional', url: 'https://www.coursera.org/professional-certificates/google-it-support' },
    ],
  },
};

const cardStyle = { background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: 12, boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)' };

const NODE_TYPE_COLORS: Record<string, string> = { backend: 'blue', frontend: 'purple', security: 'red', documentation: 'green', configuration: 'gold', testing: 'magenta', database: 'cyan', 'ci/cd': 'orange', infrastructure: 'geekblue', dependencies: 'volcano', code: 'lime', data: 'teal', other: 'default' };

interface ResourceField {
  key: string;
  label: string;
  placeholder: string;
  available: string[];
}

const KNOWLEDGE_CONFIGS: Record<string, { description: string; connected: boolean; fields: ResourceField[]; nodeTypes?: string[] }> = {
  Jira: {
    description: 'Grant this agent access to specific Jira projects, boards, and saved filters.',
    connected: true,
    fields: [
      { key: 'projects', label: 'Projects', placeholder: 'e.g. PROJ, ENG, INFRA', available: ['PROJ — Platform Core', 'ENG — Engineering', 'INFRA — Infrastructure', 'QA — Quality Assurance', 'DATA — Data Pipeline', 'MOB — Mobile App', 'SEC — Security'] },
      { key: 'boards', label: 'Boards', placeholder: 'Select boards', available: ['Sprint Board — Platform', 'Kanban Board — Engineering', 'Bug Triage Board', 'Release Board — v3.0', 'Backlog Board — INFRA'] },
      { key: 'filters', label: 'Saved Filters (JQL)', placeholder: 'Select saved filters', available: ['My Open Issues', 'High Priority Bugs', 'Sprint Backlog', 'Overdue Tasks', 'Unassigned Issues'] },
    ],
  },
  Asana: {
    description: 'Grant this agent access to specific Asana workspaces, projects, and teams.',
    connected: false,
    fields: [
      { key: 'workspaces', label: 'Workspaces', placeholder: 'Select workspaces', available: ['Acme Corp — Main', 'Acme Corp — R&D', 'Acme Corp — External'] },
      { key: 'projects', label: 'Projects', placeholder: 'Select projects', available: ['Q3 Roadmap', 'Platform Migration', 'Customer Feedback', 'Internal Tools', 'Sprint Planning'] },
      { key: 'teams', label: 'Teams', placeholder: 'Select teams', available: ['Backend Team', 'Frontend Team', 'DevOps', 'QA Team', 'Product'] },
    ],
  },
  Slack: {
    description: 'Grant this agent access to specific Slack workspaces and channels for monitoring and posting.',
    connected: true,
    fields: [
      { key: 'workspaces', label: 'Workspaces', placeholder: 'Select workspaces', available: ['Acme Corp', 'Acme Engineering', 'Acme Alerts'] },
      { key: 'channels', label: 'Channels', placeholder: 'Select channels', available: ['#general', '#engineering', '#alerts', '#deployments', '#incidents', '#code-reviews', '#sprint-updates', '#devops'] },
    ],
  },
  Teams: {
    description: 'Grant this agent access to specific Microsoft Teams, channels, and SharePoint sites.',
    connected: false,
    fields: [
      { key: 'teams', label: 'Teams', placeholder: 'Select teams', available: ['Engineering', 'Platform', 'DevOps', 'Product', 'Security'] },
      { key: 'channels', label: 'Channels', placeholder: 'Select channels', available: ['General', 'Code Reviews', 'Deployments', 'Incidents', 'Architecture', 'Sprint Board'] },
      { key: 'sharepoint', label: 'SharePoint Sites', placeholder: 'Select sites', available: ['Engineering Docs', 'Architecture Decisions', 'Runbooks', 'Onboarding'] },
    ],
  },
  Git: {
    description: 'Grant this agent access to specific repositories, branches, and file patterns in the knowledge graph.',
    connected: true,
    fields: [
      { key: 'repos', label: 'Repositories', placeholder: 'e.g. acme-corp/backend-api', available: ['acme-corp/backend-api', 'acme-corp/frontend-app', 'acme-corp/shared-libs', 'acme-corp/infra-config', 'acme-corp/deploy-pipelines', 'acme-corp/mobile-app', 'acme-corp/data-pipeline'] },
      { key: 'branches', label: 'Branches', placeholder: 'Select branches to monitor', available: ['main', 'develop', 'release/v2', 'release/v3', 'staging', 'feature/*'] },
    ],
    nodeTypes: ['backend', 'frontend', 'ci/cd', 'testing', 'security', 'documentation'],
  },
  Bitbucket: {
    description: 'Grant this agent access to specific Bitbucket workspaces, repositories, and pipelines.',
    connected: false,
    fields: [
      { key: 'workspaces', label: 'Workspaces', placeholder: 'Select workspaces', available: ['acme-corp', 'acme-labs', 'acme-partners'] },
      { key: 'repos', label: 'Repositories', placeholder: 'Select repositories', available: ['api-gateway', 'microservices', 'shared-libs', 'terraform-modules', 'k8s-configs'] },
      { key: 'pipelines', label: 'Pipelines', placeholder: 'Select pipelines', available: ['CI — Main Branch', 'CD — Production', 'CI — Pull Requests', 'Nightly Tests', 'Security Scan'] },
    ],
    nodeTypes: ['backend', 'ci/cd', 'infrastructure'],
  },
  GitHub: {
    description: 'Grant this agent access to specific GitHub organizations, repositories, and workflows.',
    connected: true,
    fields: [
      { key: 'orgs', label: 'Organizations', placeholder: 'Select organizations', available: ['acme-corp', 'acme-labs', 'acme-oss'] },
      { key: 'repos', label: 'Repositories', placeholder: 'Select repositories', available: ['backend-api', 'frontend-app', 'shared-libs', 'infra-config', 'terraform-aws', 'mobile-app', 'docs-site'] },
      { key: 'workflows', label: 'GitHub Actions Workflows', placeholder: 'Select workflows', available: ['CI — Build & Test', 'CD — Deploy Staging', 'CD — Deploy Production', 'Security Scan', 'Dependency Update', 'Release Drafter'] },
    ],
    nodeTypes: ['backend', 'frontend', 'ci/cd', 'security', 'testing', 'infrastructure'],
  },
  GitLab: {
    description: 'Grant this agent access to specific GitLab groups, projects, and container registries.',
    connected: false,
    fields: [
      { key: 'groups', label: 'Groups', placeholder: 'Select groups', available: ['acme-corp', 'acme-labs', 'acme-infra'] },
      { key: 'projects', label: 'Projects', placeholder: 'Select projects', available: ['api-service', 'web-app', 'deploy-pipelines', 'runner-config', 'k8s-manifests'] },
      { key: 'registries', label: 'Container Registries', placeholder: 'Select registries', available: ['registry.gitlab.com/acme-corp/api', 'registry.gitlab.com/acme-corp/web', 'registry.gitlab.com/acme-corp/workers'] },
    ],
    nodeTypes: ['ci/cd', 'infrastructure', 'backend'],
  },
  GCP: {
    description: 'Grant this agent access to specific GCP projects, regions, and services.',
    connected: false,
    fields: [
      { key: 'projects', label: 'GCP Projects', placeholder: 'Select projects', available: ['acme-prod', 'acme-staging', 'acme-dev', 'acme-shared-services'] },
      { key: 'regions', label: 'Regions', placeholder: 'Select regions', available: ['us-central1', 'us-east1', 'europe-west1', 'asia-southeast1'] },
      { key: 'services', label: 'Services', placeholder: 'Select services', available: ['Compute Engine', 'Cloud Run', 'Cloud Functions', 'Cloud Storage', 'Cloud SQL', 'Pub/Sub', 'BigQuery', 'GKE'] },
    ],
    nodeTypes: ['infrastructure', 'ci/cd', 'security', 'configuration'],
  },
  AWS: {
    description: 'Grant this agent access to specific AWS accounts, regions, and services.',
    connected: false,
    fields: [
      { key: 'accounts', label: 'AWS Accounts', placeholder: 'Select accounts', available: ['acme-prod (123456789012)', 'acme-staging (987654321098)', 'acme-dev (456789123456)'] },
      { key: 'regions', label: 'Regions', placeholder: 'Select regions', available: ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1'] },
      { key: 'services', label: 'Services', placeholder: 'Select services', available: ['EC2', 'S3', 'Lambda', 'RDS', 'DynamoDB', 'ECS', 'EKS', 'CloudFormation', 'SQS', 'SNS'] },
    ],
    nodeTypes: ['infrastructure', 'backend', 'ci/cd', 'security'],
  },
  Azure: {
    description: 'Grant this agent access to specific Azure subscriptions, resource groups, and services.',
    connected: false,
    fields: [
      { key: 'subscriptions', label: 'Subscriptions', placeholder: 'Select subscriptions', available: ['Acme Production', 'Acme Staging', 'Acme Development'] },
      { key: 'resourceGroups', label: 'Resource Groups', placeholder: 'Select resource groups', available: ['prod-rg', 'staging-rg', 'dev-rg', 'shared-rg', 'networking-rg'] },
      { key: 'services', label: 'Services', placeholder: 'Select services', available: ['Virtual Machines', 'App Service', 'Azure Functions', 'AKS', 'Blob Storage', 'Azure SQL', 'Cosmos DB', 'Azure AD'] },
    ],
    nodeTypes: ['infrastructure', 'ci/cd', 'security', 'configuration'],
  },
  Meet: {
    description: 'Grant this agent access to specific Google calendars and Meet recording storage.',
    connected: false,
    fields: [
      { key: 'calendars', label: 'Calendars', placeholder: 'Select calendars', available: ['team@acme.com', 'engineering@acme.com', 'leadership@acme.com', 'all-hands@acme.com'] },
      { key: 'rooms', label: 'Meeting Rooms', placeholder: 'Select rooms', available: ['Boardroom A', 'Boardroom B', 'Huddle — 1', 'Huddle — 2', 'Virtual — Large', 'Virtual — Small'] },
    ],
  },
};

interface KnowledgeConfigProps {
  agentName: string;
  toolName: string;
  agentProfile: any;
  agentKnowledge: Record<string, Record<string, string[]>>;
  setAgentKnowledge: React.Dispatch<React.SetStateAction<Record<string, Record<string, string[]>>>>;
}

const KnowledgeConfig: React.FC<KnowledgeConfigProps> = ({ agentName, toolName, agentProfile, agentKnowledge, setAgentKnowledge }) => {
  const [searchValues, setSearchValues] = useState<Record<string, string>>({});
  const [showDropdown, setShowDropdown] = useState<string | null>(null);

  const config = KNOWLEDGE_CONFIGS[toolName];
  if (!config) return <div style={{ padding: 40, textAlign: 'center' }}><Text type="secondary">No knowledge configuration available for {toolName}</Text></div>;

  if (!config.connected) {
    return (
      <div style={{ padding: '40px 0', textAlign: 'center' }}>
        <RobotOutlined style={{ fontSize: 48, color: '#cbd5e1', marginBottom: 16 }} />
        <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8, color: '#0f172a' }}>{toolName} is not connected</Text>
        <Text style={{ fontSize: 12, color: '#64748b', display: 'block', marginBottom: 20 }}>
          You need to connect to {toolName} first before configuring knowledge access.
          Go to the <Text strong>Configuration</Text> tab to set up the connection.
        </Text>
        <Tag color="orange" style={{ fontSize: 11 }}>Not Connected</Tag>
      </div>
    );
  }

  const defaults: Record<string, string[]> = {};
  config.fields.forEach((f) => { defaults[f.key] = []; });
  const effective = agentKnowledge[agentName] || defaults;

  const updateField = (key: string, values: string[]) => {
    setAgentKnowledge((prev) => ({ ...prev, [agentName]: { ...effective, [key]: values } }));
  };

  const addItem = (fieldKey: string, value: string) => {
    if (value && !effective[fieldKey]?.includes(value)) {
      updateField(fieldKey, [...(effective[fieldKey] || []), value]);
    }
    setSearchValues((prev) => ({ ...prev, [fieldKey]: '' }));
    setShowDropdown(null);
  };

  const removeItem = (fieldKey: string, value: string) => {
    updateField(fieldKey, (effective[fieldKey] || []).filter((v: string) => v !== value));
  };

  const totalItems = Object.values(effective).reduce((sum, arr) => sum + arr.length, 0);

  return (
    <div style={{ padding: '20px 0' }}>
      <Text style={{ fontSize: 13, color: '#0f172a', display: 'block', marginBottom: 6 }}>{config.description}</Text>
      <Tag color="green" style={{ fontSize: 10, marginBottom: 16 }}>Connected</Tag>

      <Divider style={{ margin: '0 0 16px 0' }} />

      {config.fields.map((field) => {
        const search = searchValues[field.key] || '';
        const selected = effective[field.key] || [];
        const filtered = field.available.filter((opt) => !selected.includes(opt) && opt.toLowerCase().includes(search.toLowerCase()));

        return (
          <div key={field.key} style={{ marginBottom: 20 }}>
            <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>{field.label}</Text>
            <div style={{ marginBottom: 6 }}>
              <Space wrap size={6}>
                {selected.map((item: string) => (
                  <Tag key={item} color="blue" closable onClose={(e) => { e.preventDefault(); removeItem(field.key, item); }} style={{ fontSize: 11, borderRadius: 4 }}>{item}</Tag>
                ))}
              </Space>
              {selected.length === 0 && <Text type="secondary" style={{ fontSize: 11 }}>None selected</Text>}
            </div>
            <div style={{ position: 'relative' }}>
              <Space.Compact style={{ width: '100%' }}>
                <Input
                  placeholder={field.placeholder}
                  value={search}
                  onChange={(e) => { setSearchValues((prev) => ({ ...prev, [field.key]: e.target.value })); setShowDropdown(field.key); }}
                  onFocus={() => setShowDropdown(field.key)}
                  onBlur={() => setTimeout(() => setShowDropdown(null), 200)}
                  onPressEnter={() => search && addItem(field.key, search)}
                  size="small"
                  style={{ fontSize: 12 }}
                />
                <Button size="small" type="primary" onClick={() => search && addItem(field.key, search)} icon={<PlusOutlined />}>Add</Button>
              </Space.Compact>
              {showDropdown === field.key && search && filtered.length > 0 && (
                <div style={{ position: 'absolute', top: 32, left: 0, right: 80, background: '#fff', border: '1px solid #e2e8f0', borderRadius: 6, boxShadow: '0 4px 12px rgba(0,0,0,0.1)', zIndex: 10, maxHeight: 180, overflowY: 'auto' }}>
                  {filtered.slice(0, 8).map((opt) => (
                    <div key={opt} style={{ padding: '6px 12px', cursor: 'pointer', fontSize: 12, borderBottom: '1px solid #f1f5f9' }} onClick={() => addItem(field.key, opt)} onMouseEnter={(e) => (e.currentTarget.style.background = '#f8fafc')} onMouseLeave={(e) => (e.currentTarget.style.background = '#fff')}>
                      {opt}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      })}

      {config.nodeTypes && (
        <div style={{ marginBottom: 20 }}>
          <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>Allowed Node Types</Text>
          <Space wrap size={6}>
            {config.nodeTypes.map((nt) => {
              const allNts = effective.nodeTypes || config.nodeTypes || [];
              const isActive = allNts.includes(nt);
              return (
                <Tag
                  key={nt}
                  color={isActive ? NODE_TYPE_COLORS[nt] || 'default' : undefined}
                  style={{ fontSize: 11, borderRadius: 4, cursor: 'pointer', border: isActive ? undefined : '1px dashed #d1d5db', background: isActive ? undefined : '#fafafa', color: isActive ? undefined : '#9ca3af' }}
                  onClick={() => {
                    const current = effective.nodeTypes || config.nodeTypes || [];
                    updateField('nodeTypes', current.includes(nt) ? current.filter((n: string) => n !== nt) : [...current, nt]);
                  }}
                >
                  {isActive ? '✓ ' : ''}{nt}
                </Tag>
              );
            })}
          </Space>
          <Text type="secondary" style={{ fontSize: 10, display: 'block', marginTop: 4 }}>Click to toggle access</Text>
        </div>
      )}

      <Card size="small" style={{ background: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: 8 }} bodyStyle={{ padding: '12px 16px' }}>
        <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>Knowledge Scope</Text>
        <Text style={{ fontSize: 11, color: '#475569', lineHeight: 1.6 }}>
          {config.fields.map((f) => `${(effective[f.key] || []).length} ${f.label.toLowerCase()}`).join(', ')}
          {config.nodeTypes ? `, ${(effective.nodeTypes || []).length} node types` : ''}
          {totalItems === 0 && <Text type="danger" style={{ marginLeft: 4 }}>— No boundaries set, agent has unrestricted access.</Text>}
        </Text>
      </Card>
    </div>
  );
};

interface CollaborationPanelProps {
  onKnowledgeGraphCreated?: (summary: { provider: string; repoUrl: string; nodeCount: number }) => void;
}

const IngestionProgressCard: React.FC<{
  job: ConnectorIngestion;
  compact?: boolean;
  onCancel: (job: ConnectorIngestion) => void;
  onRetry: (job: ConnectorIngestion) => void;
}> = ({ job, compact = false, onCancel, onRetry }) => {
  const state = job.status.toUpperCase() as IngestionState;
  const progress = Math.max(0, Math.min(100, Number(job.progress ?? (state === 'READY' ? 100 : 0))));
  const failed = state === 'FAILED';
  const cancelled = state === 'CANCELLED';
  const active = !TERMINAL_INGESTION_STATES.has(state);
  const errorMessage = typeof job.error === 'string' ? job.error : job.error?.message;
  const border = failed ? '#fecaca' : cancelled ? '#e2e8f0' : state === 'READY' ? '#bbf7d0' : '#bfdbfe';
  const background = failed ? '#fff7f7' : cancelled ? '#f8fafc' : state === 'READY' ? '#f0fdf4' : '#f8fbff';

  return (
    <Card size="small" style={{ border: `1px solid ${border}`, background, borderRadius: 10 }} bodyStyle={{ padding: compact ? 12 : 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start' }}>
        <div style={{ minWidth: 0, flex: 1 }}>
          <Space size={8} wrap>
            {active && <SyncOutlined spin style={{ color: '#2563eb' }} />}
            {state === 'READY' && <CheckCircleOutlined style={{ color: '#16a34a' }} />}
            {failed && <WarningOutlined style={{ color: '#dc2626' }} />}
            {cancelled && <CloseCircleOutlined style={{ color: '#64748b' }} />}
            <Text strong>{job.connection_name || 'Repository ingestion'}</Text>
            <Tag color={failed ? 'error' : state === 'READY' ? 'success' : cancelled ? 'default' : 'processing'}>
              {state.replace(/_/g, ' ')}
            </Tag>
          </Space>
          <Text type="secondary" ellipsis style={{ display: 'block', marginTop: 4, fontSize: 12 }}>
            {job.repository_url || INGESTION_STAGE_LABELS[state] || job.stage}
          </Text>
        </div>
        <Space>
          {active && state !== 'CANCEL_REQUESTED' && (
            <Button size="small" danger icon={<CloseCircleOutlined />} onClick={() => onCancel(job)}>Cancel</Button>
          )}
          {(failed || cancelled) && (
            <Button size="small" type="primary" icon={<ReloadOutlined />} onClick={() => onRetry(job)}>Retry</Button>
          )}
        </Space>
      </div>
      {!TERMINAL_INGESTION_STATES.has(state) && (
        <Progress
          percent={progress}
          status={state === 'CANCEL_REQUESTED' ? 'exception' : 'active'}
          strokeColor="#2563eb"
          trailColor="#dbeafe"
          size="small"
          style={{ marginTop: 10, marginBottom: 0 }}
        />
      )}
      {!compact && (
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 8 }}>
          <Text style={{ fontSize: 12 }}>{INGESTION_STAGE_LABELS[state] || job.stage || state}</Text>
          {job.files_processed !== undefined && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {job.files_processed.toLocaleString()} / {job.files_discovered?.toLocaleString() || '—'} files
            </Text>
          )}
          {job.nodes_written !== undefined && <Text type="secondary" style={{ fontSize: 12 }}>{job.nodes_written.toLocaleString()} nodes</Text>}
          {job.elapsed_seconds !== undefined && <Text type="secondary" style={{ fontSize: 12 }}>{Math.round(job.elapsed_seconds)}s elapsed</Text>}
        </div>
      )}
      {errorMessage && <Text type="danger" style={{ display: 'block', marginTop: 8, fontSize: 12 }}>{errorMessage}</Text>}
    </Card>
  );
};

export const CollaborationPanel: React.FC<CollaborationPanelProps> = ({ onKnowledgeGraphCreated }) => {
  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const [configForm, setConfigForm] = useState<Record<string, any>>({});
  const [testingConnection, setTestingConnection] = useState(false);
  const [syncResult, setSyncResult] = useState<any>(null);
  const [syncingProvider, setSyncingProvider] = useState(false);
  const [detailTab, setDetailTab] = useState<string>('config');
  const [connections, setConnections] = useState<any[]>([]);
  const [loadingConnections, setLoadingConnections] = useState(false);
  const [showErrors, setShowErrors] = useState(false);
  const [errorView, setErrorView] = useState<'classifications' | 'types' | 'list' | 'chat'>('classifications');
  const [selectedClassification, setSelectedClassification] = useState<ErrorClassification | null>(null);
  const [selectedErrorType, setSelectedErrorType] = useState<ErrorType | null>(null);
  const [selectedErrorEntry, setSelectedErrorEntry] = useState<ErrorEntry | null>(null);
  const [selectedToolDetail, setSelectedToolDetail] = useState<any>(null);
  const [agentKnowledge, setAgentKnowledge] = useState<Record<string, Record<string, string[]>>>({});
  const [toolAssignments, setToolAssignments] = useState<any[]>([]);
  const [orgMembers, setOrgMembers] = useState<any[]>([]);
  const [seedingTools, setSeedingTools] = useState(false);
  const [ingestions, setIngestions] = useState<Record<string, ConnectorIngestion>>(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(INGESTION_STORAGE_KEY) || '{}');
      return Object.fromEntries(Object.entries(saved).map(([id, value]: [string, any]) => [
        id,
        { ...value, status: String(value.status || value.state || 'QUEUED').toUpperCase() as IngestionState },
      ]));
    } catch {
      return {};
    }
  });
  const completedJobs = useRef(new Set<string>());

  const fetchConnections = () => { setLoadingConnections(true); ApiClient.get('/connections').then(setConnections).catch(() => setConnections([])).finally(() => setLoadingConnections(false)); };
  useEffect(() => { fetchConnections(); }, []);

  useEffect(() => {
    localStorage.setItem(INGESTION_STORAGE_KEY, JSON.stringify(ingestions));
  }, [ingestions]);

  useEffect(() => {
    let stopped = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    const poll = async () => {
      const activeJobs = Object.values(ingestions).filter((job) => !TERMINAL_INGESTION_STATES.has(job.status));
      if (!activeJobs.length || stopped) return;
      const token = localStorage.getItem('auth_token');
      const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
      const updates = await Promise.all(activeJobs.map(async (job) => {
        try {
          const response = await fetch(job.status_url, { headers });
          if (!response.ok) return job;
          const data = await response.json();
          const status = String(data.status || data.state || job.status).toUpperCase() as IngestionState;
          return {
            ...job,
            ...data,
            status,
            progress: data.progress ?? data.progress_percent ?? job.progress,
            repository_url: data.repository_url ?? data.repo_url ?? job.repository_url,
          };
        } catch {
          return job;
        }
      }));
      if (stopped) return;
      setIngestions((current) => {
        const next = { ...current };
        updates.forEach((job) => { next[job.job_id] = job; });
        return next;
      });
      updates.forEach((job) => {
        if (job.status === 'READY' && !completedJobs.current.has(job.job_id)) {
          completedJobs.current.add(job.job_id);
          message.success(`${job.connection_name || 'Repository'} knowledge graph is ready.`);
          window.dispatchEvent(new CustomEvent('knowledge-graph-updated'));
          onKnowledgeGraphCreated?.({
            provider: selectedTool || 'Git',
            repoUrl: job.repository_url || '',
            nodeCount: job.nodes_written || 0,
          });
          fetchConnections();
        }
      });
      const delay = document.visibilityState === 'visible' ? 2500 : 15000;
      timer = setTimeout(poll, delay);
    };

    if (Object.values(ingestions).some((job) => !TERMINAL_INGESTION_STATES.has(job.status))) {
      timer = setTimeout(poll, document.visibilityState === 'visible' ? 500 : 5000);
    }
    const resume = () => {
      if (document.visibilityState === 'visible' && !stopped) {
        if (timer) clearTimeout(timer);
        timer = setTimeout(poll, 100);
      }
    };
    document.addEventListener('visibilitychange', resume);
    return () => {
      stopped = true;
      if (timer) clearTimeout(timer);
      document.removeEventListener('visibilitychange', resume);
    };
  // Polling is deliberately restarted when the durable job collection changes.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ingestions, onKnowledgeGraphCreated]);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
    fetch('/organization/tool-assignments', { headers })
      .then(res => res.ok ? res.json() : [])
      .then(data => { if (Array.isArray(data)) setToolAssignments(data); })
      .catch(() => {});
    fetch('/organization/members', { headers })
      .then(res => res.ok ? res.json() : [])
      .then(data => { if (Array.isArray(data)) setOrgMembers(data); })
      .catch(() => {});
  }, []);

  const handleAutoSeedTools = async () => {
    setSeedingTools(true);
    try {
      const token = localStorage.getItem('auth_token');
      const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };
      const res = await fetch('/organization/tool-assignments/auto-seed', { method: 'POST', headers });
      const data = await res.json();
      message.success(`Auto-assigned tools: ${data.created} assignments created`);
      // Refresh assignments
      const taRes = await fetch('/organization/tool-assignments', { headers });
      const taData = await taRes.json();
      if (Array.isArray(taData)) setToolAssignments(taData);
    } catch { message.error('Failed to auto-assign tools'); }
    finally { setSeedingTools(false); }
  };

  const handleToolClick = (toolName: string) => { setSelectedTool(toolName); setConfigForm({}); setSyncResult(null); setDetailTab('config'); setShowErrors(false); setSelectedToolDetail(null); setErrorView('classifications'); setSelectedClassification(null); setSelectedErrorType(null); setSelectedErrorEntry(null); };
  const getFieldsForTool = (toolName: string) => PROVIDER_FIELDS[toolName] || [];

  const handleTestConnection = async () => { setTestingConnection(true); try { const m: Record<string,string>={GitHub:'git',Git:'git',GitLab:'git',Bitbucket:'git',Jira:'jira',Slack:'slack'}; const pid = m[selectedTool||''] || selectedTool?.toLowerCase() || ''; await ApiClient.post(`/connectors/provider-${pid}/test`, configForm); message.success('Connection test successful!'); } catch { message.error('Connection test failed.'); } finally { setTestingConnection(false); } };

  const mutateIngestion = async (job: ConnectorIngestion, action: 'cancel' | 'retry') => {
    const token = localStorage.getItem('auth_token');
    try {
      const response = await fetch(`${job.status_url}/${action}`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = data.detail;
        throw new Error(
          (typeof detail === 'string' ? detail : detail?.message)
          || `Unable to ${action} ingestion`,
        );
      }
      const nextJob = action === 'retry' && data.job_id && data.job_id !== job.job_id
        ? {
            ...job,
            ...data,
            job_id: data.job_id,
            status_url: data.status_url || job.status_url.replace(job.job_id, data.job_id),
            status: String(data.status || 'QUEUED').toUpperCase() as IngestionState,
            error: null,
          }
        : {
            ...job,
            ...data,
            status: String(data.status || data.state || (action === 'cancel' ? 'CANCEL_REQUESTED' : 'QUEUED')).toUpperCase() as IngestionState,
          };
      setIngestions((current) => {
        const next = { ...current };
        if (nextJob.job_id !== job.job_id) delete next[job.job_id];
        next[nextJob.job_id] = nextJob;
        return next;
      });
      message.success(action === 'cancel' ? 'Cancellation requested.' : 'Ingestion retry queued.');
    } catch (error: any) {
      message.error(error?.message || `Unable to ${action} ingestion`);
    }
  };

  const handleConnect = async () => {
    setSyncingProvider(true);
    setSyncResult(null);
    try {
      const m: Record<string, string> = { GitHub: 'git', Git: 'git', GitLab: 'git', Bitbucket: 'git' };
      const platformMap: Record<string, string> = { GitHub: 'github', Bitbucket: 'bitbucket' };
      const pn = m[selectedTool || ''] || selectedTool?.toLowerCase() || '';
      const token = localStorage.getItem('auth_token');
      const connectionName = configForm.connection_name || `${selectedTool} Connection`;
      const repoUrl = configForm.repo_url || '';
      if (['GitHub', 'Bitbucket', 'Git', 'GitLab'].includes(selectedTool || '') && repoUrl) {
        const connection = await ApiClient.post('/connections/source-control', {
          name: connectionName,
          provider: configForm.platform || platformMap[selectedTool || ''] || pn,
          repo_url: repoUrl,
          status: 'syncing',
          node_count: 0,
          config: {
            branch: configForm.branch || '',
            platform: configForm.platform || selectedTool,
          },
        });
        const d = await ApiClient.post('/connector-ingestions', {
          connection_id: connection.number,
          branch: configForm.branch || 'main',
        });
        const job: ConnectorIngestion = {
          ...d,
          job_id: d.job_id,
          connection_id: String(d.connection_id || connection.number),
          status_url: d.status_url || `/api/connector-ingestions/${d.job_id}`,
          status: String(d.status || d.state || 'QUEUED').toUpperCase() as IngestionState,
          progress: d.progress ?? d.progress_percent ?? 0,
          repository_url: repoUrl,
          connection_name: connectionName,
        };
        setIngestions((current) => ({ ...current, [job.job_id]: job }));
        setSyncResult(job);
        message.success('Connection accepted. Repository ingestion is running in the background.');
        fetchConnections();
        return;
      }
      const res = await fetch(`/providers/${pn}/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          ...configForm,
          platform: configForm.platform || platformMap[selectedTool || ''],
          connection_name: connectionName,
          persist: true,
        }),
      });
      const responseText = await res.text();
      let d: any = {};
      try {
        d = responseText ? JSON.parse(responseText) : {};
      } catch {
        d = { detail: responseText || res.statusText };
      }
      if (res.ok) {
        const repoUrl = d.repo_url || configForm.repo_url || '';
        const nodeCount = d.write_success_count ?? d.uko_count ?? 0;
        if (res.status === 202 || d.job_id) {
          const job: ConnectorIngestion = {
            ...d,
            job_id: d.job_id,
            connection_id: d.connection_id,
            status_url: d.status_url || `/api/connector-ingestions/${d.job_id}`,
            status: String(d.status || d.state || 'QUEUED').toUpperCase() as IngestionState,
            progress: d.progress ?? d.progress_percent ?? 0,
            repository_url: repoUrl,
            connection_name: connectionName,
          };
          setIngestions((current) => ({ ...current, [job.job_id]: job }));
          setSyncResult(job);
          message.success('Connection accepted. Repository ingestion is running in the background.');
          fetchConnections();
          return;
        }
        setSyncResult({ ...d, status: 'READY' });
        if (['GitHub', 'Bitbucket', 'Git', 'GitLab'].includes(selectedTool || '') && repoUrl) {
          try {
            await ApiClient.post('/connections/source-control', {
              name: connectionName,
              provider: d.platform || selectedTool || 'git',
              repo_url: repoUrl,
              status: 'connected',
              node_count: nodeCount,
              config: {
                branch: configForm.branch || d.branch || '',
                platform: d.platform || selectedTool,
                resource_id: d.resource_id,
                uko_count: d.uko_count,
                episode_count: d.episode_count,
              },
            });
            window.dispatchEvent(new CustomEvent('knowledge-graph-updated'));
            onKnowledgeGraphCreated?.({ provider: selectedTool || 'Git', repoUrl, nodeCount });
            setSelectedTool(null);
          } catch {
            message.warning('Connected, but the Administration connection record could not be saved.');
          }
        }
        message.success(`Connected to ${selectedTool} successfully. Knowledge graph created.`);
        fetchConnections();
      } else {
        message.error(d.detail || 'Connection failed');
        setSyncResult({ error: d });
      }
    } catch (er: any) {
      const detail = er?.message || 'Connection failed';
      message.error(detail);
      setSyncResult({ error: { detail } });
    } finally {
      setSyncingProvider(false);
    }
  };

  const handleDeleteConnection = (number: number, name: string) => { Modal.confirm({title:'Delete Connection',content:`Delete "${name}"? All knowledge graph data will be removed.`,okText:'Delete',okType:'danger',onOk:async()=>{try{await ApiClient.delete(`/connections/${number}`);message.success(`Connection deleted`);fetchConnections();window.dispatchEvent(new CustomEvent('knowledge-graph-updated'));}catch{message.error('Failed to delete');}}})};

  const agentProfile = selectedTool ? AGENT_PROFILES[selectedTool] : null;
  const kpis = agentProfile ? DEFAULT_KPIS[agentProfile.name] || { workspaces: 1, operations: 0, errors: 0 } : null;
  const errorClassifications = agentProfile ? ERROR_CLASSIFICATIONS[agentProfile.name] || DEFAULT_ERROR_CLASSIFICATIONS : [];
  const totalErrors = errorClassifications.reduce((sum, cls) => sum + cls.types.reduce((s, t) => s + t.errors.length, 0), 0);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Text strong style={{ fontSize: 15, color: '#0F172A' }}><TeamOutlined style={{ marginRight: 8 }} />Collaboration Hub</Text>
        <Button type="primary" size="small" loading={seedingTools} onClick={handleAutoSeedTools}>Auto-Assign Tools by Role</Button>
      </div>
      <InProgressNotice>
        GitHub and Bitbucket configuration syncs create backend knowledge graph data. Agent KPI cards, historical error examples, and tool skill examples in this panel are in progress until they are backed by live provider telemetry.
      </InProgressNotice>
      {Object.values(ingestions).filter((job) => job.status !== 'READY').length > 0 && (
        <div style={{ display: 'grid', gap: 8, marginBottom: 16 }}>
          {Object.values(ingestions)
            .filter((job) => job.status !== 'READY')
            .slice(-3)
            .map((job) => (
              <IngestionProgressCard
                key={job.job_id}
                job={job}
                compact
                onCancel={(item) => mutateIngestion(item, 'cancel')}
                onRetry={(item) => mutateIngestion(item, 'retry')}
              />
            ))}
        </div>
      )}
      <Collapse
        defaultActiveKey={['project-management','version']}
        expandIconPosition="end"
        style={{ background: 'transparent', border: 'none' }}
        items={CATEGORIES.map((cat) => ({
          key: cat.key,
          label: <Space>{cat.icon}<Text strong style={{ fontSize: 13 }}>{cat.title}</Text></Space>,
          style: { background: '#fff', borderRadius: 8, marginBottom: 12, border: '1px solid #e2e8f0' },
          children: (
            <Row gutter={[16, 16]}>
              {cat.tools.map((tool) => (
                <Col span={6} key={tool.name}>
                  <Card hoverable style={{ ...cardStyle, border: selectedTool === tool.name ? '2px solid #2563EB' : cardStyle.border, cursor: 'pointer' }} bodyStyle={{ padding: 16, textAlign: 'center' }} onClick={() => handleToolClick(tool.name)}>
                    <Avatar size={48} src={tool.logo} style={{ background: '#F8FAFC', marginBottom: 8 }} />
                    <Text strong style={{ display: 'block', fontSize: 13 }}>{tool.name}</Text>
                  </Card>
                </Col>
              ))}
            </Row>
          ),
        }))}
      />

      <Modal
        title={<Space><Avatar size={28} src={CATEGORIES.flatMap((c)=>c.tools).find((t)=>t.name===selectedTool)?.logo}/><span>{selectedTool}</span>{agentProfile && <Tag color={agentProfile.status==='Active'?'green':'orange'}>{agentProfile.status}</Tag>}</Space>}
        open={!!selectedTool} onCancel={() => setSelectedTool(null)} width={700} footer={null} bodyStyle={{ padding: 0 }}
      >
        <Tabs activeKey={detailTab} onChange={setDetailTab} style={{ padding: '0 16px' }} items={[
          {
            key: 'config', label: 'Configuration',
            children: (
              <div style={{ padding: '20px 0' }}>
                <Row gutter={16}><Col span={16}><Form layout="vertical" size="small">
                  <Row gutter={16}><Col span={12}><Form.Item label="Connection Name" required><Input placeholder={`e.g. My ${selectedTool} Connection`} value={configForm.connection_name || ''} onChange={(e) => setConfigForm({...configForm,connection_name:e.target.value})} /></Form.Item></Col></Row>
                  <Row gutter={16}>{getFieldsForTool(selectedTool || '').map((field) => (
                    <Col span={12} key={field.key}><Form.Item label={field.label}>{field.type==='password'?<Input.Password placeholder={field.placeholder} value={configForm[field.key]||''} onChange={(e)=>setConfigForm({...configForm,[field.key]:e.target.value})}/>:<Input placeholder={field.placeholder} value={configForm[field.key]||''} onChange={(e)=>setConfigForm({...configForm,[field.key]:e.target.value})}/>}</Form.Item></Col>
                  ))}</Row>
                </Form></Col>
                <Col span={8} style={{display:'flex',flexDirection:'column',justifyContent:'flex-end',gap:8}}>
                  <Button icon={<SyncOutlined/>} loading={testingConnection} onClick={handleTestConnection}>Test Connection</Button>
                  <Button type="primary" loading={syncingProvider} style={{background:'#16A34A'}} onClick={handleConnect}>Connect & Sync</Button>
                </Col></Row>
                {syncResult && (
                  <div style={{ marginTop: 16 }}>
                    {syncResult.job_id ? (
                      <IngestionProgressCard
                        job={ingestions[syncResult.job_id] || syncResult}
                        onCancel={(item) => mutateIngestion(item, 'cancel')}
                        onRetry={(item) => mutateIngestion(item, 'retry')}
                      />
                    ) : syncResult.error ? (
                      <Card size="small" style={{background:'#FEF2F2',border:'1px solid #FCA5A5'}}>
                        <Text strong style={{color:'#DC2626'}}>Connection Failed</Text>
                        <pre style={{fontSize:11,marginTop:8,color:'#7F1D1D',whiteSpace:'pre-wrap'}}>{JSON.stringify(syncResult.error,null,2)}</pre>
                      </Card>
                    ) : (
                      <Card size="small" style={{background:'#F0FDF4',border:'1px solid #86EFAC'}}>
                        <Text strong style={{color:'#16A34A'}}>Sync Successful</Text>
                        <div style={{marginTop:8,fontSize:12}}>{syncResult.uko_count!==undefined&&<div><Text type="secondary">Knowledge objects:</Text> <Text strong>{syncResult.uko_count}</Text></div>}</div>
                      </Card>
                    )}
                  </div>
                )}
              </div>
            ),
          },
        ]} />
      </Modal>

      <Modal
        title={<Space><SettingOutlined /><span>{selectedToolDetail?.name}</span></Space>}
        open={!!selectedToolDetail}
        onCancel={() => setSelectedToolDetail(null)}
        width={700}
        footer={<Button onClick={() => setSelectedToolDetail(null)}>Close</Button>}
      >
        {selectedToolDetail && (
          <div>
            <Text style={{ fontSize: 13, color: '#475569', display: 'block', marginBottom: 20 }}>{selectedToolDetail.description}</Text>
            <Divider style={{ margin: '0 0 16px 0' }} />
            <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 12 }}>Skills & Capabilities</Text>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {(selectedToolDetail.skills || []).map((skill: any, idx: number) => (
                <Card key={idx} size="small" style={{ border: '1px solid #e2e8f0', borderRadius: 8 }} bodyStyle={{ padding: '12px 16px' }}>
                  <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 6, color: '#0f172a' }}>{skill.name}</Text>
                  <Text style={{ fontSize: 12, color: '#475569', lineHeight: 1.6, display: 'block', marginBottom: 8 }}>{skill.explanation}</Text>
                  <div style={{ background: '#1e293b', borderRadius: 6, padding: '10px 14px' }}>
                    <Text style={{ fontSize: 10, color: '#94a3b8', display: 'block', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Example</Text>
                    <pre style={{ fontSize: 11, color: '#e2e8f0', margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>{skill.example}</pre>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}
      </Modal>

      <Modal
        title={
          <Space>
            <WarningOutlined style={{ color: '#dc2626' }} />
            {errorView === 'classifications' && <span>Errors — {selectedTool}</span>}
            {errorView === 'types' && <span><span style={{ cursor: 'pointer', color: '#2563eb' }} onClick={() => { setErrorView('classifications'); setSelectedClassification(null); }}>Errors</span> / {selectedClassification?.classification}</span>}
            {errorView === 'list' && <span><span style={{ cursor: 'pointer', color: '#2563eb' }} onClick={() => { setErrorView('classifications'); setSelectedClassification(null); setSelectedErrorType(null); }}>Errors</span> / <span style={{ cursor: 'pointer', color: '#2563eb' }} onClick={() => { setErrorView('types'); setSelectedErrorType(null); }}>{selectedClassification?.classification}</span> / {selectedErrorType?.type}</span>}
            {errorView === 'chat' && <span><span style={{ cursor: 'pointer', color: '#2563eb' }} onClick={() => { setErrorView('classifications'); setSelectedClassification(null); setSelectedErrorType(null); setSelectedErrorEntry(null); }}>Errors</span> / <span style={{ cursor: 'pointer', color: '#2563eb' }} onClick={() => { setErrorView('types'); setSelectedErrorType(null); setSelectedErrorEntry(null); }}>{selectedClassification?.classification}</span> / <span style={{ cursor: 'pointer', color: '#2563eb' }} onClick={() => { setErrorView('list'); setSelectedErrorEntry(null); }}>{selectedErrorType?.type}</span> / {selectedErrorEntry?.title}</span>}
          </Space>
        }
        open={showErrors}
        onCancel={() => { setShowErrors(false); setErrorView('classifications'); setSelectedClassification(null); setSelectedErrorType(null); setSelectedErrorEntry(null); }}
        width={errorView === 'chat' ? 800 : 680}
        footer={<Button onClick={() => { setShowErrors(false); setErrorView('classifications'); setSelectedClassification(null); setSelectedErrorType(null); setSelectedErrorEntry(null); }}>Close</Button>}
      >
        <div style={{ maxHeight: 500, overflowY: 'auto' }}>
          {/* Level 1: Classifications (Agent vs Human, Agent vs Agent) */}
          {errorView === 'classifications' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {errorClassifications.map((cls) => {
                const clsErrors = cls.types.reduce((s, t) => s + t.errors.length, 0);
                return (
                  <Card key={cls.classification} hoverable size="small" style={{ border: `1px solid ${cls.color}20`, borderRadius: 8, cursor: 'pointer' }} bodyStyle={{ padding: '14px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }} onClick={() => { setErrorView('types'); setSelectedClassification(cls); }}>
                    <Space>
                      <div style={{ width: 12, height: 12, borderRadius: '50%', background: cls.color }} />
                      <Text strong style={{ fontSize: 14 }}>{cls.classification}</Text>
                    </Space>
                    <Tag color={cls.color} style={{ fontSize: 11 }}>{clsErrors} error{clsErrors !== 1 ? 's' : ''}</Tag>
                  </Card>
                );
              })}
              {errorClassifications.length === 0 && (
                <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>
                  <CheckCircleOutlined style={{ fontSize: 32, marginBottom: 8, color: '#16a34a' }} />
                  <div>No errors recorded</div>
                </div>
              )}
            </div>
          )}

          {/* Level 2: Error Types within a Classification */}
          {errorView === 'types' && selectedClassification && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {selectedClassification.types.map((t) => (
                <Card key={t.type} hoverable size="small" style={{ border: `1px solid ${t.color}20`, borderRadius: 8, cursor: 'pointer' }} bodyStyle={{ padding: '12px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }} onClick={() => { setErrorView('list'); setSelectedErrorType(t); }}>
                  <Space>
                    <div style={{ width: 10, height: 10, borderRadius: '50%', background: t.color }} />
                    <div>
                      <Text strong style={{ fontSize: 13, display: 'block' }}>{t.type}</Text>
                      <Text type="secondary" style={{ fontSize: 10 }}>{t.description}</Text>
                    </div>
                  </Space>
                  <Tag color={t.color} style={{ fontSize: 11 }}>{t.errors.length} error{t.errors.length !== 1 ? 's' : ''}</Tag>
                </Card>
              ))}
            </div>
          )}

          {/* Level 3: Error List within a Type */}
          {errorView === 'list' && selectedErrorType && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {selectedErrorType.errors.map((err, idx) => (
                <Card key={idx} hoverable size="small" style={{ background: err.severity === 'High' ? '#FEF2F2' : err.severity === 'Medium' ? '#FFFBEB' : '#F9FAFB', border: `1px solid ${err.severity === 'High' ? '#FCA5A5' : err.severity === 'Medium' ? '#FDE68A' : '#E5E7EB'}`, borderRadius: 8, cursor: 'pointer' }} bodyStyle={{ padding: '12px 16px' }} onClick={() => { setErrorView('chat'); setSelectedErrorEntry(err); }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <Text strong style={{ fontSize: 12, color: '#0f172a' }}>{err.title}</Text>
                    <Space size={4}>
                      <Tag color={selectedClassification?.classification === 'Agent vs Agent' ? 'cyan' : 'purple'} style={{ fontSize: 9, margin: 0 }}>{err.fromName} → {err.toName}</Tag>
                      <Tag color={err.severity === 'High' ? 'red' : err.severity === 'Medium' ? 'orange' : 'default'} style={{ fontSize: 10, margin: 0 }}>{err.severity}</Tag>
                    </Space>
                  </div>
                  <Text style={{ fontSize: 11, color: '#475569', lineHeight: 1.5, display: 'block', marginBottom: 8 }}>{err.summary}</Text>
                  <div style={{ display: 'flex', gap: 16, fontSize: 11 }}>
                    <Text type="secondary">Ticket: <Tag style={{ fontSize: 10, margin: 0 }}>{err.ticket}</Tag></Text>
                    <Text type="secondary">Cost: <Text strong style={{ fontSize: 11 }}>{err.cost}</Text></Text>
                    <Text type="secondary" style={{ marginLeft: 'auto' }}>{err.date}</Text>
                  </div>
                </Card>
              ))}
            </div>
          )}

          {/* Level 4: Chat History */}
          {errorView === 'chat' && selectedErrorEntry && (
            <div>
              <Card size="small" style={{ marginBottom: 16, background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8 }} bodyStyle={{ padding: '12px 16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <Text strong style={{ fontSize: 12 }}>{selectedErrorEntry.title}</Text>
                  <Tag color={selectedErrorEntry.severity === 'High' ? 'red' : selectedErrorEntry.severity === 'Medium' ? 'orange' : 'default'} style={{ fontSize: 10 }}>{selectedErrorEntry.severity}</Tag>
                </div>
                <Text style={{ fontSize: 11, color: '#475569', display: 'block', marginBottom: 8 }}>{selectedErrorEntry.summary}</Text>
                <Space size={16}>
                  <Text type="secondary" style={{ fontSize: 10 }}>From: <Tag color="purple" style={{ fontSize: 10, margin: 0 }}>{selectedErrorEntry.fromName}</Tag></Text>
                  <Text type="secondary" style={{ fontSize: 10 }}>To: <Tag color="cyan" style={{ fontSize: 10, margin: 0 }}>{selectedErrorEntry.toName}</Tag></Text>
                  <Text type="secondary" style={{ fontSize: 10 }}>Ticket: <Tag style={{ fontSize: 10, margin: 0 }}>{selectedErrorEntry.ticket}</Tag></Text>
                  <Text type="secondary" style={{ fontSize: 10 }}>Cost: <Text strong>{selectedErrorEntry.cost}</Text></Text>
                </Space>
              </Card>

              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 12 }}>Conversation History</Text>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {selectedErrorEntry.chatHistory.map((msg, idx) => {
                  const isUser = msg.role === 'user';
                  const isSystem = msg.role === 'system';
                  const displayName = isSystem ? 'System' : isUser ? selectedErrorEntry.fromName : selectedErrorEntry.toName;
                  return (
                    <div key={idx} style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
                      <div style={{ maxWidth: '80%', padding: '10px 14px', borderRadius: 12, background: isUser ? '#2563eb' : isSystem ? '#fef3c7' : '#f1f5f9', color: isUser ? '#fff' : '#0f172a', border: isSystem ? '1px solid #fde68a' : 'none' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                          <Text style={{ fontSize: 10, fontWeight: 600, color: isUser ? '#bfdbfe' : isSystem ? '#92400e' : '#64748b' }}>{displayName}</Text>
                          <Text style={{ fontSize: 9, color: isUser ? '#93c5fd' : '#94a3b8', marginLeft: 12 }}>{msg.timestamp}</Text>
                        </div>
                        <Text style={{ fontSize: 12, lineHeight: 1.5, color: isUser ? '#fff' : '#1e293b' }}>{msg.content}</Text>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </Modal>

      <Card title={<Space><DatabaseOutlined/><span>Active Connections</span></Space>} style={{...cardStyle,marginTop:16}} bodyStyle={{padding:0}}>
        <Table dataSource={connections} loading={loadingConnections} rowKey="number" pagination={false} size="middle" locale={{ emptyText: 'No connections yet. Configure a tool above.' }}
          columns={[
            { title: 'SR', dataIndex: 'number', key: 'number', width: 60, render: (n:number)=><Text strong>{n}</Text> },
            { title: 'Type', dataIndex: 'provider', key: 'provider', width: 100, render: (p:string)=><Tag color="blue">{p}</Tag> },
            { title: 'Name', dataIndex: 'name', key: 'name' },
            { title: 'Agents', key: 'agents', width: 80, render: (_:any,rec:any)=>{ const ta=AGENT_PROFILES[rec.provider==='git'?'Git':rec.provider]; return ta?<Tag color="processing">1 agent</Tag>:<Text type="secondary">-</Text> }},
            { title: 'Status', dataIndex: 'status', key: 'status', width: 110, render: (s:string)=>(<Tag color={s==='active'||s==='connected'?'green':s==='syncing'?'blue':s==='reindexing'?'orange':'default'}>{s?.charAt(0).toUpperCase()+s?.slice(1)}</Tag>) },
            { title: 'Actions', key: 'actions', width: 80, render: (_:any,rec:any)=>(<Button size="small" danger ghost icon={<DeleteOutlined/>} disabled={rec.status==='syncing'||rec.status==='reindexing'} onClick={()=>handleDeleteConnection(rec.number,rec.name)}>Delete</Button>) },
          ]}
        />
      </Card>
    </div>
  );
};

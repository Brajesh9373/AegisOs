# Issue Lifecycle Standard

## Purpose

The **Issue Lifecycle Standard** defines the mandatory tracking and resolution progression for every bug, feature request, and architectural improvement logged within the AegisAI ecosystem. This strict governance model prevents loose task tracking, ensuring that every issue is systematically triaged, rigorously tested against regressions, and verifiably closed by a human or digital supervisor.

---

## 1. Issue Statuses (The Lifecycle)

Every issue must mathematically traverse these defined states.

- **New:** The issue is logged but has not been evaluated by an engineering manager.
- **Triaged:** The issue has been reviewed, its severity confirmed, and it has been routed to the correct domain backlog.
- **Approved:** The implementation approach or bug fix strategy is architecturally cleared for execution.
- **In Progress:** A Digital Employee or Human Engineer is actively mutating code to resolve the issue.
- **Blocked:** Execution is halted due to a missing dependency, infrastructure outage, or Guardian security gate.
- **Waiting Review:** The code modifications are submitted (via PR) and awaiting peer or architectural approval.
- **Testing:** The automated QA pipeline and CI/CD matrix are actively verifying the fix.
- **Verified:** The fix has passed all topological checks and integration tests on a staging environment.
- **Completed:** The issue is resolved, merged into `main`, and deployed.
- **Rejected:** The issue was deemed invalid, non-reproducible, or architecturally unsound.
- **Deferred:** The issue is valid but parked for a future implementation phase.
- **Closed:** Terminal state for all Completed, Rejected, or Deferred issues.

---

## 2. Issue Definition Requirements

Every issue tracked within the repository must structurally contain the following parameters to be considered valid for Triage:

- **Priority:** (Low, Medium, High, Critical) The operational urgency for scheduling the work.
- **Severity:** (Minor, Major, Fatal) The actual impact the issue has on the running system.
- **Owner:** The explicit Digital Team or Engineer assigned to execute the resolution.
- **Sprint:** The targeted `ENGINEERING_SPRINT` block this issue is allocated to.
- **Related Package:** The explicit monorepo boundary (e.g., `@aegisai/workflow`) affected.
- **Verification:** The specific automated or manual test required to prove the issue is resolved.
- **Evidence:** Cryptographic logs, error stack traces, or screenshots proving the issue exists.

### For Bug/Defect Issues:

- **Root Cause:** A detailed technical explanation of exactly why the system failed (determined post-triage).
- **Resolution:** The explicit architectural or code change made to eliminate the root cause.
- **Regression Tests:** The specific unit or E2E tests added to the CI suite to mathematically guarantee this exact bug can never silently occur again.

---

## Implementation Mapping

- **Owner Package:** Platform Governance
- **Owner Modules:** Issue Management
- **Related Packages:** None
- **Required Contracts:** None
- **Required Types:** None
- **Required Runtime Components:** None
- **Required Builder Components:** None
- **Required APIs:** None
- **Required Database Models:** None
- **Required Workflows:** Bug Triage Workflow
- **Required Skills:** None
- **Required Tests:** None
- **Verification Commands:** `cat .aegis/governance/ISSUE_LIFECYCLE_STANDARD.md`
- **Roadmap Phase:** Phase 2
- **Implementation Status:** Completed

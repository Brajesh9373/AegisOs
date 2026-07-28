# AegisAI Testing Architecture Specification

This document defines the definitive, permanent Testing Architecture for AegisAI. It establishes the strategies, layers, and strict constraints required to mathematically prove the stability and security of the platform before any code reaches production.

## 1. Testing Philosophy
In an Enterprise AI OS, "it works on my machine" is unacceptable. The system orchestrates non-deterministic LLMs and heavily regulated data; therefore, the surrounding infrastructure must be absolutely deterministic. Testing is not an afterthought; it is the physical proof that the architecture behaves as specified. If a feature cannot be automatically tested, it cannot be merged.

## 2. Testing Pyramid
AegisAI follows a rigid testing pyramid: 70% Unit Tests (fast, isolated logic), 20% Integration Tests (database/API boundaries), and 10% End-to-End Tests (browser/workflow simulation). AI Evaluation Tests sit parallel to this pyramid.

## 3. Unit Testing
Tests individual functions and classes in complete isolation. Network calls and database queries are strictly mocked. These tests execute in milliseconds and enforce standard code behavior.

## 4. Integration Testing
Tests the interaction between AegisAI modules (e.g., API to Database, Runtime to Guardian). These tests use ephemeral, containerized test databases (e.g., Testcontainers) to ensure real SQL execution without mocking the data layer.

## 5. End-to-End (E2E) Testing
Full system validation. These tests spin up the entire AegisAI stack (UI, API, Task Engine, Database) and simulate a human user clicking through a browser or an Agent completing a multi-step workflow.

## 6. Contract Testing
Ensures that AegisAI microservices (and external SDK Plugins) agree on API payloads. If the Task Engine changes an expected JSON schema, the contract test fails immediately, preventing deployment.

## 7. Runtime Testing
Validates the orchestration logic. Ensures that the Runtime correctly handles LLM timeouts, malformed tool JSON, and correct parameter injection without relying on actual external LLM calls (uses mocked LLM responses).

## 8. Guardian Testing
The most critical test suite. Guardian policies are tested by throwing thousands of simulated malicious payloads (XSS, Prompt Injections, unauthorized tenant IDs) at the engine to prove it blocks them 100% of the time.

## 9. Security Testing
Automated SAST (Static Application Security Testing) and DAST (Dynamic Application Security Testing) run in the CI pipeline to scan for CVEs, leaked secrets, and known vulnerabilities.

## 10. Performance Testing
Validates the p95 and p99 latency of critical API routes (e.g., policy evaluation) to ensure new code does not introduce unacceptable bottlenecks.

## 11. Load Testing
Simulates high concurrency. Tests how the Task Engine handles 10,000 simultaneous background jobs and verifies that the database connection pool degrades gracefully instead of crashing.

## 12. AI Evaluation Testing
A specialized suite evaluating the non-deterministic output of Agents. It runs a set of golden prompts against various LLMs and uses a judge-LLM (or exact regex matching) to score the accuracy, formatting, and safety of the response.

## 13. Skill Testing
Validates external Integrations. Because we cannot hit production Jira/GitHub instances in CI, these tests use robust HTTP replay tools (e.g., VCR) to mock the exact HTTP responses from third-party APIs.

## 14. Prompt Testing
Validates that prompt templates compile correctly without syntax errors and that the resulting token count does not exceed context limits.

## 15. Workflow Testing
Simulates complex Directed Acyclic Graphs (DAGs). Verifies that a workflow correctly suspends for a human approval step and resumes flawlessly when the approval event is fired.

## 16. Regression Testing
When a bug is discovered in production, the first step of the fix is writing a regression test that reliably reproduces the bug. The bug is only considered fixed when this test passes.

## 17. Test Data
Tests must never use production data dumps. All test data must be synthetically generated (e.g., using Faker libraries) or manually crafted and sanitized fixtures.

## 18. Test Isolation
Every test must start with a clean state. Database transactions are rolled back after every single test. A test must never fail because a previous test left garbage data behind.

## 19. CI Testing
Continuous Integration is the absolute gatekeeper. Every Pull Request triggers the entire testing suite. Merging is mathematically impossible if coverage drops below the required threshold (e.g., 90%) or if a single test fails.

## 20. Release Validation
Before a new version of AegisAI is tagged for deployment, it undergoes a final automated deployment to a staging environment where the E2E suite runs against the packaged artifacts.

## 21. Future Expansion
The architecture supports the integration of "Chaos Engineering," where an internal Chaos Agent randomly kills worker nodes or drops database packets in staging to prove the system's auto-recovery mechanisms work.

## 22. Permanent Constraints
* Every single feature must be testable.
* Every production bug requires a permanent regression test.
* Tests must be 100% deterministic (no "flaky" tests allowed).
* Tests must be perfectly isolated from one another.
* Tests must be repeatable on any developer's local machine without manual setup.

---

## Never Do

* **Never** connect a test suite to a production database or a shared staging database; tests must use ephemeral, isolated data stores.
* **Never** rely on actual external network calls (e.g., hitting the real OpenAI API) in the standard Unit/Integration CI pipeline; this causes non-deterministic failures (flakiness).
* **Never** write tests that depend on the execution order (e.g., Test B requires Test A to run first).
* **Never** merge code that lowers the global test coverage percentage.

---

## Testing Constitution
The permanent Testing principles of AegisAI:
1. **The Principle of Proof**: Code does not work until a test proves it works. Assumption is the enemy of enterprise stability.
2. **The Principle of Determinism**: A test that passes 99 times and fails 1 time is not a passing test; it is a broken test. We demand absolute binary certainty.
3. **The Principle of the Gate**: The CI pipeline is an unbribable, emotionless gatekeeper. No deadline, no executive, and no emergency bypasses a failing test suite.

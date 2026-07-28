# Architecture Governance Rule

Blueprint v3.2 is the Constitutional Source of Truth.

No package implementation may change platform architecture.

Any architectural change requires:

1. Architecture Decision Record (ADR)
2. Blueprint update
3. Architecture Review
4. Blueprint Freeze
5. Implementation approval

Code must always follow the Blueprint.
The Blueprint never follows the code.

# React UI Production Rules

Every React page must satisfy:

1. Production quality
2. Ant Design only
3. Responsive
4. Dark mode ready
5. RBAC aware
6. No placeholder data
7. No placeholder buttons
8. No fake login
9. Real backend integration
10. Unit tested

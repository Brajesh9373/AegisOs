# Technical Debt Register

_(Note: No issue may be deleted from this register. All unresolved issues remain here until explicitly closed.)_

| ID         | Priority | Category             | Description                                                                   | Impact                                                                 | Owner        | Target Phase | Status |
| :--------- | :------- | :------------------- | :---------------------------------------------------------------------------- | :--------------------------------------------------------------------- | :----------- | :----------- | :----- |
| **TD-001** | Critical | Repository Structure | ~30 root-level architectural generation scripts (`*.js`) polluting workspace. | High risk of context loss if deleted; blocks pristine workspace setup. | DevOps       | Phase 2      | Open   |
| **TD-002** | High     | Binary Tracking      | `AegisAI.zip` recovery artifact left in the active repository root.           | High risk of bloating Git history permanently if accidentally staged.  | DevOps       | Phase 2      | Open   |
| **TD-003** | High     | Workspace Hygiene    | `/scratch/` directory is unstructured and actively tracked by Git.            | Pollutes commit history with undocumented experimentation.             | Platform Eng | Phase 2      | Open   |
| **TD-004** | Medium   | Dependency Mismatch  | Missing packages (`database`, `sdk`, `ui`) remain dangling in configurations. | May cause CI/CD or Turbo topological resolution warnings.              | Platform Eng | Phase 2      | Open   |
| **TD-005** | Medium   | Documentation Drift  | Legacy `README.md` files exist in legacy module folders.                      | Creates conflicting architectural truth contrary to Blueprint v3.2.    | Platform Eng | Phase 2      | Open   |
| **TD-006** | Low      | Package Hygiene      | Potential unused exports and dev dependencies across the Monorepo.            | Slower install times and minor security surface area bloat.            | Platform Eng | Phase 3      | Open   |

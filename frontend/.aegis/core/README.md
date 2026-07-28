# AegisAI Core Architecture Documentation

Welcome to the `.aegis/core/` directory. This is the absolute foundation of the AegisAI platform. 

## Purpose of Core Architecture
The documents in this directory do not describe *how* a specific feature is implemented; they describe *why* the system exists and the immutable physical laws that govern its operation. If a proposed feature, library, or codebase change conflicts with the principles outlined here, the proposal must be rejected. The Core Architecture protects the platform from entropy and scope creep.

## The Core Documents

1.  **`constitution.md`**
    *   *Description:* The highest law of the platform. Defines the three pillars: Control, Governance, and Accountability. It establishes that AI is a tool, not an autonomous agent, and that human responsibility is absolute.
    *   *Status:* **IMMUTABLE**.

2.  **`architecture.md`**
    *   *Description:* The grand vision and the structural layers of the system (Presentation, Application, Governance, Runtime, Execution, Data, Infrastructure). It defines how these layers stack and prevents layer-jumping.
    *   *Status:* **IMMUTABLE** (Requires an epic-level ADR to modify).

3.  **`coding-rules.md`**
    *   *Description:* The strict, non-negotiable standards for how code is physically written, reviewed, and merged. It covers naming conventions, testing requirements, and error-handling philosophies.
    *   *Status:* Locked (Can be updated via standard ADR).

## Dependency Order
These documents are the root dependencies for all other specifications in the `.aegis/` folder. 
*   `specs/` (Data schemas, APIs) depend on the structural rules in `architecture.md`.
*   `modules/` (Specific feature designs) depend on the philosophical laws in `constitution.md`.
*   The actual `src/` codebase depends on `coding-rules.md`.

You must read and internalize these three documents before reading anything else.

## Immutability
Documents marked as **IMMUTABLE** cannot be casually updated. They are the bedrock of the enterprise offering. If a customer asks for a feature that violates `constitution.md` (e.g., "I want the AI to secretly monitor employee chats without an audit log"), the answer is no. Modifying an immutable document requires unanimous consensus from the founding architecture board.

## Architecture Governance
The `.aegis/core/` directory acts as the ultimate reference point for Code Reviewers (both human and AI). During a Pull Request, the reviewer's primary job is not just to check for bugs, but to ask: *"Does this code violate the Constitution? Does this code bypass the layers defined in the Architecture?"* If the answer is yes, the PR is closed.

# Architecture Generation Scripts Archive

## Purpose

This archive preserves the explicit one-time scripts used to procedurally build the aegisOS Platform Blueprint v3.2. These scripts mapped out the structural rules, packages, dependencies, and lifecycle states defining the AI platform.

## Historical Context

During Phase 1 (Baseline Definition), the platform architecture was defined programmatically rather than manually written. This ensured a structured, mathematically sound generation of the `aegisOS-Platform-Blueprint-v3.2.md` artifact.

## Why these scripts are archived

These scripts represent a fixed point in time. The aegisOS Blueprint is now officially **Frozen** at v3.2. Architectural mutations are no longer performed via procedural scripts, but rather through formal Architecture Decision Records (ADRs) and direct governance updates.

## Disclaimer

**THESE SCRIPTS ARE NOT PART OF THE PRODUCTION TOOLCHAIN.**
They must not be integrated into CI/CD pipelines, executed on active workspaces, or shipped to runtime environments. They are retained strictly for forensic traceability and historical compliance.

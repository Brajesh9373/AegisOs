# aegisOS Development Guide

## Architecture
The platform is built as a strict monorepo using pnpm workspaces.
All packages must adhere to the Blueprint constraints.

## Running Locally (Docker)
We use Docker Compose to orchestrate the entire stack.
`docker compose up` starts:
- **web**: React Frontend (Vite)
- **api**: Express Backend
- **database**: PostgreSQL Database

## Database Seeding
To initialize the SQLite database with default roles and data:
`pnpm tsx scripts/seed.ts`

## Adding Packages
Always update `tsconfig.json` paths and run `pnpm install` at the root.

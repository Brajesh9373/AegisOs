# Sprint 8.2 — AegisOS Public Website Reference Integration & BA Simulation

## Status
ONGOING

## Objective
Convert the provided `aegisos-landing.html` design/content into the AegisOS public React landing page (`/landing`) using a premium white theme, maintaining full responsive behavior, and introducing a high-fidelity frontend-only BA simulation flow.

## Files & Components Affected
- `frontend/apps/web/src/pages/public/Landing.tsx`: Public Landing Page Component
- `frontend/apps/web/src/styles/public/public_styles.css`: Isolated styling layer for public pages
- `frontend/apps/web/src/styles/public/tokens.css`: Isolated theme design tokens

## Simulation Boundaries
- **No Backend Calls:** Authentication, lead submission, Whisper voice transcription, PDF parsing, and routing are simulated in frontend React state.
- **BYOK Sandbox:** API Key validation is simulated locally. Keys are never sent to any backend API or logged.
- **Handoff & Fallbacks:** Handoff to Specialized Business Analysts and the missing capability review request form are fully simulated.
- **Cost limit alert:** Complimentary usage limit is simulated without exposing dollar or token amounts.

## Validation
- TypeScript compilation: `npx -p typescript@5.4.2 tsc --noEmit --project ./apps/web/tsconfig.json`
- Production build validation inside Vite and Docker.

## Known Future Backend Work
- Integrating actual discovery session endpoint `/api/discovery` with the landing chat.
- Connecting real BYOK configuration updates to backend PostgreSQL storage.
- Real capability requests collection.
- Transitioning guest simulated onboarding into the actual `/login` and registration path.
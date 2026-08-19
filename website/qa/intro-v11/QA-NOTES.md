# V11 intro visual QA

Checked static states at 1536×864 and 390×844:

- Entry: AegisOS centered with sufficient safe area on all sides.
- Zoom: wordmark fills the viewport without exposing unintended scrollbars.
- Pass-through: typography is scaled beyond the viewport before opacity/background release.
- Mobile: wordmark remains centered and the scroll affordance/index remain within safe areas.

Runtime note: full Next.js execution was not available in the build container because npm registry DNS is unavailable. TSX files were syntax-transpiled with TypeScript 5.8.3 and `intro-v11.css` was parsed with tinycss2 without errors.

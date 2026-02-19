# Frontend (Next.js 16)

## Stack
- Next.js 16.1.6 (Turbopack, React Compiler 1.0)
- React 19.2.4 with auto-memoization
- Tailwind CSS 4.1.18 (CSS-first, @theme directive)
- next-intl 4.8.2 for i18n (EN, PT-BR, ES)
- motion 12.34.0 for animations (import from "motion/react")
- Zustand 5.0.11 for state management
- Recharts 3.7.0 for charts
- DOMPurify 3.3.1 for XSS sanitization

## Commands

**MANDATORY: Always run tests inside Docker Compose (never outside).**

```bash
# Inside Docker (ALWAYS use these):
docker compose exec frontend pnpm test        # Run tests
docker compose exec frontend pnpm typecheck   # TypeScript check
docker compose exec frontend pnpm lint        # ESLint check
docker compose exec frontend pnpm build       # Production build

# Local dev only (NOT for testing):
pnpm dev          # Dev server (http://localhost:3000)
```

## Architecture
- `src/app/[locale]/` - App Router pages with locale segment
- `src/components/` - Client components organized by feature
- `src/hooks/` - Custom React hooks (SSE, theme, simulators)
- `src/stores/` - Zustand state stores (pipeline, accessibility)
- `src/i18n/` - next-intl routing + request config
- `src/proxy.ts` - Next.js 16 proxy (was middleware.ts)
- `src/styles/globals.css` - 9 persona themes via CSS custom properties

## Key Conventions
- Theme switching: `document.body.setAttribute('data-theme', id)` -- NO React re-render
- `cookies()`, `headers()`, `params`, `searchParams` MUST be awaited
- SSE: `compress: false` in next.config.ts
- Import motion from "motion/react" (NOT framer-motion)
- React Compiler: `reactCompiler: true` + babel-plugin-react-compiler
- WCAG AAA: all interactive elements get aria-labels, proper focus management
- Components under 300 lines

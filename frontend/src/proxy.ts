import createMiddleware from 'next-intl/middleware'
import { routing } from './i18n/routing'

/**
 * Next.js 16 proxy (renamed from middleware.ts — ADR-033).
 * Handles locale negotiation, redirects, and URL rewrites.
 */
export default createMiddleware(routing)

export const config = {
  matcher: '/((?!api|trpc|_next|_vercel|.*\\..*).*)',
}

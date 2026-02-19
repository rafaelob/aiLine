import type { Locale } from '@/i18n/routing'

/**
 * Type-safe locale-prefixed path helper.
 * Eliminates `as any` casts when constructing Next.js Link `href` values.
 *
 * Usage:
 *   <Link href={localePath(locale, '/dashboard')}>...</Link>
 */
export function localePath(locale: Locale | string, path: string): string {
  const normalized = path.startsWith('/') ? path : `/${path}`
  return `/${locale}${normalized}`
}

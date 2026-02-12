import { defineRouting } from 'next-intl/routing'

/**
 * Centralized routing configuration for next-intl.
 * Defines supported locales and the default locale.
 */
export const routing = defineRouting({
  locales: ['en', 'pt-BR', 'es'],
  defaultLocale: 'pt-BR',
})

export type Locale = (typeof routing.locales)[number]

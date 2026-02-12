import { getRequestConfig } from 'next-intl/server'
import { routing } from './routing'

/**
 * Server-side request configuration for next-intl.
 * Loads the appropriate message file based on the resolved locale.
 */
export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale

  if (!locale || !routing.locales.includes(locale as typeof routing.locales[number])) {
    locale = routing.defaultLocale
  }

  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default,
  }
})

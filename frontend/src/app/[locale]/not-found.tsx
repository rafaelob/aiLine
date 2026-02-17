import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'

/**
 * Not-found page for the [locale] route group.
 * Shown when a route does not match any page under the locale.
 * Uses design system tokens for consistent theming across
 * all 9 accessibility personas.
 */
export default function NotFoundPage() {
  const t = useTranslations('common')

  return (
    <main role="main" className="flex min-h-[60vh] items-center justify-center p-6">
      <div
        className={cn(
          'flex max-w-md flex-col items-center gap-6 text-center',
          'rounded-[var(--radius-lg)] border border-[var(--color-border)]',
          'bg-[var(--color-surface)] p-8',
          'shadow-[var(--shadow-lg)]',
        )}
      >
        {/* 404 indicator */}
        <div
          className={cn(
            'flex h-16 w-16 items-center justify-center rounded-full',
            'bg-[var(--color-warning)]/10',
          )}
          aria-hidden="true"
        >
          <span
            className="text-2xl font-bold"
            style={{ color: 'var(--color-warning)' }}
          >
            404
          </span>
        </div>

        <div className="flex flex-col gap-2">
          <h1 className="text-xl font-bold text-[var(--color-text)]">
            {t('not_found_title')}
          </h1>
          <p className="text-sm leading-relaxed text-[var(--color-muted)]">
            {t('not_found_description')}
          </p>
        </div>

        {/* eslint-disable-next-line @next/next/no-html-link-for-pages -- Not-found page uses <a> to ensure navigation works when router is broken */}
        <a
          href="/"
          className={cn(
            'rounded-[var(--radius-md)] px-5 py-2.5',
            'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
            'text-sm font-semibold',
            'hover:bg-[var(--color-primary-hover)]',
            'focus-visible:outline-2 focus-visible:outline-offset-2',
            'focus-visible:outline-[var(--color-primary)]',
            'transition-colors',
          )}
        >
          {t('go_home')}
        </a>
      </div>
    </main>
  )
}

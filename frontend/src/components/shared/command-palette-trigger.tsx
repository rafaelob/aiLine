'use client'

import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import { SearchIcon } from './command-palette-icons'
import { getExternalToggle } from './command-palette'

/**
 * Trigger button for opening the Command Palette from the topbar.
 * Calls the registered palette toggle via module-level ref.
 */
export function CommandPaletteTrigger() {
  const t = useTranslations('commandPalette')

  return (
    <button
      type="button"
      onClick={() => getExternalToggle()?.()}
      aria-label={t('placeholder')}
      className={cn(
        'flex items-center gap-2 px-2.5 py-2',
        'rounded-[var(--radius-md)]',
        'text-sm text-[var(--color-muted)]',
        'hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text)]',
        'transition-all duration-200',
      )}
    >
      <SearchIcon />
      <span className="hidden sm:inline text-xs font-medium">{t('hint')}</span>
    </button>
  )
}

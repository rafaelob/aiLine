'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'
import { TutorChat } from '@/components/tutor/tutor-chat'
import { ConversationReview } from '@/components/tutor/conversation-review'
import { useTutorStore } from '@/stores/tutor-store'

type Tab = 'chat' | 'review'

export function TutorPageContent() {
  const t = useTranslations('tutor')
  const [activeTab, setActiveTab] = useState<Tab>('chat')
  const sessionId = useTutorStore((s) => s.sessionId)

  return (
    <div className="space-y-4">
      {/* Tab pills */}
      <div
        className="flex items-center gap-1 p-1 rounded-[var(--radius-md)] glass w-fit"
        role="tablist"
        aria-label={t('tabs_label')}
      >
        {(['chat', 'review'] as const).map((tab) => (
          <button
            key={tab}
            role="tab"
            aria-selected={activeTab === tab}
            aria-controls={`panel-${tab}`}
            onClick={() => setActiveTab(tab)}
            className={cn(
              'relative px-4 py-2 rounded-[var(--radius-sm)] text-sm font-medium transition-colors',
              activeTab === tab
                ? 'text-[var(--color-text)]'
                : 'text-[var(--color-muted)] hover:text-[var(--color-text)]',
            )}
          >
            {activeTab === tab && (
              <motion.div
                layoutId="tutor-tab-pill"
                className="absolute inset-0 rounded-[var(--radius-sm)] bg-[var(--color-bg)] shadow-[var(--shadow-sm)]"
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              />
            )}
            <span className="relative z-10">{t(`tab_${tab}`)}</span>
          </button>
        ))}
      </div>

      {/* Tab panels */}
      <div id="panel-chat" role="tabpanel" hidden={activeTab !== 'chat'}>
        <TutorChat />
      </div>
      <div id="panel-review" role="tabpanel" hidden={activeTab !== 'review'}>
        {sessionId ? (
          <ConversationReview tutorId="default" sessionId={sessionId} />
        ) : (
          <div className="glass rounded-xl p-8 text-center">
            <p className="text-sm text-[var(--color-muted)]">{t('no_session_review')}</p>
          </div>
        )}
      </div>
    </div>
  )
}

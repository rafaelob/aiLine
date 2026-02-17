'use client'

import { useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { motion, useReducedMotion } from 'motion/react'
import { useRouter } from 'next/navigation'
import { cn } from '@/lib/cn'
import { useAccessibilityStore } from '@/stores/accessibility-store'

interface DemoProfile {
  key: string
  name: string
  description: string
  role: 'teacher' | 'student' | 'parent'
  accessibility?: string
  badge?: string
  highlight?: boolean
  color: string
  avatar: string
  route: string
}

interface LandingDemoLoginProps {
  locale: string
  title: string
  subtitle: string
  enterAs: string
  teacherLabel: string
  studentLabel: string
  parentLabel: string
  profiles: {
    teacher: { name: string; detail: string; description: string }
    students: {
      alex: { name: string; condition: string; description: string }
      maya: { name: string; condition: string; description: string }
      lucas: { name: string; condition: string; description: string }
      sofia: { name: string; condition: string; description: string }
    }
    parent: { name: string; description: string }
  }
}

const DEMO_PROFILES: DemoProfile[] = [
  {
    key: 'teacher-ms-johnson',
    name: '',
    description: '',
    role: 'teacher',
    highlight: true,
    color: 'from-blue-500 to-indigo-600',
    avatar: 'SJ',
    route: '/dashboard',
  },
  {
    key: 'student-alex-tea',
    name: '',
    description: '',
    role: 'student',
    accessibility: 'tea',
    badge: 'ASD',
    color: 'from-emerald-500 to-teal-600',
    avatar: 'AR',
    route: '/tutors',
  },
  {
    key: 'student-maya-adhd',
    name: '',
    description: '',
    role: 'student',
    accessibility: 'tdah',
    badge: 'ADHD',
    color: 'from-orange-500 to-amber-600',
    avatar: 'MC',
    route: '/tutors',
  },
  {
    key: 'student-lucas-dyslexia',
    name: '',
    description: '',
    role: 'student',
    accessibility: 'dyslexia',
    badge: 'Dyslexia',
    color: 'from-blue-500 to-cyan-600',
    avatar: 'LT',
    route: '/tutors',
  },
  {
    key: 'student-sofia-hearing',
    name: '',
    description: '',
    role: 'student',
    accessibility: 'hearing',
    badge: 'Hearing',
    color: 'from-violet-500 to-purple-600',
    avatar: 'SM',
    route: '/sign-language',
  },
  {
    key: 'parent-david',
    name: '',
    description: '',
    role: 'parent',
    color: 'from-rose-500 to-pink-600',
    avatar: 'DR',
    route: '/progress',
  },
]

function ProfileCard({
  profile,
  index,
  locale,
  enterAs,
  roleLabel,
}: {
  profile: DemoProfile
  index: number
  locale: string
  enterAs: string
  roleLabel: string
}) {
  const prefersReducedMotion = useReducedMotion()
  const noMotion = prefersReducedMotion ?? false
  const router = useRouter()
  const setTheme = useAccessibilityStore((s) => s.setTheme)
  const tLanding = useTranslations('landing')

  const handlePrefetch = useCallback(() => {
    router.prefetch(`/${locale}${profile.route}`)
  }, [locale, profile.route, router])

  const handleEnter = useCallback(() => {
    // Store demo profile in sessionStorage for the app to read
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('ailine_demo_profile', profile.key)
      sessionStorage.setItem('ailine_demo_role', profile.role)
    }

    // Set accessibility theme for student profiles
    if (profile.accessibility) {
      setTheme(profile.accessibility)
      if (typeof document !== 'undefined') {
        document.body.setAttribute('data-theme', profile.accessibility)
      }
    }

    router.push(`/${locale}${profile.route}`)
  }, [profile, locale, router, setTheme])

  return (
    <motion.article
      onMouseEnter={handlePrefetch}
      onFocus={handlePrefetch}
      initial={noMotion ? undefined : { opacity: 0, y: 20 }}
      whileInView={noMotion ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-30px' }}
      transition={noMotion ? undefined : { delay: index * 0.08, duration: 0.4 }}
      className={cn(
        'group relative overflow-hidden rounded-2xl p-5',
        'glass card-hover gradient-border-glass',
        'flex flex-col gap-3',
        profile.highlight && 'ring-2 ring-blue-400/40'
      )}
    >
      {/* "Start Here" ribbon for highlighted card */}
      {profile.highlight && (
        <div
          className={cn(
            'absolute -top-px -right-px px-3 py-1 rounded-bl-xl rounded-tr-2xl',
            'text-[10px] font-bold uppercase tracking-widest',
            'bg-gradient-to-r text-white',
            profile.color,
            'shadow-sm'
          )}
        >
          {tLanding('start_here')}
        </div>
      )}

      {/* Hover gradient overlay */}
      <div
        className={cn(
          'absolute inset-0 opacity-0 transition-opacity duration-300',
          'group-hover:opacity-100 pointer-events-none'
        )}
        style={{
          background:
            'radial-gradient(ellipse at 50% 0%, color-mix(in srgb, var(--color-primary) 6%, transparent) 0%, transparent 70%)',
        }}
        aria-hidden="true"
      />

      <div className="relative flex items-start gap-3">
        {/* Avatar */}
        <div
          className={cn(
            'flex items-center justify-center w-11 h-11 rounded-xl shrink-0',
            'bg-gradient-to-br text-white font-bold text-sm',
            profile.color
          )}
          aria-hidden="true"
        >
          {profile.avatar}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-sm font-semibold text-[var(--color-text)] truncate">
              {profile.name}
            </h3>
            {profile.badge && (
              <span
                className={cn(
                  'inline-flex items-center px-2 py-0.5 rounded-full',
                  'text-[11px] font-bold uppercase tracking-wider',
                  'bg-gradient-to-r text-white drop-shadow-[0_1px_1px_rgba(0,0,0,0.3)]',
                  profile.color
                )}
              >
                {profile.badge}
              </span>
            )}
          </div>
          <span className="text-[11px] font-medium text-[var(--color-muted)] uppercase tracking-wider">
            {roleLabel}
          </span>
        </div>
      </div>

      <p className="relative text-xs text-[var(--color-muted)] leading-relaxed">
        {profile.description}
      </p>

      <button
        type="button"
        onClick={handleEnter}
        className={cn(
          'relative w-full px-4 py-2.5 rounded-xl',
          'text-sm font-semibold',
          'bg-gradient-to-r text-white',
          profile.color,
          'shadow-md hover:shadow-lg hover:scale-[1.02]',
          'transition-all duration-200',
          'focus-visible:ring-2 focus-visible:ring-[var(--color-primary)] focus-visible:ring-offset-2'
        )}
        aria-label={`${enterAs} ${profile.name}`}
      >
        {enterAs}
      </button>
    </motion.article>
  )
}

/**
 * Demo login section with role-based profile cards.
 * Each card sets demo profile + accessibility theme and navigates to the right page.
 */
export function LandingDemoLogin(props: LandingDemoLoginProps) {
  const { locale, title, subtitle, enterAs, profiles } = props

  // Hydrate profiles with translated text
  const hydratedProfiles = DEMO_PROFILES.map((p) => {
    switch (p.key) {
      case 'teacher-ms-johnson':
        return {
          ...p,
          name: profiles.teacher.name,
          description: profiles.teacher.description,
        }
      case 'student-alex-tea':
        return {
          ...p,
          name: profiles.students.alex.name,
          description: profiles.students.alex.description,
          badge: profiles.students.alex.condition,
        }
      case 'student-maya-adhd':
        return {
          ...p,
          name: profiles.students.maya.name,
          description: profiles.students.maya.description,
          badge: profiles.students.maya.condition,
        }
      case 'student-lucas-dyslexia':
        return {
          ...p,
          name: profiles.students.lucas.name,
          description: profiles.students.lucas.description,
          badge: profiles.students.lucas.condition,
        }
      case 'student-sofia-hearing':
        return {
          ...p,
          name: profiles.students.sofia.name,
          description: profiles.students.sofia.description,
          badge: profiles.students.sofia.condition,
        }
      case 'parent-david':
        return {
          ...p,
          name: profiles.parent.name,
          description: profiles.parent.description,
        }
      default:
        return p
    }
  })

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'teacher':
        return props.teacherLabel
      case 'student':
        return props.studentLabel
      case 'parent':
        return props.parentLabel
      default:
        return role
    }
  }

  return (
    <section
      className="py-12 px-6"
      aria-labelledby="demo-login-heading"
    >
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2
            id="demo-login-heading"
            className="text-3xl sm:text-4xl font-bold text-[var(--color-text)] mb-3"
          >
            {title}
          </h2>
          <p className="text-lg text-[var(--color-muted)] max-w-2xl mx-auto">
            {subtitle}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {hydratedProfiles.map((profile, i) => (
            <ProfileCard
              key={profile.key}
              profile={profile}
              index={i}
              locale={locale}
              enterAs={enterAs}
              roleLabel={getRoleLabel(profile.role)}
            />
          ))}
        </div>
      </div>
    </section>
  )
}

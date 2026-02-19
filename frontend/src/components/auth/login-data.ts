import type { UserRole } from '@/stores/auth-store'

/* ------------------------------------------------------------------ */
/*  Role definitions                                                   */
/* ------------------------------------------------------------------ */

export interface RoleDef {
  id: UserRole
  icon: string
  color: string
  badge?: string
}

export const ROLES: RoleDef[] = [
  {
    id: 'teacher',
    icon: 'M12 14l9-5-9-5-9 5 9 5z M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z',
    color: 'from-blue-500 to-indigo-600',
    badge: 'start_here',
  },
  {
    id: 'student',
    icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253',
    color: 'from-green-500 to-emerald-600',
  },
  {
    id: 'parent',
    icon: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z',
    color: 'from-pink-500 to-rose-600',
  },
  {
    id: 'school_admin',
    icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4',
    color: 'from-amber-500 to-orange-600',
  },
  {
    id: 'super_admin',
    icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
    color: 'from-purple-500 to-violet-600',
  },
]

/* ------------------------------------------------------------------ */
/*  Demo profile definitions (per role)                                */
/* ------------------------------------------------------------------ */

export interface DemoProfile {
  key: string
  name: string
  avatar: string
  description: string
  accessibility?: string
  badge?: string
  color: string
  route: string
}

export const DEMO_PROFILES_BY_ROLE: Record<UserRole, DemoProfile[]> = {
  teacher: [
    {
      key: 'teacher',
      name: 'Ms. Sarah Johnson',
      avatar: 'SJ',
      description: 'demo_teacher_desc',
      color: 'from-blue-500 to-indigo-600',
      route: '/dashboard',
    },
  ],
  student: [
    {
      key: 'student-asd',
      name: 'Alex Rivera',
      avatar: 'AR',
      description: 'demo_alex_desc',
      accessibility: 'tea',
      badge: 'ASD',
      color: 'from-emerald-500 to-teal-600',
      route: '/tutors',
    },
    {
      key: 'student-adhd',
      name: 'Maya Chen',
      avatar: 'MC',
      description: 'demo_maya_desc',
      accessibility: 'tdah',
      badge: 'ADHD',
      color: 'from-orange-500 to-amber-600',
      route: '/tutors',
    },
    {
      key: 'student-dyslexia',
      name: 'Lucas Torres',
      avatar: 'LT',
      description: 'demo_lucas_desc',
      accessibility: 'dyslexia',
      badge: 'Dyslexia',
      color: 'from-blue-500 to-cyan-600',
      route: '/tutors',
    },
    {
      key: 'student-hearing',
      name: 'Sofia Martinez',
      avatar: 'SM',
      description: 'demo_sofia_desc',
      accessibility: 'hearing',
      badge: 'Hearing',
      color: 'from-violet-500 to-purple-600',
      route: '/sign-language',
    },
  ],
  parent: [
    {
      key: 'parent',
      name: 'David Rivera',
      avatar: 'DR',
      description: 'demo_parent_desc',
      color: 'from-rose-500 to-pink-600',
      route: '/progress',
    },
  ],
  school_admin: [],
  super_admin: [],
}

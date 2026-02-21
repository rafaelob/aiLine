import { describe, it, expect } from 'vitest'
import { ROLES, DEMO_PROFILES_BY_ROLE, type RoleDef, type DemoProfile } from './login-data'

describe('login-data', () => {
  describe('ROLES', () => {
    it('has 5 role definitions', () => {
      expect(ROLES).toHaveLength(5)
    })

    it('includes all required roles', () => {
      const ids = ROLES.map((r) => r.id)
      expect(ids).toContain('teacher')
      expect(ids).toContain('student')
      expect(ids).toContain('parent')
      expect(ids).toContain('school_admin')
      expect(ids).toContain('super_admin')
    })

    it('each role has required fields', () => {
      for (const role of ROLES) {
        expect(role.id).toBeTruthy()
        expect(role.icon).toBeTruthy()
        expect(role.color).toBeTruthy()
      }
    })

    it('teacher has start_here badge', () => {
      const teacher = ROLES.find((r) => r.id === 'teacher')
      expect(teacher?.badge).toBe('start_here')
    })
  })

  describe('DEMO_PROFILES_BY_ROLE', () => {
    it('has profiles for 3 non-admin roles (F-251)', () => {
      const roles = Object.keys(DEMO_PROFILES_BY_ROLE)
      expect(roles).toHaveLength(3)
      expect(roles).toContain('teacher')
      expect(roles).toContain('student')
      expect(roles).toContain('parent')
    })

    it('student role has 4 profiles with accessibility types', () => {
      const students = DEMO_PROFILES_BY_ROLE.student!
      expect(students).toHaveLength(4)
      const keys = students.map((p) => p.key)
      expect(keys).toContain('student-asd')
      expect(keys).toContain('student-adhd')
      expect(keys).toContain('student-dyslexia')
      expect(keys).toContain('student-hearing')
    })

    it('each profile has required fields', () => {
      for (const profiles of Object.values(DEMO_PROFILES_BY_ROLE)) {
        for (const profile of profiles) {
          expect(profile.key).toBeTruthy()
          expect(profile.name).toBeTruthy()
          expect(profile.avatar).toBeTruthy()
          expect(profile.description).toBeTruthy()
          expect(profile.color).toBeTruthy()
          expect(profile.route).toBeTruthy()
          expect(profile.route.startsWith('/')).toBe(true)
        }
      }
    })

    it('student-asd has tea accessibility profile', () => {
      const asd = DEMO_PROFILES_BY_ROLE.student!.find((p) => p.key === 'student-asd')
      expect(asd?.accessibility).toBe('tea')
    })

    it('student-hearing routes to sign-language', () => {
      const hearing = DEMO_PROFILES_BY_ROLE.student!.find((p) => p.key === 'student-hearing')
      expect(hearing?.route).toBe('/sign-language')
    })
  })
})

import '@testing-library/jest-dom/vitest'
import { createElement } from 'react'

// Mock next-intl
vi.mock('next-intl', () => ({
  useTranslations: (namespace?: string) => {
    return (key: string) => (namespace ? `${namespace}.${key}` : key)
  },
  useLocale: () => 'pt-BR',
  NextIntlClientProvider: ({ children }: { children: React.ReactNode }) => children,
}))

// Mock next-intl/server
vi.mock('next-intl/server', () => ({
  getMessages: vi.fn(async () => ({})),
  getTranslations: vi.fn(async (opts?: { locale?: string; namespace?: string }) => {
    const ns = typeof opts === 'object' ? opts?.namespace : opts
    return (key: string) => (ns ? `${ns}.${key}` : key)
  }),
  getRequestConfig: vi.fn((fn: unknown) => fn),
}))

// Mock next/navigation
vi.mock('next/navigation', () => ({
  usePathname: () => '/pt-BR',
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  useParams: () => ({ locale: 'pt-BR' }),
  useSearchParams: () => new URLSearchParams(),
  notFound: vi.fn(),
  redirect: vi.fn(),
}))

// Mock next/link (no JSX in .ts file -- use createElement)
vi.mock('next/link', () => ({
  default: ({ children, href, ...rest }: Record<string, unknown>) =>
    createElement('a', { href, ...rest }, children as React.ReactNode),
}))

// Mock next/script
vi.mock('next/script', () => ({
  default: (_props: Record<string, unknown>) => null,
}))

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = value
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
    get length() {
      return Object.keys(store).length
    },
    key: (index: number) => Object.keys(store)[index] ?? null,
  }
})()

Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

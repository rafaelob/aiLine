import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LoginPage from './page'
import { useAuthStore } from '@/stores/auth-store'
import { useAccessibilityStore } from '@/stores/accessibility-store'

// Mock the child components to isolate page orchestration logic
vi.mock('@/components/auth/role-selection-phase', () => ({
  RoleSelectionPhase: ({
    onRoleSelect,
  }: {
    locale: string
    noMotion: boolean
    onRoleSelect: (role: string) => void
  }) => (
    <div data-testid="role-selection">
      <button onClick={() => onRoleSelect('teacher')}>Select Teacher</button>
      <button onClick={() => onRoleSelect('student')}>Select Student</button>
    </div>
  ),
}))

vi.mock('@/components/auth/login-form-phase', () => ({
  LoginFormPhase: ({
    selectedRole,
    onBack,
    onDemoLogin,
    onEmailChange,
    onPasswordChange,
    onSubmit,
    email,
    password,
    isLoading,
    error,
  }: {
    locale: string
    noMotion: boolean
    selectedRole: string
    demoProfiles: unknown[]
    email: string
    password: string
    isLoading: boolean
    error: string | null
    onBack: () => void
    onDemoLogin: (profile: { key: string; route: string; accessibility?: string }) => void
    onEmailChange: (v: string) => void
    onPasswordChange: (v: string) => void
    onSubmit: (e: React.FormEvent) => void
  }) => (
    <div data-testid="login-form">
      <span data-testid="selected-role">{selectedRole}</span>
      <button onClick={onBack}>Back</button>
      <button
        onClick={() =>
          onDemoLogin({ key: 'teacher', route: '/dashboard' })
        }
      >
        Demo Teacher
      </button>
      <button
        onClick={() =>
          onDemoLogin({ key: 'student-asd', route: '/tutors', accessibility: 'tea' })
        }
      >
        Demo Student ASD
      </button>
      <input
        data-testid="email"
        value={email}
        onChange={(e) => onEmailChange(e.target.value)}
      />
      <input
        data-testid="password"
        value={password}
        onChange={(e) => onPasswordChange(e.target.value)}
      />
      <form
        onSubmit={onSubmit}
        data-testid="login-form-element"
      >
        <button type="submit">Submit</button>
      </form>
      {isLoading && <span data-testid="loading">Loading</span>}
      {error && <span data-testid="error">{error}</span>}
    </div>
  ),
}))

vi.mock('@/lib/api', () => ({
  API_BASE: '/api',
  setDemoProfile: vi.fn(),
  demoLogin: vi.fn().mockResolvedValue(null),
  getAuthHeaders: () => ({}),
}))

vi.mock('@/hooks/use-theme', () => ({
  cssTheme: (id: string) => id,
}))

vi.mock('@/components/auth/login-data', () => ({
  DEMO_PROFILES_BY_ROLE: {
    teacher: [{ key: 'teacher', name: 'Teacher', route: '/dashboard', color: 'blue', avatar: 'T', description: '' }],
    student: [],
    parent: [],
    school_admin: [],
    super_admin: [],
  },
}))

const pushMock = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock, replace: vi.fn(), back: vi.fn(), forward: vi.fn(), refresh: vi.fn(), prefetch: vi.fn() }),
  useParams: () => ({ locale: 'en' }),
  usePathname: () => '/en/login',
  useSearchParams: () => new URLSearchParams(),
  notFound: vi.fn(),
  redirect: vi.fn(),
}))

describe('LoginPage', () => {
  const user = userEvent.setup()

  beforeEach(async () => {
    pushMock.mockReset()
    useAuthStore.setState({ user: null, token: null, isAuthenticated: false })
    useAccessibilityStore.setState({ theme: 'standard' })
    vi.mocked(await import('@/lib/api')).setDemoProfile.mockClear()
  })

  it('renders role selection phase initially', () => {
    render(<LoginPage />)
    expect(screen.getByTestId('role-selection')).toBeInTheDocument()
    expect(screen.queryByTestId('login-form')).not.toBeInTheDocument()
  })

  it('renders title and subtitle', () => {
    render(<LoginPage />)
    expect(screen.getByText('login.title')).toBeInTheDocument()
    expect(screen.getByText('login.subtitle')).toBeInTheDocument()
  })

  it('transitions to login form when role is selected', async () => {
    render(<LoginPage />)
    await user.click(screen.getByText('Select Teacher'))
    expect(screen.getByTestId('login-form')).toBeInTheDocument()
    expect(screen.getByTestId('selected-role')).toHaveTextContent('teacher')
  })

  it('transitions back to role selection when back is clicked', async () => {
    render(<LoginPage />)
    await user.click(screen.getByText('Select Teacher'))
    expect(screen.getByTestId('login-form')).toBeInTheDocument()

    await user.click(screen.getByText('Back'))
    expect(screen.getByTestId('role-selection')).toBeInTheDocument()
  })

  it('handles demo login by setting profile and navigating', async () => {
    const { setDemoProfile } = await import('@/lib/api')
    render(<LoginPage />)
    await user.click(screen.getByText('Select Teacher'))
    await user.click(screen.getByText('Demo Teacher'))

    expect(setDemoProfile).toHaveBeenCalledWith('teacher')
    expect(pushMock).toHaveBeenCalledWith('/en/dashboard')
  })

  it('handles demo login with accessibility profile', async () => {
    render(<LoginPage />)
    await user.click(screen.getByText('Select Student'))
    await user.click(screen.getByText('Demo Student ASD'))

    expect(pushMock).toHaveBeenCalledWith('/en/tutors')
    // The accessibility theme should be set
    const a11yState = useAccessibilityStore.getState()
    expect(a11yState.theme).toBe('tea')
  })

  it('handles email login success', async () => {
    const loginFn = vi.fn()
    useAuthStore.setState({ login: loginFn } as never)

    // Mock successful fetch
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          access_token: 'jwt-123',
          user: {
            id: 'u1',
            email: 'test@example.com',
            display_name: 'Test',
            role: 'teacher',
            locale: 'en',
            avatar_url: '',
            accessibility_profile: 'standard',
            is_active: true,
          },
        }),
    })

    render(<LoginPage />)
    await user.click(screen.getByText('Select Teacher'))

    // Type email and password
    await user.type(screen.getByTestId('email'), 'test@example.com')
    await user.type(screen.getByTestId('password'), 'password123')

    // Submit form
    await user.click(screen.getByText('Submit'))

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/auth/login',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ email: 'test@example.com', password: 'password123', role: 'teacher' }),
      }),
    )
    expect(loginFn).toHaveBeenCalledWith('jwt-123', expect.objectContaining({ id: 'u1' }))
    expect(pushMock).toHaveBeenCalledWith('/en/dashboard')
  })

  it('handles email login failure', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({ detail: 'Invalid credentials' }),
    })

    render(<LoginPage />)
    await user.click(screen.getByText('Select Teacher'))
    await user.type(screen.getByTestId('email'), 'bad@example.com')
    await user.type(screen.getByTestId('password'), 'wrong')
    await user.click(screen.getByText('Submit'))

    // Wait for error to appear
    expect(await screen.findByTestId('error')).toHaveTextContent('Invalid credentials')
  })

  it('renders main landmark element', () => {
    render(<LoginPage />)
    expect(screen.getByRole('main')).toBeInTheDocument()
  })
})

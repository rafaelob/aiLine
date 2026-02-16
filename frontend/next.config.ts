import type { NextConfig } from 'next'
import createNextIntlPlugin from 'next-intl/plugin'

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts')

const nextConfig: NextConfig = {
  reactCompiler: true,
  compress: false, // Required for SSE streaming (ADR-006)
  typedRoutes: true,
  output: 'standalone', // Required for Docker multi-stage builds
  async rewrites() {
    const apiUrl = process.env.API_INTERNAL_URL ?? 'http://localhost:8000'
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/:path*`,
      },
    ]
  },
}

export default withNextIntl(nextConfig)

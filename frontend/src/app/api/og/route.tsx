import { ImageResponse } from 'next/og'
import type { NextRequest } from 'next/server'

export const runtime = 'edge'

/**
 * Dynamic Open Graph image generator for social preview cards.
 *
 * Usage: /api/og?title=My+Plan&subtitle=5th+Grade+Math
 *
 * Renders a branded card with the AiLine logo, title, and subtitle
 * at 1200x630 (standard OG image dimensions).
 */
export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl
  const title = searchParams.get('title') ?? 'AiLine'
  const subtitle =
    searchParams.get('subtitle') ?? 'Adaptive Inclusive Learning'

  return new ImageResponse(
    (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          width: '100%',
          height: '100%',
          background: 'linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #60a5fa 100%)',
          fontFamily: 'sans-serif',
          color: '#ffffff',
          padding: '60px',
        }}
      >
        {/* Logo area */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '16px',
            marginBottom: '40px',
          }}
        >
          <div
            style={{
              width: '64px',
              height: '64px',
              borderRadius: '16px',
              background: 'rgba(255, 255, 255, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '32px',
              fontWeight: 700,
            }}
          >
            A
          </div>
          <span style={{ fontSize: '36px', fontWeight: 700, letterSpacing: '-0.02em' }}>
            AiLine
          </span>
        </div>

        {/* Title */}
        <div
          style={{
            fontSize: '56px',
            fontWeight: 700,
            textAlign: 'center',
            lineHeight: 1.2,
            maxWidth: '900px',
            marginBottom: '16px',
          }}
        >
          {title}
        </div>

        {/* Subtitle */}
        <div
          style={{
            fontSize: '28px',
            fontWeight: 400,
            textAlign: 'center',
            opacity: 0.85,
            maxWidth: '800px',
          }}
        >
          {subtitle}
        </div>

        {/* Footer tag */}
        <div
          style={{
            position: 'absolute',
            bottom: '30px',
            right: '40px',
            fontSize: '18px',
            opacity: 0.6,
          }}
        >
          ailine.app
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
    },
  )
}

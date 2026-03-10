import * as React from "react"

export type SvgSize = "inline" | "spot" | "hero" | "full"

export interface BaseClaySvgProps extends React.SVGProps<SVGSVGElement> {
  children: React.ReactNode
  primaryColor?: string
  secondaryColor?: string
  accentColor?: string
  size?: SvgSize
  title?: string
  desc?: string
  decorative?: boolean
}

const sizeMap: Record<SvgSize, number> = {
  inline: 24,
  spot: 120,
  hero: 240,
  full: 400,
}

export const BaseClaySvg = React.forwardRef<SVGSVGElement, BaseClaySvgProps>(
  (
    {
      children,
      primaryColor = "var(--theme-primary, #6366f1)",
      secondaryColor = "var(--theme-secondary, #a855f7)",
      accentColor = "var(--theme-accent, #ec4899)",
      size = "hero",
      title,
      desc,
      decorative = true,
      className,
      viewBox = "0 0 400 400",
      ...props
    },
    ref
  ) => {
    const titleId = React.useId(); const finalTitleId = title ? titleId : undefined
    const descId = React.useId(); const finalDescId = desc ? descId : undefined
    const ariaLabelledBy = [finalTitleId, finalDescId].filter(Boolean).join(" ") || undefined

    const width = sizeMap[size] || sizeMap.hero

    return (
      <svg
        ref={ref}
        xmlns="http://www.w3.org/2000/svg"
        viewBox={viewBox}
        width="100%"
        height="100%"
        style={{ maxWidth: width, maxHeight: width }}
        className={`clay-illustration transition-all duration-500 ease-in-out ${className || ""}`}
        role={decorative ? "presentation" : "img"}
        aria-hidden={decorative ? "true" : undefined}
        aria-labelledby={!decorative ? ariaLabelledBy : undefined}
        {...props}
      >
        {title && <title id={finalTitleId}>{title}</title>}
        {desc && <desc id={finalDescId}>{desc}</desc>}

        <defs>
          {/* Soft Clay Grain Texture + 3D Lighting */}
          <filter id="clay-effect" x="-20%" y="-20%" width="140%" height="140%">
            {/* Base Drop Shadow */}
            <feDropShadow dx="0" dy="8" stdDeviation="12" floodColor={primaryColor} floodOpacity="0.25" result="shadow" />
            
            {/* Grain Texture */}
            <feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="3" result="noise" />
            <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.1 0" in="noise" result="coloredNoise" />
            
            {/* Inner Highlight for "3D" feel */}
            <feOffset dx="-2" dy="-2" in="SourceAlpha" result="offsetHighlight" />
            <feGaussianBlur stdDeviation="3" in="offsetHighlight" result="blurHighlight" />
            <feComposite operator="out" in="SourceAlpha" in2="blurHighlight" result="inverseHighlight" />
            <feFlood floodColor="white" floodOpacity="0.8" result="highlightColor" />
            <feComposite operator="in" in="highlightColor" in2="inverseHighlight" result="innerHighlight" />

            {/* Inner Shadow for "Clay" depth */}
            <feOffset dx="4" dy="4" in="SourceAlpha" result="offsetShadow" />
            <feGaussianBlur stdDeviation="4" in="offsetShadow" result="blurShadow" />
            <feComposite operator="out" in="SourceAlpha" in2="blurShadow" result="inverseShadow" />
            <feFlood floodColor="black" floodOpacity="0.15" result="shadowColor" />
            <feComposite operator="in" in="shadowColor" in2="inverseShadow" result="innerShadow" />

            {/* Blend it all together */}
            <feBlend in="SourceGraphic" in2="coloredNoise" mode="multiply" result="texturedBase" />
            <feBlend in="innerHighlight" in2="texturedBase" mode="screen" result="highlightedBase" />
            <feBlend in="innerShadow" in2="highlightedBase" mode="multiply" result="finalClay" />
            
            {/* Combine with Drop Shadow */}
            <feMerge>
              <feMergeNode in="shadow" />
              <feMergeNode in="finalClay" />
            </feMerge>
          </filter>
          
          <linearGradient id="clay-grad-primary" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={primaryColor} stopOpacity="0.85" />
            <stop offset="100%" stopColor={primaryColor} stopOpacity="1" />
          </linearGradient>

          <linearGradient id="clay-grad-secondary" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={secondaryColor} stopOpacity="0.8" />
            <stop offset="100%" stopColor={secondaryColor} stopOpacity="1" />
          </linearGradient>

          <linearGradient id="clay-grad-accent" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={accentColor} stopOpacity="0.9" />
            <stop offset="100%" stopColor={accentColor} stopOpacity="1" />
          </linearGradient>
        </defs>

        <g filter="url(#clay-effect)">
          {children}
        </g>
      </svg>
    )
  }
)

BaseClaySvg.displayName = "BaseClaySvg"

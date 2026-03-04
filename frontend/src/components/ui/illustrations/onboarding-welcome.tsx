import * as React from "react"
import { BaseClaySvg, BaseClaySvgProps } from "./base-clay-svg"

export const OnboardingWelcome = React.forwardRef<SVGSVGElement, Omit<BaseClaySvgProps, "children">>((props, ref) => {
  return (
    <BaseClaySvg
      ref={ref}
      viewBox="0 0 400 400"
      title={props.title || "Welcome to AiLine"}
      desc={props.desc || "A diverse group of pebble characters waving in front of a school building."}
      decorative={props.decorative ?? false}
      {...props}
    >
      {/* Background School Building */}
      <rect x="80" y="100" width="240" height="200" rx="30" fill="url(#clay-grad-secondary)" opacity="0.4" />
      <rect x="160" y="180" width="80" height="120" rx="40" fill="url(#clay-grad-secondary)" opacity="0.6" />
      <circle cx="200" cy="140" r="20" fill="url(#clay-grad-accent)" opacity="0.5" />

      {/* Ground */}
      <ellipse cx="200" cy="350" rx="250" ry="80" fill="url(#clay-grad-secondary)" opacity="0.3" />

      {/* Pebble Character 1 (Left - Waving) */}
      <g transform="translate(60, 220)">
        <rect x="0" y="0" width="70" height="90" rx="35" fill="url(#clay-grad-primary)" />
        {/* Eyes */}
        <circle cx="25" cy="35" r="5" fill="#1e1e1e" />
        <circle cx="45" cy="35" r="5" fill="#1e1e1e" />
        {/* Smile */}
        <path d="M 25,50 Q 35,60 45,50" fill="none" stroke="#1e1e1e" strokeWidth="4" strokeLinecap="round" />
        {/* Waving Arm */}
        <path d="M 60,40 Q 80,10 90,30" fill="none" stroke="url(#clay-grad-primary)" strokeWidth="14" strokeLinecap="round" />
      </g>

      {/* Pebble Character 2 (Center - Jumping) */}
      <g transform="translate(150, 200)">
        <rect x="0" y="0" width="80" height="100" rx="40" fill="url(#clay-grad-accent)" />
        {/* Eyes */}
        <circle cx="30" cy="40" r="6" fill="#1e1e1e" />
        <circle cx="50" cy="40" r="6" fill="#1e1e1e" />
        {/* Big Smile */}
        <path d="M 25,60 Q 40,75 55,60" fill="none" stroke="#1e1e1e" strokeWidth="5" strokeLinecap="round" />
        {/* Arms up */}
        <path d="M 10,40 Q -10,10 -20,20" fill="none" stroke="url(#clay-grad-accent)" strokeWidth="16" strokeLinecap="round" />
        <path d="M 70,40 Q 90,10 100,20" fill="none" stroke="url(#clay-grad-accent)" strokeWidth="16" strokeLinecap="round" />
      </g>

      {/* Pebble Character 3 (Right - Friendly) */}
      <g transform="translate(250, 230)">
        <rect x="0" y="0" width="75" height="95" rx="37.5" fill="url(#clay-grad-primary)" />
        {/* Eyes */}
        <circle cx="25" cy="35" r="5" fill="#1e1e1e" />
        <circle cx="45" cy="35" r="5" fill="#1e1e1e" />
        {/* Smile */}
        <path d="M 25,50 Q 35,55 45,50" fill="none" stroke="#1e1e1e" strokeWidth="4" strokeLinecap="round" />
        {/* Holding an object (book/tablet) */}
        <rect x="20" y="60" width="40" height="30" rx="8" fill="url(#clay-grad-secondary)" />
        <path d="M 10,60 Q 20,70 30,65" fill="none" stroke="url(#clay-grad-primary)" strokeWidth="14" strokeLinecap="round" />
      </g>

    </BaseClaySvg>
  )
})

OnboardingWelcome.displayName = "OnboardingWelcome"

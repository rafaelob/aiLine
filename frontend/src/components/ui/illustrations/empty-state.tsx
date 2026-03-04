import * as React from "react"
import { BaseClaySvg, BaseClaySvgProps } from "./base-clay-svg"

export const EmptyStateTelescope = React.forwardRef<SVGSVGElement, Omit<BaseClaySvgProps, "children">>((props, ref) => {
  return (
    <BaseClaySvg
      ref={ref}
      viewBox="0 0 400 400"
      title={props.title || "Telescope exploring stars"}
      desc={props.desc || "A pebble character looking through a telescope at glowing stars."}
      decorative={props.decorative ?? false}
      {...props}
    >
      {/* Background Stars / Sparkles */}
      <circle cx="80" cy="100" r="8" fill="url(#clay-grad-accent)" />
      <circle cx="320" cy="140" r="12" fill="url(#clay-grad-secondary)" />
      <circle cx="120" cy="240" r="6" fill="url(#clay-grad-secondary)" />
      <path d="M 280,60 Q 285,75 300,80 Q 285,85 280,100 Q 275,85 260,80 Q 275,75 280,60" fill="url(#clay-grad-accent)" />

      {/* Hill/Ground */}
      <path d="M 0,400 Q 200,320 400,400 Z" fill="url(#clay-grad-secondary)" opacity="0.4" />

      {/* Telescope Stand */}
      <path d="M 220,280 L 190,360 L 210,360 L 230,280 Z" fill="url(#clay-grad-secondary)" />
      <path d="M 220,280 L 250,360 L 230,360 L 210,280 Z" fill="url(#clay-grad-secondary)" />
      
      {/* Telescope Tube (Rounded) */}
      <rect x="140" y="200" width="160" height="40" rx="20" transform="rotate(-30 220 220)" fill="url(#clay-grad-primary)" />
      <rect x="120" y="190" width="40" height="60" rx="10" transform="rotate(-30 220 220)" fill="url(#clay-grad-accent)" />
      <rect x="290" y="205" width="30" height="30" rx="8" transform="rotate(-30 220 220)" fill="url(#clay-grad-secondary)" />

      {/* Pebble Character */}
      <rect x="100" y="240" width="80" height="110" rx="40" fill="url(#clay-grad-primary)" />
      {/* Eyes */}
      <circle cx="150" cy="270" r="6" fill="#1e1e1e" />
      <circle cx="170" cy="270" r="6" fill="#1e1e1e" />
      {/* Arm holding telescope */}
      <path d="M 120,290 Q 140,320 180,260" fill="none" stroke="url(#clay-grad-primary)" strokeWidth="16" strokeLinecap="round" />
    </BaseClaySvg>
  )
})

EmptyStateTelescope.displayName = "EmptyStateTelescope"

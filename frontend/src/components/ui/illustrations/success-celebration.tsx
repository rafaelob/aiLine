import * as React from "react"
import { BaseClaySvg, BaseClaySvgProps } from "./base-clay-svg"

export const SuccessCelebration = React.forwardRef<SVGSVGElement, Omit<BaseClaySvgProps, "children">>((props, ref) => {
  return (
    <BaseClaySvg
      ref={ref}
      viewBox="0 0 400 400"
      title={props.title || "Success Celebration"}
      desc={props.desc || "Pebble characters celebrating with a trophy and confetti in a dignified manner."}
      decorative={props.decorative ?? false}
      {...props}
    >
      {/* Background Soft Glow */}
      <circle cx="200" cy="200" r="160" fill="url(#clay-grad-secondary)" opacity="0.15" />

      {/* Confetti Particles */}
      <rect x="80" y="80" width="10" height="20" rx="4" transform="rotate(45 80 80)" fill="url(#clay-grad-accent)" />
      <circle cx="320" cy="100" r="8" fill="url(#clay-grad-primary)" />
      <rect x="280" y="60" width="12" height="12" rx="3" transform="rotate(-20 280 60)" fill="url(#clay-grad-secondary)" />
      <circle cx="100" cy="250" r="6" fill="url(#clay-grad-accent)" />
      <rect x="330" y="220" width="8" height="16" rx="4" transform="rotate(15 330 220)" fill="url(#clay-grad-primary)" />

      {/* Trophy Centerpiece */}
      <g transform="translate(160, 160)">
        {/* Trophy Base */}
        <path d="M 20,120 L 60,120 L 50,140 L 30,140 Z" fill="url(#clay-grad-secondary)" />
        {/* Trophy Cup */}
        <path d="M 0,0 Q 40,100 80,0 Z" fill="url(#clay-grad-accent)" />
        {/* Trophy Handles */}
        <path d="M 0,20 C -20,10 -20,60 10,70" fill="none" stroke="url(#clay-grad-accent)" strokeWidth="6" strokeLinecap="round" />
        <path d="M 80,20 C 100,10 100,60 70,70" fill="none" stroke="url(#clay-grad-accent)" strokeWidth="6" strokeLinecap="round" />
      </g>

      {/* Left Character (Cheering) */}
      <g transform="translate(80, 200)">
        <rect x="0" y="0" width="70" height="90" rx="35" fill="url(#clay-grad-primary)" />
        <circle cx="25" cy="30" r="5" fill="#1e1e1e" />
        <circle cx="45" cy="30" r="5" fill="#1e1e1e" />
        {/* Happy closed smile */}
        <path d="M 25,45 Q 35,55 45,45" fill="none" stroke="#1e1e1e" strokeWidth="4" strokeLinecap="round" />
        <path d="M 10,40 Q -10,0 0, -10" fill="none" stroke="url(#clay-grad-primary)" strokeWidth="12" strokeLinecap="round" />
      </g>

      {/* Right Character (Holding Trophy Base) */}
      <g transform="translate(240, 220)">
        <rect x="0" y="0" width="75" height="95" rx="37.5" fill="url(#clay-grad-primary)" />
        <circle cx="25" cy="35" r="5" fill="#1e1e1e" />
        <circle cx="45" cy="35" r="5" fill="#1e1e1e" />
        <path d="M 25,50 Q 35,60 45,50" fill="none" stroke="#1e1e1e" strokeWidth="4" strokeLinecap="round" />
        <path d="M 15,55 Q -10,60 -30,40" fill="none" stroke="url(#clay-grad-primary)" strokeWidth="12" strokeLinecap="round" />
      </g>

    </BaseClaySvg>
  )
})

SuccessCelebration.displayName = "SuccessCelebration"

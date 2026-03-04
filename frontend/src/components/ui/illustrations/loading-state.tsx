import * as React from "react"
import { BaseClaySvg, BaseClaySvgProps } from "./base-clay-svg"

export const LoadingStateBlocks = React.forwardRef<SVGSVGElement, Omit<BaseClaySvgProps, "children">>((props, ref) => {
  return (
    <BaseClaySvg
      ref={ref}
      viewBox="0 0 400 400"
      title={props.title || "Loading content"}
      desc={props.desc || "A pebble character stacking colorful blocks progressively."}
      decorative={props.decorative ?? true}
      {...props}
    >
      {/* Background soft area */}
      <ellipse cx="200" cy="300" rx="150" ry="50" fill="url(#clay-grad-secondary)" opacity="0.2" />

      {/* Stacked Blocks */}
      <g transform="translate(200, 120)">
        {/* Bottom Block */}
        <rect x="0" y="100" width="60" height="40" rx="10" fill="url(#clay-grad-secondary)" />
        {/* Middle Block */}
        <rect x="5" y="60" width="50" height="40" rx="8" fill="url(#clay-grad-accent)" />
        {/* Floating/Animating Top Block */}
        <rect x="10" y="0" width="40" height="40" rx="8" fill="url(#clay-grad-primary)">
          <animate attributeName="y" values="0; 20; 0" dur="2s" repeatCount="indefinite" />
        </rect>
      </g>

      {/* Pebble Character (Focused on stacking) */}
      <g transform="translate(100, 160)">
        <rect x="0" y="0" width="80" height="110" rx="40" fill="url(#clay-grad-primary)" />
        {/* Eyes (Looking slightly up and right at the blocks) */}
        <circle cx="55" cy="40" r="5" fill="#1e1e1e" />
        <circle cx="75" cy="40" r="5" fill="#1e1e1e" />
        {/* Focused neutral expression */}
        <line x1="60" y1="55" x2="70" y2="55" stroke="#1e1e1e" strokeWidth="4" strokeLinecap="round" />
        
        {/* Arm reaching out to the floating block */}
        <path d="M 50,60 Q 80,40 100,60" fill="none" stroke="url(#clay-grad-primary)" strokeWidth="12" strokeLinecap="round">
          <animate attributeName="d" values="M 50,60 Q 80,40 100,60; M 50,60 Q 80,60 100,80; M 50,60 Q 80,40 100,60" dur="2s" repeatCount="indefinite" />
        </path>
      </g>

    </BaseClaySvg>
  )
})

LoadingStateBlocks.displayName = "LoadingStateBlocks"

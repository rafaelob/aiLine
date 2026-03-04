import * as React from "react"
import { BaseClaySvg, BaseClaySvgProps } from "./base-clay-svg"

export const ErrorGentle = React.forwardRef<SVGSVGElement, Omit<BaseClaySvgProps, "children">>((props, ref) => {
  return (
    <BaseClaySvg
      ref={ref}
      viewBox="0 0 400 400"
      title={props.title || "Let's untangle this"}
      desc={props.desc || "A pebble character sitting next to a tangled yarn ball, looking calm and ready to help."}
      decorative={props.decorative ?? false}
      {...props}
    >
      {/* Background soft blob */}
      <circle cx="200" cy="220" r="140" fill="url(#clay-grad-secondary)" opacity="0.2" />

      {/* Tangled Yarn Ball (Represents the Error) */}
      <g transform="translate(220, 200)">
        <circle cx="50" cy="50" r="45" fill="url(#clay-grad-accent)" opacity="0.8" />
        {/* Tangled strands */}
        <path d="M 20,30 Q 80,10 60,60 T 40,80 Q 10,50 30,20" fill="none" stroke="url(#clay-grad-accent)" strokeWidth="6" strokeLinecap="round" />
        <path d="M 80,40 Q 20,30 40,70 T 70,80 Q 90,50 60,20" fill="none" stroke="url(#clay-grad-secondary)" strokeWidth="4" strokeLinecap="round" opacity="0.6" />
        <path d="M 30,50 Q 50,80 80,50" fill="none" stroke="url(#clay-grad-primary)" strokeWidth="5" strokeLinecap="round" opacity="0.5" />
        
        {/* Loose string */}
        <path d="M -80,90 Q -30,110 15,80" fill="none" stroke="url(#clay-grad-accent)" strokeWidth="6" strokeLinecap="round" />
      </g>

      {/* Pebble Character (Sitting calmly) */}
      <g transform="translate(80, 180)">
        <rect x="0" y="0" width="85" height="110" rx="42.5" fill="url(#clay-grad-primary)" />
        {/* Eyes (Calm, looking slightly down at the yarn) */}
        <circle cx="55" cy="40" r="5.5" fill="#1e1e1e" />
        <circle cx="75" cy="40" r="5.5" fill="#1e1e1e" />
        {/* Gentle supportive smile */}
        <path d="M 60,55 Q 65,60 70,55" fill="none" stroke="#1e1e1e" strokeWidth="4" strokeLinecap="round" />
        
        {/* Arm holding the loose string */}
        <path d="M 40,60 Q 60,90 80,85" fill="none" stroke="url(#clay-grad-primary)" strokeWidth="15" strokeLinecap="round" />
        
        {/* Legs sitting */}
        <path d="M 20,100 Q 20,130 50,130" fill="none" stroke="url(#clay-grad-primary)" strokeWidth="16" strokeLinecap="round" />
      </g>

    </BaseClaySvg>
  )
})

ErrorGentle.displayName = "ErrorGentle"

import * as React from "react"
import { BaseClaySvg, BaseClaySvgProps } from "./base-clay-svg"

export type PersonaType = "teacher" | "student-asd" | "student-adhd" | "student-dyslexia" | "parent"

export interface PersonaAvatarProps extends Omit<BaseClaySvgProps, "children"> {
  persona: PersonaType
}

export const PersonaAvatar = React.forwardRef<SVGSVGElement, PersonaAvatarProps>(
  ({ persona, ...props }, ref) => {
    
    const titles: Record<PersonaType, string> = {
      "teacher": "Teacher Avatar",
      "student-asd": "Student Avatar (ASD)",
      "student-adhd": "Student Avatar (ADHD)",
      "student-dyslexia": "Student Avatar (Dyslexia)",
      "parent": "Parent Avatar",
    }
    
    return (
      <BaseClaySvg
        ref={ref}
        viewBox="0 0 200 200"
        title={props.title || titles[persona]}
        decorative={props.decorative ?? false}
        {...props}
      >
        {/* Soft Background Circle */}
        <circle cx="100" cy="100" r="90" fill="url(#clay-grad-secondary)" opacity="0.3" />

        {/* Base Pebble Body (Shared) */}
        <rect x="60" y="70" width="80" height="100" rx="40" fill="url(#clay-grad-primary)" />
        
        {/* Base Eyes */}
        <circle cx="85" cy="100" r="5" fill="#1e1e1e" />
        <circle cx="115" cy="100" r="5" fill="#1e1e1e" />
        
        {/* Base Smile */}
        <path d="M 90,115 Q 100,125 110,115" fill="none" stroke="#1e1e1e" strokeWidth="4" strokeLinecap="round" />

        {/* Persona Specific Details */}
        {persona === "teacher" && (
          <g>
            {/* Glasses */}
            <rect x="70" y="90" width="25" height="20" rx="6" fill="none" stroke="url(#clay-grad-accent)" strokeWidth="3" />
            <rect x="105" y="90" width="25" height="20" rx="6" fill="none" stroke="url(#clay-grad-accent)" strokeWidth="3" />
            <line x1="95" y1="100" x2="105" y2="100" stroke="url(#clay-grad-accent)" strokeWidth="3" />
            {/* Pointer / Book */}
            <rect x="65" y="130" width="30" height="40" rx="4" fill="url(#clay-grad-secondary)" />
          </g>
        )}

        {persona === "student-asd" && (
          <g>
            {/* Noise-canceling headphones */}
            <path d="M 60,100 Q 60,60 100,60 T 140,100" fill="none" stroke="url(#clay-grad-accent)" strokeWidth="8" strokeLinecap="round" />
            <rect x="50" y="85" width="15" height="30" rx="7.5" fill="url(#clay-grad-secondary)" />
            <rect x="135" y="85" width="15" height="30" rx="7.5" fill="url(#clay-grad-secondary)" />
          </g>
        )}

        {persona === "student-adhd" && (
          <g>
            {/* Fidget toy in hand */}
            <circle cx="70" cy="140" r="12" fill="url(#clay-grad-accent)" />
            <circle cx="85" cy="135" r="8" fill="url(#clay-grad-secondary)" />
            <circle cx="65" cy="155" r="8" fill="url(#clay-grad-secondary)" />
            {/* Active posture (arm waving slightly) */}
            <path d="M 60,120 Q 40,110 50,130" fill="none" stroke="url(#clay-grad-primary)" strokeWidth="10" strokeLinecap="round" />
          </g>
        )}

        {persona === "student-dyslexia" && (
          <g>
            {/* Book with reading ruler */}
            <rect x="70" y="130" width="60" height="30" rx="5" fill="url(#clay-grad-secondary)" />
            <line x1="75" y1="140" x2="125" y2="140" stroke="url(#clay-grad-accent)" strokeWidth="4" strokeLinecap="round" />
            {/* Hand holding it */}
            <path d="M 60,120 Q 65,140 75,145" fill="none" stroke="url(#clay-grad-primary)" strokeWidth="10" strokeLinecap="round" />
          </g>
        )}

        {persona === "parent" && (
          <g>
            {/* Heart symbol indicating care */}
            <path d="M 120,130 A 10,10 0 0,1 140,130 A 10,10 0 0,1 160,130 Q 160,150 140,165 Q 120,150 120,130 Z" fill="url(#clay-grad-accent)" />
            {/* Arm gently resting */}
            <path d="M 130,110 Q 150,130 140,140" fill="none" stroke="url(#clay-grad-primary)" strokeWidth="12" strokeLinecap="round" />
          </g>
        )}
      </BaseClaySvg>
    )
  }
)

PersonaAvatar.displayName = "PersonaAvatar"

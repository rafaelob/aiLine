import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

// MEGA SPRINT 37: Soft Clay Bento Card
// Core layout primitive for Dashboard and views.
const cardVariants = cva(
  "rounded-3xl border-2 bg-card text-card-foreground shadow-sm overflow-hidden transition-all duration-300",
  {
    variants: {
      variant: {
        default: "border-muted shadow-sm hover:shadow-md",
        interactive: "border-muted shadow-sm hover:border-primary/50 hover:shadow-lg hover:-translate-y-1 cursor-pointer",
        clay: "border-transparent bg-white/80 backdrop-blur-md shadow-[0_8px_30px_rgb(0,0,0,0.04)]",
        focus: "border-primary shadow-[0_0_0_4px_rgba(29,78,216,0.1)]", // Visual focus without ring
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, ...props }, ref) => (
    <div
      ref={ref}
      className={cardVariants({ variant, className })}
      {...props}
    />
  )
)
Card.displayName = "Card"

// ... Additional sub-components like CardHeader, CardTitle, CardContent, CardFooter omitted for brevity in planning phase.

export { Card, cardVariants }
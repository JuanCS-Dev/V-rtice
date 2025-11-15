import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

/**
 * Button variants using class-variance-authority
 * Follows Vértice design system (GREEN primary, clean aesthetic)
 */
const buttonVariants = cva(
  // Base styles
  "inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        // Primary - GREEN (#10b981)
        primary:
          "bg-primary-500 text-white hover:bg-primary-600 active:bg-primary-700 shadow-sm",
        // Secondary - Subtle gray
        secondary:
          "bg-gray-100 text-gray-900 hover:bg-gray-200 active:bg-gray-300 dark:bg-gray-800 dark:text-gray-100 dark:hover:bg-gray-700",
        // Outline - Border only
        outline:
          "border border-gray-300 bg-transparent hover:bg-gray-50 active:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-900",
        // Ghost - Minimal
        ghost:
          "hover:bg-gray-100 active:bg-gray-200 dark:hover:bg-gray-900 dark:active:bg-gray-800",
        // Destructive - Red
        destructive:
          "bg-red-600 text-white hover:bg-red-700 active:bg-red-800 shadow-sm",
        // Link - Text only
        link: "text-primary-500 underline-offset-4 hover:underline",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-10 px-4 text-sm",
        lg: "h-12 px-6 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /**
   * If true, the button will render as its child element (useful for custom components)
   */
  asChild?: boolean;
}

/**
 * Button Component
 *
 * Clean, accessible button following WCAG 2.1 AA standards.
 * Supports multiple variants, sizes, and states.
 *
 * @example
 * ```tsx
 * <Button variant="primary" size="md">Click me</Button>
 * <Button variant="outline" size="lg" disabled>Disabled</Button>
 * <Button asChild><Link to="/home">Go Home</Link></Button>
 * ```
 */
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  },
);

Button.displayName = "Button";

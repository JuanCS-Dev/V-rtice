import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const spinnerVariants = cva(
  "animate-spin rounded-full border-2 border-current border-t-transparent",
  {
    variants: {
      size: {
        sm: "h-4 w-4",
        md: "h-6 w-6",
        lg: "h-8 w-8",
        xl: "h-12 w-12",
      },
      variant: {
        primary: "text-primary-500",
        secondary: "text-gray-500",
        white: "text-white",
      },
    },
    defaultVariants: {
      size: "md",
      variant: "primary",
    },
  },
);

export interface LoadingSpinnerProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof spinnerVariants> {
  label?: string;
}

export const LoadingSpinner = React.forwardRef<
  HTMLDivElement,
  LoadingSpinnerProps
>(({ className, size, variant, label = "Loading...", ...props }, ref) => {
  return (
    <div
      ref={ref}
      role="status"
      aria-live="polite"
      aria-label={label}
      className={cn("inline-block", className)}
      {...props}
    >
      <div className={cn(spinnerVariants({ size, variant }))} />
      <span className="sr-only">{label}</span>
    </div>
  );
});

LoadingSpinner.displayName = "LoadingSpinner";

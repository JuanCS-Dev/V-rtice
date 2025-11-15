import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary-500 text-white",
        secondary:
          "border-transparent bg-gray-200 text-gray-900 dark:bg-gray-800 dark:text-gray-100",
        success: "border-transparent bg-green-600 text-white",
        warning: "border-transparent bg-amber-500 text-white",
        danger: "border-transparent bg-red-600 text-white",
        info: "border-transparent bg-blue-600 text-white",
        outline: "border-current text-current",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(badgeVariants({ variant, className }))}
        {...props}
      />
    );
  },
);

Badge.displayName = "Badge";

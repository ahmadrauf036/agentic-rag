import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, ...rest }, ref) {
    return (
      <input
        ref={ref}
        className={cn(
          "h-10 w-full rounded-lg border border-border bg-surface px-3 text-sm text-fg",
          "placeholder:text-fg-muted transition-colors focus:border-accent focus:outline-none",
          "focus:shadow-[0_0_0_3px_rgb(99_168_248/0.2)]",
          className,
        )}
        {...rest}
      />
    );
  },
);
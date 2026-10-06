import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "icon";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
} & (
    | { size: "icon"; "aria-label": string }
    | { size?: "sm" | "md" }
  );

const variants: Record<Variant, string> = {
  primary:
    "bg-accent text-accent-fg shadow-glow hover:shadow-glow-lg hover:brightness-110 active:brightness-95",
  secondary: "bg-surface-2 text-fg border border-border hover:border-accent/60",
  ghost: "text-fg-muted hover:text-fg hover:bg-surface-2",
  danger: "bg-danger/15 text-danger hover:bg-danger/25",
};

const sizes: Record<Size, string> = {
  sm: "h-8 px-3 text-sm gap-1.5",
  md: "h-10 px-4 text-sm gap-2",
  icon: "h-9 w-9",
};

export const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  { variant = "primary", size = "md", className, type = "button", ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-lg font-medium",
        "transition-all duration-150 disabled:pointer-events-none disabled:opacity-40",
        variants[variant],
        sizes[size],
        className,
      )}
      {...rest}
    />
  );
});
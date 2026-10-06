import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

interface TooltipProps {
  label: string;
  children: ReactNode;
  side?: "top" | "bottom" | "right";
  className?: string;
}

const position = {
  top: "bottom-full left-1/2 mb-1.5 -translate-x-1/2",
  bottom: "top-full left-1/2 mt-1.5 -translate-x-1/2",
  right: "left-full top-1/2 ml-1.5 -translate-y-1/2",
};

export function Tooltip({ label, children, side = "top", className }: TooltipProps) {
  return (
    <span className={cn("group/tip relative inline-flex", className)}>
      {children}
      <span
        role="tooltip"
        className={cn(
          "pointer-events-none absolute z-40 whitespace-nowrap rounded-md border border-border",
          "bg-surface-2 px-2 py-1 text-xs text-fg opacity-0 transition-opacity duration-150",
          "group-hover/tip:opacity-100 group-hover/tip:delay-300 group-focus-within/tip:opacity-100",
          position[side],
        )}
      >
        {label}
      </span>
    </span>
  );
}
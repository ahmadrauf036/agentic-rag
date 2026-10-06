import type { ReactNode } from "react";
import { Button } from "@/components/ui/Button";
import { Tooltip } from "@/components/ui/ToolTip";
import { cn } from "@/lib/cn";

/** Hidden until hover/focus on desktop, always visible on touch. */
export const ACTIONS_ROW =
  "mt-1.5 flex items-center gap-0.5 transition-opacity " +
  "md:opacity-0 md:group-hover:opacity-100 md:group-focus-within:opacity-100";

interface Props {
  label: string;
  onClick: () => void;
  children: ReactNode;
  active?: boolean;
  disabled?: boolean;
}

export default function ActionButton({ label, onClick, children, active, disabled }: Props) {
  return (
    <Tooltip label={label} side="bottom">
      <Button
        size="icon"
        variant="ghost"
        aria-label={label}
        disabled={disabled}
        onClick={onClick}
        className={cn("h-7 w-7", active && "text-accent")}
      >
        {children}
      </Button>
    </Tooltip>
  );
}
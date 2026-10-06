import { Link } from "react-router-dom";
import { Trash2 } from "lucide-react";
import { cn } from "@/lib/cn";
import type { SessionInfo } from "@/types";

interface Props {
  session: SessionInfo;
  active: boolean;
  onNavigate: () => void;
  onDelete: (session: SessionInfo) => void;
}

export default function SessionItem({ session, active, onNavigate, onDelete }: Props) {
const title = session.title || "Untitled chat";
const paused = !!session.paused_reason;
  return (
    <li className="group relative">
      <Link
  to={`/chat/${session.thread_id}`}
  onClick={onNavigate}
  aria-current={active ? "page" : undefined}
  title={paused ? `${title} (paused: ${session.paused_reason})` : title}
  className={cn(
    "block truncate rounded-lg py-2 pl-3 pr-9 text-sm transition-colors",
    active
      ? "bg-surface-2 text-fg shadow-[inset_2px_0_0_var(--color-accent)]"
      : "text-fg-muted hover:bg-surface-2/60 hover:text-fg",
    paused && "line-through decoration-fg-muted/70 opacity-60",
  )}
>
  {title}
  {paused && <span className="sr-only"> (paused)</span>}
</Link>
      <button
        type="button"
        aria-label={`Delete chat: ${title}`}
        onClick={() => onDelete(session)}
        className={cn(
          "absolute right-1.5 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center",
          "rounded-md text-fg-muted transition-opacity hover:bg-danger/15 hover:text-danger",
          "md:opacity-0 md:group-hover:opacity-100 focus-visible:opacity-100",
          active && "md:opacity-100",
        )}
      >
        <Trash2 size={14} />
      </button>
    </li>
  );
}
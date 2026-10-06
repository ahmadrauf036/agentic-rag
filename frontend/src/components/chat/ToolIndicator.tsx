import { Check, Loader2 } from "lucide-react";
import type { ToolActivity } from "@/hooks/useChatStream";
import type { ToolName } from "@/types";

const LABELS: Record<ToolName, { running: string; done: string }> = {
  document_search: { running: "Searching documents…", done: "Searched documents" },
  calculator: { running: "Calculating…", done: "Calculated" },
  memory_search: { running: "Searching memory…", done: "Searched memory" },
  recent_sessions: { running: "Checking recent chats…", done: "Checked recent chats" },
  recent_messages: { running: "Checking recent messages…", done: "Checked recent messages" },
};

export default function ToolIndicator({ tools }: { tools: ToolActivity[] }) {
  if (tools.length === 0) return null;
  return (
    <div className="mb-3 flex flex-wrap gap-2" aria-live="polite">
      {tools.map((t) => {
        const label = LABELS[t.tool] ?? { running: `Running ${t.tool}…`, done: t.tool };
        return (
          <span
            key={t.id}
            className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-2.5 py-1 text-xs text-fg-muted"
          >
            {t.running ? (
              <Loader2 size={12} className="animate-spin text-accent" />
            ) : (
              <Check size={12} className="text-accent" />
            )}
            {t.running ? label.running : label.done}
          </span>
        );
      })}
    </div>
  );
}
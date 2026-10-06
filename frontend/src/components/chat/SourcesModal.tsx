import { FileText } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import type { Source } from "@/types";

interface Props {
  sources: Source[] | null; // null = closed
  onClose: () => void;
}

export default function SourcesModal({ sources, onClose }: Props) {
  return (
    <Modal open={sources !== null} onClose={onClose} title="Sources" className="max-w-xl">
      <ul className="space-y-3">
        {(sources ?? []).map((s, i) => (
          <li key={i} className="rounded-xl border border-border bg-surface-2 p-3">
            <div className="mb-1.5 flex items-center gap-2 text-sm font-medium">
              <FileText size={14} className="shrink-0 text-accent" />
              <span className="truncate">{s.source}</span>
              {s.page !== null && s.page !== undefined && (
                <span className="ml-auto shrink-0 text-xs font-normal text-fg-muted">
                  Page {s.page}
                </span>
              )}
            </div>
            <p className="whitespace-pre-wrap wrap-break-word text-sm text-fg-muted">{s.snippet}</p>
          </li>
        ))}
      </ul>
    </Modal>
  );
}
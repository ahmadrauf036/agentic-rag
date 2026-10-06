import { FileText } from "lucide-react";
import { useDocuments } from "@/context/DocumentContext";
import { Button } from "@/components/ui/Button";

interface Props {
  selectedCount: number;
  onOpenPicker: () => void;
}

export default function StartState({ selectedCount, onOpenPicker }: Props) {
  const { documents, loading } = useDocuments();
  const none = selectedCount === 0;

  return (
    <div className="flex flex-col items-center gap-3 py-20 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-2xl border border-border bg-surface text-accent shadow-glow">
        <FileText size={22} />
      </span>
      <h2 className="text-lg font-semibold">
        {none ? "Choose documents to chat with" : "Ready when you are"}
      </h2>
      <p className="max-w-sm text-sm text-fg-muted">
        {none
          ? "Pick one or more documents, then send your first message. The selection can't be changed afterwards."
          : `${selectedCount} document${selectedCount === 1 ? "" : "s"} selected. Type your first message below to start.`}
      </p>
      <Button
        variant={none ? "primary" : "secondary"}
        onClick={onOpenPicker}
        disabled={loading || documents.length === 0}
      >
        {none ? "Select document(s)" : "Change selection"}
      </Button>
      {!loading && documents.length === 0 && (
        <p className="text-xs text-fg-muted">No documents are available yet.</p>
      )}
    </div>
  );
}
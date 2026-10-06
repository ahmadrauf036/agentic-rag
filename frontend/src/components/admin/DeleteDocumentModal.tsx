import { useCallback, useEffect, useState } from "react";
import { AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import type { DocumentInfo } from "@/types";

/** TEMP: replace with the real shape once the backend documents /dependents. */
function parseDependents(raw: unknown): number {
  if (typeof raw === "number") return raw;
  if (Array.isArray(raw)) return raw.length;
  if (raw && typeof raw === "object") {
    const r = raw as Record<string, unknown>;
    for (const k of ["count", "dependent_sessions", "paused_sessions", "num_sessions", "total"]) {
      if (typeof r[k] === "number") return r[k] as number;
    }
    for (const k of ["sessions", "dependents"]) {
      if (Array.isArray(r[k])) return (r[k] as unknown[]).length;
    }
  }
  throw new Error("Unexpected response from the server.");
}

interface Props {
  doc: DocumentInfo | null; // null = closed
  onClose: () => void;
  onDeleted: (pausedSessions: number) => void;
}

export default function DeleteDocumentModal({ doc, onClose, onDeleted }: Props) {
  const [count, setCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  const hash = doc?.file_hash;

  useEffect(() => {
    if (!hash) return;
    let cancelled = false;
    setCount(null);
    setError(null);
    setDeleteError(null);
    setLoading(true);

    api.documents
      .dependents(hash)
      .then((raw: any) => {
        if (!cancelled) setCount(parseDependents(raw));
      })
      .catch((e:any) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Could not check affected chats");
      })
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, [hash, attempt]);

  const retry = useCallback(() => setAttempt((a) => a + 1), []);

  const close = () => {
    if (!deleting) onClose();
  };

  const confirm = async () => {
    if (!hash) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      const res = await api.documents.remove(hash);
      onDeleted(res.paused_sessions ?? 0);
    } catch (e) {
      setDeleteError(e instanceof Error ? e.message : "Could not delete the document");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Modal open={doc !== null} onClose={close} title="Delete document?" className="max-w-md">
      <p className="text-sm text-fg-muted">
        <span className="break-all text-fg">{doc?.source}</span> will be permanently removed from
        the shared library.
      </p>

      <div className="mt-4" aria-live="polite">
        {loading ? (
          <Skeleton className="h-14 w-full rounded-xl" />
        ) : error ? (
          <div role="alert" className="rounded-xl border border-danger/40 bg-danger/10 p-3 text-sm">
            <p className="text-danger">Couldn't check which chats this affects: {error}</p>
            <Button variant="secondary" size="sm" className="mt-2" onClick={retry}>
              Retry
            </Button>
          </div>
        ) : count !== null ? (
          count > 0 ? (
            <div className="flex items-start gap-2.5 rounded-xl border border-warning/40 bg-warning/10 p-3 text-sm text-warning">
              <AlertTriangle size={16} className="mt-0.5 shrink-0" />
              <p>
                This will pause <strong>{count}</strong> chat{count === 1 ? "" : "s"} across all
                users. They can no longer answer new questions. Re-uploading the same file resumes
                them.
              </p>
            </div>
          ) : (
            <p className="rounded-xl border border-border bg-surface-2 p-3 text-sm text-fg-muted">
              No chats use this document.
            </p>
          )
        ) : null}
      </div>

      {deleteError && (
        <p role="alert" className="mt-3 text-sm text-danger">
          {deleteError}
        </p>
      )}

      <div className="mt-5 flex justify-end gap-2">
        <Button variant="ghost" disabled={deleting} onClick={close}>
          Cancel
        </Button>
        <Button
          variant="danger"
          // Can't confirm until we know the impact
          disabled={deleting || loading || count === null}
          onClick={confirm}
        >
          {deleting ? "Deleting…" : "Delete"}
        </Button>
      </div>
    </Modal>
  );
}
import { useRef, useState, type DragEvent } from "react";
import { CheckCircle2, FileText, Info, Trash2, Upload, X } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useDocuments } from "@/context/DocumentContext";
import { useSessions } from "@/context/SessionsContext";
import { useToast } from "@/components/ui/Toast";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatBytes, validateFiles } from "@/lib/upload";
import { cn } from "@/lib/cn";
import type { DocumentInfo, UploadResult } from "@/types";
import DeleteDocumentModal from "./DeleteDocumentModal";

export default function DocumentsTab() {
  const { documents, loading, error, refresh } = useDocuments();
  const { refresh: refreshSessions } = useSessions();
  const toast = useToast();

  const inputRef = useRef<HTMLInputElement>(null);
  const [queue, setQueue] = useState<File[]>([]);
  const [rejected, setRejected] = useState<{ name: string; reason: string }[]>([]);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [result, setResult] = useState<UploadResult | null>(null);
    const [toDelete, setToDelete] = useState<DocumentInfo | null>(null);
  const addFiles = (list: FileList | File[]) => {
    const { accepted, rejected: bad } = validateFiles(Array.from(list), queue);
    setQueue((q) => [...q, ...accepted]);
    setRejected(bad);
    setUploadError(null);
    setResult(null);
  };
  const handleDeleted = async (paused: number) => {
  const name = toDelete?.source ?? "Document";
  setToDelete(null);
  toast.success(
    paused > 0
      ? `${name} deleted. ${paused} chat${paused === 1 ? "" : "s"} paused.`
      : `${name} deleted.`,
  );
  await refresh(); // library and chat picker
  if (paused > 0) void refreshSessions({ silent: true }); // sidebar: paused state
};
  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (!uploading) addFiles(e.dataTransfer.files);
  };

  const upload = async () => {
    if (queue.length === 0 || uploading) return;
    setUploading(true);
    setUploadError(null);
    setResult(null);
    try {
      const res = await api.documents.upload(queue);
      setResult(res);
      setQueue([]);
      setRejected([]);
      toast.success("Upload complete");
      await refresh(); // updates this list and the chat picker
      if (res.unpaused_sessions > 0) void refreshSessions({ silent: true });
    } catch (e) {
      // 403 / 413 / 429 / 500: show the backend's detail verbatim
      setUploadError(e instanceof Error ? e.message : "Upload failed");
      if (e instanceof ApiError && e.status === 429) toast.error("Upload limit reached");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Drop zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          if (!uploading) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={cn(
          "flex flex-col items-center gap-2 rounded-2xl border-2 border-dashed px-4 py-8 text-center transition-colors",
          dragging ? "border-accent bg-accent/10" : "border-border bg-surface",
        )}
      >
        <Upload size={24} className="text-accent" />
        <p className="text-sm">Drag and drop files here, or</p>
        <Button
          variant="secondary"
          size="sm"
          disabled={uploading}
          onClick={() => inputRef.current?.click()}
        >
          Choose files
        </Button>
        <p className="text-xs text-fg-muted">Up to 20 MB per file. 10 uploads per hour.</p>
        <input
          ref={inputRef}
          type="file"
          multiple
          hidden
          onChange={(e) => {
            if (e.target.files) addFiles(e.target.files);
            e.target.value = ""; // allow re-picking the same file
          }}
        />
      </div>

      {/* Rejected by client-side checks */}
      {rejected.length > 0 && (
        <ul role="alert" className="space-y-1 rounded-xl border border-danger/40 bg-danger/10 p-3 text-sm text-danger">
          {rejected.map((r, i) => (
            <li key={i}>
              <span className="break-all font-medium">{r.name}</span>: {r.reason}
            </li>
          ))}
        </ul>
      )}

      {/* Queue */}
      {queue.length > 0 && (
        <div className="space-y-3">
          <ul className="divide-y divide-border rounded-xl border border-border">
            {queue.map((f, i) => (
              <li key={`${f.name}-${f.size}`} className="flex items-center gap-3 px-4 py-2.5 text-sm">
                <FileText size={14} className="shrink-0 text-accent" />
                <span className="min-w-0 flex-1 truncate">{f.name}</span>
                <span className="shrink-0 text-xs text-fg-muted">{formatBytes(f.size)}</span>
                <button
                  type="button"
                  aria-label={`Remove ${f.name}`}
                  disabled={uploading}
                  onClick={() => setQueue((q) => q.filter((_, j) => j !== i))}
                  className="rounded p-1 text-fg-muted hover:text-fg disabled:opacity-40"
                >
                  <X size={14} />
                </button>
              </li>
            ))}
          </ul>
          <Button onClick={upload} disabled={uploading}>
            {uploading
              ? "Uploading and indexing…"
              : `Upload ${queue.length} file${queue.length === 1 ? "" : "s"}`}
          </Button>
          {uploading && (
            <p className="text-xs text-fg-muted">
              Large files can take a while to index. Keep this page open.
            </p>
          )}
        </div>
      )}

      {uploadError && (
        <p role="alert" className="rounded-xl border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger">
          {uploadError}
        </p>
      )}

      {result && (
        <div role="status" className="flex items-start gap-2.5 rounded-xl border border-accent/30 bg-accent/10 px-4 py-3 text-sm">
          <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-accent" />
          <div className="space-y-1">
            <p>
              Indexed {result.files.length} file{result.files.length === 1 ? "" : "s"} (
              {result.num_chunks} chunks).
            </p>
            {result.unpaused_sessions > 0 && (
              <p className="flex items-center gap-1.5 text-fg-muted">
                <Info size={12} />
                {result.unpaused_sessions} paused chat
                {result.unpaused_sessions === 1 ? " was" : "s were"} resumed.
              </p>
            )}
          </div>
        </div>
      )}

      {/* Library */}
      <section>
        <h2 className="mb-2 text-sm font-medium">
          Library{!loading && !error && ` (${documents.length})`}
        </h2>
        {error ? (
          <div className="rounded-xl border border-border bg-surface p-8 text-center text-sm">
            <p className="text-danger">{error}</p>
            <Button variant="secondary" size="sm" className="mt-3" onClick={() => refresh()}>
              Retry
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-border">
            <table className="w-full min-w-105 border-collapse text-left text-sm">
              <thead className="bg-surface text-xs text-fg-muted">
                <tr>
                  <th className="px-4 py-2.5 font-medium">File</th>
                  <th className="px-4 py-2.5 font-medium">ID</th>
                  <th className="px-4 py-2.5 text-right font-medium">Chunks</th>
                  <th className="px-4 py-2.5 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loading ? (
                  [0, 1, 2].map((i) => (
                    <tr key={i} aria-hidden="true">
                      {[0, 1, 2].map((c) => (
                        <td key={c} className="px-4 py-3">
                          <Skeleton className="h-4 w-full max-w-40" />
                        </td>
                      ))}
                    </tr>
                  ))
                ) : documents.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="px-4 py-10 text-center text-fg-muted">
                      No documents yet. Upload one above.
                    </td>
                  </tr>
                ) : (
                  documents.map((d:DocumentInfo) => (
                    <tr key={d.file_hash} className="hover:bg-surface/60">
                      <td className="px-4 py-3">
                        <span className="break-all">{d.source}</span>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-fg-muted">{d.file_hash}</td>
                      <td className="px-4 py-3 text-right tabular-nums text-fg-muted">
                        {d.chunk_count}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                            type="button"
                            aria-label={`Delete ${d.source}`}
                            onClick={() => setToDelete(d)}
                            className="rounded-md p-1.5 text-fg-muted transition-colors hover:bg-danger/15 hover:text-danger"
                        >
                            <Trash2 size={14} />
                        </button>
                        </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
        
      </section>
      <DeleteDocumentModal doc={toDelete} onClose={() => setToDelete(null)} onDeleted={handleDeleted} />
    </div>
  );
}
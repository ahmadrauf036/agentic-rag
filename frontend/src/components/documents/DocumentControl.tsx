import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronDown, FileText, Lock, Search } from "lucide-react";
import { useDocuments } from "@/context/DocumentContext";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Skeleton } from "@/components/ui/Skeleton";
import { cn } from "@/lib/cn";

interface Props {
  locked: boolean;
  /** Locked mode */
  lockedFiles: string[];
  lockedPage: number | null;
  lockedLoading: boolean;
  /** Picker mode */
  selected: string[];
  onSelectedChange: (next: string[]) => void;
  page: string;
  onPageChange: (value: string) => void;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function DocumentsControl(props: Props) {
  return props.locked ? <LockedChips {...props} /> : <Picker {...props} />;
}

/* ---------- Locked: read-only chips (8.4) ---------- */
/* ---------- Locked: read-only dropdown (8.4) ---------- */

function LockedChips({ lockedFiles, lockedPage, lockedLoading }: Props) {
  const { nameFor, loading } = useDocuments();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  if (lockedLoading || (loading && lockedFiles.length > 0)) {
    return <Skeleton className="h-8 w-36 rounded-lg" />;
  }
  if (lockedFiles.length === 0) return null;

  const names = lockedFiles.map((h) => nameFor(h) ?? "Unknown document");
  const label = names.length === 1 ? names[0] : `${names.length} documents`;

  return (
    <div ref={rootRef} className="relative min-w-0 shrink-0">
      <Button
        variant="secondary"
        size="sm"
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="max-w-56"
      >
        <Lock size={12} className="shrink-0 text-fg-muted" aria-hidden="true" />
        <span className="truncate">{label}</span>
        <ChevronDown
          size={14}
          className={cn("shrink-0 transition-transform", open && "rotate-180")}
        />
      </Button>

      {open && (
        <div
          role="dialog"
          aria-label="Documents for this chat"
          className="absolute right-0 top-full z-30 mt-2 w-80 max-w-[calc(100vw-2rem)] animate-pop-in rounded-xl border border-border bg-surface-2 p-3 shadow-xl"
        >
          <ul className="max-h-64 space-y-0.5 overflow-y-auto">
            {names.map((name, i) => (
              <li
                key={i}
                className="flex items-center gap-2.5 rounded-lg px-2 py-2 text-sm"
              >
                <FileText size={14} className="shrink-0 text-accent" />
                <span
                  className={cn(
                    "min-w-0 flex-1 truncate",
                    name === "Unknown document" && "italic text-fg-muted",
                  )}
                  title={name}
                >
                  {name}
                </span>
              </li>
            ))}
          </ul>

          {lockedPage !== null && (
            <p className="mt-2 border-t border-border pt-2 text-xs text-fg-muted">
              Limited to page {lockedPage}
            </p>
          )}

          <p className="mt-2 flex items-center gap-1.5 border-t border-border pt-2 text-xs text-fg-muted">
            <Lock size={11} aria-hidden="true" />
            Locked. Documents can't be changed for this chat.
          </p>
        </div>
      )}
    </div>
  );
}

/* ---------- Picker: multi-select + page input (8.2, 8.3) ---------- */

function Picker({ selected, onSelectedChange, page, onPageChange, open, onOpenChange }: Props) {
  const { documents, loading, error, refresh } = useDocuments();
  const [query, setQuery] = useState("");
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) onOpenChange(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onOpenChange(false);
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open, onOpenChange]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? documents.filter((d) => (d.source as string).toLowerCase().includes(q)) : documents;
  }, [documents, query]);

  const toggle = (hash: string) =>
    onSelectedChange(
      selected.includes(hash) ? selected.filter((h) => h !== hash) : [...selected, hash],
    );

  const count = selected.length;

  return (
    <div ref={rootRef} className="relative shrink-0">
      <Button
        variant={count > 0 ? "secondary" : "primary"}
        size="sm"
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => onOpenChange(!open)}
      >
        <FileText size={14} />
        {count === 0 ? "Select document(s)" : `${count} selected`}
        <ChevronDown size={14} className={cn("transition-transform", open && "rotate-180")} />
      </Button>

      {open && (
        <div
          role="dialog"
          aria-label="Select documents"
          className="absolute right-0 top-full z-30 mt-2 w-80 max-w-[calc(100vw-2rem)] animate-pop-in rounded-xl border border-border bg-surface-2 p-3 shadow-xl"
        >
          {documents.length > 6 && (
            <div className="relative mb-2">
              <Search
                size={14}
                className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-fg-muted"
              />
              <Input
                type="search"
                placeholder="Filter documents"
                aria-label="Filter documents"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="h-9 pl-8 [&::-webkit-search-cancel-button]:hidden"
              />
            </div>
          )}

          <div className="max-h-64 overflow-y-auto">
            {loading ? (
              <div className="space-y-2" aria-busy="true" aria-label="Loading documents">
                {[0, 1, 2].map((i) => (
                  <Skeleton key={i} className="h-8 w-full" />
                ))}
              </div>
            ) : error ? (
              <div className="py-4 text-center text-sm">
                <p className="text-danger">{error}</p>
                <Button variant="secondary" size="sm" className="mt-3" onClick={() => refresh()}>
                  Retry
                </Button>
              </div>
            ) : documents.length === 0 ? (
              <p className="py-4 text-center text-sm text-fg-muted">No documents available yet.</p>
            ) : filtered.length === 0 ? (
              <p className="py-4 text-center text-sm text-fg-muted">No documents match.</p>
            ) : (
              <ul className="space-y-0.5">
                {filtered.map((d) => (
                  <li key={d.file_hash as string}>
                    <label className="flex cursor-pointer items-center gap-2.5 rounded-lg px-2 py-2 text-sm transition-colors hover:bg-surface">
                      <input
                        type="checkbox"
                        checked={selected.includes(d.file_hash as string)}
                        onChange={() => toggle(d.file_hash as string)}
                        className="h-4 w-4 shrink-0 accent-accent"
                      />
                      <span className="min-w-0 flex-1 truncate" title={d.source as string}>
                        {d.source as string}
                      </span>
                    </label>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {count === 1 && (
            <div className="mt-3 border-t border-border pt-3">
              <label className="mb-1.5 block text-xs text-fg-muted" htmlFor="doc-page">
                Page number (optional)
              </label>
              <Input
                id="doc-page"
                inputMode="numeric"
                placeholder="All pages"
                value={page}
                onChange={(e) => onPageChange(e.target.value.replace(/\D/g, "").slice(0, 5))}
                className="h-9"
              />
            </div>
          )}

          <p className="mt-3 text-xs text-fg-muted">
            Your selection is locked once you send the first message.
          </p>
          <Button size="sm" className="mt-3 w-full" onClick={() => onOpenChange(false)}>
            Done
          </Button>
        </div>
      )}
    </div>
  );
}
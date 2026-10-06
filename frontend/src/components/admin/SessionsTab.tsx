import { useCallback, useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useDocuments } from "@/context/DocumentContext";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatDateTime } from "@/lib/date";
import { cn } from "@/lib/cn";
import type { AdminSession } from "@/types";

export type SessionFilter = "all" | "active" | "paused";

const FILTERS: { id: SessionFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "active", label: "Active" },
  { id: "paused", label: "Paused" },
];

export default function SessionsTab({ initialFilter = "all" }: { initialFilter?: SessionFilter }) {
  const { nameFor } = useDocuments();

  const [sessions, setSessions] = useState<AdminSession[]>([]);
  const [emails, setEmails] = useState<Map<string, string>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<SessionFilter>(initialFilter);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const [s, u] = await Promise.allSettled([api.admin.sessions(), api.admin.users()]);

    if (s.status === "rejected") {
      const e = s.reason;
      setError(
        e instanceof ApiError && e.status === 403
          ? "Admin access required."
          : e instanceof Error
            ? e.message
            : "Failed to load chats",
      );
    } else {
      setSessions(s.value); // backend already sorts by updated_at desc
    }
    if (u.status === "fulfilled") {
      setEmails(new Map(u.value.map((x) => [x.id, x.email])));
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const owner = (id: string) => emails.get(id) ?? `${id.slice(0, 8)}…`;

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return sessions.filter((s) => {
      if (filter === "paused" && !s.paused_reason) return false;
      if (filter === "active" && s.paused_reason) return false;
      if (!q) return true;
      return (s.title || "").toLowerCase().includes(q) || owner(s.user_id).toLowerCase().includes(q);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessions, emails, query, filter]);

  const docLabel = (files: string[]) => {
    if (files.length === 0) return "—";
    const first = nameFor(files[0]) ?? "Unknown document";
    return files.length > 1 ? `${first} +${files.length - 1}` : first;
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative w-full max-w-sm">
          <Search
            size={14}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-fg-muted"
          />
          <Input
            type="search"
            placeholder="Search by title or user"
            aria-label="Search chats by title or user"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-8 [&::-webkit-search-cancel-button]:hidden"
          />
        </div>
        <div role="group" aria-label="Filter by status" className="flex gap-1">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              type="button"
              aria-pressed={filter === f.id}
              onClick={() => setFilter(f.id)}
              className={cn(
                "rounded-full border px-3 py-1 text-xs transition-colors",
                filter === f.id
                  ? "border-accent/50 bg-accent/10 text-accent"
                  : "border-border text-fg-muted hover:text-fg",
              )}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {error ? (
        <div className="rounded-xl border border-border bg-surface p-8 text-center text-sm">
          <p className="text-danger">{error}</p>
          <Button variant="secondary" size="sm" className="mt-3" onClick={load}>
            Retry
          </Button>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-border">
          <table className="w-full min-w-190 border-collapse text-left text-sm">
            <thead className="bg-surface text-xs text-fg-muted">
              <tr>
                <th className="px-4 py-2.5 font-medium">Chat</th>
                <th className="px-4 py-2.5 font-medium">User</th>
                <th className="px-4 py-2.5 font-medium">Documents</th>
                <th className="px-4 py-2.5 font-medium">Status</th>
                <th className="px-4 py-2.5 font-medium">Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading ? (
                [0, 1, 2, 3].map((i) => (
                  <tr key={i} aria-hidden="true">
                    {[0, 1, 2, 3, 4].map((c) => (
                      <td key={c} className="px-4 py-3">
                        <Skeleton className="h-4 w-full max-w-36" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-10 text-center text-fg-muted">
                    {sessions.length === 0 ? "No chats yet." : "No chats match these filters."}
                  </td>
                </tr>
              ) : (
                filtered.map((s) => (
                  <tr key={s.thread_id} className="hover:bg-surface/60">
                    <td className="max-w-[16rem] px-4 py-3">
                      <span className="block truncate" title={s.title}>
                        {s.title || "Untitled chat"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-fg-muted">
                      <span className="break-all">{owner(s.user_id)}</span>
                    </td>
                    <td className="max-w-48 px-4 py-3 text-fg-muted">
                      <span className="block truncate">
                        {docLabel(s.selected_files)}
                        {s.page !== null && ` (p. ${s.page})`}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {s.paused_reason ? (
                        <span
                          title={s.paused_reason}
                          className="inline-flex rounded-full border border-warning/40 bg-warning/10 px-2 py-0.5 text-xs text-warning"
                        >
                          Paused
                        </span>
                      ) : (
                        <span className="inline-flex rounded-full border border-border bg-surface px-2 py-0.5 text-xs text-fg-muted">
                          Active
                        </span>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-fg-muted">
                      {formatDateTime(s.updated_at)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {!loading && !error && (
        <p className="text-xs text-fg-muted">
          Showing {filtered.length} of {sessions.length} chats.
        </p>
      )}
    </div>
  );
}
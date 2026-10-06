import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { cn } from "@/lib/cn";
import type { AdminStats } from "@/types";

interface Props {
  onViewPaused: () => void;
}

export default function OverviewTab({ onViewPaused }: Props) {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setStats(await api.admin.stats());
    } catch (e) {
      setError(
        e instanceof ApiError && e.status === 403
          ? "Admin access required."
          : e instanceof Error
            ? e.message
            : "Failed to load stats",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (error) {
    return (
      <div className="rounded-xl border border-border bg-surface p-8 text-center text-sm">
        <p className="text-danger">{error}</p>
        <Button variant="secondary" size="sm" className="mt-3" onClick={load}>
          Retry
        </Button>
      </div>
    );
  }

  const cards = stats && [
    { label: "Users", value: stats.total_users, hint: `${stats.total_admins} admin${stats.total_admins === 1 ? "" : "s"}` },
    { label: "Documents", value: stats.total_documents, hint: "in the shared library" },
    { label: "Chunks", value: stats.total_chunks, hint: "embedded across all documents" },
    { label: "Chats", value: stats.total_sessions, hint: "across all users" },
    {
      label: "Paused chats",
      value: stats.paused_sessions,
      hint: stats.paused_sessions > 0 ? "a document was deleted" : "none paused",
      warn: stats.paused_sessions > 0,
      action: stats.paused_sessions > 0 ? onViewPaused : undefined,
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button variant="ghost" size="sm" onClick={load} disabled={loading}>
          <RefreshCw size={14} className={cn(loading && "animate-spin")} />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
        {loading || !cards
          ? [0, 1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-24 rounded-xl" />)
          : cards.map((c) => {
              const body = (
                <>
                  <p className="text-xs text-fg-muted">{c.label}</p>
                  <p className={cn("mt-1 text-3xl font-semibold tabular-nums", c.warn && "text-warning")}>
                    {c.value.toLocaleString()}
                  </p>
                  <p className="mt-1 text-xs text-fg-muted">{c.hint}</p>
                </>
              );
              const base = "rounded-xl border bg-surface p-4 text-left";
              return c.action ? (
                <button
                  key={c.label}
                  type="button"
                  onClick={c.action}
                  className={cn(base, "border-warning/40 transition-colors hover:border-warning")}
                >
                  {body}
                </button>
              ) : (
                <div key={c.label} className={cn(base, "border-border")}>
                  {body}
                </div>
              );
            })}
      </div>
    </div>
  );
}
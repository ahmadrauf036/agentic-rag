import { useEffect, useMemo, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatTokens } from "@/lib/format";
import { cn } from "@/lib/cn";
import type { UserUsage } from "@/types";

const RANGES = [
  { days: 7, label: "7 days" },
  { days: 30, label: "30 days" },
  { days: 90, label: "90 days" },
] as const;

const exact = (n: number) => n.toLocaleString();

export default function UsageTab() {
  const [days, setDays] = useState<number>(30);
  const [rows, setRows] = useState<UserUsage[]>([]);
  const [emails, setEmails] = useState<Map<string, string>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.allSettled([api.usage.all(days), api.admin.users()]).then(([u, users]) => {
      if (cancelled) return;
      if (u.status === "rejected") {
        const e = u.reason;
        setError(
          e instanceof ApiError && e.status === 403
            ? "Admin access required."
            : e instanceof Error
              ? e.message
              : "Failed to load usage",
        );
      } else {
        setRows(u.value); // backend sorts by total_tokens desc
      }
      if (users.status === "fulfilled") {
        setEmails(new Map(users.value.map((x) => [x.id, x.email])));
      }
      setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, [days, attempt]);

  const totals = useMemo(
    () =>
      rows.reduce(
        (a, r) => ({
          input: a.input + r.total_input_tokens,
          output: a.output + r.total_output_tokens,
          total: a.total + r.total_tokens,
          requests: a.requests + r.request_count,
        }),
        { input: 0, output: 0, total: 0, requests: 0 },
      ),
    [rows],
  );
  const max = rows[0]?.total_tokens || 1;

  const cards = [
    { label: "Total tokens", value: totals.total },
    { label: "Input tokens", value: totals.input },
    { label: "Output tokens", value: totals.output },
    { label: "Requests", value: totals.requests, plain: true },
  ];

  return (
    <div className="space-y-4">
      <div role="group" aria-label="Time range" className="flex gap-1">
        {RANGES.map((r) => (
          <button
            key={r.days}
            type="button"
            aria-pressed={days === r.days}
            onClick={() => setDays(r.days)}
            className={cn(
              "rounded-full border px-3 py-1 text-xs transition-colors",
              days === r.days
                ? "border-accent/50 bg-accent/10 text-accent"
                : "border-border text-fg-muted hover:text-fg",
            )}
          >
            Last {r.label}
          </button>
        ))}
      </div>

      {error ? (
        <div className="rounded-xl border border-border bg-surface p-8 text-center text-sm">
          <p className="text-danger">{error}</p>
          <Button variant="secondary" size="sm" className="mt-3" onClick={() => setAttempt((a) => a + 1)}>
            Retry
          </Button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {cards.map((c) =>
              loading ? (
                <Skeleton key={c.label} className="h-20 rounded-xl" />
              ) : (
                <div key={c.label} className="rounded-xl border border-border bg-surface p-4">
                  <p className="text-xs text-fg-muted">{c.label}</p>
                  <p className="mt-1 text-2xl font-semibold tabular-nums" title={exact(c.value)}>
                    {c.plain ? exact(c.value) : formatTokens(c.value)}
                  </p>
                </div>
              ),
            )}
          </div>

          <div className="overflow-x-auto rounded-xl border border-border">
            <table className="w-full min-w-160 border-collapse text-left text-sm">
              <thead className="bg-surface text-xs text-fg-muted">
                <tr>
                  <th className="px-4 py-2.5 font-medium">User</th>
                  <th className="px-4 py-2.5 text-right font-medium">Input</th>
                  <th className="px-4 py-2.5 text-right font-medium">Output</th>
                  <th className="px-4 py-2.5 text-right font-medium">Total</th>
                  <th className="px-4 py-2.5 text-right font-medium">Requests</th>
                  <th className="w-32 px-4 py-2.5 font-medium">Share</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loading ? (
                  [0, 1, 2].map((i) => (
                    <tr key={i} aria-hidden="true">
                      {[0, 1, 2, 3, 4, 5].map((c) => (
                        <td key={c} className="px-4 py-3">
                          <Skeleton className="h-4 w-full max-w-32" />
                        </td>
                      ))}
                    </tr>
                  ))
                ) : rows.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-10 text-center text-fg-muted">
                      No usage in this period.
                    </td>
                  </tr>
                ) : (
                  rows.map((r) => (
                    <tr key={r.user_id} className="hover:bg-surface/60">
                      <td className="px-4 py-3">
                        <span className="break-all">
                          {emails.get(r.user_id) ?? `${r.user_id.slice(0, 8)}…`}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums text-fg-muted" title={exact(r.total_input_tokens)}>
                        {formatTokens(r.total_input_tokens)}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums text-fg-muted" title={exact(r.total_output_tokens)}>
                        {formatTokens(r.total_output_tokens)}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums" title={exact(r.total_tokens)}>
                        {formatTokens(r.total_tokens)}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums text-fg-muted">
                        {exact(r.request_count)}
                      </td>
                      <td className="px-4 py-3">
                        <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-2" aria-hidden="true">
                          <div
                            className="h-full rounded-full bg-accent"
                            style={{ width: `${(r.total_tokens / max) * 100}%` }}
                          />
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
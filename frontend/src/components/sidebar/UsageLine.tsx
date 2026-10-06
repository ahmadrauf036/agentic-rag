import { useEffect, useState } from "react";
import { Activity } from "lucide-react";
import { api } from "@/lib/api";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatTokens } from "@/lib/format";
import type { UsageSummary } from "@/types";

const DAYS = 30;

/** Mounted only while the profile menu is open, so it fetches fresh each time. */
export default function UsageLine() {
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api.usage
      .me(DAYS)
      .then((u) => !cancelled && setUsage(u))
      .catch(() => !cancelled && setFailed(true));
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mb-3 border-t border-border pt-3">
      <p className="mb-1 flex items-center gap-1.5 text-xs text-fg-muted">
        <Activity size={12} aria-hidden="true" />
        Usage, last {DAYS} days
      </p>
      {failed ? (
        <p className="text-xs text-fg-muted">Usage unavailable.</p>
      ) : !usage ? (
        <Skeleton className="h-4 w-40" />
      ) : (
        <p className="text-sm tabular-nums">
          <span title={usage.total_tokens.toLocaleString()}>
            {formatTokens(usage.total_tokens)} tokens
          </span>
          <span className="text-fg-muted"> · {usage.request_count.toLocaleString()} requests</span>
        </p>
      )}
    </div>
  );
}
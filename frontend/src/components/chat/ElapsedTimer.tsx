import { useEffect, useState } from "react";
import { Timer } from "lucide-react";

export const formatMs = (ms: number) =>
  ms < 60_000
    ? `${(ms / 1000).toFixed(1)}s`
    : `${Math.floor(ms / 60_000)}m ${Math.floor((ms % 60_000) / 1000)}s`;

export default function ElapsedTimer({ startedAt }: { startedAt: number }) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const i = setInterval(() => setNow(Date.now()), 100);
    return () => clearInterval(i);
  }, []);

  return (
    <span
      className="inline-flex items-center gap-1 text-xs tabular-nums text-fg-muted"
      aria-hidden="true"
    >
      <Timer size={12} />
      {formatMs(Math.max(0, now - startedAt))}
    </span>
  );
}
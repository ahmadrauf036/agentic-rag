import { PauseCircle } from "lucide-react";

export default function PausedBanner({ reason }: { reason: string }) {
  return (
    <div
      role="alert"
      className="flex shrink-0 items-start gap-2.5 border-b border-warning/30 bg-warning/10 px-4 py-3 text-sm text-warning"
    >
      <PauseCircle size={16} className="mt-0.5 shrink-0" />
      <p>{reason}</p>
    </div>
  );
}
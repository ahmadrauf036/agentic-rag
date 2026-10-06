export function parseTimestamp(value: string): Date | null {
  const iso = value
    .replace(" ", "T")
    .replace(/(\.\d{3})\d+/, "$1"); // trim microseconds to milliseconds
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? null : d;
}

export function formatDateTime(value: string | null): string {
  if (!value) return "Never";
  const d = parseTimestamp(value);
  if (!d) return "Unknown";
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}
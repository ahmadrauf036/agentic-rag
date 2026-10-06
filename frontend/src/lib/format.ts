/** 6353 -> "6.4K", 1_250_000 -> "1.25M". Use toLocaleString() for exact values in tooltips. */
export function formatTokens(n: number): string {
  if (n < 1_000) return String(n);
  if (n < 1_000_000) return `${(n / 1_000).toFixed(n < 10_000 ? 1 : 0)}K`;
  return `${(n / 1_000_000).toFixed(2)}M`;
}
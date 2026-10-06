export const MAX_FILE_BYTES = 20 * 1024 * 1024;

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** Splits files into acceptable ones and rejected ones with a reason. */
export function validateFiles(files: File[], existing: File[]) {
  const accepted: File[] = [];
  const rejected: { name: string; reason: string }[] = [];
  const seen = new Set(existing.map((f) => `${f.name}|${f.size}`));

  for (const f of files) {
    const key = `${f.name}|${f.size}`;
    if (f.size === 0) rejected.push({ name: f.name, reason: "File is empty" });
    else if (f.size > MAX_FILE_BYTES)
      rejected.push({ name: f.name, reason: `Over 20 MB (${formatBytes(f.size)})` });
    else if (seen.has(key)) rejected.push({ name: f.name, reason: "Already added" });
    else {
      seen.add(key);
      accepted.push(f);
    }
  }
  return { accepted, rejected };
}
import { getAuthHeaders, parseError } from "@/lib/api";
import type { ChatStreamRequest, SSEEvent } from "@/types";

const BASE_URL = import.meta.env.VITE_API_URL;

const EVENT_TYPES = new Set(["tool_start", "tool_end", "sources", "token", "done", "error"]);

function parseBlock(block: string): SSEEvent | null {
  let type = "message";
  const dataLines: string[] = [];

  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) type = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).replace(/^ /, ""));
  }

  if (!EVENT_TYPES.has(type) || dataLines.length === 0) return null;

  try {
    return { type, data: JSON.parse(dataLines.join("\n")) } as SSEEvent;
  } catch {
    return null; // malformed payload, skip it
  }
}

/**
 * Streams POST /chat/stream. Resolves when the stream ends or is aborted.
 * Throws ApiError for non-2xx responses and network errors.
 */
export async function streamChat(
  body: ChatStreamRequest,
  onEvent: (event: SSEEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
        ...(await getAuthHeaders()),
      },
      body: JSON.stringify(body),
      signal,
    });
  } catch (err) {
    if ((err as Error).name === "AbortError") return;
    throw err;
  }

  if (!res.ok) throw await parseError(res);
  if (!res.body) throw new Error("Response has no body");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");

      let idx: number;
      while ((idx = buffer.indexOf("\n\n")) !== -1) {
        const block = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        const event = parseBlock(block);
        if (event) onEvent(event);
      }
    }

    // Flush any trailing block without a final blank line
    const tail = parseBlock(buffer.trim());
    if (tail) onEvent(tail);
  } catch (err) {
    if ((err as Error).name === "AbortError") return;
    throw err;
  } finally {
    reader.releaseLock();
  }
}
import { useCallback, useLayoutEffect, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { ChatMessage, SessionInfo } from "@/types";

export type ChatStatus = "idle" | "loading" | "ready" | "not-found" | "error";

export function useChatSession(chatId: string | undefined, fresh: boolean) {
  const [session, setSession] = useState<SessionInfo | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<ChatStatus>(chatId ? "loading" : "idle");
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  // Read inside the effect without making them dependencies
  const messagesRef = useRef(messages);
  messagesRef.current = messages;
  const freshRef = useRef(fresh);
  freshRef.current = fresh;

  // Layout effect so the reset happens before paint (no flash of the previous chat).
  useLayoutEffect(() => {
    let cancelled = false;

    if (!chatId) {
      setSession(null);
      setMessages([]);
      setError(null);
      setStatus("idle");
      return;
    }

    // Just-started chat: the live stream already owns the messages in memory.
    // Don't overwrite them with a history fetch. (After a page reload the
    // router state may still say "fresh", but memory is empty, so we fetch.)
    if (freshRef.current && messagesRef.current.length > 0) {
      setError(null);
      setStatus("ready");
      api.sessions
        .get(chatId)
        .then((s) => !cancelled && setSession(s))
        .catch(() => {}); // row may not be readable yet, refreshSession() covers it
      return () => {
        cancelled = true;
      };
    }

    setStatus("loading");
    setError(null);
    setSession(null);
    setMessages([]);

    Promise.all([api.sessions.get(chatId), api.sessions.messages(chatId)])
      .then(([s, m]) => {
        if (cancelled) return;
        setSession(s);
        setMessages(m.map((msg, i) => ({ ...msg, id: `history-${i}` })));
        setStatus("ready");
      })
      .catch((e) => {
        if (cancelled) return;
        if (e instanceof ApiError && e.status === 404) {
          setStatus("not-found");
        } else {
          setError(e instanceof Error ? e.message : "Failed to load chat");
          setStatus("error");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [chatId, attempt]);

  const retry = useCallback(() => setAttempt((a) => a + 1), []);

  /** Re-fetch only the session row (e.g. after a stream finishes). */
  const refreshSession = useCallback(async () => {
    if (!chatId) return;
    try {
      setSession(await api.sessions.get(chatId));
    } catch {
      /* non-fatal */
    }
  }, [chatId]);

  return { session, messages, setMessages, status, error, retry, refreshSession };
}
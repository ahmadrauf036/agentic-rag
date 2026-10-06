import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError } from "@/lib/api";
import { streamChat } from "@/lib/sse";
import { useSessions } from "@/context/SessionsContext";
import { useToast } from "@/components/ui/Toast";
import type { ChatMessage, SSEEvent, Source, ToolName } from "@/types";

export interface ToolActivity {
  id: number;
  tool: ToolName;
  running: boolean;
}
export interface LiveMessage {
  content: string;
  tools: ToolActivity[];
  sources: Source[];
  startedAt: number;
}

interface Options {
  chatId: string | undefined;
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  refreshSession: () => Promise<void>;
  selection?: { files?: string[]; page?: number | null };
}

const uid = () => crypto.randomUUID();
const sourceKey = (s: Source) => `${s.source}|${s.page}|${s.snippet}`;

export function useChatStream({ chatId, setMessages, refreshSession, selection }: Options) {
  const navigate = useNavigate();
  const { addSession, refresh } = useSessions();
  const toast = useToast();

  const [live, setLive] = useState<LiveMessage | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const threadRef = useRef<string | null>(null); // thread currently streaming
    
  // Latest values for use inside the long-running send()
  const chatIdRef = useRef(chatId);
  chatIdRef.current = chatId;
  const refreshSessionRef = useRef(refreshSession);
  refreshSessionRef.current = refreshSession;
  const selectionRef = useRef(selection);
  selectionRef.current = selection;

  // Navigated to a different chat mid-stream: abort and discard.
  // (Navigating to our own new thread id is NOT a switch.)
  useEffect(() => {
    if (threadRef.current && threadRef.current !== chatId) {
      abortRef.current?.abort();
      abortRef.current = null;
      threadRef.current = null;
      setLive(null);
    }
  }, [chatId]);

  useEffect(
    () => () => {
      abortRef.current?.abort();
      threadRef.current = null;
    },
    [],
  );

  /** Resolves false only if the request failed before any stream event (caller restores the draft). */
  const send = useCallback(
  async (text: string, opts?: { retry?: boolean }): Promise<boolean> => {
      const message = text.trim();
      if (!message || threadRef.current) return true;
        const startedAt = Date.now();
      const isNew = !chatIdRef.current;
      const threadId = chatIdRef.current ?? uid();
      const userMsgId = `user-${uid()}`;
      const sel = selectionRef.current;
      const files = sel?.files;
        const page = sel?.page ?? null;

      const controller = new AbortController();
      abortRef.current = controller;
      threadRef.current = threadId;

      let content = "";
      let tools: ToolActivity[] = [];
      let sources: Source[] = [];
      let toolSeq = 0;
      let gotEvent = false;
      let navigated = !isNew;
      let doneReceived = false;
      let streamError: string | null = null;

        if (!opts?.retry) {
            setMessages((prev) => [...prev, { id: userMsgId, role: "user", content: message }]);
        }
      setLive({ content: "", tools: [], sources: [], startedAt });

      const onFirstEvent = () => {
        gotEvent = true;
        if (navigated) return;
        navigated = true;
        const now = new Date().toISOString();
        addSession({
          thread_id: threadId,
          title: message.length > 40 ? `${message.slice(0, 40)}…` : message,
          selected_files: files ?? [],
          page,
          paused_reason: null,
          created_at: now,
          updated_at: now,
        });
        navigate(`/chat/${threadId}`, { state: { fresh: true } });
      };

      const handle = (ev: SSEEvent) => {
        if (threadRef.current !== threadId) return; // switched away
        onFirstEvent();

        switch (ev.type) {
          case "tool_start":
            tools = [...tools, { id: toolSeq++, tool: ev.data.tool, running: true }];
            break;
          case "tool_end": {
            const idx = [...tools].reverse().findIndex((t) => t.tool === ev.data.tool && t.running);
            if (idx !== -1) {
              const target = tools.length - 1 - idx;
              tools = tools.map((t, i) => (i === target ? { ...t, running: false } : t));
            }
            break;
          }
          case "sources": {
            const seen = new Set(sources.map(sourceKey));
            const fresh = (ev.data.sources ?? []).filter((s) => !seen.has(sourceKey(s)));
            if (fresh.length) sources = [...sources, ...fresh];
            break;
          }
          case "token":
            content += ev.data.text;
            break;
          case "done":
            doneReceived = true;
            break;
          case "error":
            // The backend can emit `error` after `done` (memory write failed). The reply is fine.
            if (!doneReceived) streamError = ev.data.detail;
            break;
        }
        setLive({ content, tools, sources, startedAt });
      };

      try {
        await streamChat(
          {
            thread_id: threadId,
            message,
            ...(isNew ? { selected_files: files, page } : {}),
          },
          handle,
          controller.signal,
        );
      } catch (e) {
        if (threadRef.current !== threadId) return true; // switched away

        const detail = e instanceof Error ? e.message : "Something went wrong.";
        if (!gotEvent) {
          // Request rejected before streaming (400 / 403 / 502 / network)
          threadRef.current = null;
          abortRef.current = null;
          setMessages((prev) => prev.filter((m) => m.id !== userMsgId));
          setLive(null);
          toast.error(detail);
          if (e instanceof ApiError && e.status === 403) void refreshSessionRef.current();
          return false;
        }
        streamError = detail; // connection dropped mid-stream
      }

      if (threadRef.current !== threadId) return true; // switched away: don't touch the new chat

      threadRef.current = null;
      abortRef.current = null;

      if (content) {
        setMessages((prev) => [
          ...prev,
          {
  id: `assistant-${uid()}`,
  role: "assistant",
  content,
  sources: sources.length ? sources : null,
  durationMs: Date.now() - startedAt,
},
        ]);
      }
      setLive(null);
      if (streamError) toast.error(streamError);

      if (gotEvent) {
        void refreshSessionRef.current(); // pick up paused_reason / real title
        void refresh({ silent: true }); // sidebar: real title + ordering
      }
      return true;
    },
    [addSession, navigate, refresh, setMessages, toast],
  );

  const stop = useCallback(() => abortRef.current?.abort(), []);

  return { live, streaming: live !== null, send, stop };
}
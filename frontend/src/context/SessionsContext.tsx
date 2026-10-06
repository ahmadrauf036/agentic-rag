import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import type { SessionInfo } from "@/types";

interface SessionsState {
  sessions: SessionInfo[];
  loading: boolean;
  error: string | null;
  /** silent = refetch without showing the skeleton */
  refresh: (opts?: { silent?: boolean }) => Promise<void>;
  addSession: (session: SessionInfo) => void;
  removeSession: (threadId: string) => Promise<void>;
}

const SessionsContext = createContext<SessionsState | null>(null);

const byRecent = (a: SessionInfo, b: SessionInfo) =>
  new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();

export function SessionsProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const userId = user?.id;

  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (opts?: { silent?: boolean }) => {
    if (!opts?.silent) setLoading(true);
    setError(null);
    try {
      const list = await api.sessions.list();
      setSessions([...list].sort(byRecent));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load chats");
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch once per logged-in user; clear on logout.
  useEffect(() => {
    if (!userId) {
      setSessions([]);
      setLoading(false);
      return;
    }
    refresh();
  }, [userId, refresh]);

  const addSession = useCallback((session: SessionInfo) => {
    setSessions((prev) =>
      [session, ...prev.filter((s) => s.thread_id !== session.thread_id)].sort(byRecent),
    );
  }, []);

  const removeSession = useCallback(
    async (threadId: string) => {
      const snapshot = sessions;
      setSessions((prev) => prev.filter((s) => s.thread_id !== threadId)); // optimistic
      try {
        await api.sessions.remove(threadId);
      } catch (e) {
        setSessions(snapshot); // roll back
        throw e;
      }
    },
    [sessions],
  );

  return (
    <SessionsContext.Provider
      value={{ sessions, loading, error, refresh, addSession, removeSession }}
    >
      {children}
    </SessionsContext.Provider>
  );
}

export function useSessions(): SessionsState {
  const ctx = useContext(SessionsContext);
  if (!ctx) throw new Error("useSessions must be used inside <SessionsProvider>");
  return ctx;
}
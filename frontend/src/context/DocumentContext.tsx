import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import type { DocumentInfo } from "@/types";

interface DocumentsState {
  documents: DocumentInfo[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  /** file_hash -> filename (null if the document no longer exists) */
  nameFor: (hash: string) => string | null;
}

const DocumentsContext = createContext<DocumentsState | null>(null);

export function DocumentsProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const userId = user?.id;

  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await api.documents.list();
      setDocuments([...list].sort((a, b) => (a.source as string).localeCompare(b.source as string)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load documents");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!userId) {
      setDocuments([]);
      setLoading(false);
      return;
    }
    refresh();
  }, [userId, refresh]);

  const byHash = useMemo(
  () => new Map<string, string>(documents.map((d) => [d.file_hash, d.source])),
  [documents],
);
  const nameFor = useCallback((hash: string) => byHash.get(hash) ?? null, [byHash]);

  return (
    <DocumentsContext.Provider value={{ documents, loading, error, refresh, nameFor }}>
      {children}
    </DocumentsContext.Provider>
  );
}

export function useDocuments(): DocumentsState {
  const ctx = useContext(DocumentsContext);
  if (!ctx) throw new Error("useDocuments must be used inside <DocumentsProvider>");
  return ctx;
}
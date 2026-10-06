import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Search, X } from "lucide-react";
import { useSessions } from "@/context/SessionsContext";
import { Skeleton } from "@/components/ui/Skeleton";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useToast } from "@/components/ui/Toast";
import SessionItem from "@/components/sidebar/SessionItem";
import type { SessionInfo } from "@/types";

const SKELETON_WIDTHS = ["w-4/5", "w-3/5", "w-11/12", "w-2/3", "w-3/4", "w-1/2"];

export default function SessionList({ onNavigate }: { onNavigate: () => void }) {
  const { sessions, loading, error, refresh, removeSession } = useSessions();
  const { chatId } = useParams();
  const navigate = useNavigate();
  const toast = useToast();

  const [query, setQuery] = useState("");
  const [pendingDelete, setPendingDelete] = useState<SessionInfo | null>(null);

  // Title-only, client-side substring match
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return sessions;
    return sessions.filter((s) => (s.title || "Untitled chat").toLowerCase().includes(q));
  }, [sessions, query]);

  const confirmDelete = async () => {
    const target = pendingDelete;
    if (!target) return;
    setPendingDelete(null);

    if (target.thread_id === chatId) navigate("/chat");
    try {
      await removeSession(target.thread_id); // optimistic, rolls back on failure
    } catch {
      toast.error("Could not delete the chat. Try again.");
    }
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* Search */}
      <div className="relative px-3 pb-2">
        <Search
          size={14}
          className="pointer-events-none absolute left-6 top-1/2 -translate-y-[calc(50%+4px)] text-fg-muted"
        />
        <Input
          type="search"
          placeholder="Search chats"
          aria-label="Search chats by title"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="h-9 pl-8 pr-8 [&::-webkit-search-cancel-button]:hidden"
        />
        {query && (
          <button
            type="button"
            aria-label="Clear search"
            onClick={() => setQuery("")}
            className="absolute right-5 top-1/2 -translate-y-[calc(50%+4px)] rounded p-1 text-fg-muted hover:text-fg"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* List body */}
      <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-2">
        {loading ? (
          <div className="space-y-1.5 px-1 py-1" aria-busy="true" aria-label="Loading chats">
            {SKELETON_WIDTHS.map((w, i) => (
              <div key={i} className="flex h-9 items-center px-2">
                <Skeleton className={`h-4 ${w}`} />
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="px-3 py-6 text-center text-sm">
            <p className="text-danger">{error}</p>
            <Button variant="secondary" size="sm" className="mt-3" onClick={() => refresh()}>
              Retry
            </Button>
          </div>
        ) : sessions.length === 0 ? (
          <p className="px-3 py-6 text-center text-sm text-fg-muted">
            No chats yet. Start a new one!
          </p>
        ) : filtered.length === 0 ? (
          <p className="px-3 py-6 text-center text-sm text-fg-muted">
            No chats match “{query.trim()}”.
          </p>
        ) : (
          <ul className="space-y-0.5">
            {filtered.map((s) => (
              <SessionItem
                key={s.thread_id}
                session={s}
                active={s.thread_id === chatId}
                onNavigate={onNavigate}
                onDelete={setPendingDelete}
              />
            ))}
          </ul>
        )}
      </div>

      {/* Delete confirmation */}
      <Modal
        open={pendingDelete !== null}
        onClose={() => setPendingDelete(null)}
        title="Delete chat?"
        className="max-w-sm"
      >
        <p className="text-sm text-fg-muted">
          <span className="text-fg">“{pendingDelete?.title || "Untitled chat"}”</span> and all of
          its messages will be permanently deleted. This can’t be undone.
        </p>
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setPendingDelete(null)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={confirmDelete}>
            Delete
          </Button>
        </div>
      </Modal>
    </div>
  );
}
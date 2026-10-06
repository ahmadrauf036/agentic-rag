import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useOutletContext, useParams } from "react-router-dom";
import { ArrowDown } from "lucide-react";
import { useChatSession } from "@/hooks/useChatSession";
import { useChatStream } from "@/hooks/useChatStream";
import { useAutoScroll } from "@/hooks/useAutoScroll";
import type { LayoutContext } from "@/components/AppLayout";
import MessageListSkeleton from "@/components/chat/MessageListSkeleton";
import MessageList from "@/components/chat/MessageList";
import StreamingMessage from "@/components/chat/StreamingMessage";
import ChatInput, { type ChatInputHandle } from "@/components/chat/ChatInput";
import PausedBanner from "@/components/chat/PausedBanner";
import ChatError from "@/components/chat/ChatError";
import SourcesModal from "@/components/chat/SourcesModal";
import DocumentsControl from "@/components/documents/DocumentControl";
import StartState from "@/components/documents/StartState";
import { useToast } from "@/components/ui/Toast";
import { cn } from "@/lib/cn";
import type { Source } from "@/types";

export default function ChatPage() {
  const { chatId } = useParams();
  const location = useLocation();
  const { sidebarOpen } = useOutletContext<LayoutContext>();
  const toast = useToast();

  const fresh = (location.state as { fresh?: boolean } | null)?.fresh === true;

  // Document selection (only meaningful for a not-yet-started chat)
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [pageInput, setPageInput] = useState("");
  const [pickerOpen, setPickerOpen] = useState(false);

  const pageNumber = useMemo(() => {
    const n = parseInt(pageInput, 10);
    return selectedFiles.length === 1 && Number.isFinite(n) && n > 0 ? n : null;
  }, [pageInput, selectedFiles.length]);

  const chat = useChatSession(chatId, fresh);
  const stream = useChatStream({
    chatId,
    setMessages: chat.setMessages,
    refreshSession: chat.refreshSession,
    selection: { files: selectedFiles, page: pageNumber },
  });
  const { scrollRef, contentRef, onScroll, showJump, scrollToBottom, stickToBottom } =
    useAutoScroll(chatId);

  const [draft, setDraft] = useState("");
  const [hiddenIds, setHiddenIds] = useState<Set<string>>(new Set());
  const [sourcesOpen, setSourcesOpen] = useState<Source[] | null>(null);
  const inputRef = useRef<ChatInputHandle>(null);

  // Per-chat UI state
  useEffect(() => {
    setDraft("");
    setHiddenIds(new Set());
    setSourcesOpen(null);
  }, [chatId]);

  // "New chat" (including clicking it while already on /chat) resets the selection.
  // location.key changes on every navigation; we only act when no chat is open.
  useEffect(() => {
    if (!chatId) {
      setSelectedFiles([]);
      setPageInput("");
      setPickerOpen(false);
    }
  }, [chatId, location.key]);

  const handleSelectedChange = useCallback((next: string[]) => {
    setSelectedFiles(next);
    if (next.length !== 1) setPageInput(""); // page only applies to a single document
  }, []);

  const visibleMessages = useMemo(
    () => chat.messages.filter((m) => !hiddenIds.has(m.id)),
    [chat.messages, hiddenIds],
  );

  const handleSend = async (text: string) => {
    // A new chat needs at least one document (the backend rejects it otherwise)
    if (!chatId && selectedFiles.length === 0) {
      toast.error("Select at least one document first.");
      setPickerOpen(true);
      return;
    }
    setPickerOpen(false);
    setDraft("");
    stickToBottom();
    const ok = await stream.send(text);
    if (!ok) setDraft((d) => d || text);
  };

  const handleEdit = useCallback((text: string) => {
    setDraft(text);
    inputRef.current?.focus();
  }, []);

  const send = stream.send;
  const handleRetry = useCallback(async () => {
    const lastAi = visibleMessages[visibleMessages.length - 1];
    if (!lastAi || lastAi.role !== "assistant") return;
    const lastUser = [...visibleMessages].reverse().find((m) => m.role === "user");
    if (!lastUser) return;

    setHiddenIds((prev) => new Set(prev).add(lastAi.id));
    stickToBottom();
    const ok = await send(lastUser.content, { retry: true });
    if (!ok) {
      setHiddenIds((prev) => {
        const next = new Set(prev);
        next.delete(lastAi.id);
        return next;
      });
    }
  }, [visibleMessages, send, stickToBottom]);

  const paused = chat.session?.paused_reason ?? null;
  const failed = chat.status === "not-found" || chat.status === "error";
  const hasContent = visibleMessages.length > 0 || stream.live !== null;

  // Locked as soon as the chat exists or the first message is in flight
  const locked = !!chatId || hasContent;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header
        className={cn(
          "flex h-14 shrink-0 items-center justify-between gap-3 border-b border-border pr-4",
          "transition-[padding] duration-200",
          sidebarOpen ? "pl-4" : "pl-14",
        )}
      >
        <h1 className="min-w-0 truncate text-sm font-medium">
          {chat.session?.title || "New chat"}
        </h1>
        <DocumentsControl
          locked={locked}
          lockedFiles={chat.session?.selected_files ?? selectedFiles}
          lockedPage={chat.session ? chat.session.page : pageNumber}
          lockedLoading={!!chatId && chat.status === "loading"}
          selected={selectedFiles}
          onSelectedChange={handleSelectedChange}
          page={pageInput}
          onPageChange={setPageInput}
          open={pickerOpen}
          onOpenChange={setPickerOpen}
        />
      </header>

      {failed ? (
        <ChatError
          kind={chat.status === "not-found" ? "not-found" : "error"}
          message={chat.error}
          onRetry={chat.retry}
        />
      ) : (
        <>
          {paused && <PausedBanner reason={paused} />}

          <div className="relative min-h-0 flex-1">
            <div ref={scrollRef} onScroll={onScroll} className="h-full overflow-y-auto">
              <div ref={contentRef} className="mx-auto w-full max-w-3xl px-4 py-6">
                {chat.status === "loading" ? (
                  <MessageListSkeleton />
                ) : hasContent ? (
                  <div className="space-y-6">
                    <MessageList
                      messages={visibleMessages}
                      chatId={chatId}
                      canRetry={!stream.streaming && !paused}
                      onEdit={handleEdit}
                      onRetry={handleRetry}
                      onViewSources={setSourcesOpen}
                    />
                    {stream.live && <StreamingMessage live={stream.live} />}
                  </div>
                ) : chat.status === "idle" ? (
                  <StartState
                    selectedCount={selectedFiles.length}
                    onOpenPicker={() => setPickerOpen(true)}
                  />
                ) : (
                  <div className="py-24 text-center text-fg-muted">No messages yet.</div>
                )}
              </div>
            </div>

            {showJump && (
              <button
                type="button"
                aria-label="Scroll to latest message"
                onClick={() => scrollToBottom(true)}
                className="absolute bottom-3 left-1/2 flex h-9 w-9 -translate-x-1/2 items-center justify-center rounded-full border border-border bg-surface-2 text-fg shadow-lg transition-colors hover:border-accent/60"
              >
                <ArrowDown size={16} />
              </button>
            )}
          </div>

          <footer className="shrink-0 px-4 pb-4">
            <div className="mx-auto max-w-3xl">
              <ChatInput
                ref={inputRef}
                value={draft}
                onChange={setDraft}
                onSend={handleSend}
                onStop={stream.stop}
                streaming={stream.streaming}
                disabled={!!paused || chat.status === "loading"}
              />
            </div>
          </footer>
        </>
      )}

      <SourcesModal sources={sourcesOpen} onClose={() => setSourcesOpen(null)} />
    </div>
  );
}
import { memo, useCallback } from "react";
import UserBubble from "@/components/chat/UserBubble";
import AssistantBubble from "@/components/chat/AssistantBubble";
import { useSpeechSynthesis } from "@/hooks/useSpeechSynthesis";
import { useToast } from "@/components/ui/Toast";
import { copyText } from "@/lib/clipboard";
import { stripMarkdown } from "@/lib/markdown";
import type { ChatMessage, Source } from "@/types";

interface Props {
  messages: ChatMessage[];
  chatId: string | undefined;
  /** False while streaming or paused: hides "Try again". */
  canRetry: boolean;
  onEdit: (text: string) => void;
  onRetry: () => void;
  onViewSources: (sources: Source[]) => void;
}

const MessageList = memo(function MessageList({
  messages,
  chatId,
  canRetry,
  onEdit,
  onRetry,
  onViewSources,
}: Props) {
  const toast = useToast();
  const speech = useSpeechSynthesis();

  const share = useCallback(async () => {
    if (!chatId) return;
    const url = `${window.location.origin}/chat/${chatId}`;
    (await copyText(url)) ? toast.success("Chat link copied") : toast.error("Could not copy link");
  }, [chatId, toast]);

  const last = messages[messages.length - 1];

  return (
    <>
      {messages.map((m) =>
        m.role === "user" ? (
          <UserBubble key={m.id} content={m.content} onEdit={onEdit} />
        ) : (
          <AssistantBubble
            key={m.id}
            content={m.content}
            sources={m.sources}
            // Only the final message in the chat can be retried
            canRetry={canRetry && m === last}
            speaking={speech.speakingId === m.id}
            speechSupported={speech.supported}
            onToggleSpeak={() => speech.toggle(m.id, stripMarkdown(m.content))}
            onShare={share}
            onRetry={onRetry}
            onViewSources={onViewSources}
            durationMs={m.durationMs}
          />
        ),
      )}
    </>
  );
});

export default MessageList;
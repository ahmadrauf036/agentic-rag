import { memo } from "react";
import { BookOpen, Copy, RotateCcw, Share2, Square, Volume2 } from "lucide-react";
import Markdown from "@/components/chat/Markdown";
import ActionButton, { ACTIONS_ROW } from "@/components/chat/ActionButton";
import { useToast } from "@/components/ui/Toast";
import { copyText } from "@/lib/clipboard";
import type { Source } from "@/types";
import { formatMs } from "./ElapsedTimer";

interface Props {
  content: string;
  sources?: Source[] | null;
  canRetry: boolean;
  speaking: boolean;
  speechSupported: boolean;
  onToggleSpeak: () => void;
  onShare: () => void;
  onRetry: () => void;
  onViewSources: (sources: Source[]) => void;
  durationMs?: number;
}

const AssistantBubble = memo(function AssistantBubble({
  content,
  sources,
  canRetry,
  speaking,
  speechSupported,
  onToggleSpeak,
  onShare,
  onRetry,
  onViewSources,
  durationMs,
}: Props) {
  const toast = useToast();
  const hasSources = !!sources && sources.length > 0;

  const copy = async () =>
    (await copyText(content)) ? toast.success("Copied") : toast.error("Could not copy");

  return (
    <div className="group text-[15px] leading-relaxed wrap-break-word">
      <Markdown>{content}</Markdown>
    {durationMs !== undefined && (
  <p className="mt-2 text-xs tabular-nums text-fg-muted">
    Answered in {formatMs(durationMs)}
  </p>
)}
      <div className={ACTIONS_ROW}>
        <ActionButton label="Copy" onClick={copy}>
          <Copy size={14} />
        </ActionButton>
        {speechSupported && (
          <ActionButton
            label={speaking ? "Stop reading" : "Read aloud"}
            active={speaking}
            onClick={onToggleSpeak}
          >
            {speaking ? <Square size={13} fill="currentColor" /> : <Volume2 size={14} />}
          </ActionButton>
        )}
        <ActionButton label="Copy chat link" onClick={onShare}>
          <Share2 size={14} />
        </ActionButton>
        {canRetry && (
          <ActionButton label="Try again" onClick={onRetry}>
            <RotateCcw size={14} />
          </ActionButton>
        )}
        {hasSources && (
          <ActionButton label="View sources" onClick={() => onViewSources(sources!)}>
            <BookOpen size={14} />
          </ActionButton>
        )}
      </div>
    </div>
  );
});

export default AssistantBubble;
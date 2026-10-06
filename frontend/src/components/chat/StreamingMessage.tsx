import Markdown from "@/components/chat/Markdown";
import ToolIndicator from "@/components/chat/ToolIndicator";
import ElapsedTimer from "@/components/chat/ElapsedTimer";
import type { LiveMessage } from "@/hooks/useChatStream";

export default function StreamingMessage({ live }: { live: LiveMessage }) {
  const waiting = !live.content && live.tools.length === 0;

  return (
    <div className="text-[15px] leading-relaxed wrap-break-word">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        {waiting && (
          <div className="flex gap-1" role="status" aria-label="Assistant is thinking">
            {[0, 150, 300].map((d) => (
              <span
                key={d}
                className="h-1.5 w-1.5 animate-pulse rounded-full bg-fg-muted"
                style={{ animationDelay: `${d}ms` }}
              />
            ))}
          </div>
        )}
        <ToolIndicator tools={live.tools} />
        <ElapsedTimer startedAt={live.startedAt} />
      </div>

      {live.content && (
        <>
          <Markdown>{live.content}</Markdown>
          <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse bg-accent align-middle" />
        </>
      )}
    </div>
  );
}
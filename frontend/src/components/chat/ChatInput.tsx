import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useLayoutEffect,
  useRef,
  type Dispatch,
  type SetStateAction,
} from "react";
import { ArrowUp, Mic, Square } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Tooltip } from "@/components/ui/ToolTip";
import { useToast } from "@/components/ui/Toast";
import { useSpeechRecognition } from "@/hooks/useSpeechRecognition";
import { cn } from "@/lib/cn";

export interface ChatInputHandle {
  focus: () => void;
}

interface Props {
  value: string;
  onChange: Dispatch<SetStateAction<string>>;
  onSend: (text: string) => void;
  onStop: () => void;
  streaming: boolean;
  disabled: boolean;
}

const MAX_HEIGHT = 200;

const ChatInput = forwardRef<ChatInputHandle, Props>(function ChatInput(
  { value, onChange, onSend, onStop, streaming, disabled },
  ref,
) {
  const taRef = useRef<HTMLTextAreaElement>(null);
  const toast = useToast();

  useImperativeHandle(ref, () => ({ focus: () => taRef.current?.focus() }), []);

  // Speech fills the box; it never sends.
  const speech = useSpeechRecognition({
    onFinal: (text) =>
      onChange((prev) => {
        const chunk = text.trim();
        if (!chunk) return prev;
        return prev && !/\s$/.test(prev) ? `${prev} ${chunk}` : prev + chunk;
      }),
  });

  useEffect(() => {
    if (speech.error) toast.error(speech.error);
  }, [speech.error, toast]);

  // Stop listening if the input gets disabled
  useEffect(() => {
    if (disabled && speech.listening) speech.stop();
  }, [disabled, speech]);

  // Auto-grow
  useLayoutEffect(() => {
    const el = taRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT)}px`;
  }, [value]);

  const canSend = !disabled && !streaming && value.trim().length > 0;

  const submit = () => {
    if (!canSend) return;
    if (speech.listening) speech.stop();
    onSend(value);
  };

  return (
    <div>
      {speech.listening && (
        <p className="mb-1.5 px-2 text-xs text-accent" aria-live="polite">
          Listening…{" "}
          {speech.interim && <span className="italic text-fg-muted">{speech.interim}</span>}
        </p>
      )}

      <div
        className={cn(
          "flex items-end gap-1.5 rounded-2xl border border-border bg-surface p-2 transition-colors",
          "focus-within:border-accent/70 focus-within:shadow-[0_0_0_3px_rgb(99_168_248/0.15)]",
          disabled && "opacity-60",
        )}
      >
        <textarea
          ref={taRef}
          rows={1}
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder={disabled ? "This chat is unavailable" : "Message…"}
          aria-label="Message"
          className="max-h-50 min-h-9 flex-1 resize-none bg-transparent px-2 py-1.5 text-[15px] text-fg placeholder:text-fg-muted focus:outline-none!"
        />

        {speech.supported && (
          <Tooltip label={speech.listening ? "Stop dictation" : "Dictate"}>
            <Button
              size="icon"
              variant="ghost"
              aria-label={speech.listening ? "Stop dictation" : "Start dictation"}
              aria-pressed={speech.listening}
              disabled={disabled}
              onClick={speech.toggle}
              className={cn(speech.listening && "animate-pulse bg-accent/15 text-accent shadow-glow")}
            >
              <Mic size={18} />
            </Button>
          </Tooltip>
        )}

        {streaming ? (
          <Tooltip label="Stop">
            <Button size="icon" aria-label="Stop generating" onClick={onStop}>
              <Square size={14} fill="currentColor" />
            </Button>
          </Tooltip>
        ) : (
          <Tooltip label="Send">
            <Button size="icon" aria-label="Send message" disabled={!canSend} onClick={submit}>
              <ArrowUp size={18} />
            </Button>
          </Tooltip>
        )}
      </div>
    </div>
  );
});

export default ChatInput;
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";

const THRESHOLD = 80; // px from bottom that still counts as "at the bottom"

export function useAutoScroll(resetKey: unknown) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const stickRef = useRef(true);
  const [showJump, setShowJump] = useState(false);

  const scrollToBottom = useCallback((smooth = false) => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: smooth ? "smooth" : "auto" });
  }, []);

  const onScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const near = el.scrollHeight - el.scrollTop - el.clientHeight < THRESHOLD;
    stickRef.current = near;
    setShowJump(!near);
  }, []);

  // Follow content growth while stuck to the bottom
  useEffect(() => {
    const content = contentRef.current;
    if (!content) return;
    const ro = new ResizeObserver(() => {
      if (stickRef.current) scrollToBottom();
    });
    ro.observe(content);
    return () => ro.disconnect();
  }, [scrollToBottom]);

  // New chat: start stuck to the bottom
  useLayoutEffect(() => {
    stickRef.current = true;
    setShowJump(false);
    scrollToBottom();
  }, [resetKey, scrollToBottom]);

  /** Call when the user sends a message: always jump to the bottom. */
  const stickToBottom = useCallback(() => {
    stickRef.current = true;
    setShowJump(false);
    scrollToBottom(true);
  }, [scrollToBottom]);

  return { scrollRef, contentRef, onScroll, showJump, scrollToBottom, stickToBottom };
}
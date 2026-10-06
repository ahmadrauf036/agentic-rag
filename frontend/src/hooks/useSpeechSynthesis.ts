import { useCallback, useEffect, useState } from "react";

export function useSpeechSynthesis() {
  const supported = typeof window !== "undefined" && "speechSynthesis" in window;
  /** id of the message currently being read, or null */
  const [speakingId, setSpeakingId] = useState<string | null>(null);

  const stop = useCallback(() => {
    if (!supported) return;
    window.speechSynthesis.cancel();
    setSpeakingId(null);
  }, [supported]);

  const speak = useCallback(
    (id: string, text: string) => {
      if (!supported) return;
      window.speechSynthesis.cancel(); // interrupt anything already playing

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.onend = () => setSpeakingId((cur) => (cur === id ? null : cur));
      utterance.onerror = () => setSpeakingId((cur) => (cur === id ? null : cur));

      setSpeakingId(id);
      window.speechSynthesis.speak(utterance);
    },
    [supported],
  );

  const toggle = useCallback(
    (id: string, text: string) => {
      if (speakingId === id) stop();
      else speak(id, text);
    },
    [speakingId, speak, stop],
  );

  // Stop talking when the component unmounts (e.g. navigating away)
  useEffect(() => () => {
    if (supported) window.speechSynthesis.cancel();
  }, [supported]);

  return { supported, speakingId, speak, stop, toggle };
}
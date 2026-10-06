import { useCallback, useEffect, useRef, useState } from "react";

/* Minimal typings (not in lib.dom.d.ts) */
interface SRAlternative {
  transcript: string;
}
interface SRResult {
  isFinal: boolean;
  0: SRAlternative;
}
interface SREvent {
  resultIndex: number;
  results: ArrayLike<SRResult>;
}
interface SRErrorEvent {
  error: string;
}
interface SRInstance {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((e: SREvent) => void) | null;
  onerror: ((e: SRErrorEvent) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}
type SRConstructor = new () => SRInstance;

const getCtor = (): SRConstructor | null => {
  const w = window as unknown as {
    SpeechRecognition?: SRConstructor;
    webkitSpeechRecognition?: SRConstructor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
};

const ERROR_MESSAGES: Record<string, string> = {
  "not-allowed": "Microphone access was blocked.",
  "service-not-allowed": "Microphone access was blocked.",
  "no-speech": "No speech detected. Try again.",
  "audio-capture": "No microphone found.",
  network: "Speech recognition needs a network connection.",
};

interface Options {
  lang?: string;
  /** Called with each finalized chunk of speech. */
  onFinal: (text: string) => void;
}

export function useSpeechRecognition({ lang = "en-US", onFinal }: Options) {
  const supported = getCtor() !== null;
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState("");
  const [error, setError] = useState<string | null>(null);

  const recRef = useRef<SRInstance | null>(null);
  const onFinalRef = useRef(onFinal);
  onFinalRef.current = onFinal;

  const start = useCallback(() => {
    const Ctor = getCtor();
    if (!Ctor || recRef.current) return;

    const rec = new Ctor();
    rec.lang = lang;
    rec.continuous = true;
    rec.interimResults = true;

    rec.onresult = (e) => {
      let interimText = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const result = e.results[i];
        if (result.isFinal) onFinalRef.current(result[0].transcript);
        else interimText += result[0].transcript;
      }
      setInterim(interimText);
    };

    rec.onerror = (e) => {
      if (e.error !== "aborted") {
        setError(ERROR_MESSAGES[e.error] ?? `Speech error: ${e.error}`);
      }
    };

    rec.onend = () => {
      recRef.current = null;
      setListening(false);
      setInterim("");
    };

    setError(null);
    recRef.current = rec;
    rec.start();
    setListening(true);
  }, [lang]);

  const stop = useCallback(() => {
    recRef.current?.stop();
  }, []);

  const toggle = useCallback(() => {
    if (recRef.current) stop();
    else start();
  }, [start, stop]);

  useEffect(() => () => recRef.current?.abort(), []);

  return { supported, listening, interim, error, start, stop, toggle };
}
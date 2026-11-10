import { useCallback, useRef, useState } from "react";

// Browser speech APIs (Chrome/Edge/Safari). Swap for cloud STT/TTS later without changing callers.
/* eslint-disable @typescript-eslint/no-explicit-any */
export function useSpeech() {
  const [listening, setListening] = useState(false);
  const recognition = useRef<any>(null);

  const w = window as any;
  const Recognition = w.SpeechRecognition ?? w.webkitSpeechRecognition;
  const supported = Boolean(Recognition) && "speechSynthesis" in window;

  const speak = useCallback((text: string) => {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(new SpeechSynthesisUtterance(text));
  }, []);

  const stop = useCallback(() => {
    recognition.current?.stop();
    setListening(false);
  }, []);

  const listen = useCallback(
    (onText: (text: string) => void) => {
      if (!Recognition) return;
      window.speechSynthesis?.cancel();
      const rec = new Recognition();
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = "en-US";
      rec.onresult = (e: any) => {
        const text = Array.from(e.results as ArrayLike<any>)
          .map((r) => r[0].transcript)
          .join(" ");
        onText(text);
      };
      rec.onend = () => setListening(false);
      rec.start();
      recognition.current = rec;
      setListening(true);
    },
    [Recognition]
  );

  return { supported, listening, speak, listen, stop };
}

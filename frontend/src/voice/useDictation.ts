import { useEffect, useRef, useState } from "react";
import type { Lang } from "./voiceKeys";

type SpeechResult = { isFinal: boolean; 0: { transcript: string } };
type RecognitionEvent = Event & { results: { length: number; [index: number]: SpeechResult } };
type RecognitionErrorEvent = Event & { error: string };
interface SpeechRecognitionInstance {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onend: (() => void) | null;
  onerror: ((event: RecognitionErrorEvent) => void) | null;
  onresult: ((event: RecognitionEvent) => void) | null;
  start(): void;
  stop(): void;
}
type SpeechRecognitionConstructor = new () => SpeechRecognitionInstance;
type SpeechWindow = Window & {
  SpeechRecognition?: SpeechRecognitionConstructor;
  webkitSpeechRecognition?: SpeechRecognitionConstructor;
};

const errorMessages: Record<string, string> = {
  "not-allowed": "Microphone permission was denied. Type instead.",
  "no-speech": "No speech was detected. Try again or type instead.",
  network: "Browser speech service needs an internet connection.",
  "audio-capture": "No microphone was available. Type instead.",
};

export function useDictation(lang: Lang) {
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const [listening, setListening] = useState(false);
  const [interimText, setInterimText] = useState("");
  const [finalText, setFinalText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const speechWindow = window as SpeechWindow;
  const Constructor = speechWindow.SpeechRecognition || speechWindow.webkitSpeechRecognition;

  useEffect(() => () => {
    recognitionRef.current?.stop();
  }, []);

  function start(): void {
    if (!Constructor || listening) return;
    setError(null);
    setInterimText("");
    setFinalText("");
    const recognition = new Constructor();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = lang === "hi" ? "hi-IN" : lang === "ta" ? "ta-IN" : "en-IN";
    recognition.onresult = event => {
      let interim = "";
      let final = "";
      for (let index = event.results.length - 1; index >= 0; index -= 1) {
        const result = event.results[index];
        if (result.isFinal) final = `${result[0].transcript} ${final}`;
        else interim = `${result[0].transcript} ${interim}`;
      }
      setFinalText(final.trim());
      setInterimText(interim.trim());
    };
    recognition.onerror = event => {
      setError(errorMessages[event.error] || "Dictation failed. Type instead.");
      setListening(false);
    };
    recognition.onend = () => setListening(false);
    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }

  function stop(): void {
    recognitionRef.current?.stop();
    setListening(false);
  }

  return {
    start,
    stop,
    interimText,
    finalText,
    listening,
    supported: Boolean(Constructor),
    error,
  };
}

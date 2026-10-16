import { useEffect, useRef, useState } from "react";
import type { CSSProperties } from "react";
import { RecorderError, startRecording, stopRecording } from "./recorder";
import { speak } from "./speak";
import type { Lang, VoiceKey } from "./voiceKeys";

type VoiceButtonStatus = "idle" | "recording" | "processing";

interface VoiceButtonProps {
  lang: Lang;
  onRecorded: (blob: Blob, mimeType: string) => void;
  disabled?: boolean;
}

interface SpeakButtonProps {
  lang: Lang;
  text?: string;
  voiceKey?: VoiceKey;
}

const styles: Record<string, CSSProperties> = {
  wrapper: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 8,
    fontFamily: "system-ui, sans-serif",
  },
  micButton: {
    minWidth: 64,
    minHeight: 64,
    padding: "12px 20px",
    borderRadius: 16,
    border: "2px solid #1a56db",
    background: "#ffffff",
    color: "#1a56db",
    fontSize: 18,
    fontWeight: 600,
    cursor: "pointer",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
  },
  micButtonRecording: {
    background: "#fee2e2",
    borderColor: "#dc2626",
    color: "#b91c1c",
  },
  micButtonDisabled: {
    opacity: 0.5,
    cursor: "not-allowed",
  },
  timer: {
    fontSize: 13,
    fontVariantNumeric: "tabular-nums",
  },
  speakButton: {
    minHeight: 44,
    padding: "8px 16px",
    borderRadius: 10,
    border: "1px solid #4b5563",
    background: "#f9fafb",
    color: "#111827",
    fontSize: 15,
    cursor: "pointer",
  },
  error: {
    margin: 0,
    color: "#b91c1c",
    fontSize: 14,
    textAlign: "center",
  },
};

function formatElapsed(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function recorderErrorText(error: unknown): string {
  if (error instanceof RecorderError) {
    if (error.kind === "permission_denied") {
      return "Microphone blocked. Type instead.";
    }
    if (error.kind === "no_device") {
      return "No microphone found. Type instead.";
    }
  }
  return "Recording failed. Type instead.";
}

export function VoiceButton({ lang, onRecorded, disabled = false }: VoiceButtonProps) {
  const [status, setStatus] = useState<VoiceButtonStatus>("idle");
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [errorText, setErrorText] = useState<string | null>(null);
  const intervalRef = useRef<number | null>(null);
  const startingRef = useRef(false);

  useEffect(() => {
    if (status !== "recording") {
      if (intervalRef.current !== null) {
        window.clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }
    const startedAt = Date.now();
    setElapsedSeconds(0);
    intervalRef.current = window.setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1000));
    }, 250);
    return () => {
      if (intervalRef.current !== null) {
        window.clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [status]);

  async function handleToggle(): Promise<void> {
    if (disabled || status === "processing" || startingRef.current) return;

    if (status === "recording") {
      setStatus("processing");
      try {
        const { blob, mimeType } = await stopRecording();
        setErrorText(null);
        onRecorded(blob, mimeType);
      } catch (error) {
        setErrorText(recorderErrorText(error));
      } finally {
        setStatus("idle");
      }
      return;
    }

    setErrorText(null);
    startingRef.current = true;
    setStatus("recording");
    try {
      await startRecording();
    } catch (error) {
      setStatus("idle");
      setErrorText(recorderErrorText(error));
    } finally {
      startingRef.current = false;
    }
  }

  const isRecording = status === "recording";
  const ariaLabel = isRecording ? "Stop recording" : "Start voice recording";

  return (
    <div style={styles.wrapper}>
      <button
        type="button"
        aria-label={ariaLabel}
        disabled={disabled || status === "processing"}
        onClick={() => void handleToggle()}
        style={{
          ...styles.micButton,
          ...(isRecording ? styles.micButtonRecording : {}),
          ...(disabled || status === "processing" ? styles.micButtonDisabled : {}),
        }}
      >
        <span aria-hidden="true">{isRecording ? "⏹" : "🎙️"}</span>
        <span>
          {status === "idle" && "Tap to speak"}
          {isRecording && "Stop"}
          {status === "processing" && "Processing…"}
        </span>
        {isRecording && (
          <span style={styles.timer} aria-hidden="true">
            {formatElapsed(elapsedSeconds)} / 0:45
          </span>
        )}
      </button>
      {errorText && (
        <p role="alert" style={styles.error} lang={lang}>
          {errorText}
        </p>
      )}
    </div>
  );
}

export function SpeakButton({ lang, text, voiceKey }: SpeakButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [showUnavailable, setShowUnavailable] = useState(false);

  async function handleClick(): Promise<void> {
    setIsLoading(true);
    setShowUnavailable(false);
    try {
      const result = await speak({ lang, text, key: voiceKey });
      if (result === "unavailable") setShowUnavailable(true);
    } catch {
      setShowUnavailable(true);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div style={styles.wrapper}>
      <button
        type="button"
        aria-label="Play spoken message"
        disabled={isLoading}
        onClick={() => void handleClick()}
        style={{
          ...styles.speakButton,
          ...(isLoading ? styles.micButtonDisabled : {}),
        }}
      >
        {isLoading ? "Loading audio…" : "🔊 Listen"}
      </button>
      {showUnavailable && (
        <p role="alert" style={styles.error}>
          Audio not available on this device
        </p>
      )}
    </div>
  );
}
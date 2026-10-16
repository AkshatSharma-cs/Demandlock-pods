export type RecorderErrorKind =
  | "permission_denied"
  | "unsupported"
  | "no_device";

export class RecorderError extends Error {
  readonly kind: RecorderErrorKind;

  constructor(kind: RecorderErrorKind, message?: string) {
    super(message ?? kind);
    this.name = "RecorderError";
    this.kind = kind;
  }
}

export interface RecordingResult {
  blob: Blob;
  mimeType: string;
  durationMs: number;
}

const MIME_CANDIDATES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/mp4",
] as const;

const MAX_RECORDING_MS = 45_000;

interface RecorderState {
  recorder: MediaRecorder | null;
  stream: MediaStream | null;
  chunks: Blob[];
  startedAt: number;
  resolveStop: ((result: RecordingResult) => void) | null;
  rejectStop: ((error: Error) => void) | null;
  autoStopTimer: number | null;
  pendingResult: RecordingResult | null;
}

const state: RecorderState = {
  recorder: null,
  stream: null,
  chunks: [],
  startedAt: 0,
  resolveStop: null,
  rejectStop: null,
  autoStopTimer: null,
  pendingResult: null,
};

function releaseMicrophone(): void {
  state.stream?.getTracks().forEach((track) => track.stop());
  state.stream = null;
}

function clearAutoStop(): void {
  if (state.autoStopTimer !== null) {
    window.clearTimeout(state.autoStopTimer);
    state.autoStopTimer = null;
  }
}

function pickMimeType(): string {
  for (const candidate of MIME_CANDIDATES) {
    if (MediaRecorder.isTypeSupported(candidate)) return candidate;
  }
  return "";
}

function finalizeRecording(): void {
  clearAutoStop();
  const durationMs = Date.now() - state.startedAt;
  const mimeType = state.recorder?.mimeType || "audio/webm";
  const blob = new Blob(state.chunks, { type: mimeType });
  const resolve = state.resolveStop;

  state.pendingResult = resolve ? null : { blob, mimeType, durationMs };
  state.recorder = null;
  state.chunks = [];
  state.resolveStop = null;
  state.rejectStop = null;
  releaseMicrophone();

  resolve?.({ blob, mimeType, durationMs });
}

function failRecording(error: Error): void {
  clearAutoStop();
  const reject = state.rejectStop;
  state.recorder = null;
  state.chunks = [];
  state.resolveStop = null;
  state.rejectStop = null;
  releaseMicrophone();
  reject?.(error);
}

export async function startRecording(): Promise<void> {
  if (state.recorder && state.recorder.state !== "inactive") {
    throw new RecorderError("unsupported", "Recording is already in progress.");
  }
  if (
    typeof window === "undefined" ||
    typeof MediaRecorder === "undefined" ||
    !navigator.mediaDevices?.getUserMedia
  ) {
    throw new RecorderError(
      "unsupported",
      "Audio recording is not supported on this device."
    );
  }

  let stream: MediaStream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (error) {
    const name = (error as DOMException).name;
    if (name === "NotAllowedError" || name === "SecurityError") {
      throw new RecorderError("permission_denied", "Microphone permission was denied.");
    }
    if (
      name === "NotFoundError" ||
      name === "OverconstrainedError" ||
      name === "NotReadableError"
    ) {
      throw new RecorderError("no_device", "No usable microphone was found.");
    }
    throw new RecorderError("unsupported", "Could not access the microphone.");
  }

  if (stream.getAudioTracks().length === 0) {
    stream.getTracks().forEach((track) => track.stop());
    throw new RecorderError("no_device", "No audio input device was found.");
  }

  const mimeType = pickMimeType();
  let recorder: MediaRecorder;
  try {
    recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
  } catch {
    stream.getTracks().forEach((track) => track.stop());
    throw new RecorderError("unsupported", "Could not start the audio recorder.");
  }

  state.stream = stream;
  state.chunks = [];
  state.recorder = recorder;
  state.startedAt = Date.now();
  state.pendingResult = null;

  recorder.ondataavailable = (event: BlobEvent) => {
    if (event.data.size > 0) state.chunks.push(event.data);
  };
  recorder.onstop = () => {
    if (state.recorder !== recorder) return;
    finalizeRecording();
  };
  recorder.onerror = () => {
    if (state.recorder !== recorder) return;
    failRecording(new RecorderError("unsupported", "The recorder failed."));
  };

  recorder.start();
  state.autoStopTimer = window.setTimeout(() => {
    if (state.recorder === recorder && recorder.state !== "inactive") {
      recorder.stop();
    }
  }, MAX_RECORDING_MS);
}

export function stopRecording(): Promise<RecordingResult> {
  return new Promise((resolve, reject) => {
    const recorder = state.recorder;
    if (!recorder || recorder.state === "inactive") {
      if (state.pendingResult) {
        resolve(state.pendingResult);
        state.pendingResult = null;
        return;
      }
      reject(new RecorderError("unsupported", "Recording has not started."));
      return;
    }
    state.resolveStop = resolve;
    state.rejectStop = reject;
    try {
      recorder.stop();
    } catch (error) {
      state.resolveStop = null;
      state.rejectStop = null;
      reject(error instanceof Error ? error : new RecorderError("unsupported"));
    }
  });
}
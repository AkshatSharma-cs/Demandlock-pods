import { audioUrl, BCP47, VOICE_KEYS } from "./voiceKeys";
import type { Lang, VoiceKey } from "./voiceKeys";

export type SpeakResult = "prerecorded" | "synthesis" | "unavailable";

export interface VoiceSupport {
  synthesis: boolean;
  prerecordedKeysCached: VoiceKey[];
}

const PLAY_TIMEOUT_MS = 5000;
const VOICES_TIMEOUT_MS = 1500;
const SYNTHESIS_START_TIMEOUT_MS = 2000;

let currentAudio: HTMLAudioElement | null = null;

function playPrerecorded(lang: Lang, key: VoiceKey): Promise<boolean> {
  return new Promise((resolve) => {
    if (typeof window === "undefined" || typeof Audio === "undefined") {
      resolve(false);
      return;
    }

    const audio = new Audio(audioUrl(lang, key));
    currentAudio = audio;

    let settled = false;
    const finish = (ok: boolean) => {
      if (settled) return;
      settled = true;
      window.clearTimeout(timer);
      if (!ok && currentAudio === audio) currentAudio = null;
      resolve(ok);
    };

    const timer = window.setTimeout(() => {
      audio.pause();
      finish(false);
    }, PLAY_TIMEOUT_MS);

    audio.addEventListener("playing", () => finish(true), { once: true });
    audio.addEventListener("error", () => finish(false), { once: true });
    audio.play().catch(() => finish(false));
  });
}

function loadVoices(): Promise<SpeechSynthesisVoice[]> {
  return new Promise((resolve) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      resolve([]);
      return;
    }
    const synth = window.speechSynthesis;

    const existing = synth.getVoices();
    if (existing.length > 0) {
      resolve(existing);
      return;
    }

    let settled = false;
    const finish = (voices: SpeechSynthesisVoice[]) => {
      if (settled) return;
      settled = true;
      window.clearTimeout(timer);
      synth.onvoiceschanged = null;
      resolve(voices);
    };
    const onVoicesChanged = () => {
      const voices = synth.getVoices();
      if (voices.length > 0) finish(voices);
    };
    const timer = window.setTimeout(() => finish(synth.getVoices()), VOICES_TIMEOUT_MS);

    synth.onvoiceschanged = onVoicesChanged;
  });
}

function pickVoice(
  voices: SpeechSynthesisVoice[],
  bcp47: string
): SpeechSynthesisVoice | undefined {
  const target = bcp47.toLowerCase();
  const exact = voices.find((voice) => voice.lang.toLowerCase() === target);
  if (exact) return exact;
  const prefix = target.split("-")[0];
  return voices.find((voice) => voice.lang.toLowerCase().startsWith(prefix));
}

function speakWithSynthesis(text: string, lang: Lang): Promise<boolean> {
  return new Promise((resolve) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      resolve(false);
      return;
    }
    const synth = window.speechSynthesis;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = BCP47[lang];

    let settled = false;
    const finish = (ok: boolean) => {
      if (settled) return;
      settled = true;
      window.clearTimeout(timer);
      resolve(ok);
    };

    utterance.onstart = () => finish(true);
    utterance.onerror = () => finish(false);
    const timer = window.setTimeout(() => {
      finish(synth.speaking || synth.pending);
    }, SYNTHESIS_START_TIMEOUT_MS);

    void loadVoices().then((voices) => {
      if (settled) return;
      const voice = pickVoice(voices, BCP47[lang]);
      if (voice) utterance.voice = voice;
      synth.speak(utterance);
    });
  });
}

export async function speak(opts: {
  text?: string;
  key?: VoiceKey;
  lang: Lang;
}): Promise<SpeakResult> {
  stopSpeaking();

  if (opts.key) {
    const played = await playPrerecorded(opts.lang, opts.key);
    if (played) return "prerecorded";
  }

  if (opts.text) {
    const spoken = await speakWithSynthesis(opts.text, opts.lang);
    if (spoken) return "synthesis";
  }

  return "unavailable";
}

export function stopSpeaking(): void {
  if (typeof window === "undefined") return;
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
  if (currentAudio) {
    currentAudio.pause();
    try {
      currentAudio.currentTime = 0;
    } catch {
      // Ignore seek errors on detached media elements.
    }
    currentAudio = null;
  }
}

async function isCached(url: string): Promise<boolean> {
  if (typeof window === "undefined" || !("caches" in window)) return false;
  try {
    const cacheNames = await window.caches.keys();
    for (const cacheName of cacheNames) {
      const cache = await window.caches.open(cacheName);
      if (await cache.match(url)) return true;
    }
  } catch {
    return false;
  }
  return false;
}

export async function getVoiceSupport(lang: Lang): Promise<VoiceSupport> {
  const synthesis =
    typeof window !== "undefined" && "speechSynthesis" in window;
  const prerecordedKeysCached: VoiceKey[] = [];

  await Promise.all(
    VOICE_KEYS.map(async (key) => {
      const url = audioUrl(lang, key);
      try {
        if (await isCached(url)) {
          prerecordedKeysCached.push(key);
          return;
        }
        const response = await fetch(url, { method: "HEAD" });
        if (response.ok) prerecordedKeysCached.push(key);
      } catch {
        // Offline or blocked: tolerate and report this clip as unavailable.
      }
    })
  );

  return { synthesis, prerecordedKeysCached };
}
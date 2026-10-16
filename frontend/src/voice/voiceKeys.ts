export type Lang = "hi" | "ta" | "te" | "en";

export const VOICE_KEYS = [
  "welcome",
  "practice_task",
  "safeguard_message",
  "pod_explanation",
] as const;

export type VoiceKey = (typeof VOICE_KEYS)[number];

export const BCP47: Record<Lang, string> = {
  hi: "hi-IN",
  ta: "ta-IN",
  te: "te-IN",
  en: "en-IN",
};

export function audioUrl(lang: Lang, key: VoiceKey): string {
  return `/audio/${lang}/${key}.mp3`;
}
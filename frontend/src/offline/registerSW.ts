import { registerSW as register } from "virtual:pwa-register";

export function registerSW() {
  if (import.meta.env.PROD) register({ immediate: true });
}
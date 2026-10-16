import { defineConfig } from "vitest/config";
export default defineConfig({ test: { environment: "jsdom", setupFiles: ["./src/offline/testSetup.ts"] } });

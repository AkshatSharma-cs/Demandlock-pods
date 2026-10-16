import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["audio/**"],
      manifest: {
        name: "DemandLock Pods", short_name: "DemandLock", display: "standalone",
        start_url: "/", theme_color: "#14284B",
        icons: [
          { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" }
        ]
      },
      workbox: {
        runtimeCaching: [
          { urlPattern: /\/audio\/.*/i, handler: "CacheFirst", options: { cacheName: "audio", expiration: { maxEntries: 50 } } },
          { urlPattern: /\/api\/v1\/(pods|modules|knowledge|students\/.*\/pods|demand-tickets|dashboard\/impact)/i, handler: "NetworkFirst", options: { cacheName: "api", networkTimeoutSeconds: 4, expiration: { maxAgeSeconds: 604800 } } }
        ]
      }
    })
  ],
  server: { host: true, allowedHosts: true, proxy: { "/api": "http://localhost:8000", "/health": "http://localhost:8000" } }
});
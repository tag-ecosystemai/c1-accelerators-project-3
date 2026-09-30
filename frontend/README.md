# Frontend

React/Vite interface for the SentinelAI supply-chain disruption demo.

## Run locally

1. Copy .env.example to .env (or fill the local .env already created).
2. Set VITE_GEMINI_API_KEY and optionally VITE_GEMINI_MODEL.
3. Run npm install, then npm run dev.
4. Open the local URL shown by Vite.

The guide has two modes: Static FAQ works without an API key; Gemini 3 sends questions directly from the browser to Google's Gemini API. The configured default is gemini-3-flash-preview.

Key warning: Vite embeds variables prefixed with VITE_ in browser code. Visitors can extract the key from a deployed site. Use only a restricted, low-quota demo key for this browser-direct prototype. Do not use a private or production key here; use a backend proxy for a public production deployment.
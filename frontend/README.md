# SentinelAI Frontend

React interface for SentinelAI supply-chain disruption project. This frontend is a product demo: shipment records, risk scores, evidence, routes, metrics and timestamps are illustrative sample data, not live logistics information.

## What is included

- **Landing page:** explains the SentinelAI concept, planned signal-to-briefing workflow, candidate data sources, West African demo context, PRD evaluation targets, MVP scope and human-review guardrails.

- **Responsive layout:** desktop, tablet and mobile navigation and layouts.

- **Operations dashboard:** sample shipment list with search/filter, delay-risk indicators, selected-shipment details, evidence, likely cause, suggested alternative and signal freshness.

- **Data uploads:** separate upload areas in the dashboard for shipment data and RAG knowledge documents.
  - **Shipment data:** one CSV, XLSX or XLS file for the shipment-analysis pipeline.
  - **RAG documents:** multiple PDF, DOCX, TXT or MD files for supplier profiles, procedures and reference knowledge.
  - The frontend validates file formats and lists selected files. Uploading to storage, shipment ingestion and RAG indexing still require separate backend endpoints.

- **Navigation guide:** the chat panel has two modes (You need to create your own API keys on google AI Studio):
  - **Static FAQ** answers common product and navigation questions without an API key.
  - **Gemini 3** sends the conversation to the Gemini API and can answer questions about SentinelAI in context.

The dashboard is currently a frontend demonstration 

## Stack

- JavaScript with React and JSX
- Vite for local development and production builds
- CSS for styling and responsive breakpoints
- Lucide React for icons
- Gemini REST generateContent API for the optional Dynamic chat mode (default model: gemini-3-flash-preview) (needed to be approved by team)

## Requirements

Install Node.js and npm on your computer. Use the repository's frontend folder as the working directory for the commands below. (Before that, first get the frontend from the github)

## Run locally

1. Open a terminal in frontend.
2. Install the project dependencies with **npm install**.
3. Create the local environment file from the example.

   **PowerShell:** Copy-Item .env.example .env

   **macOS/Linux:** cp .env.example .env

4. Open frontend/.env and set your Gemini API key: (not compulsory to run the front.It's just additional feature )

   VITE_GEMINI_API_KEY=your_restricted_demo_key
   VITE_GEMINI_MODEL=gemini-3-flash-preview

   The model variable is optional; the frontend uses gemini-3-flash-preview when it is not set. Save the file, then restart Vite if it was already running.

5. Start the development server with npm run dev.
6. Open the local URL printed by Vite, usually http://localhost:5173.

You can use the landing page and Static FAQ mode without a Gemini key. Choose Gemini 3 in the chat panel to use the Dynamic mode. The Dashboard buttons on the landing page open the sample operations dashboard.

## Build and preview

Create a production build with npm run build. Preview the build locally with npm run preview.

## Gemini key security

This prototype calls Gemini directly from the browser, as requested. Because Vite exposes variables prefixed with VITE_ to browser code, visitors can inspect the built site and retrieve the key. Use only a restricted demo key with a low quota; do not put a private or production key in this frontend. The local .env file is ignored by Git; never commit it.

Google recommends a backend proxy to keep API keys out of client-side code: https://ai.google.dev/gemini-api/docs/api-key. (if we approve the bot on the landing page, we will add the API key on the backend)

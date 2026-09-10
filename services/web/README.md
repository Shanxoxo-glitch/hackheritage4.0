# Sahayak (सहायक) — Anonymous Support Sanctuary & Multi-Role Platform

> A private, anonymous sanctuary to steady yourself, unburden, and connect with human care when you're ready. Built with craft for communities across India.

[![Vite](https://img.shields.io/badge/Vite-8.1.5-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TanStack](https://img.shields.io/badge/TanStack-Router%20%2B%20Start-FF4154?logo=react&logoColor=white)](https://tanstack.com/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-v4-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![PWA](https://img.shields.io/badge/PWA-Installable-5A0FC8?logo=pwa&logoColor=white)](https://web.dev/progressive-web-apps/)

---

## 🧭 The Three Roles

| Role | What they do | Key Features |
|---|---|---|
| **Victim** | Daily check-ins, crisis grounding, confidential requests, case lookup | • One-question-per-screen check-in<br>• Organic Garden of Days<br>• Sanctuary chat with living breathing orb<br>• Letter-flow request with wax-seal codeword<br>• Safety Quick Exit (<kbd>Esc</kbd>) |
| **Counsellor** | Case reviews, triage alerts, field notes, escalation approvals | • Manila paper-file case dossiers<br>• Timeline distress trajectory chart<br>• Field clinical notebook editor<br>• Triage alert queue with approve/reject<br>• Explainable AI decision trace audit |
| **Admin** | Observatory monitoring, caseload distribution, response SLAs | • 14-day community wellbeing area chart<br>• District triage breakdown bar chart<br>• Case status donut distribution<br>• SLA response time monitoring (zero PII) |

---

## 🚀 Quick Start Guide

### Prerequisites
- **Node.js** (v20 or higher recommended)
- **Bun** (recommended for fastest install) or **npm**

### 1. Clone the Repository
```bash
git clone https://github.com/Shanxoxo-glitch/sahayak-the-app.git
cd sahayak-the-app
```

### 2. Install Dependencies
Using **Bun** (recommended):
```bash
bun install
```
*Or using npm:*
```bash
npm install
```

### 3. Start the Development Server
```bash
bun run dev
# or: npm run dev
```

The application will be running at:
👉 **[http://localhost:8080/](http://localhost:8080/)** *(or the next available port shown in your terminal, e.g. `8081`)*

### 4. Build for Production
To test production compilation:
```bash
bun run build
# or: npm run build
```

Preview production build:
```bash
bun run preview
# or: npm run preview
```

---

## 🗺️ Application Routes & Demo Links

Once the server is running, navigate directly to any of the following views or use the floating **"Explore Roles"** switcher in the bottom-right corner:

### Victim Sanctuary
- `/` — **Landing Page**: Brand story, hero hands with clay border, and India crisis bar.
- `/checkin` — **Daily Check-in**: One question per screen (Mood arc, Sleep, Feelings chips, Reflection) ending with a full-screen breathing circle.
- `/history` — **Garden of Days**: Check-ins visualised as an organic blooming garden alongside calendar dots.
- `/chat` — **Sanctuary Crisis Chat**: Full-screen chat with the living breathing orb, 5-4-3-2-1 grounding anchor drawer, and immediate danger keyword detection.
- `/request` — **Confidential Help Request**: Letter intake with plain-language consent toggles and an animated wax-seal codeword moment.
- `/status` — **Case Status**: Confidential case milestone lookup using the secret codeword.
- `/help` — **India Helplines**: 24/7 directory for Tele-MANAS (14416), KIRAN (1800-599-0019), Vandrevala, AASRA, Childline (1098), and Emergency (112).

### Counsellor Field Office
- `/counsellor` — **Case Records**: Tactile paper-file dossiers, timeline distress chart, status ribbon, and field clinical notebook.
- `/counsellor/alerts` — **Triage Alert Queue**: Real-time alerts with risk badges, composite scores, and "Approve Escalation" / "De-escalate" human-in-the-loop decisions.
- `/counsellor/trace/thread-8492` — **AI Decision Trace**: Explainable AI audit showing decision route, reasoning breakdown, and fusion confidence bar.

### Admin & Demo Hub
- `/admin` — **Admin Observatory**: Privacy-preserving aggregated wellbeing trends and district caseload charts.
- `/portal` — **Role Portal**: Multi-role demo hub explaining how the three perspectives interact.

---

## 🛡️ Safety-Critical Features

- **Quick Exit (<kbd>Esc</kbd>)**: A prominent button on all victim pages and a global <kbd>Esc</kbd> hotkey that instantly wipes local session storage, cookies, and redirects to an innocent Google Weather search.
- **Strict Anonymity**: No accounts, passwords, or government IDs required for victims. Every request is identified solely by a pseudonymous, evocative codeword (e.g. `quiet-river-17`).
- **No Client Scores**: Victims never see clinical distress numbers or triage algorithms; they only see warm, reassuring language.

---

## 🛠️ Architecture & Tech Stack

- **Framework**: TanStack Start + TanStack Router (file-based routing)
- **UI & Styling**: React 19, Tailwind CSS v4, Radix UI Primitives, Lucide Icons
- **Typography**: Instrument Serif (display headings) & Work Sans (clean body)
- **Charts**: Recharts (Timeline overlay, Community wellbeing area chart, District caseload bar chart)
- **State & Storage**: Client data layer (`src/lib/store.ts`) backed by `localStorage` with pre-seeded demo records
- **API Seam**: Shared API client (`src/lib/api.ts`) supporting live SSE streaming or local offline simulation engine
- **PWA**: Web App Manifest (`public/manifest.json`) and Service Worker (`public/sw.js`) for offline capabilities

---

## 📄 License

Built with care for hackathon presentation and community wellbeing.

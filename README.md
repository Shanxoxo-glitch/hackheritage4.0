# PS26094 Unified Monorepo — AI Distress & Legal Monitoring Engine

**SIH 2026 Problem Statement 26094**: AI-Powered Dynamic Mental Health Monitoring & Distress Prediction System under the SC/ST Prevention of Atrocities (PoA) Act.

## Architecture & Service Map

| Service | Owner | Port | Description |
| :--- | :--- | :--- | :--- |
| **services/backend/** | Shaan | :8400 | System of record, ER Schema, Escalation Ladder (Tier 0–4), Telephony Gateway |
| **services/orchestrator/** | Avik | :8000 | LangGraph agentic decision workflow engine |
| **services/scoring/** | Sohon | :8100 | Perception signal extraction (Sentiment, Threat, Voice features) |
| **services/risk-engine/** | Soham | :8200 | Evidential risk fusion & time-series trajectory forecasting |
| **services/web/** | Soham | :80 | Victim PWA + Counsellor Triage Dashboard |

## Quick Start

```bash
git clone https://github.com/Shanxoxo-glitch/hackheritage4.0.git
cd hackheritage4.0
make up
```

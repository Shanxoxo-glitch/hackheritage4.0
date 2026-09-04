# Frozen API Contracts Specification

| Path | Method | Source | Target | Description |
| :--- | :--- | :--- | :--- | :--- |
| /v1/signals/text | POST | Web / IVRS | Scoring | Extract sentiment & threat score from text |
| /v1/fusion | POST | Orchestrator | Risk Engine | Evidential signal fusion -> composite distress score |
| /v1/case/{id}/context | GET | Orchestrator | Backend | Fetch victim case context & legal stage |
| /v1/alerts | POST | Risk Engine | Backend | Append tamper-evident hash-chained alert |

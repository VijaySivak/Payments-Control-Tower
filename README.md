# AI Payments Control Tower

A full-stack cross-border payments operations intelligence platform built with Next.js 14 + FastAPI. Features a deterministic AI reasoning stack with explainable RCA, recommendations, repair playbooks, agent orchestration, and control tower intelligence — all served through a real-time operations console.

## Project Structure

```
Payments Control Tower/
├── backend/          # FastAPI Python backend
│   ├── app/
│   │   ├── ai/               # Phase 3 AI engine modules
│   │   │   ├── rca_engine.py            # Root cause analysis (deterministic)
│   │   │   ├── recommendation_engine.py # Action recommendation generator
│   │   │   ├── repair_actions.py        # Repair playbook catalog & recommender
│   │   │   ├── guardrail_engine.py      # Policy / safety guardrail layer
│   │   │   ├── agent_orchestrator.py    # Multi-agent pipeline orchestrator
│   │   │   └── control_tower_ai.py      # System-level AI views
│   │   ├── api/
│   │   │   ├── payments_v2.py           # Payments + simulation + replay routes
│   │   │   ├── control_tower_v2.py      # Control tower metric routes
│   │   │   └── ai_v3.py                 # Phase 3 AI routes
│   │   ├── domain/       # Enums + domain models
│   │   ├── repositories/ # In-memory data store
│   │   ├── schemas/      # Pydantic schemas (payments + ai_schemas)
│   │   ├── seed/         # Seed data generator
│   │   ├── services/     # Business logic (metrics, journey, simulation)
│   │   ├── utils/        # Geo utilities
│   │   └── main.py       # FastAPI app entrypoint (v3.0)
│   ├── requirements.txt
│   └── venv/
│
└── frontend/         # Next.js 14 App Router frontend
    ├── src/
    │   ├── app/
    │   │   ├── page.tsx                  # Dashboard + AI operator brief
    │   │   ├── payments/page.tsx         # Payments list
    │   │   ├── payments/[id]/page.tsx    # Payment detail + AI package
    │   │   ├── anomalies/page.tsx        # Anomaly registry + AI triage banner
    │   │   ├── ai-insights/page.tsx      # AI Operations Console (Phase 3)
    │   │   └── replay/page.tsx           # Simulation + AI scenario analysis
    │   ├── components/
    │   │   ├── ai/       # Phase 3 AI UI components
    │   │   │   ├── AISummaryBanner.tsx
    │   │   │   ├── RCASummaryCard.tsx
    │   │   │   ├── RecommendationList.tsx
    │   │   │   ├── RepairActionTable.tsx
    │   │   │   ├── AgentTracePanel.tsx
    │   │   │   └── ConfidenceBadge.tsx
    │   │   ├── map/      # SVG world map + route/node/tooltip layers
    │   │   └── shared/   # Badge, MetricCard, Panel, SectionHeader, etc.
    │   ├── hooks/        # useApi, usePoll
    │   ├── lib/
    │   │   ├── api/      # Typed fetch client (paymentsApi, controlTowerApi, aiApi)
    │   │   ├── constants/ # Color/style maps keyed by domain enums
    │   │   ├── formatters/ # Currency, date, label formatters
    │   │   └── types/    # Full TypeScript domain types (Phase 1–3)
    └── package.json
```

## Quick Start

### Prerequisites
- **Node.js ≥ 18.17** (use `nvm use 20` if needed)
- **Python ≥ 3.11**

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend runs at **http://localhost:8000**  
Interactive API docs: **http://localhost:8000/docs**

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:3000**

> If you get a Node version error, run: `nvm use 20 && npm run dev`

## Pages

| Route | Description |
|-------|-------------|
| `/` | Control Tower dashboard — KPIs, AI operator brief, priority queue, live map, charts |
| `/payments` | Paginated payments table with filters |
| `/payments/[id]` | Payment detail — journey, timeline, logs, anomalies, **AI package** (RCA + recommendations + repair actions + agent trace) |
| `/anomalies` | Anomaly registry with severity/type filters, charts, **AI triage intelligence banner** |
| `/ai-insights` | **AI Operations Console** — operator summary, priority queue, system insights, corridor risk, node watchlist, delay hotspots |
| `/replay` | Simulate new payments or replay existing scenarios with **AI scenario analysis** |

## API Endpoints

### Payments & Simulation
| Method | Path | Description |
|--------|------|-------------|
| GET | `/payments` | List payments with filters & pagination |
| GET | `/payments/{id}` | Payment detail |
| GET | `/payments/{id}/journey` | Route nodes |
| GET | `/payments/{id}/timeline` | Event timeline |
| GET | `/payments/{id}/logs` | System logs |
| GET | `/payments/{id}/anomalies` | Payment anomalies |
| GET | `/payments/{id}/observability` | Observability package |
| POST | `/payments/simulate` | Simulate a new payment |
| POST | `/payments/simulate/advanced` | Advanced simulation with scenario injection |
| POST | `/payments/{id}/replay` | Basic replay |
| POST | `/payments/{id}/replay/advanced` | Replay with before/after comparison |

### Control Tower
| Method | Path | Description |
|--------|------|-------------|
| GET | `/control-tower/overview` | KPI overview |
| GET | `/control-tower/health` | System health |
| GET | `/control-tower/live` | Active payments feed |
| GET | `/control-tower/anomalies` | Anomaly list with filters |
| GET | `/control-tower/map-flows` | Map flow data |
| GET | `/control-tower/corridors` | Corridor stats |
| GET | `/control-tower/countries` | Country stats |
| GET | `/control-tower/stage-metrics` | Stage pipeline health |
| GET | `/control-tower/node-health` | Intermediary node health |
| GET | `/control-tower/delay-hotspots` | Delay hotspot analysis |
| GET | `/control-tower/exception-patterns` | Exception pattern analysis |

### AI Intelligence (Phase 3)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/payments/{id}/ai-package` | Full AI package — RCA + recommendations + repair actions + summary + agent trace |
| GET | `/payments/{id}/rca` | Root cause analysis |
| GET | `/payments/{id}/recommendations` | Action recommendations |
| GET | `/payments/{id}/repair-actions` | Repair playbooks |
| GET | `/payments/{id}/agent-trace` | Agent execution trace |
| GET | `/payments/{id}/ai-summary` | Operator-readable AI summary |
| GET | `/anomalies/{id}/rca` | Anomaly-level RCA |
| GET | `/anomalies/{id}/recommendations` | Anomaly-level recommendations |
| GET | `/ai/operator-summary` | System-wide operator brief |
| GET | `/ai/priority-queue` | Ranked payments needing attention |
| GET | `/ai/system-anomaly-insights` | AI-grouped system anomaly patterns |
| GET | `/ai/corridor-risk-insights` | Corridor risk rankings |
| GET | `/ai/node-risk-watchlist` | At-risk intermediary nodes |

## AI Architecture (Phase 3)

The AI layer is **deterministic and rule-based by default** — every output is explainable with reasoning steps and confidence scores. It is designed to be LLM-augmentable in future.

```
AgentOrchestrator
 ├── IntakeAgent        — validates payment, loads context
 ├── ContextAgent       — enriches with anomalies, SLA, node data
 ├── RCAAgent           — runs RCAEngine, builds reasoning chain
 ├── RecommendationAgent — generates prioritised action list
 ├── RepairAgent        — matches repair playbooks
 ├── GuardrailAgent     — applies policy / safety checks
 └── SummaryAgent       — produces operator-readable summary
```

Each agent output is captured in an `AgentTrace` with per-agent duration, findings, and policy decisions — surfaced in the frontend `AgentTracePanel`.

## Tech Stack

**Frontend:** Next.js 14 (App Router) · TypeScript · Tailwind CSS · Recharts · Lucide React · clsx  
**Backend:** FastAPI 0.110 · Pydantic v2 · Uvicorn · In-memory repository · Python 3.11+

## Phase Roadmap

- ✅ **Phase 1** — Full frontend shell, backend data layer, simulation engine, SVG world map
- ✅ **Phase 2** — Advanced simulation, replay comparison, observability, stage/node/corridor analytics
- ✅ **Phase 3** — AI reasoning stack (RCA, recommendations, repair actions, agent orchestration), AI Operations Console, per-payment AI package, dashboard AI brief

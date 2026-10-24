# RevenueOS — GTM Operations Workspace

A portfolio project exploring the work of a RevTech & Operations Engineer: CRM integration, account intelligence, data reconciliation, workflow design, and data governance.

> **Demo status:** uses synthetic account data and a local SQLite database. It does not connect to a live Salesforce org, a real LLM, n8n, Clay, or a billing system. The current note extraction endpoint is rule-based and explicitly labels itself as a demo. A real LLM adapter is a planned next milestone.

## What it demonstrates

- A browser-based internal-tool UI for account review and operational workflows.
- A FastAPI backend with typed request validation and JSON endpoints.
- Salesforce-inspired account data and warehouse reconciliation (owner and ARR mismatches).
- Review status updates persisted in SQLite.
- A note-extraction endpoint with a clear boundary between the current deterministic demo and a future LLM integration.
- CSV export, issue review, workflow catalogue, integration map, and governance definitions.
- Basic automated tests for health, account data, reconciliation, extraction, and input validation.

## Run locally

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate       # Windows PowerShell
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. Interactive API documentation is at http://127.0.0.1:8000/docs.

## Run tests

```bash
pytest -q
```

## Architecture

```text
Browser UI (HTML/CSS/JavaScript)
            |
            v
      FastAPI backend
       /     |      \
 accounts  reconcile  extract
    |          |        |
    v          v        v
 SQLite    CRM-vs-WH   Rule-based demo
           comparison  (LLM adapter planned)
```

## Data and safety choices

- All names, account IDs, ARR values, notes, and mismatches are synthetic.
- No credentials or customer data belong in this repository.
- No live CRM writes are implemented.
- AI output should be validated and presented for human review before consequential actions.
- Production use would require authentication/authorization, audit logging, secrets management, rate limiting, monitoring, robust database migrations, and security review.

## Roadmap

1. **MVP (current):** internal-tool UI, API, synthetic records, reconciliation, review status, tests.
2. **LLM extraction:** provider adapter, structured output schema, retries/timeouts, evaluation examples, and human review.
3. **CRM integration:** read-only Salesforce sandbox connector using environment-based secrets and incremental sync.
4. **Workflow orchestration:** n8n webhook or a small event-driven job, idempotency, failure handling, and audit trail.
5. **Product quality:** user feedback, accessibility, observability, CI on GitHub Actions, deployment, and measured workflow outcomes.

## Honest portfolio positioning

Describe this as a **personal RevTech prototype**. Do not claim it is connected to Mentimeter or that the demo currently calls an LLM or Salesforce. Explain the design decisions, tests, known limitations, and next steps.

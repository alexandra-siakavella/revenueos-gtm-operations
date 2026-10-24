from __future__ import annotations

import re
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "revenueos.db"
STATIC_PATH = ROOT / "static"

app = FastAPI(
    title="RevenueOS",
    description="A portfolio demo for CRM intelligence, data reconciliation, and GTM operations.",
    version="0.1.0",
)
app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")

DEMO_ACCOUNTS = [
    {"account_id": "ACC-1001", "name": "Northstar Analytics", "owner": "Maya Chen", "crm_owner": "Maya Chen", "warehouse_owner": "Maya Chen", "arr": 96000, "warehouse_arr": 96000, "stage": "Negotiation", "last_activity": "2026-10-23", "notes": "Champion confirmed budget review. Legal review is expected next week. Renewal risk appears low."},
    {"account_id": "ACC-1002", "name": "Brightpath Health", "owner": "Jon Bell", "crm_owner": "Jon Bell", "warehouse_owner": "Ava Patel", "arr": 72000, "warehouse_arr": 72000, "stage": "Evaluation", "last_activity": "2026-10-22", "notes": "The operations lead asked for security documentation. Next meeting should include the security team."},
    {"account_id": "ACC-1003", "name": "Orbit Commerce", "owner": "Ava Patel", "crm_owner": "Ava Patel", "warehouse_owner": "Ava Patel", "arr": 125000, "warehouse_arr": 110000, "stage": "Contracting", "last_activity": "2026-10-21", "notes": "Commercial terms updated. The latest proposal is 125000 ARR, pending final approval."},
    {"account_id": "ACC-1004", "name": "Juniper Systems", "owner": "Maya Chen", "crm_owner": "Maya Chen", "warehouse_owner": "Maya Chen", "arr": 48000, "warehouse_arr": 48000, "stage": "Discovery", "last_activity": "2026-10-20", "notes": "Discovery completed. The team will share requirements after their internal planning meeting."},
    {"account_id": "ACC-1005", "name": "Redwood Labs", "owner": "Jon Bell", "crm_owner": "Jon Bell", "warehouse_owner": "Jon Bell", "arr": 84000, "warehouse_arr": 84000, "stage": "Renewal", "last_activity": "2026-10-18", "notes": "Customer mentioned a possible reduction in seats. Account owner should confirm expected renewal value."},
]


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(connect()) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS accounts (
            account_id TEXT PRIMARY KEY, name TEXT NOT NULL, owner TEXT NOT NULL,
            crm_owner TEXT NOT NULL, warehouse_owner TEXT NOT NULL,
            arr INTEGER NOT NULL, warehouse_arr INTEGER NOT NULL, stage TEXT NOT NULL,
            last_activity TEXT NOT NULL, notes TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Open'
        )""")
        count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO accounts (account_id,name,owner,crm_owner,warehouse_owner,arr,warehouse_arr,stage,last_activity,notes) VALUES (:account_id,:name,:owner,:crm_owner,:warehouse_owner,:arr,:warehouse_arr,:stage,:last_activity,:notes)",
                DEMO_ACCOUNTS,
            )
        conn.commit()


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(STATIC_PATH / "index.html")


def account_dict(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["arr_variance"] = item["arr"] - item["warehouse_arr"]
    item["owner_mismatch"] = item["crm_owner"] != item["warehouse_owner"]
    item["has_issue"] = item["owner_mismatch"] or item["arr_variance"] != 0
    return item


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "synthetic-demo", "database": "sqlite"}


@app.get("/api/accounts")
def list_accounts() -> dict[str, Any]:
    with closing(connect()) as conn:
        rows = conn.execute("SELECT * FROM accounts ORDER BY account_id").fetchall()
    accounts = [account_dict(row) for row in rows]
    return {"accounts": accounts, "count": len(accounts)}


@app.get("/api/summary")
def summary() -> dict[str, Any]:
    with closing(connect()) as conn:
        rows = conn.execute("SELECT * FROM accounts").fetchall()
    accounts = [account_dict(row) for row in rows]
    return {
        "account_count": len(accounts),
        "total_arr": sum(a["arr"] for a in accounts),
        "open_issues": sum(a["has_issue"] and a["status"] != "Resolved" for a in accounts),
        "owner_mismatches": sum(a["owner_mismatch"] for a in accounts),
        "arr_mismatches": sum(a["arr_variance"] != 0 for a in accounts),
    }


class ResolveRequest(BaseModel):
    status: str = Field(pattern="^(Open|In review|Resolved)$")


@app.patch("/api/accounts/{account_id}/status")
def update_status(account_id: str, body: ResolveRequest) -> dict[str, str]:
    with closing(connect()) as conn:
        cur = conn.execute("UPDATE accounts SET status=? WHERE account_id=?", (body.status, account_id))
        conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"account_id": account_id, "status": body.status}


class ExtractRequest(BaseModel):
    notes: str = Field(min_length=1, max_length=10000)


@app.post("/api/extract")
def extract_note(req: ExtractRequest) -> dict[str, Any]:
    """Deterministic demo extraction; a real LLM provider will be added in a later step."""
    text = req.notes.strip()
    amount = re.search(r"(?:ARR|annual recurring revenue|proposal(?: is| of)?)[^0-9$€£]{0,20}[$€£]?\s*([0-9][0-9,]*)", text, re.I)
    owner = re.search(r"(?:owner|owned by|assigned to)\s+(?:is\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text, re.I)
    stage = next((s for s in ["Discovery", "Evaluation", "Negotiation", "Contracting", "Renewal"] if s.lower() in text.lower()), None)
    return {
        "extracted": {
            "arr": int(amount.group(1).replace(",", "")) if amount else None,
            "owner": owner.group(1) if owner else None,
            "stage": stage,
        },
        "source_text": text,
        "method": "rule-based-demo",
        "notice": "Demo extraction only—not an LLM call. Values must be reviewed before use.",
    }


@app.get("/api/reconcile")
def reconcile() -> dict[str, Any]:
    with closing(connect()) as conn:
        rows = conn.execute("SELECT * FROM accounts ORDER BY account_id").fetchall()
    issues = []
    for row in rows:
        a = account_dict(row)
        if a["owner_mismatch"]:
            issues.append({"account_id": a["account_id"], "account": a["name"], "field": "Owner", "crm_value": a["crm_owner"], "warehouse_value": a["warehouse_owner"], "severity": "High", "status": a["status"]})
        if a["arr_variance"]:
            issues.append({"account_id": a["account_id"], "account": a["name"], "field": "ARR", "crm_value": a["arr"], "warehouse_value": a["warehouse_arr"], "severity": "High", "status": a["status"]})
    return {"issues": issues, "count": len(issues)}

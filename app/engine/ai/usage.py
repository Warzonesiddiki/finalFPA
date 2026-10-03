import sqlite3
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from app.engine.store.db import DatabaseManager

class AIUsageStore:
    """Manages AI usage logging, estimated cost, and monthly token cap enforcement per doc 10 §8 & §9."""

    def __init__(self, db_mgr: Optional[DatabaseManager] = None):
        self.db_mgr = db_mgr or DatabaseManager()
        self._ensure_table()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_mgr.sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS AiUsageLog (
                    call_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,
                    prompt_version TEXT NOT NULL,
                    model TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    input_row_count INTEGER NOT NULL DEFAULT 0,
                    tokens_in INTEGER NOT NULL DEFAULT 0,
                    tokens_out INTEGER NOT NULL DEFAULT 0,
                    estimated_cost_usd REAL NOT NULL DEFAULT 0.0,
                    outcome TEXT NOT NULL DEFAULT 'ok'
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS AiSettings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )
            conn.commit()

    def log_call(
        self,
        prompt_id: str,
        prompt_version: str,
        model: str,
        provider: str,
        input_row_count: int,
        tokens_in: int,
        tokens_out: int,
        outcome: str = "ok"
    ) -> Dict[str, Any]:
        """Record an AI call telemetry and estimate cost (USD) per doc 10 §8."""
        call_id = f"aicall_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.utcnow().isoformat()

        # Cost estimation formula: e.g. $5.00 per 1M input tokens, $15.00 per 1M output tokens for GPT-4o
        cost_in = (tokens_in / 1_000_000.0) * 5.00
        cost_out = (tokens_out / 1_000_000.0) * 15.00
        estimated_cost_usd = round(cost_in + cost_out, 6)

        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO AiUsageLog (
                    call_id, timestamp, prompt_id, prompt_version, model, provider,
                    input_row_count, tokens_in, tokens_out, estimated_cost_usd, outcome
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    call_id, timestamp, prompt_id, prompt_version, model, provider,
                    input_row_count, tokens_in, tokens_out, estimated_cost_usd, outcome
                )
            )
            conn.commit()

        return {
            "callId": call_id,
            "timestamp": timestamp,
            "promptId": prompt_id,
            "promptVersion": prompt_version,
            "model": model,
            "provider": provider,
            "inputRowCount": input_row_count,
            "tokensIn": tokens_in,
            "tokensOut": tokens_out,
            "estimatedCostUsd": estimated_cost_usd,
            "outcome": outcome,
        }

    def get_monthly_token_cap(self) -> int:
        """Get configured hard monthly token cap (default 1,000,000) per doc 10 §9."""
        with self._get_conn() as conn:
            cur = conn.execute("SELECT value FROM AiSettings WHERE key = 'monthly_token_cap'")
            row = cur.fetchone()
            if row:
                try:
                    return int(row["value"])
                except ValueError:
                    pass
        return 1_000_000

    def set_monthly_token_cap(self, cap: int) -> int:
        """Set hard monthly token cap."""
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO AiSettings (key, value) VALUES ('monthly_token_cap', ?)",
                (str(cap),)
            )
            conn.commit()
        return cap

    def check_cap_exceeded(self, additional_tokens: int = 0) -> bool:
        """Check if cumulative monthly token usage exceeds hard cap per doc 10 §9."""
        cap = self.get_monthly_token_cap()
        stats = self.get_usage_stats()
        total_tokens = stats["totalTokens"] + additional_tokens
        return total_tokens > cap

    def get_usage_stats(self, period_month: Optional[str] = None) -> Dict[str, Any]:
        """Get aggregated usage stats, logs table, and cap utilization per doc 10 §8 & §10."""
        with self._get_conn() as conn:
            if period_month:
                cur = conn.execute(
                    "SELECT * FROM AiUsageLog WHERE timestamp LIKE ? ORDER BY timestamp DESC",
                    (f"{period_month}%",)
                )
            else:
                cur = conn.execute("SELECT * FROM AiUsageLog ORDER BY timestamp DESC")
            rows = [dict(r) for r in cur.fetchall()]

        total_calls = len(rows)
        tokens_in_sum = sum(r["tokens_in"] for r in rows)
        tokens_out_sum = sum(r["tokens_out"] for r in rows)
        total_tokens = tokens_in_sum + tokens_out_sum
        total_cost = sum(r["estimated_cost_usd"] for r in rows)
        monthly_cap = self.get_monthly_token_cap()
        cap_exceeded = total_tokens > monthly_cap
        utilization_pct = round((total_tokens / monthly_cap) * 100.0, 2) if monthly_cap > 0 else 0.0

        formatted_logs = [
            {
                "callId": r["call_id"],
                "timestamp": r["timestamp"],
                "promptId": r["prompt_id"],
                "promptVersion": r["prompt_version"],
                "model": r["model"],
                "provider": r["provider"],
                "inputRowCount": r["input_row_count"],
                "tokensIn": r["tokens_in"],
                "tokensOut": r["tokens_out"],
                "totalTokens": r["tokens_in"] + r["tokens_out"],
                "estimatedCostUsd": r["estimated_cost_usd"],
                "outcome": r["outcome"],
            }
            for r in rows
        ]

        return {
            "totalCalls": total_calls,
            "tokensIn": tokens_in_sum,
            "tokensOut": tokens_out_sum,
            "totalTokens": total_tokens,
            "totalEstimatedCostUsd": round(total_cost, 6),
            "monthlyTokenCap": monthly_cap,
            "capExceeded": cap_exceeded,
            "utilizationPct": utilization_pct,
            "logs": formatted_logs,
        }

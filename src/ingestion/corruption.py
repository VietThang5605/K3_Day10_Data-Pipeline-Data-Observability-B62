from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from core.utils import now_utc, write_json

from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: Path | str) -> pd.DataFrame:
    """Tự động làm hỏng dữ liệu sạch một cách có kiểm soát để phục vụ thí nghiệm Observability & Recovery."""
    if df.empty:
        raise ValueError("Cannot corrupt an empty DataFrame.")

    corrupted_df = df.copy()
    corruption_logs: list[dict[str, Any]] = []

    # --- Scenario 1: Blank Summary (Targeting paper 10.1111/exsy.70341 for Question q1) ---
    target_q1_mask = corrupted_df["paper_id"].str.lower() == "10.1111/exsy.70341"
    if target_q1_mask.any():
        corrupted_df.loc[target_q1_mask, "summary"] = ""
        corrupted_df.loc[target_q1_mask, "summary_chars"] = 0
        corruption_logs.append(
            {
                "scenario": "Blank Summary Injection",
                "paper_id": "10.1111/exsy.70341",
                "action": "Cleared all summary and embedding text for Hi-RAG paper.",
                "affected_questions": ["Question q1 (Hi-RAG MCPBench Question)"],
                "impact_reason": "When summary is erased, vector embedding loses context about 201 tools and 40 services. RAG Agent fails to extract facts and LLM Judge rates as FAILED.",
            }
        )

    # --- Scenario 2: Add Noise / Poison Content (Targeting paper 10.21203/rs.3.rs-10178277/v1 for q2 and 10.1007/s10278-026-02086-9 for q7) ---
    target_noise_map = [
        (
            "10.21203/rs.3.rs-10178277/v1",
            "Question q2 (CM-RAF-Lag-Llama MSE Question)",
            "Replaced summary with ancient agricultural and culinary noise for CM-RAF-Lag-Llama paper.",
            "Vector embedding undergoes severe semantic drift toward agriculture/cooking. ChromaDB retrieves irrelevant papers, causing 100% incorrect RAG answer on 28.85% MSE reduction.",
        ),
        (
            "10.1007/s10278-026-02086-9",
            "Question q7 & q9 (JADE-Plus Medical AI Question)",
            "Replaced medical summary with culinary noise for JADE-Plus paper.",
            "Medical AI vector embedding is completely corrupted. RAG Agent cannot retrieve medical knowledge, leading to factual hallucinations.",
        ),
    ]
    for pid, q_info, act, reason in target_noise_map:
        mask = corrupted_df["paper_id"].str.lower() == pid.lower()
        if mask.any():
            corrupted_df.loc[mask, "summary"] = (
                "Poisoned content: This paper discusses ancient agricultural techniques and traditional culinary recipes instead of retrieval-augmented generation or AI."
            )
            corrupted_df.loc[mask, "summary_chars"] = len(corrupted_df.loc[mask, "summary"].values[0])
            corruption_logs.append(
                {
                    "scenario": "Add Noise / Semantic Poisoning",
                    "paper_id": pid,
                    "action": act,
                    "affected_questions": [q_info],
                    "impact_reason": reason,
                }
            )

    # --- Scenario 3: Stale Published Date (Setting published date to year 2000 for 5 records) ---
    stale_indices = corrupted_df.index[:5]
    corrupted_df.loc[stale_indices, "published"] = "2000-01-01"
    corrupted_df.loc[stale_indices, "age_days"] = 9500

    for idx in stale_indices:
        pid = str(corrupted_df.loc[idx, "paper_id"])
        title = str(corrupted_df.loc[idx, "title"])
        corruption_logs.append(
            {
                "scenario": "Stale Published Date Injection",
                "paper_id": pid,
                "action": f"Backdated publication date for paper '{title[:40]}...' to 2000-01-01 (age > 9500 days).",
                "affected_questions": ["Observability Freshness Signal"],
                "impact_reason": "Setting published date to year 2000 forces age_days beyond 180-day threshold. Observability monitor automatically triggers STALE DATA 🔴 status.",
            }
        )

    # --- Scenario 4: Duplicates & Missing Paper ID (Duplicate first 2 rows and set one paper_id to blank) ---
    duplicate_rows = corrupted_df.iloc[:2].copy()
    duplicate_rows.iloc[0, duplicate_rows.columns.get_loc("paper_id")] = ""
    corruption_logs.append(
        {
            "scenario": "Duplicates & Missing Paper ID",
            "paper_id": "Blank / Duplicated Record",
            "action": "Duplicated 2 rows and erased paper_id for one record.",
            "affected_questions": ["Observability Completeness & Uniqueness Signals"],
            "impact_reason": "Violates Data Contract. Uniqueness check reports FAILED 🔴 due to duplicate rows and Completeness check reports FAILED 🔴 due to missing primary key.",
        }
    )
    corrupted_df = pd.concat([corrupted_df, duplicate_rows], ignore_index=True)

    # --- Rebuild text_for_embedding for all rows ---
    def _rebuild_embedding_text(row: pd.Series) -> str:
        parts = []
        if row["title"]:
            parts.append(f"Title: {row['title']}")
        if row["summary"]:
            parts.append(f"Summary: {row['summary']}")
        if row["authors_joined"]:
            parts.append(f"Authors: {row['authors_joined']}")
        if row["categories_joined"]:
            parts.append(f"Categories: {row['categories_joined']}")
        if row["published"]:
            parts.append(f"Published: {row['published']}")
        return "\n".join(parts)

    corrupted_df["text_for_embedding"] = corrupted_df.apply(_rebuild_embedding_text, axis=1)

    # Write log file
    target_log_path = Path(output_log_path)
    target_log_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(target_log_path, corruption_logs)

    return corrupted_df


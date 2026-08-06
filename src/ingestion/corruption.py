from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

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
                "scenario": "blank_summary",
                "paper_id": "10.1111/exsy.70341",
                "action": "Cleared summary content to test retrieval failure on question q1.",
            }
        )

    # --- Scenario 2: Add Noise / Poison Content (Targeting paper 10.21203/rs.3.rs-10178277/v1 for q2 and 10.1007/s10278-026-02086-9 for q7) ---
    target_noise_ids = ["10.21203/rs.3.rs-10178277/v1", "10.1007/s10278-026-02086-9"]
    for pid in target_noise_ids:
        mask = corrupted_df["paper_id"].str.lower() == pid.lower()
        if mask.any():
            corrupted_df.loc[mask, "summary"] = (
                "Poisoned content: This paper discusses ancient agricultural techniques and traditional culinary recipes instead of retrieval-augmented generation or AI."
            )
            corrupted_df.loc[mask, "summary_chars"] = len(corrupted_df.loc[mask, "summary"].values[0])
            corruption_logs.append(
                {
                    "scenario": "add_noise",
                    "paper_id": pid,
                    "action": "Replaced summary with irrevelant culinary noise to disrupt semantic search on q2/q7.",
                }
            )

    # --- Scenario 3: Stale Published Date (Setting published date to year 2000 for 5 records) ---
    stale_indices = corrupted_df.index[:5]
    corrupted_df.loc[stale_indices, "published"] = "2000-01-01"
    corrupted_df.loc[stale_indices, "age_days"] = 9500
    for idx in stale_indices:
        pid = corrupted_df.loc[idx, "paper_id"]
        corruption_logs.append(
            {
                "scenario": "stale_date",
                "paper_id": pid,
                "action": "Set published date to 2000-01-01 to trigger Freshness Check failure.",
            }
        )

    # --- Scenario 4: Duplicates & Missing Paper ID (Duplicate first 2 rows and set one paper_id to blank) ---
    duplicate_rows = corrupted_df.iloc[:2].copy()
    duplicate_rows.iloc[0, duplicate_rows.columns.get_loc("paper_id")] = ""
    corruption_logs.append(
        {
            "scenario": "missing_and_duplicate_paper_id",
            "paper_id": "",
            "action": "Added duplicate rows and injected blank paper_id to trigger Uniqueness and Completeness failures.",
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


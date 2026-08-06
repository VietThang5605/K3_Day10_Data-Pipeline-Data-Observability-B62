from __future__ import annotations

import json
from pathlib import Path
import pandas as pd
from core.utils import now_utc, write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Simulate data corruption in a controlled way.

    Saves log to output_log_path.
    """
    df_corrupted = df.copy()

    # Identify papers queried in the test set to ensure overlap
    test_set_dois = {
        "10.1111/exsy.70341", "10.21203/rs.3.rs-10012178/v1", "10.32473/flairs.39.1.141782",
        "10.2118/234689-pa", "10.55041/isjem07213", "10.3390/buildings16132637",
        "10.1007/s10278-026-02086-9", "10.21203/rs.3.rs-9882260/v1", "10.20944/preprints202604.0339.v1",
        "10.21203/rs.3.rs-10178277/v1", "10.52060/juptik.v4i1.4318", "10.70121/001c.158711"
    }

    log_data = {
        "dropped_papers": [],
        "blank_summary_papers": [],
        "stale_date_papers": [],
        "noise_injected_papers": [],
        "duplicated_papers": [],
        "truncated_title_papers": []
    }

    # 1. Drop a few latest records (that are not in the test set)
    non_test_indices = df_corrupted[~df_corrupted["paper_id"].isin(test_set_dois)].index
    if len(non_test_indices) >= 3:
        drop_indices = non_test_indices[-3:]
        log_data["dropped_papers"] = df_corrupted.loc[drop_indices, "paper_id"].tolist()
        df_corrupted = df_corrupted.drop(drop_indices).reset_index(drop=True)

    # 2. Blank summary at some rows (including at least one test set doc: 10.1111/exsy.70341)
    blank_targets = ["10.1111/exsy.70341"]
    # Add another non-test paper if possible
    other_papers = df_corrupted[~df_corrupted["paper_id"].isin(test_set_dois)]["paper_id"].tolist()
    if other_papers:
        blank_targets.append(other_papers[0])

    for paper_id in blank_targets:
        mask = df_corrupted["paper_id"] == paper_id
        if mask.any():
            df_corrupted.loc[mask, "summary"] = ""
            df_corrupted.loc[mask, "summary_chars"] = 0
            log_data["blank_summary_papers"].append(paper_id)

    # 3. Inject noise into summary and title (including test set doc: 10.2118/234689-pa)
    noise_targets = ["10.2118/234689-pa"]
    if len(other_papers) > 1:
        noise_targets.append(other_papers[1])

    for paper_id in noise_targets:
        mask = df_corrupted["paper_id"] == paper_id
        if mask.any():
            orig_title = df_corrupted.loc[mask, "title"].values[0]
            orig_summary = df_corrupted.loc[mask, "summary"].values[0]
            df_corrupted.loc[mask, "title"] = f"NOISE_ERROR_Gibberish {orig_title}"
            df_corrupted.loc[mask, "summary"] = f"NOISE_ERROR_Gibberish_1234567890 {orig_summary}"
            log_data["noise_injected_papers"].append(paper_id)

    # 4. Truncate some titles
    truncate_targets = []
    if len(other_papers) > 2:
        truncate_targets = other_papers[2:4]
    for paper_id in truncate_targets:
        mask = df_corrupted["paper_id"] == paper_id
        if mask.any():
            orig_title = df_corrupted.loc[mask, "title"].values[0]
            df_corrupted.loc[mask, "title"] = orig_title[:10]
            log_data["truncated_title_papers"].append(paper_id)

    # 5. Make published date stale (including test set doc: 10.1007/s10278-026-02086-9)
    stale_targets = ["10.1007/s10278-026-02086-9"]
    if len(other_papers) > 4:
        stale_targets.append(other_papers[4])

    run_day = pd.Timestamp(now_utc()).tz_convert("UTC").normalize()
    stale_date = pd.Timestamp("2000-01-01", tz="UTC").normalize()
    stale_age_days = int((run_day - stale_date).days)

    for paper_id in stale_targets:
        mask = df_corrupted["paper_id"] == paper_id
        if mask.any():
            df_corrupted.loc[mask, "published"] = "2000-01-01"
            df_corrupted.loc[mask, "age_days"] = stale_age_days
            log_data["stale_date_papers"].append(paper_id)

    # 6. Add duplicate rows (keeping same paper_id)
    if not df_corrupted.empty:
        # Duplicate the first paper in the dataframe
        dup_row = df_corrupted.iloc[[0]].copy()
        df_corrupted = pd.concat([df_corrupted, dup_row], ignore_index=True)
        log_data["duplicated_papers"].append(dup_row["paper_id"].values[0])

    # 7. Rebuild text_for_embedding for all rows using updated fields
    def _build_embedding_text(row):
        parts = [
            f"Title: {row['title']}",
            f"Summary: {row['summary']}",
        ]
        if "authors_joined" in row and row["authors_joined"]:
            parts.append(f"Authors: {row['authors_joined']}")
        if "categories_joined" in row and row["categories_joined"]:
            parts.append(f"Categories: {row['categories_joined']}")
        if "published" in row and row["published"]:
            parts.append(f"Published: {row['published']}")
        return "\n".join(parts)

    df_corrupted["text_for_embedding"] = df_corrupted.apply(_build_embedding_text, axis=1)

    # 8. Write corruption log to output_log_path
    write_json(Path(output_log_path), log_data)

    return df_corrupted


from __future__ import annotations

from datetime import datetime
import html
import re

import pandas as pd

from ingestion.crossref import PaperRecord


def _normalize_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalize_items(values: list[str] | None) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        item = _normalize_text(value)
        key = item.casefold()
        if item and key not in seen:
            cleaned.append(item)
            seen.add(key)
    return cleaned


def _infer_categories(title: str, summary: str) -> list[str]:
    title_text = title.casefold()
    summary_text = summary.casefold()
    rules = [
        ("Healthcare AI", ["clinical", "medical", "diagnostic", "healthcare", "patient", "jawbone"]),
        ("Knowledge Graphs", ["knowledge graph", "graph neural network", "graph-based", "kgqa", "graphrag"]),
        ("Agentic AI", ["agentic", "agent-controlled", "autonomous agent", "multi-agent", "tool selection"]),
        ("Retrieval-Augmented Generation", ["retrieval-augmented", "rag", "retrieval augmented"]),
        ("Large Language Models", ["large language model", "llm", "language models"]),
        ("Governance", ["governance", "compliance", "risk", "regulated", "safety"]),
        ("Finance", ["financial", "finance", "equity", "market", "forecasting"]),
        ("Education", ["student", "education", "learning", "teaching"]),
    ]

    scored: list[tuple[int, int, str]] = []
    for index, (category, keywords) in enumerate(rules):
        title_hits = int(any(keyword in title_text for keyword in keywords))
        summary_hits = int(any(keyword in summary_text for keyword in keywords))
        score = title_hits * 3 + summary_hits
        if score:
            scored.append((-score, index, category))

    categories = [category for _, _, category in sorted(scored)]
    return categories or ["Uncategorized"]


def _parse_date(value: object) -> pd.Timestamp | pd.NaT:
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return pd.NaT
    return parsed.normalize()


def _format_date(value: pd.Timestamp | pd.NaT) -> str:
    if pd.isna(value):
        return ""
    return value.date().isoformat()


def _build_embedding_text(row: dict[str, object]) -> str:
    parts = [
        f"Title: {row['title']}",
        f"Summary: {row['summary']}",
    ]
    if row["authors_joined"]:
        parts.append(f"Authors: {row['authors_joined']}")
    if row["categories_joined"]:
        parts.append(f"Categories: {row['categories_joined']}")
    if row["published"]:
        parts.append(f"Published: {row['published']}")
    return "\n".join(parts)


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """TODO(student): clean raw records thanh dataframe san sang de embed.

    Pseudo-code:
    1. Normalize title, summary, authors, categories.
    2. Parse published/updated date.
    3. Tinh age_days.
    4. Tao cot helper:
       - authors_joined
       - categories_joined
       - summary_chars
       - text_for_embedding
    5. Drop duplicates va filter row xau.
    6. Sort dataframe va return.
    """
    run_timestamp = pd.Timestamp(run_date)
    if run_timestamp.tzinfo is None:
        run_timestamp = run_timestamp.tz_localize("UTC")
    else:
        run_timestamp = run_timestamp.tz_convert("UTC")
    run_day = run_timestamp.normalize()

    rows: list[dict[str, object]] = []
    filter_counts = {
        "missing_paper_id": 0,
        "missing_title": 0,
        "missing_summary": 0,
        "invalid_published": 0,
    }

    for record in records:
        paper_id = _normalize_text(record.paper_id).lower()
        title = _normalize_text(record.title)
        summary = _normalize_text(record.summary)
        published_date = _parse_date(record.published)

        if not paper_id:
            filter_counts["missing_paper_id"] += 1
            continue
        if not title:
            filter_counts["missing_title"] += 1
            continue
        if not summary:
            filter_counts["missing_summary"] += 1
            continue
        if pd.isna(published_date):
            filter_counts["invalid_published"] += 1
            continue

        authors = _normalize_items(record.authors)
        categories = _normalize_items(record.categories)
        if not categories:
            categories = _infer_categories(title, summary)
        primary_category = _normalize_text(record.primary_category)
        if not primary_category or primary_category == "unknown":
            primary_category = categories[0]
        updated_date = _parse_date(record.updated)
        authors_joined = ", ".join(authors)
        categories_joined = ", ".join(categories)

        row: dict[str, object] = {
            "paper_id": paper_id,
            "title": title,
            "summary": summary,
            "authors": authors,
            "categories": categories,
            "primary_category": primary_category,
            "published": _format_date(published_date),
            "updated": _format_date(updated_date),
            "abs_url": _normalize_text(record.abs_url),
            "pdf_url": _normalize_text(record.pdf_url),
            "comment": _normalize_text(record.comment),
            "age_days": int((run_day - published_date).days),
            "authors_joined": authors_joined,
            "categories_joined": categories_joined,
            "summary_chars": len(summary),
        }
        row["text_for_embedding"] = _build_embedding_text(row)
        rows.append(row)

    columns = [
        "paper_id",
        "title",
        "summary",
        "authors",
        "categories",
        "primary_category",
        "published",
        "updated",
        "age_days",
        "authors_joined",
        "categories_joined",
        "summary_chars",
        "text_for_embedding",
        "abs_url",
        "pdf_url",
        "comment",
    ]
    df = pd.DataFrame(rows, columns=columns)
    before_dedupe = len(df)
    if not df.empty:
        df = (
            df.sort_values(["published", "updated", "paper_id"], ascending=[False, False, True])
            .drop_duplicates(subset=["paper_id"], keep="first")
            .reset_index(drop=True)
        )

    df.attrs["cleaning_report"] = {
        "input_records": len(records),
        "kept_records": len(df),
        "dropped_duplicates": before_dedupe - len(df),
        "filtered": filter_counts,
    }
    return df

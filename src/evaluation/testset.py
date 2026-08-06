from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

_MIN_DOCS = 5


def _truncate(text: str, max_chars: int = 300) -> str:
    """Rút gọn text dài thành câu đầu tiên, tối đa max_chars ký tự."""
    text = text.strip()
    first_dot = text.find(". ")
    if 0 < first_dot <= max_chars:
        return text[: first_dot + 1].strip()
    return text[:max_chars].rstrip() + ("..." if len(text) > max_chars else "")


def build_test_set(df: pd.DataFrame, output_path: Path | str) -> list[dict[str, Any]]:
    """Build the Frozen Evaluation Test Set in English from the cleaned dataframe and save to JSON."""
    if df.empty:
        raise ValueError("DataFrame cleaned data is empty. Cannot build test set.")

    existing_paper_ids = set(df["paper_id"].str.lower().unique())

    # Golden Test Set of 10 English questions mapped directly to clean paper records
    samples: list[dict[str, Any]] = [
        # --- Group 1: factual (2 items) ---
        {
            "id": "q1",
            "question_type": "factual",
            "question": "In the Hi-RAG paper, how many tools and real-enterprise services are included in the MCPBench benchmark?",
            "ground_truth": "The MCPBench benchmark comprises 201 tools across 40 real-enterprise services.",
            "ground_truth_doc_ids": ["10.1111/exsy.70341"],
        },
        {
            "id": "q2",
            "question_type": "factual",
            "question": "In the evaluation on the IDX7 dataset panel, by what percentage does the retrieval component in CM-RAF-Lag-Llama reduce the MSE compared to Lag-Llama alone?",
            "ground_truth": "The retrieval variant reduces Lag-Llama MSE by 28.85% for the IDX7 panel.",
            "ground_truth_doc_ids": ["10.21203/rs.3.rs-10178277/v1"],
        },

        # --- Group 2: metadata (2 items) ---
        {
            "id": "q3",
            "question_type": "metadata",
            "question": "Who is the author of the study on adapting LLaMA-2-13B for insurance information delivery in Kenya?",
            "ground_truth": "The author of the study is AMOS MBEKI NYAGAR.",
            "ground_truth_doc_ids": ["10.21203/rs.3.rs-9770645/v1"],
        },
        {
            "id": "q4",
            "question_type": "metadata",
            "question": "Which authors conducted the bibliometric review of Agentic AI architectures from 2023 to 2025?",
            "ground_truth": "The bibliometric review was conducted by Ben J. Weber, Clara M. Hofmann, and Amara N. Okoye.",
            "ground_truth_doc_ids": ["10.63646/kpqm1958"],
        },

        # --- Group 3: summary (2 items) ---
        {
            "id": "q5",
            "question_type": "summary",
            "question": "According to the bibliometric review by Ben J. Weber et al., how did the annual output of publications on agentic AI change from 2023 to 2025?",
            "ground_truth": "Annual output rose sharply from 4 publications in 2023 to 96 in 2024 and reached 710 in 2025 (totaling 810 publications from the Web of Science Core Collection).",
            "ground_truth_doc_ids": ["10.63646/kpqm1958"],
        },
        {
            "id": "q6",
            "question_type": "summary",
            "question": "According to Haopeng Yang's review, at which stages of a RAG-enhanced LLM system can errors leading to hallucination arise?",
            "ground_truth": "Errors leading to hallucination may arise during query formulation, document retrieval, evidence aggregation, and answer grounding.",
            "ground_truth_doc_ids": ["10.54254/2753-8818/2026.dl34055"],
        },

        # --- Group 4: application (2 items) ---
        {
            "id": "q7",
            "question_type": "application",
            "question": "What is the primary medical application and objective of the JADE-Plus framework?",
            "ground_truth": "JADE-Plus is designed for diagnostic decision support in jawbone lesion assessment and automated structured reporting using multimodal agentic RAG and vision-language models.",
            "ground_truth_doc_ids": ["10.1007/s10278-026-02086-9"],
        },
        {
            "id": "q8",
            "question_type": "application",
            "question": "In which specific domain and tasks is the SafeRAG framework applied?",
            "ground_truth": "SafeRAG is applied in the petroleum geology domain for well log analysis and lithology identification.",
            "ground_truth_doc_ids": ["10.2118/234689-pa"],
        },

        # --- Group 5: comparative (2 items) ---
        {
            "id": "q9",
            "question_type": "comparative",
            "question": "What common objective do both JADE-Plus and SafeRAG share when applying RAG in specialized domains?",
            "ground_truth": "Both frameworks combine RAG with LLMs to mitigate decision risks and enhance diagnostic or analytical accuracy in high-stakes domain-specific applications (JADE-Plus for medical radiology and SafeRAG for petroleum geology).",
            "ground_truth_doc_ids": ["10.1007/s10278-026-02086-9", "10.2118/234689-pa"],
        },
        {
            "id": "q10",
            "question_type": "comparative",
            "question": "Compare the primary goals of RAG integration between AMOS MBEKI NYAGAR's study in Kenya and Sohail Khan's study on Knowledge Graphs.",
            "ground_truth": "AMOS MBEKI NYAGAR's study uses RAG to ground LLM outputs in regulatory insurance documents for financial inclusion in Kenya, whereas Sohail Khan's study integrates RAG with GNNs and Knowledge Graphs to enable robust multi-hop question answering.",
            "ground_truth_doc_ids": ["10.21203/rs.3.rs-9770645/v1", "10.22214/ijraset.2026.82233"],
        },
    ]

    # Validate that all referenced paper_ids exist in the clean dataset
    for sample in samples:
        for doc_id in sample["ground_truth_doc_ids"]:
            if doc_id.lower() not in existing_paper_ids:
                raise ValueError(
                    f"Sample {sample['id']} references paper_id '{doc_id}' which does not exist in clean data."
                )

    # Write output to JSON
    target_path = Path(output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)

    return samples


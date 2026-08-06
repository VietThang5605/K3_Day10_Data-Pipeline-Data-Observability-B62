from __future__ import annotations

from dataclasses import dataclass
import re

from core.config import Settings
from core.utils import first_sentence
from retrieval.index import LocalEmbeddingIndex, SearchResult
from retrieval.llm import build_llm


@dataclass(frozen=True)
class AnswerResult:
    question: str
    answer: str
    retrieved_doc_ids: list[str]
    retrieved_contexts: list[str]
    retrieved_titles: list[str]


def _extract_answer_heuristic(question: str, top_result: SearchResult) -> str:
    lowered = question.lower()
    metadata = top_result.metadata
    if "who authored" in lowered or "list the authors" in lowered:
        return metadata.get("authors_joined", "")
    if "when was" in lowered or "publication date" in lowered or "published on" in lowered:
        return metadata.get("published", "")
    if "what categories" in lowered:
        return metadata.get("categories_joined", "")
    return first_sentence(metadata.get("summary", ""))


def _generate_answer_with_llm(question: str, retrieved_results: list[SearchResult], settings: Settings) -> str:
    if not retrieved_results:
        return "I don't know from the indexed corpus."
    try:
        llm = build_llm(settings=settings, temperature=0.0)
        context_blocks = []
        for res in retrieved_results:
            context_blocks.append(f"Title: {res.title}\nContent: {res.content}")
        context_str = "\n\n---\n\n".join(context_blocks)

        prompt = f"""You are a precise research assistant answering questions about indexed scholarly papers.
Answer the user's question based strictly on the provided retrieved paper contexts. Be concise, direct, and factual. Do not extrapolate beyond the retrieved facts.

Retrieved Contexts:
{context_str}

Question: {question}

Answer:"""
        response = llm.invoke(prompt)
        return getattr(response, "content", str(response)).strip()
    except Exception:
        return _extract_answer_heuristic(question, retrieved_results[0])


def answer_question(question: str, settings: Settings, index: LocalEmbeddingIndex, top_k: int | None = None) -> AnswerResult:
    title_match = re.search(r"'([^']+)'", question)
    exact = index.lookup(title_match.group(1)) if title_match else None
    retrieved = index.search(question, top_k=top_k)
    if exact:
        exact_result = SearchResult(
            paper_id=exact["paper_id"],
            title=exact["title"],
            score=1.0,
            content=exact["content"],
            metadata=exact["metadata"],
        )
        deduped = [exact_result] + [item for item in retrieved if item.paper_id != exact_result.paper_id]
        retrieved = deduped[: (top_k or settings.top_k)]
    if not retrieved:
        answer = "I don't know from the indexed corpus."
    else:
        answer = _generate_answer_with_llm(question, retrieved, settings)
    return AnswerResult(
        question=question,
        answer=answer,
        retrieved_doc_ids=[item.paper_id for item in retrieved],
        retrieved_contexts=[item.content for item in retrieved],
        retrieved_titles=[item.title for item in retrieved],
    )


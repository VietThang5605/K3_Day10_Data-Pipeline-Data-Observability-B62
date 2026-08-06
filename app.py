from __future__ import annotations

import pandas as pd
import streamlit as st

from core.config import load_settings
from core.utils import read_json
from retrieval.index import LocalEmbeddingIndex
from retrieval.qa import answer_question

# Page Configuration
st.set_page_config(
    page_title="RAG Chatbot Test Sandbox",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        .main {
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
            color: #f8fafc;
        }
        .stApp {
            background: transparent;
        }
        .chat-card-clean {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(59, 130, 246, 0.4);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
        }
        .chat-card-corrupted {
            background: rgba(127, 29, 29, 0.4);
            border: 1px solid rgba(239, 68, 68, 0.5);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
        }
        .context-card {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 14px;
            margin-bottom: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_system_settings():
    return load_settings()


@st.cache_resource
def load_chroma_index(mode: str):
    settings = get_system_settings()
    if mode == "corrupted":
        embeddings_path = settings.paths.corrupted_embeddings_json
        json_path = settings.paths.corrupted_clean_json
    elif mode == "repaired":
        embeddings_path = settings.paths.repaired_embeddings_json
        json_path = settings.paths.repaired_clean_json
    else:  # baseline
        embeddings_path = settings.paths.embeddings_json
        json_path = settings.paths.clean_json

    if not json_path.exists():
        return None, f"Dataset for {mode} mode does not exist."

    df = pd.read_json(json_path)
    index = LocalEmbeddingIndex.build(df=df, settings=settings, embeddings_output_path=embeddings_path)
    return index, None


@st.cache_data
def load_frozen_testset():
    settings = get_system_settings()
    if settings.paths.eval_testset.exists():
        return read_json(settings.paths.eval_testset)
    return []


def main():
    settings = get_system_settings()
    testset = load_frozen_testset()

    # --- Sidebar Configuration ---
    st.sidebar.image("https://img.icons8.com/isometric-folders/100/bot.png", width=64)
    st.sidebar.title("RAG Chatbot Sandbox")
    st.sidebar.markdown("---")

    system_mode = st.sidebar.radio(
        "🎯 Choose Data State (Chế độ Dữ liệu):",
        options=[
            "🟢 Baseline Mode (Clean)",
            "🔴 Corruption Mode (Lỗi)",
            "🔵 Repaired Mode (Phục hồi)",
            "⚡ 3-Mode Comparison (So sánh 3 cột)",
        ],
        index=0,
    )

    is_compare_mode = "3-Mode Comparison" in system_mode

    mode_key = "baseline"
    badge_text = "🟢 BASELINE MODE (Clean 23 Papers)"
    if "Corruption" in system_mode:
        mode_key = "corrupted"
        badge_text = "🔴 CORRUPTION MODE (Corrupted Data)"
    elif "Repaired" in system_mode:
        mode_key = "repaired"
        badge_text = "🔵 REPAIRED MODE (Clean 23 Papers)"
    elif is_compare_mode:
        mode_key = "compare"
        badge_text = "⚡ 3-MODE COMPARISON MATRIX"

    st.sidebar.info(f"Active Mode: **{badge_text}**")
    st.sidebar.markdown("---")

    st.sidebar.subheader("System Config")
    st.sidebar.write(f"• **LLM Model**: `{settings.model_name}`")
    st.sidebar.write(f"• **LLM Judge**: `{settings.judge_llm_model}`")
    st.sidebar.write(f"• **Embedding**: `{settings.embedding_model}`")
    st.sidebar.write(f"• **Vector Store**: `ChromaDB ({mode_key})`")

    st.sidebar.markdown("---")
    st.sidebar.markdown("🔗 **Observability Dashboard**: [Open FastAPI Dashboard](http://localhost:8000)")
    st.sidebar.markdown("📐 **Architecture Blueprint**: [View System Topology](http://localhost:8000/architecture)")

    # Sidebar Explanation of Score Calculation
    st.sidebar.markdown("---")
    st.sidebar.subheader("📐 Score Calculation Formula")
    st.sidebar.markdown(
        """
        **Similarity Score** trong ChromaDB được tính dựa trên khoảng cách vector giữa câu hỏi và bài báo:

        $$\\text{Score} = \\frac{1}{1 + \\text{Distance}}$$

        * **Score $\\approx$ 1.0**: Tương đồng ngữ nghĩa cực cao.
        * **Score thấp (< 0.5)**: Tương đồng thấp / Dữ liệu nhiễu.
        """
    )

    # Main UI Header
    st.title("🤖 Interactive RAG Agent Chatbot Test Sandbox")
    st.caption("Thử nghiệm tương tác câu hỏi với RAG Agent ở 3 chế độ dữ liệu khác nhau để trực quan hóa sự sụt giảm và phục hồi chất lượng trả lời.")

    # Select Question from Frozen Test Set
    testset_options = ["-- Select Question from Frozen Benchmark Test Set --"] + [
        f"[{q.get('id', q.get('question_id', ''))}] ({q.get('question_type', '').upper()}) {q.get('question', '')}" for q in testset
    ]
    selected_opt = st.selectbox("📌 Select Test Question:", options=testset_options)

    default_query = ""
    selected_sample = None
    if selected_opt != "-- Select Question from Frozen Benchmark Test Set --":
        q_id = selected_opt.split("]")[0].replace("[", "")
        selected_sample = next((s for s in testset if s.get("id") == q_id or s.get("question_id") == q_id), None)
        if selected_sample:
            default_query = selected_sample["question"]

    user_query = st.text_area("❓ Question Input:", value=default_query, height=80, placeholder="Type your question...")

    if st.button("🚀 Ask RAG Agent", type="primary", use_container_width=True):
        if not user_query.strip():
            st.warning("Please enter a question.")
        else:
            if is_compare_mode:
                # 3-Column Parallel Comparison Mode
                st.markdown("## ⚡ Side-by-Side 3-Mode Comparison Matrix")
                if selected_sample:
                    st.info(
                        f"🎯 **Expected Ground Truth**: {selected_sample['ground_truth']}\n\n"
                        f"📄 **Expected Paper IDs**: `{', '.join(selected_sample['ground_truth_doc_ids'])}`"
                    )

                col1, col2, col3 = st.columns(3)
                modes_info = [
                    ("🟢 Baseline (Clean)", "baseline", col1),
                    ("🔴 Corrupted (Lỗi)", "corrupted", col2),
                    ("🔵 Repaired (Khôi phục)", "repaired", col3),
                ]

                for label, m_key, col in modes_info:
                    with col:
                        st.subheader(label)
                        index, err = load_chroma_index(m_key)
                        if err:
                            st.error(err)
                        else:
                            ans = answer_question(question=user_query, index=index, settings=settings)
                            
                            # Answer Box
                            if m_key == "corrupted":
                                st.error(f"**Answer**:\n\n{ans.answer}")
                            elif m_key == "baseline":
                                st.success(f"**Answer**:\n\n{ans.answer}")
                            else:
                                st.info(f"**Answer**:\n\n{ans.answer}")

                            # Top-1 Top Score Metrics
                            scores = getattr(ans, "retrieved_scores", [0.0] * len(ans.retrieved_doc_ids))
                            top1_score = scores[0] if scores else 0.0
                            st.metric("Top-1 Similarity Score", f"{top1_score:.4f}")

                            # Top-4 Retrieved Cards
                            st.markdown("#### 📚 Retrieved Contexts")
                            for rank, (doc_id, title, ctx, sc) in enumerate(
                                zip(ans.retrieved_doc_ids, ans.retrieved_titles, ans.retrieved_contexts, scores), 1
                            ):
                                with st.expander(f"#{rank} | Score: {sc:.4f} | {doc_id}", expanded=(rank == 1)):
                                    st.write(f"**Title**: {title}")
                                    st.write(f"**Score**: `{sc:.4f}`")
                                    st.code(ctx[:300] + "...", language="text")
            else:
                # Single Mode Execution
                with st.spinner(f"Querying RAG Agent in {mode_key.upper()} mode..."):
                    index, err = load_chroma_index(mode_key)
                    if err:
                        st.error(err)
                    else:
                        answer_res = answer_question(question=user_query, index=index, settings=settings)

                        # Display Answer Box
                        st.markdown("### 💡 Agent Generated Answer")
                        if mode_key == "corrupted":
                            st.error(f"**Answer ({mode_key.upper()})**:\n\n{answer_res.answer}")
                        else:
                            st.success(f"**Answer ({mode_key.upper()})**:\n\n{answer_res.answer}")

                        # Ground Truth Reference Comparison
                        if selected_sample:
                            st.markdown("### 🎯 Ground Truth Benchmark Reference")
                            st.info(
                                f"**Expected Ground Truth**: {selected_sample['ground_truth']}\n\n"
                                f"**Expected Paper IDs**: `{', '.join(selected_sample['ground_truth_doc_ids'])}`"
                            )

                        # Retrieved Context Cards (Top-4) with Score
                        st.markdown("### 📚 Top-4 Retrieved Context Cards (with Similarity Scores)")
                        scores = getattr(answer_res, "retrieved_scores", [0.0] * len(answer_res.retrieved_doc_ids))
                        for rank, (doc_id, title, ctx, score) in enumerate(
                            zip(answer_res.retrieved_doc_ids, answer_res.retrieved_titles, answer_res.retrieved_contexts, scores), 1
                        ):
                            with st.expander(f"Rank #{rank} | Score: {score:.4f} | DOI: {doc_id} | {title}", expanded=(rank == 1)):
                                st.write(f"**Title**: {title}")
                                st.write(f"**Paper ID**: `{doc_id}`")
                                st.write(f"**Similarity Score**: `{score:.4f}`")
                                st.code(ctx[:400] + "...", language="text")


if __name__ == "__main__":
    main()

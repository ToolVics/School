from __future__ import annotations
import json
import os
import streamlit as st
from app.core.pipeline import Pipeline
from app.core.refine import refine_entry
from app.config import RAW_KB_PATH, FINAL_KB_PATH, MODULES_PATH
from app.utils.file_utils import list_directories, list_files, read_jsonl, rewrite_jsonl
from app.utils.pdf_utils import generate_pdf_from_knowledge
from app.langchain_support import build_langchain_chat_chain

st.set_page_config(page_title="Course AI Pipeline", layout="wide")

if 'input_folder' not in st.session_state:
    st.session_state.input_folder = ''
if 'pipeline_data' not in st.session_state:
    st.session_state.pipeline_data = {'raw': [], 'final': [], 'modules': {'modules': []}, 'plans': []}
if 'cancel_requested' not in st.session_state:
    st.session_state.cancel_requested = False
if 'running' not in st.session_state:
    st.session_state.running = False


def load_jsonl(path: str):
    if not path:
        return []
    return read_jsonl(path)


def render_run_status():
    st.header("📤 Run & Status")
    st.session_state.input_folder = st.text_input(
        "Input folder",
        st.session_state.input_folder,
        help="Path on disk containing PDFs, DOCX, PPTX, HTML, images, or text files.",
    )

    with st.expander("Browse for a folder", expanded=False):
        browser_root = st.text_input(
            "Browse from directory",
            value=os.getcwd(),
            help="Change this to explore other locations on your machine.",
        )
        available_subdirs = list_directories(browser_root)
        if not available_subdirs:
            st.info("No subfolders found at this location or access denied.")
        else:
            pick_default = 0
            if st.session_state.input_folder in available_subdirs:
                pick_default = available_subdirs.index(st.session_state.input_folder)
            chosen = st.selectbox("Pick a subfolder", options=available_subdirs, index=pick_default)
            if st.button("Use selected folder", type="secondary"):
                st.session_state.input_folder = chosen
                st.success(f"Selected folder: {chosen}")
    api_key_set = bool(os.environ.get("OPENAI_API_KEY"))
    if not api_key_set:
        st.error("OPENAI_API_KEY is not set. Please add it to your environment or .env file before running the pipeline.")

    files = list_files(st.session_state.input_folder)
    st.caption(f"Discovered {len(files)} files in the selected folder.")

    progress_extract = st.progress(0, text="Extraction pending")
    progress_supervisor = st.progress(0, text="Supervisor pending")
    progress_links = st.progress(0, text="Link following pending")
    progress_batch = st.progress(0, text="Batch summarization pending")
    progress_refine = st.progress(0, text="Refinement pending")
    progress_cluster = st.progress(0, text="Clustering pending")

    status_placeholder = st.empty()

    def _progress(stage: str, current: int, total: int):
        frac = min(1.0, current / total) if total else 0
        label = f"{stage.title()} {current}/{total}" if total else f"{stage.title()}"
        if stage == "extract":
            progress_extract.progress(frac, text=label)
        elif stage == "supervisor":
            progress_supervisor.progress(frac, text=label)
        elif stage == "links":
            progress_links.progress(frac, text=label)
        elif stage == "batch":
            progress_batch.progress(frac, text=label)
        elif stage == "refine":
            progress_refine.progress(frac, text=label)
        elif stage == "cluster":
            progress_cluster.progress(frac, text="Clustering modules")

    def _cancel_check() -> bool:
        return bool(st.session_state.cancel_requested)

    run_disabled = not api_key_set or not st.session_state.input_folder or st.session_state.running
    start_col, cancel_col = st.columns([3, 1])
    with start_col:
        if st.button("📦 Build Complete Knowledge Base", disabled=run_disabled, width="stretch"):
            st.session_state.cancel_requested = False
            st.session_state.running = True
            try:
                pipeline = Pipeline(st.session_state.input_folder)
                status_placeholder.info("Pipeline running...")
                st.session_state.pipeline_data = pipeline.run(progress_callback=_progress, cancel_check=_cancel_check)
                status_placeholder.success("Pipeline finished.")
            except RuntimeError as exc:
                status_placeholder.error(str(exc))
            finally:
                st.session_state.running = False
                st.session_state.cancel_requested = False
    with cancel_col:
        if st.button("Cancel", type="primary", disabled=not st.session_state.running, width="stretch"):
            st.session_state.cancel_requested = True
            status_placeholder.warning("Cancellation requested; finishing current step...")

    st.write("Latest run summary")
    st.json(
        {
            "raw_entries": len(st.session_state.pipeline_data.get('raw', [])),
            "final_entries": len(st.session_state.pipeline_data.get('final', [])),
            "modules": len(st.session_state.pipeline_data.get('modules', {}).get('modules', [])),
        }
    )


def render_supervisor():
    st.header("📊 Supervisor & Agent Chain")
    plans = st.session_state.pipeline_data.get('plans', [])
    if not plans:
        st.info("Run the pipeline to see supervisor routing decisions per file.")
        return
    st.dataframe(plans, width="stretch", hide_index=True)


def render_raw():
    st.header("⚡ Raw Batch Summaries")
    raw_entries = load_jsonl(RAW_KB_PATH)
    st.write(raw_entries)


def render_chat():
    st.header("🔎 Chat with Course (Streaming)")
    final_entries = load_jsonl(FINAL_KB_PATH)
    if not final_entries:
        st.info("No knowledge base found. Run the pipeline first to chat with the course.")
        return

    question = st.text_input("Ask a question about the course")
    if question:
        try:
            chain = build_langchain_chat_chain(final_entries)
            with st.spinner("Responding via LangChain + OpenAI..."):
                answer = chain.invoke(question)
            st.markdown(answer)
        except Exception as exc:  # noqa: BLE001 broad for UI safety
            st.error(f"Chat failed: {exc}")


def render_modules():
    st.header("🧩 Module Clusters")
    data = {'modules': []}
    if MODULES_PATH and os.path.exists(MODULES_PATH):
        try:
            with open(MODULES_PATH, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
        except (json.JSONDecodeError, OSError):
            data = {'modules': []}
    if not data.get('modules'):
        st.info("No modules available yet. Run the pipeline after processing files.")
        return
    st.dataframe(data.get('modules', []), width="stretch", hide_index=True)


def render_refine():
    st.header("🧹 Refine Knowledge Base")
    raw_entries = load_jsonl(RAW_KB_PATH)
    final_entries = load_jsonl(FINAL_KB_PATH)
    if not raw_entries:
        st.info("No raw summaries available. Run the pipeline first.")
        return

    filenames = [entry.get('filename', '') for entry in raw_entries]
    selection = st.multiselect("Select files to re-run refinement", filenames)

    if st.button("Re-run refinement", disabled=not selection):
        updated_final = final_entries.copy()
        for filename in selection:
            raw_match = next((r for r in raw_entries if r.get('filename') == filename), None)
            if not raw_match:
                continue
            new_refine = refine_entry(filename, raw_match.get('raw_summary', ''), raw_match.get('links', []))
            updated_final = [f for f in updated_final if f.get('filename') != filename]
            updated_final.append(new_refine)
        rewrite_jsonl(FINAL_KB_PATH, updated_final)
        st.success("Refinement re-run complete. Reload the Raw and Chat tabs to see updates.")


def render_export():
    st.header("📑 Export Summaries (PDF)")
    final_entries = load_jsonl(FINAL_KB_PATH)
    if st.button("Export PDF"):
        dest = generate_pdf_from_knowledge(final_entries, 'app/db/knowledge_summary.pdf')
        st.success(f"Exported to {dest}")
    st.write(final_entries)


tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📤 Run & Status",
    "📊 Supervisor & Agent Chain",
    "⚡ Raw Batch Summaries",
    "🔎 Chat with Course (Streaming)",
    "🧩 Module Clusters",
    "🧹 Refine Knowledge Base",
    "📑 Export Summaries (PDF)",
])

with tab1:
    render_run_status()
with tab2:
    render_supervisor()
with tab3:
    render_raw()
with tab4:
    render_chat()
with tab5:
    render_modules()
with tab6:
    render_refine()
with tab7:
    render_export()

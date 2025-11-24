from __future__ import annotations
import json
import os
import streamlit as st
from app.core.pipeline import Pipeline
from app.config import RAW_KB_PATH, FINAL_KB_PATH, MODULES_PATH
from app.utils.file_utils import list_files, read_jsonl
from app.utils.pdf_utils import generate_pdf_from_knowledge

st.set_page_config(page_title="Course AI Pipeline", layout="wide")

if 'input_folder' not in st.session_state:
    st.session_state.input_folder = ''
if 'pipeline_data' not in st.session_state:
    st.session_state.pipeline_data = {'raw': [], 'final': [], 'modules': {'modules': []}}


def load_jsonl(path: str):
    if not path:
        return []
    return read_jsonl(path)


def render_run_status():
    st.header("📤 Run & Status")
    st.session_state.input_folder = st.text_input("Input folder", st.session_state.input_folder)
    if st.button("📦 Build Complete Knowledge Base"):
        pipeline = Pipeline(st.session_state.input_folder)
        st.session_state.pipeline_data = pipeline.run()
    files = list_files(st.session_state.input_folder)
    st.write(f"Found {len(files)} files")
    st.progress(min(1.0, len(files) / 10))


def render_supervisor():
    st.header("📊 Supervisor & Agent Chain")
    st.json({"message": "Supervisor plans are generated dynamically during runs."})


def render_raw():
    st.header("⚡ Raw Batch Summaries")
    raw_entries = load_jsonl(RAW_KB_PATH)
    st.write(raw_entries)


def render_chat():
    st.header("🔎 Chat with Course (Streaming)")
    st.write("Chat interface placeholder. Stream responses using ModelRouter.stream_chat().")


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
    st.json(data)


def render_refine():
    st.header("🧹 Refine Knowledge Base")
    st.write("Select files to rerun refinement (not implemented in UI demo).")


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

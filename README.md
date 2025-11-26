# Course Knowledge Base Builder

This repository contains a complete Python + Streamlit application for building a production-ready course knowledge base from mixed-format course materials. The system extracts text (with OCR fallbacks), plans processing via an AI supervisor, follows referenced links, summarizes content in batches, refines results, clusters modules, and exposes an interactive UI and LangChain-powered chat.

## Features
- Multi-format extraction for PDF, DOCX, PPTX, HTML, images (with OCR fallback), and plain text.
- AI supervisor that decides how to process each file, including link following limits.
- Safe link downloader with inference fallback for unavailable pages and YouTube transcript handling.
- Batch chunking and summarization with GPT models, plus refinement into high-quality knowledge entries.
- Module clustering to group refined entries into course modules.
- Streamlit interface with progress bars, cancellation, folder selection, and per-stage visibility.
- LangChain chat tab to query the resulting knowledge base.
- PDF export for summaries and persistent JSONL/JSON knowledge stores.

## Project Structure
```
project_root/
├── .env.template          # Template for environment variables
├── requirements.txt       # Python dependencies
└── app/
    ├── config.py          # Paths and model configuration (loads .env automatically)
    ├── main.py            # CLI entry point for running the pipeline
    ├── core/              # Pipeline components (extraction, supervisor, links, batching, refine, clustering)
    │   ├── pipeline.py
    │   ├── supervisor.py
    │   ├── extractor.py
    │   ├── link_extractor.py
    │   ├── refine.py
    │   ├── module_clustering.py
    │   └── batch_processing/
    │       ├── batch_chunker.py
    │       └── batch_manager.py
    ├── extractors/        # Low-level text/HTML/PDF helpers
    │   └── extract_text.py
    ├── models/
    │   └── model_router.py  # OpenAI client wrapper using responses.create with fallbacks
    ├── utils/             # Shared utilities (files, logging, PDF export)
    │   ├── file_utils.py
    │   ├── log_utils.py
    │   └── pdf_utils.py
    ├── ui/
    │   └── ui_app.py      # Streamlit interface
    ├── db/                # Knowledge base outputs
    │   ├── knowledge_raw.jsonl
    │   ├── knowledge_final.jsonl
    │   └── modules.json
    ├── downloads/         # Cached linked files
    └── langchain_support.py # LangChain chat chain
```

## Setup
1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables**
   - Copy `.env.template` to `.env` and set at minimum `OPENAI_API_KEY`.
   - Optional overrides: `COURSE_INPUT_FOLDER`, `LINK_MODEL`, `SUMMARY_MODEL`, `REFINE_MODEL`, `SUPERVISOR_MODEL`, `CLUSTER_MODEL`, and `CHUNK_TARGET`.
   - `.env` is auto-loaded via `python-dotenv` even when running from nested directories or Streamlit.

3. **Prepare input data**
   - Place your course files in a folder accessible to the app. Supported formats include PDF, DOCX, PPTX, HTML, images, and plain text.

## Running the Pipeline
### Command Line
```bash
python -m app.main /path/to/course_folder
```
This runs the full pipeline headlessly and writes outputs to `app/db/`.

### Streamlit UI
```bash
streamlit run app/ui/ui_app.py
```
Key UI elements:
- **Input folder**: Type a path or use the folder browser expander to select a subdirectory.
- **Build Complete Knowledge Base**: Starts the pipeline once an API key and folder are provided.
- **Progress bars & status**: Shows extraction, supervisor decisions, batching, refinement, and clustering progress. A **Cancel** button stops the run safely.
- **Visibility**: Displays supervisor plans, link details, and raw/final entries for transparency.
- **Tabs**: Run & Status, Supervisor & Agent Chain, Raw Batch Summaries, Chat with Course (LangChain), Module Clusters, Refinement management, and PDF Export.

## Pipeline Overview
1. **Extraction** (`core/extractor.py`, `extractors/extract_text.py`):
   - Parses PDFs (text + OCR fallback), DOCX, PPTX (slides and notes), HTML (visible text + links), images (OCR), and plain text.
   - Returns empty text if extraction fails so downstream AI can infer as needed.
2. **Supervisor Planning** (`core/supervisor.py`): Uses the configured supervisor model to decide summarization and link-following strategy per file.
3. **Link Processing** (`core/link_extractor.py`): Extracts and downloads safe links, handles YouTube transcripts or infers content when downloads fail.
4. **Batch Summarization** (`core/batch_processing/`): Splits content into manageable chunks and summarizes with fast models, producing raw JSONL entries.
5. **Refinement** (`core/refine.py`): Combines raw summaries and link data into high-quality knowledge base records saved to `knowledge_final.jsonl`.
6. **Module Clustering** (`core/module_clustering.py`): Groups refined entries into modules stored in `modules.json`.
7. **Chat & Export** (`langchain_support.py`, `ui/ui_app.py`, `utils/pdf_utils.py`): LangChain Q&A over the knowledge base and PDF export of summaries.

## Data Stores
- `app/db/knowledge_raw.jsonl`: Raw batch summaries per file.
- `app/db/knowledge_final.jsonl`: Refined knowledge base entries.
- `app/db/modules.json`: Clustered module metadata.
- `app/downloads/`: Cached linked resources for re-use.

## Troubleshooting
- **API key errors**: Ensure `OPENAI_API_KEY` is set in `.env`; the app loads it automatically via `python-dotenv`.
- **No files detected**: Verify the input folder path is correct and contains supported files. Progress bars will remain at zero if nothing is found.
- **Cleanup between runs**: The pipeline removes stale DB files before a new run. If you need a manual reset, delete the files in `app/db/`.
- **Model overrides**: Adjust model env vars in `.env` to fine-tune cost/speed per pipeline stage.

## Development Notes
- OpenAI calls use the newest `responses.create` API with streaming support and fallback rotation across configured models.
- Utilities provide safe filename handling, directory creation, JSON/JSONL helpers, and PDF generation.
- Logging writes to console and `app.log` for operational visibility.


import os

from dotenv import find_dotenv, load_dotenv

# Ensure environment variables load even when executed from nested paths (e.g., Streamlit)
dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path)

RAW_KB_PATH = os.path.join('app', 'db', 'knowledge_raw.jsonl')
FINAL_KB_PATH = os.path.join('app', 'db', 'knowledge_final.jsonl')
MODULES_PATH = os.path.join('app', 'db', 'modules.json')
DOWNLOADS_DIR = os.path.join('app', 'downloads')
INPUT_FOLDER = os.environ.get('COURSE_INPUT_FOLDER', '')

LINK_MODEL = os.environ.get('LINK_MODEL', 'gpt-5-mini')
SUMMARY_MODEL = os.environ.get('SUMMARY_MODEL', 'gpt-5-nano')
REFINE_MODEL = os.environ.get('REFINE_MODEL', 'gpt-5.1-mini')
SUPERVISOR_MODEL = os.environ.get('SUPERVISOR_MODEL', 'gpt-5-mini')
CLUSTER_MODEL = os.environ.get('CLUSTER_MODEL', 'gpt-5-mini')

DEFAULT_CHUNK_TARGET = int(os.environ.get('CHUNK_TARGET', '900'))

import os

from dotenv import load_dotenv

load_dotenv()

RAW_KB_PATH = os.path.join('app', 'db', 'knowledge_raw.jsonl')
FINAL_KB_PATH = os.path.join('app', 'db', 'knowledge_final.jsonl')
MODULES_PATH = os.path.join('app', 'db', 'modules.json')
DOWNLOADS_DIR = os.path.join('app', 'downloads')
INPUT_FOLDER = os.environ.get('COURSE_INPUT_FOLDER', '')

LINK_MODEL = os.environ.get('LINK_MODEL', 'gpt-5-mini')
SUMMARY_MODEL = os.environ.get('SUMMARY_MODEL', 'gpt-5-nano')
REFINE_MODEL = os.environ.get('REFINE_MODEL', 'gpt-5.1-mini')

DEFAULT_CHUNK_TARGET = int(os.environ.get('CHUNK_TARGET', '900'))

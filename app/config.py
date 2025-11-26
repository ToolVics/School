import os

from dotenv import find_dotenv, load_dotenv

# Ensure environment variables load even when executed from nested paths (e.g., Streamlit)
dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path)


def get_model(task: str) -> str:
    """Return a configured model name for the given task.

    Defaults align with the latest supported OpenAI models and can be overridden via environment
    variables matching the upper-case task name (e.g., SUMMARY_MODEL).
    """

    defaults = {
        "summarize": "gpt-4.1",
        "refine": "gpt-5.1",
        "link_follow": "gpt-4.1-mini",
        "supervisor": "gpt-4.1-mini",
        "cluster": "gpt-4.1-mini",
        "chat": "gpt-4.1",
    }
    env_override = os.environ.get(f"{task.upper()}_MODEL")
    return env_override or defaults.get(task, "gpt-4.1")


RAW_KB_PATH = os.path.join('app', 'db', 'knowledge_raw.jsonl')
FINAL_KB_PATH = os.path.join('app', 'db', 'knowledge_final.jsonl')
MODULES_PATH = os.path.join('app', 'db', 'modules.json')
DOWNLOADS_DIR = os.path.join('app', 'downloads')
INPUT_FOLDER = os.environ.get('COURSE_INPUT_FOLDER', '')

LINK_MODEL = get_model('link_follow')
SUMMARY_MODEL = get_model('summarize')
REFINE_MODEL = get_model('refine')
SUPERVISOR_MODEL = get_model('supervisor')
CLUSTER_MODEL = get_model('cluster')

DEFAULT_CHUNK_TARGET = int(os.environ.get('CHUNK_TARGET', '900'))

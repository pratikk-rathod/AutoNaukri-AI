import os
from pathlib import Path
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Data File Paths
JOBS_CACHE_FILE = DATA_DIR / "jobs.json"
JOBS_TEXT_FILE = DATA_DIR / "jobs.txt"
TOP_JOBS_FILE = DATA_DIR / "top_40.json"
RESUME_FILE = DATA_DIR / "resume.txt"
APPLIED_JOBS_FILE = DATA_DIR / "applied_jobs.json"
EMBEDDINGS_CACHE_FILE = DATA_DIR / "cache_embeddings.json"
KB_FILE = DATA_DIR / "kb.json"
FORMAT_MAP_FILE = DATA_DIR / "format_map.json"

# API & Secrets
NAUKRI_EMAIL = os.getenv("NAUKRI_EMAIL", "")
NAUKRI_PASSWORD = os.getenv("NAUKRI_PASSWORD", "")

# Ollama Models
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma4:e4b")

# Job Search URLs & Constants
# Adjust this as needed in the future
NAUKRI_BASE_SEARCH_URL = "https://www.naukri.com/software-developer-ai-ml-engineer-java-python-django-aiml-java-full-stack-developer-mern-stack-developer-mean-stack-developer-full-stack-application-development-jobs?k=software%20developer%2C%20ai%20ml%20engineer%2C%20java%2C%20python%2C%20django%2C%20aiml%2C%20java%20full%20stack%20developer%2C%20mern%20stack%20developer%2C%20mean%20stack%20developer%2C%20full%20stack%20application%20development&nignbevent_src=jobsearchDeskGNB&experience=1&ctcFilter=10to15&ctcFilter=15to25&ctcFilter=6to10&ctcFilter=0to3&ctcFilter=25to50&ctcFilter=50to75&ctcFilter=75to100&ctcFilter=3to6&functionAreaIdGid=3&functionAreaIdGid=5&functionAreaIdGid=8&jobAge=7"

NAUKRI_APPLY_API_URL = "https://www.naukri.com/cloudgateway-workflow/workflow-services/apply-workflow/v1/apply"

MUST_HAVE_SKILLS = [
    'python', 'java', 'django', 'ai', 'ml',
    'mern', 'mean', 'full stack', 'backend',
    'software engineer', 'developer'
]

DEALBREAKERS = [
    'game', 'electrical', 'qa', 'bpo', 'intern', 'internship', 'temporary', 'C#', 'Dot Net Developer', '.net'
    'telecalling', 'sales', 'customer support',
    'mechanical', 'civil', 'tata consultancy services', 'tcs'
]

# Pipeline settings
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 8))
TOP_K_PERCENTAGE = float(os.getenv("TOP_K_PERCENTAGE", 0.25))
TOP_K_LLM = int(os.getenv("TOP_K_LLM", 40))

# Question answering defaults
ANSWERS_DEFAULTS = {
    "expectedCtc": os.getenv("EXPECTED_CTC", "1500000"),
    "currentCtc": os.getenv("CURRENT_CTC", "1000000"),
    "noticePeriod": os.getenv("NOTICE_PERIOD", "Immediate"),
    "experience": os.getenv("EXPERIENCE", "1")
}

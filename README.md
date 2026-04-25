# Naukri Auto Apply Pipeline 🤖

An enterprise-grade, fully automated AI recruitment pipeline that actively scrapes, rigorously scopes, and auto-applies to software engineering roles dynamically matching a candidate's portfolio. 

Powered by **Playwright** and **Ollama Local LLMs**, it features dynamic web scraping, semantic resume matching, LLM-driven job question answering, automated failure recovery, and 7-day rolling logs.

## ✨ Core Features
- **Stealth Auto-Scraping**: Evades generic detection with customized Playwright Chromium bots that parse underlying Naukri search endpoint APIs rather than volatile frontend HTML structures.
- **Deep Semantic Pre-Filtering**: Uses local vector embeddings (`nomic-embed-text`) alongside localized keyword match scoring to identify exactly which roles meet your custom domain experiences.
- **Cognitive Ranker**: Orchestrates a second-pass rank via `gemma4:e4b` to score your parsed resume against the Top 25% of jobs, producing an elite subset of applications.
- **Dynamic Application AI**: Predictively completes native Naukri apply questionnaires directly from the application endpoint, caching custom answers locally via an auto-learning JSON Knowledge Base to slash redundant LLM requests.
- **Enterprise Resiliency**: Fully utilizes `tenacity` exponential-backoffs for mitigating intermittent internal crawler/proxy failure. Maintains rolling 7-day server logs preventing memory leaks over extended chron-job deployments.

---

## 🏗️ Architecture Layout
```text
naukri_auto_apply/
├── .env                  # Core Secrets (Naukri Credentials, Node Overrides)
├── run_pipeline.py       # Master Orchestrator (CLI Command Executor)
├── requirements.txt      # Python Dependencies (requests, tenacity, playwright)
├── config/               
│   ├── logger.py         # Advanced Daily Rolling File Handler
│   └── settings.py       # Pydantic-style Env Var Manager
├── logs/                 # Archive for application status files
├── src/
│   ├── core/             # Base Utility (Parsers, Scorers, Stores)
│   └── services/         # Decoupled Domains (Scrapers, LLM Filters, Appliers)
└── data/                 # Transient operational context (Jobs, Resumes, Caches)
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
Ensure you have the following installed on your machine:
* Python 3.10+
* Playwright Browsers
* [Ollama](https://ollama.com/) server running at `http://localhost:11434`

### 2. Environment Configuration
Clone the repository and install all localized libraries:

```bash
# Clone the project wrapper
git clone https://github.com/your-username/naukri_auto_apply.git
cd naukri_auto_apply

# Initialize virtual environment
python -m venv venv
venv\Scripts\activate  # inside Windows

# Install libraries mapping
pip install -r requirements.txt

# Download required automated browsers
playwright install chromium
```

### 3. Deploy LLM Services
Ensure the local Ollama instance is downloading the required analytical models:
```bash
ollama run gemma4:e4b
ollama pull nomic-embed-text
```

### 4. Application Configuration
Copy the `.env.example` placeholder into an active `.env` configuration template, and add your user details:
```env
NAUKRI_EMAIL=your_email@gmail.com
NAUKRI_PASSWORD=your_naukri_password

EXPECTED_CTC=1500000
CURRENT_CTC=1000000
NOTICE_PERIOD=Immediate
EXPERIENCE=2
```

**Resume Configuration**
A placeholder file is provided in the repository called `data/resume.example.txt`. 
1. Duplicate or rename this file to `data/resume.txt`.
2. Paste your plain-text resume into it before running the pipeline. 
*(Note: `resume.txt` is strictly ignored by Git to ensure you never accidentally push your private resume to the public internet!)*

---

## ⚙️ Usage Options

The system runs out of a localized execution hub `run_pipeline.py`. It accepts strict runtime arguments allowing full customizability depending on what data phase you wish to run dynamically:

**Run Full Unattended Pipeline**
```bash
python run_pipeline.py --all
```

**Run Modular Scripts**
```bash
# Step 1: Execute scraping isolated
python run_pipeline.py --scrape

# Step 2: Trigger AI Resume Scoring logic 
python run_pipeline.py --filter

# Step 3: Trigger active Headless apply logic
python run_pipeline.py --apply
```

---

## 🛡️ License & Disclaimers
This framework heavily relies on undocumented portal APIs intended strictly for analytical application scaling. Usage might counteract general host TOS rules relying strongly on strict rate margins.

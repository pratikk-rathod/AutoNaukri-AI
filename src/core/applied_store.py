import json
import os
from datetime import datetime
from config.settings import APPLIED_JOBS_FILE

def load_applied():
    if not os.path.exists(APPLIED_JOBS_FILE):
        return {}
    
    with open(APPLIED_JOBS_FILE, encoding='utf-8') as f:
        data = json.load(f)
    return {job["job_id"]: job for job in data}

def save_applied(data_dict):
    data_list = list(data_dict.values())
    with open(APPLIED_JOBS_FILE, "w", encoding='utf-8') as f:
        json.dump(data_list, f, indent=2)

def is_applied(job_id, applied_map):
    return job_id in applied_map

def add_applied(job, applied_map):
    job_id = job["job_id"]

    applied_map[job_id] = {
        "job_id": job_id,
        "applied_on": datetime.now().strftime("%Y-%m-%d"),
        "title": job.get("title", ""),
        "url": job.get("url", ""),
        "description": job.get("description", "")[:500]
    }

import json
import os
from config.settings import KB_FILE, FORMAT_MAP_FILE

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def save_json(data, path):
    with open(path, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_kb():
    return load_json(KB_FILE)

def save_kb(kb):
    save_json(kb, KB_FILE)

def load_format_map():
    return load_json(FORMAT_MAP_FILE)

def save_format_map(m):
    save_json(m, FORMAT_MAP_FILE)

def clean_answer(ans):
    if not ans:
        return "Yes"

    ans = ans.strip().lower().split("\n")[0]
    ans = " ".join(ans.split()[:2])

    if "yes" in ans:
        return "Yes"
    if "no" in ans:
        return "No"
    if "immediate" in ans:
        return "Immediate"

    return ans.capitalize()

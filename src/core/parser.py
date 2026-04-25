import re

def parse_resume(text):
    t = text.lower()

    primary = ["python", "ai", "ml", "backend", "django", "spring", "angular", "react", "frontend","backend", "api", "nlp", "computer vision", "cv", "deep learning", "dl", "transformer", "pytorch", "tensorflow", "sklearn","java" ,"javascript", "sql", "docker", "aws"]
    secondary = ["c++", "go", "ruby", "php", "rust", "kubernetes", "azure", "gcp", "hadoop", "spark", "scala", "flask", "vue", "svelte", "fastapi", "graphql", "redis", "mongodb", "postgresql", "mysql",  "linux", "git", "ci/cd", "agile", "scrum", "data science", "ds", "data analysis", "data analytics", "hive", "airflow", "tableau", "power bi", "excel", "vba", "sas", "stata", "r", "julia","matlab", "cloud", "devops", "microservices", "rest", "soap", "grpc"]
    primary_skills = [s for s in primary if s in t]
    secondary_skills = [s for s in secondary if s in t]

    exp = 1
    m = re.search(r'(\d+)\s+years', t)
    if m:
        exp = int(m.group(1))

    domains = []
    if any(k in t for k in ["ai", "ml", "nlp"]):
        domains.append("ai")
    if any(k in t for k in ["spring", "django", "api"]):
        domains.append("backend")
    if any(k in t for k in ["angular", "react"]):
        domains.append("frontend")

    return {
        "primary_skills": primary_skills,
        "secondary_skills": secondary_skills,
        "experience": exp,
        "domains": domains,
        "raw": text
    }

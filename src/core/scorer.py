import numpy as np

def cosine(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def skill_score(resume, job):
    text = (job["title"] + " " + job.get("skills", "")).lower()
    score = 0

    for s in resume["primary_skills"]:
        if s in text:
            score += 2

    for s in resume["secondary_skills"]:
        if s in text:
            score += 1

    max_score = len(resume["primary_skills"])*2 + len(resume["secondary_skills"])
    return score / max_score if max_score else 0

def role_score(resume, job):
    text = job["title"].lower()
    return sum(d in text for d in resume["domains"]) / max(len(resume["domains"]), 1)

def experience_penalty(resume_exp, job):
    text = (job["title"] + job["description"]).lower()

    if "senior" in text and resume_exp < 2:
        return -0.3

    if "lead" in text and resume_exp < 3:
        return -0.4

    return 0

def penalty(job):
    t = (job["title"] + job["description"]).lower()
    p = 0

    if "intern" in t:
        p -= 0.5
    if "qa" in t or "testing" in t:
        p -= 0.7
    if "sales" in t:
        p -= 1

    return p

def final_score(resume, job, res_emb, job_emb):
    s1 = skill_score(resume, job)
    s2 = cosine(res_emb, job_emb)
    s3 = role_score(resume, job)
    s4 = penalty(job)
    s5 = experience_penalty(resume["experience"], job)

    score = (
        0.5 * s1 +
        0.3 * s2 +
        0.15 * s3 +
        0.05 * (1 + s4 + s5)
    )

    return round(score * 100, 2)

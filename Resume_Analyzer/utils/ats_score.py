def calculate_resume_score(data):
    skills = len(data["skills"])
    education = 1 if "not clearly detected" not in data["education"].lower() else 0
    projects = 1 if "not clearly detected" not in data["projects"].lower() else 0
    experience = 1 if "not clearly detected" not in data["experience"].lower() else 0

    skill_score = min(skills * 4, 40)
    completeness = education * 20 + projects * 15 + experience * 15

    return round(min(skill_score + completeness, 100), 1)

def calculate_job_match(resume_skills, job_skills):
    if not job_skills:
        return 0
    return round(len(set(resume_skills) & set(job_skills)) / len(set(job_skills)) * 100, 1)

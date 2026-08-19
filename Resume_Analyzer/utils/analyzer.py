import re

SKILLS = [
    "python", "java", "c++", "c#", "javascript", "typescript",
    "sql", "mysql", "mongodb", "machine learning", "deep learning",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
    "flask", "fastapi", "django", "git", "github", "docker",
    "aws", "azure", "gcp", "statistics", "data visualization",
    "power bi", "tableau", "html", "css", "react", "node.js",
    "spring boot", "rest api", "excel", "nlp", "opencv"
]

def contains_phrase(text, phrase):
    return re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text, re.I) is not None

def extract_skills(text):
    return sorted([skill for skill in SKILLS if contains_phrase(text, skill)])

def detect_section(text, names):
    lower = text.lower()
    for name in names:
        idx = lower.find(name)
        if idx != -1:
            return text[idx:idx + 700].strip()
    return ""

def analyze_resume(text):
    skills = extract_skills(text)
    education = detect_section(
        text,
        ["education", "academic qualification", "qualification"]
    )
    projects = detect_section(text, ["projects", "project"])
    experience = detect_section(
        text,
        ["experience", "work experience", "professional experience", "internship"]
    )

    return {
        "skills": skills,
        "education": education or "Education section not clearly detected.",
        "projects": projects or "Project section not clearly detected.",
        "experience": experience or "Experience section not clearly detected.",
        "text_length": len(text),
    }

def analyze_job_description(text):
    return {
        "skills": extract_skills(text)
    }

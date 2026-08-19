# AI Resume Analyzer

A simple Flask-based Resume Analyzer inspired by the provided UI design.

## Current Version (V1)

- Signup / Login / Logout
- SQLite database
- Dashboard statistics
- Resume PDF upload
- PDF text extraction using pdfplumber
- Basic education / project / experience section detection
- Skill extraction
- Resume ATS-style score
- Optional Job Description
- Matching skills
- Missing skills
- Job match score
- Analysis history
- Profile page

## Next Development Steps

1. Improve resume section extraction
2. Add TF-IDF + cosine similarity
3. Add Gemini AI suggestions
4. Add AI recommended job roles
5. Add score breakdown and Chart.js graph
6. Add downloadable report
7. Improve UI to closely match the reference mockup

## Run

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Open `http://127.0.0.1:5000`.

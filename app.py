import os
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy  # type: ignore[import-not-found]
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from utils.resume_parser import extract_resume_text
from utils.analyzer import analyze_resume, analyze_job_description
from utils.ats_score import calculate_resume_score, calculate_job_match

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "resumes")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "resume_analyzer.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

db = SQLAlchemy(app)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    resume_name = db.Column(db.String(255), nullable=False)
    ats_score = db.Column(db.Float, default=0)
    job_match = db.Column(db.Float, nullable=True)
    skills = db.Column(db.Text, default="")
    matched_skills = db.Column(db.Text, default="")
    missing_skills = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please fill all fields.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "warning")
        else:
            user = User(
                name=name,
                email=email,
                password=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.commit()
            flash("Account created. Please login.", "success")
            return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user_name"] = user.name
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    analyses = Analysis.query.filter_by(user_id=session["user_id"]).order_by(
        Analysis.created_at.desc()
    ).all()

    total = len(analyses)
    average = round(sum(a.ats_score for a in analyses) / total, 1) if total else 0
    best = max((a.ats_score for a in analyses), default=0)
    last = analyses[0] if analyses else None

    return render_template(
        "dashboard.html",
        analyses=analyses[:5],
        total=total,
        average=average,
        best=best,
        last=last
    )


@app.route("/upload")
@login_required
def upload():
    return render_template("upload.html")


@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    resume = request.files.get("resume")
    job_description = request.form.get("job_description", "").strip()

    if not resume or not resume.filename:
        flash("Please choose a resume PDF.", "danger")
        return redirect(url_for("upload"))

    if not resume.filename.lower().endswith(".pdf"):
        flash("Only PDF files are supported in version 1.", "danger")
        return redirect(url_for("upload"))

    filename = secure_filename(resume.filename)
    unique_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
    path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    resume.save(path)

    text = extract_resume_text(path)
    data = analyze_resume(text)
    jd_data = analyze_job_description(job_description) if job_description else {
        "skills": []
    }

    matched = sorted(set(data["skills"]) & set(jd_data["skills"]))
    missing = sorted(set(jd_data["skills"]) - set(data["skills"]))

    ats_score = calculate_resume_score(data)
    job_match = calculate_job_match(data["skills"], jd_data["skills"]) if job_description else None

    analysis = Analysis(
        user_id=session["user_id"],
        resume_name=filename,
        ats_score=ats_score,
        job_match=job_match,
        skills=", ".join(data["skills"]),
        matched_skills=", ".join(matched),
        missing_skills=", ".join(missing),
    )
    db.session.add(analysis)
    db.session.commit()

    return render_template(
        "result.html",
        analysis=analysis,
        data=data,
        matched=matched,
        missing=missing,
        job_description=bool(job_description)
    )


@app.route("/history")
@login_required
def history():
    analyses = Analysis.query.filter_by(user_id=session["user_id"]).order_by(
        Analysis.created_at.desc()
    ).all()
    return render_template("history.html", analyses=analyses)


@app.route("/history/<int:analysis_id>")
@login_required
def history_detail(analysis_id):
    analysis = Analysis.query.filter_by(
        id=analysis_id, user_id=session["user_id"]
    ).first_or_404()

    data = {
        "skills": [x.strip() for x in analysis.skills.split(",") if x.strip()],
        "education": "Detected from resume",
        "projects": [],
        "experience": "Not yet extracted in v1",
    }
    matched = [x.strip() for x in analysis.matched_skills.split(",") if x.strip()]
    missing = [x.strip() for x in analysis.missing_skills.split(",") if x.strip()]

    return render_template(
        "result.html",
        analysis=analysis,
        data=data,
        matched=matched,
        missing=missing,
        job_description=analysis.job_match is not None
    )


@app.route("/profile")
@login_required
def profile():
    user = User.query.get_or_404(session["user_id"])
    total = Analysis.query.filter_by(user_id=user.id).count()
    return render_template("profile.html", user=user, total=total)


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)

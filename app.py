"""
AI Resume Screening & Ranking System
Main Flask Application
"""

import os
import tempfile
import re
import json
import string
from pathlib import Path


from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename

import PyPDF2
import pdfplumber
import docx
# import nltk
# from nltk.corpus import stopwords
# from nltk.tokenize import word_tokenize, sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Note: spacy is optional — core functionality uses NLTK + scikit-learn

# ---------------------------------------------------------------------------
# NLTK data (download once)
# ---------------------------------------------------------------------------
# nltk.download("punkt", quiet=True)
# nltk.download("punkt_tab", quiet=True)
# nltk.download("stopwords", quiet=True)
# nltk.download("averaged_perceptron_tagger", quiet=True)
# nltk.download("averaged_perceptron_tagger_eng", quiet=True)

# ---------------------------------------------------------------------------
# Flask app configuration
# ---------------------------------------------------------------------------
app = Flask(__name__)
# app.secret_key = "ai_resume_screening_secret_key_2024"
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "dev-secret-key"
)
# app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt"}

# os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ---------------------------------------------------------------------------
# Skill keywords database (categorised)
# ---------------------------------------------------------------------------
SKILL_CATEGORIES = {
    "programming_languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "ruby",
        "go", "golang", "rust", "swift", "kotlin", "php", "scala", "r",
        "matlab", "perl", "dart", "lua", "sql", "html", "css", "sass",
        "less", "bash", "shell", "powershell", "objective-c", "assembly",
    ],
    "frameworks_libraries": [
        "react", "angular", "vue", "vuejs", "nextjs", "next.js", "nuxt",
        "django", "flask", "fastapi", "spring", "spring boot", "express",
        "node", "nodejs", "node.js", ".net", "asp.net", "laravel",
        "rails", "ruby on rails", "flutter", "react native", "svelte",
        "bootstrap", "tailwind", "jquery", "tensorflow", "pytorch",
        "keras", "scikit-learn", "pandas", "numpy", "matplotlib",
        "opencv", "selenium", "playwright", "cypress",
    ],
    "databases": [
        "mysql", "postgresql", "postgres", "mongodb", "redis", "sqlite",
        "oracle", "sql server", "dynamodb", "cassandra", "elasticsearch",
        "firebase", "firestore", "neo4j", "mariadb", "couchdb",
        "supabase", "cockroachdb",
    ],
    "cloud_devops": [
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes",
        "k8s", "jenkins", "ci/cd", "terraform", "ansible", "nginx",
        "apache", "linux", "git", "github", "gitlab", "bitbucket",
        "heroku", "vercel", "netlify", "cloudflare", "circleci",
        "travis", "grafana", "prometheus", "datadog",
    ],
    "data_ai_ml": [
        "machine learning", "deep learning", "nlp",
        "natural language processing", "computer vision", "ai",
        "artificial intelligence", "data science", "data analysis",
        "data engineering", "big data", "hadoop", "spark", "kafka",
        "airflow", "etl", "data pipeline", "tableau", "power bi",
        "looker", "statistics", "regression", "classification",
        "neural network", "transformers", "bert", "gpt", "llm",
        "generative ai", "rag", "langchain",
    ],
    "soft_skills": [
        "leadership", "communication", "teamwork", "problem solving",
        "critical thinking", "project management", "agile", "scrum",
        "time management", "collaboration", "mentoring", "presentation",
        "negotiation", "decision making", "adaptability", "creativity",
    ],
}

# Flatten all skills into one lookup set (lowercase)
ALL_SKILLS = set()
for skills in SKILL_CATEGORIES.values():
    for s in skills:
        ALL_SKILLS.add(s.lower())


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(filepath: str) -> str:
    """Extract text from a PDF file using pdfplumber (fallback: PyPDF2)."""
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception:
        pass

    if not text.strip():
        try:
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception:
            pass

    return text.strip()


def extract_text_from_docx(filepath: str) -> str:
    """Extract text from a DOCX file."""
    try:
        doc = docx.Document(filepath)
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    except Exception:
        return ""


def extract_text_from_txt(filepath: str) -> str:
    """Extract text from a plain text file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except Exception:
        return ""


def extract_text(filepath: str) -> str:
    """Route to the correct extractor based on file extension."""
    ext = filepath.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        return extract_text_from_pdf(filepath)
    elif ext == "docx":
        return extract_text_from_docx(filepath)
    elif ext == "txt":
        return extract_text_from_txt(filepath)
    return ""


# ---------------------------------------------------------------------------
# NLP / Text processing
# ---------------------------------------------------------------------------
def clean_text(text: str) -> str:
    """Lowercase, remove special chars, extra whitespace."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s.#+/]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_skills(text: str) -> list[str]:
    """Extract recognised skills from text."""
    text_lower = text.lower()
    found = []
    # Check multi-word skills first (longest first)
    sorted_skills = sorted(ALL_SKILLS, key=len, reverse=True)
    for skill in sorted_skills:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    return list(dict.fromkeys(found))  # deduplicate, preserve order


def extract_experience_years(text: str) -> int | None:
    """Try to extract years of experience from resume text."""
    patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)",
        r"experience\s*(?:of)?\s*(\d+)\+?\s*(?:years?|yrs?)",
        r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:in|of|working)",
    ]
    for pat in patterns:
        match = re.search(pat, text.lower())
        if match:
            return int(match.group(1))
    return None


def extract_education(text: str) -> list[str]:
    """Extract education-related keywords."""
    degrees = [
        "ph.d", "phd", "doctorate", "master", "mba", "m.s.", "ms",
        "m.tech", "mtech", "m.sc", "msc", "bachelor", "b.s.", "bs",
        "b.tech", "btech", "b.sc", "bsc", "b.e.", "be", "diploma",
        "associate", "b.a.", "ba", "m.a.", "ma", "b.com", "m.com",
        "bca", "mca", "b.ed", "m.ed",
    ]
    text_lower = text.lower()
    found = []
    for deg in degrees:
        if deg in text_lower:
            found.append(deg.upper())
    return list(dict.fromkeys(found))


def extract_email(text: str) -> str | None:
    match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    match = re.search(r"[\+]?[\d\s\-().]{7,15}", text)
    return match.group(0).strip() if match else None


def extract_name_heuristic(text: str) -> str:
    """Extract candidate name – first non-empty line as heuristic."""
    for line in text.split("\n"):
        line = line.strip()
        if line and len(line) < 60 and not re.search(r"@|http|www|\d{5,}", line):
            return line
    return "Unknown Candidate"


# ---------------------------------------------------------------------------
# Scoring engine
# ---------------------------------------------------------------------------
def compute_tfidf_score(job_text: str, resume_text: str) -> float:
    """Cosine similarity between JD and resume using TF-IDF."""
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    try:
        vectors = vectorizer.fit_transform([clean_text(job_text), clean_text(resume_text)])
        score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
        return round(float(score), 4)
    except Exception:
        return 0.0


def compute_skill_match_score(jd_skills: list[str], resume_skills: list[str]) -> dict:
    """Compute skill overlap metrics."""
    jd_set = set(s.lower() for s in jd_skills)
    resume_set = set(s.lower() for s in resume_skills)

    if not jd_set:
        return {"matched": [], "missing": [], "extra": list(resume_set), "score": 0.0}

    matched = jd_set & resume_set
    missing = jd_set - resume_set
    extra = resume_set - jd_set
    score = len(matched) / len(jd_set) if jd_set else 0.0

    return {
        "matched": sorted(matched),
        "missing": sorted(missing),
        "extra": sorted(extra),
        "score": round(score, 4),
    }


def generate_suggestions(
    skill_info: dict,
    resume_education: list[str],
    resume_experience: int | None,
    jd_text: str,
) -> list[str]:
    """Generate actionable improvement suggestions for the resume."""
    suggestions = []

    # Missing skills
    if skill_info["missing"]:
        top_missing = skill_info["missing"][:8]
        suggestions.append(
            f"🔧 **Add missing key skills**: {', '.join(top_missing)}. "
            f"Highlight relevant projects or certifications that demonstrate these skills."
        )

    # Skill match threshold
    if skill_info["score"] < 0.3:
        suggestions.append(
            "⚠️ **Low skill alignment** — Your resume matches fewer than 30% of the "
            "required skills. Consider tailoring your resume specifically for this role."
        )
    elif skill_info["score"] < 0.6:
        suggestions.append(
            "📈 **Moderate skill alignment** — You match some required skills. "
            "Add projects or experience descriptions that showcase the missing ones."
        )

    # Experience
    jd_lower = jd_text.lower()
    jd_exp = extract_experience_years(jd_text)
    if jd_exp and resume_experience is not None:
        if resume_experience < jd_exp:
            suggestions.append(
                f"📅 **Experience gap**: The JD asks for {jd_exp}+ years but your resume "
                f"shows ~{resume_experience} years. Emphasise freelance, open-source, or "
                f"internship work to bridge the gap."
            )

    # Education
    edu_keywords = ["bachelor", "master", "phd", "degree", "b.tech", "m.tech", "mba"]
    jd_needs_degree = any(kw in jd_lower for kw in edu_keywords)
    if jd_needs_degree and not resume_education:
        suggestions.append(
            "🎓 **Education section** — The JD mentions degree requirements. "
            "Ensure your education section is clearly visible with degree names and institutions."
        )

    # Quantifiable achievements
    suggestions.append(
        "📊 **Quantify achievements** — Use numbers (e.g., 'Reduced load time by 40%', "
        "'Managed a team of 8') to make your impact concrete."
    )

    # ATS optimisation
    suggestions.append(
        "🤖 **ATS optimisation** — Use standard section headings (Experience, Education, "
        "Skills) and avoid tables/columns that ATS parsers may misread."
    )

    # Keywords
    if skill_info["missing"]:
        suggestions.append(
            "🔑 **Keyword density** — Naturally weave missing keywords into your "
            "work-experience bullet points rather than listing them in isolation."
        )

    return suggestions


def rank_resumes(job_description: str, resumes: list[dict]) -> list[dict]:
    """
    Main ranking pipeline.
    Each resume dict: {"filename": str, "text": str}
    Returns list sorted by overall_score descending.
    """
    jd_skills = extract_skills(job_description)
    results = []

    for resume in resumes:
        text = resume["text"]
        filename = resume["filename"]

        if not text.strip():
            results.append({
                "filename": filename,
                "name": "Unknown Candidate",
                "email": None,
                "phone": None,
                "overall_score": 0,
                "tfidf_score": 0,
                "skill_score": 0,
                "skills_matched": [],
                "skills_missing": [],
                "skills_extra": [],
                "education": [],
                "experience_years": None,
                "suggestions": ["❌ Could not extract text from this file. Please ensure the file is not image-based or corrupted."],
            })
            continue

        # Extraction
        resume_skills = extract_skills(text)
        education = extract_education(text)
        experience = extract_experience_years(text)
        name = extract_name_heuristic(text)
        email = extract_email(text)
        phone = extract_phone(text)

        # Scoring
        tfidf_score = compute_tfidf_score(job_description, text)
        skill_info = compute_skill_match_score(jd_skills, resume_skills)

        # Weighted overall score (0-100)
        overall = round(
            (tfidf_score * 0.40 + skill_info["score"] * 0.60) * 100, 1
        )

        # Suggestions
        suggestions = generate_suggestions(skill_info, education, experience, job_description)

        results.append({
            "filename": filename,
            "name": name,
            "email": email,
            "phone": phone,
            "overall_score": overall,
            "tfidf_score": round(tfidf_score * 100, 1),
            "skill_score": round(skill_info["score"] * 100, 1),
            "skills_matched": skill_info["matched"],
            "skills_missing": skill_info["missing"],
            "skills_extra": skill_info["extra"],
            "education": education,
            "experience_years": experience,
            "suggestions": suggestions,
        })

    results.sort(key=lambda r: r["overall_score"], reverse=True)

    # Assign ranks
    for i, r in enumerate(results, 1):
        r["rank"] = i

    return results


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    """Receive JD + resumes, return ranked results as JSON."""
    job_description = request.form.get("job_description", "").strip()
    if not job_description:
        return jsonify({"error": "Please provide a job description."}), 400

    files = request.files.getlist("resumes")
    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "Please upload at least one resume."}), 400

    resumes = []

    for file in files:
     if file and file.filename and allowed_file(file.filename):

        filename = secure_filename(file.filename)

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(filename)[1]
        ) as temp_file:
            file.save(temp_file.name)
            filepath = temp_file.name

        try:
            text = extract_text(filepath)

            resumes.append({
                "filename": filename,
                "text": text
            })

        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
                pass

    if not resumes:
        return jsonify({"error": "No valid files uploaded. Supported formats: PDF, DOCX, TXT."}), 400

    results = rank_resumes(job_description, resumes)
    jd_skills = extract_skills(job_description)

    return jsonify({
        "success": True,
        "jd_skills": jd_skills,
        "total_resumes": len(results),
        "results": results,
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
# if __name__ == "__main__":
#     app.run(debug=True, port=5000)

if __name__ == "__main__":
    app.run(debug=True)


    #For web browser
# if __name__ == "__main__":
#     import webbrowser
#     from threading import Timer

#     url = "http://127.0.0.1:5000"

#     Timer(1, lambda: webbrowser.open(url)).start()

#     app.run(debug=True, use_reloader=False)

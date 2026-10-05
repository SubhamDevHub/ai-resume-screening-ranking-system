# 🤖 AI Resume Screening & Ranking System

An intelligent, AI-powered web application that reads job descriptions, accepts multiple resumes, ranks them by relevance, and provides actionable suggestions to improve each resume for the target role.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)
![NLP](https://img.shields.io/badge/NLP-scikit--learn-F7931E?logo=scikit-learn&logoColor=white)

---

## ✨ Features

- **📄 Multi-format Resume Parsing** — Supports PDF, DOCX, and TXT files
- **🧠 NLP-based Matching** — TF-IDF vectorization + cosine similarity for semantic matching
- **🏷️ Smart Skill Extraction** — Detects 150+ technical and soft skills automatically
- **📊 Dual Scoring** — Weighted combination of content similarity (40%) and skill match (60%)
- **🏆 Auto-Ranking** — Candidates ranked from best to worst match
- **💡 Improvement Suggestions** — AI-generated, actionable resume improvement tips
- **🎨 Premium Dark UI** — Glassmorphism design with smooth animations

---

## 🗂️ Project Structure

```
AI Resume Screening & Ranking System/
├── app.py                  # Main Flask application (backend + NLP engine)
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── templates/
│   └── index.html          # Frontend HTML template
├── static/
│   ├── css/
│   │   └── style.css       # Premium dark-mode design system
│   └── js/
│       └── app.js          # Frontend JavaScript logic
└── uploads/                # Temporary file uploads (auto-created)
```

---

## 🚀 How to Run

### Prerequisites

- **Python 3.10+** installed ([Download Python](https://www.python.org/downloads/))
- **pip** (comes with Python)

### Step-by-Step Setup

#### 1. Open Terminal / Command Prompt

Navigate to the project folder:

```bash
cd "C:\Users\Subham\OneDrive\Desktop\AI Resume Screening & Ranking System"
```

#### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
```

#### 3. Activate the Virtual Environment

**Windows (CMD):**
```bash
venv\Scripts\activate
```

**Windows (PowerShell):**
```bash
.\venv\Scripts\Activate.ps1
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

#### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 5. Download the spaCy English model (Optional, for enhanced NLP)

```bash
python -m spacy download en_core_web_sm
```

#### 6. Run the Application

```bash
python app.py
```

#### 7. Open in Browser

Visit: **http://127.0.0.1:5000**

---

## 📦 Packages Used

| Package | Version | Purpose |
|---|---|---|
| **Flask** | 3.0.3 | Web framework for the backend server |
| **PyPDF2** | 3.0.1 | PDF text extraction (fallback) |
| **pdfplumber** | 0.11.4 | Advanced PDF text extraction |
| **python-docx** | 1.1.2 | DOCX file parsing |
| **scikit-learn** | 1.5.2 | TF-IDF vectorization & cosine similarity |
| **nltk** | 3.9.1 | Tokenization, stopwords, POS tagging |
| **spacy** | 3.7.6 | NLP pipeline (optional, for entity extraction) |
| **Werkzeug** | 3.0.4 | Secure file upload handling |

---

## 🧠 How the AI Scoring Works

### 1. Text Extraction
Resumes are parsed from PDF/DOCX/TXT into plain text using `pdfplumber` (primary) and `PyPDF2` (fallback).

### 2. Skill Extraction
A curated database of 150+ skills across 6 categories (programming, frameworks, databases, cloud/DevOps, AI/ML, soft skills) is matched against both the JD and each resume.

### 3. TF-IDF + Cosine Similarity (40% weight)
Both documents are vectorised using TF-IDF (Term Frequency–Inverse Document Frequency), and cosine similarity measures semantic overlap.

### 4. Skill Match Score (60% weight)
The percentage of JD-required skills found in the resume.

### 5. Final Score
```
Overall Score = (TF-IDF Score × 0.40) + (Skill Match Score × 0.60) × 100
```

### 6. Suggestions
The engine generates tailored improvement advice based on:
- Missing skills gap
- Experience year requirements
- Education requirements
- ATS optimisation tips
- Quantifiable achievement recommendations

---

## 📸 Usage

1. **Paste** the full job description in the left panel
2. **Upload** one or more resumes (PDF, DOCX, or TXT)
3. Click **"Analyze & Rank Resumes"**
4. View ranked results with scores, skill analysis, and suggestions
5. Click **"View Details"** on any card for full breakdown

---

## 📝 License

This project is for educational and personal use.

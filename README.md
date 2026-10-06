# Job Description & Resume Matcher

A Flask web app that ranks a batch of resumes against a job description using TF-IDF and cosine similarity, with user accounts and match history.

## Overview

Recruiters and hiring teams often need to quickly shortlist candidates from a pile of resumes against a specific job description. This app automates that first pass: upload a job description and a set of resumes, and it returns the top 5 best-matching resumes with similarity scores.

## Features

- **User authentication** — registration and login with hashed passwords (Werkzeug), session-based auth
- **Resume upload & parsing** — accepts PDF, DOCX, and TXT resumes; extracts raw text from each using `PyPDF2` and `docx2txt`
- **Resume matching** — vectorizes the job description and all uploaded resumes with TF-IDF (`scikit-learn`), ranks resumes by cosine similarity to the job description
- **Top-5 results** — returns the 5 highest-scoring resumes with similarity percentages
- **Match history** — every match run is saved to MongoDB per user and can be reviewed later

## Tech Stack

| Component | Technology |
|---|---|
| Backend | Flask (Python) |
| Text matching | scikit-learn (TF-IDF + cosine similarity) |
| Resume parsing | PyPDF2 (PDF), docx2txt (DOCX) |
| Database | MongoDB (`pymongo`) |
| Auth | Werkzeug password hashing, Flask sessions |
| Frontend | Flask templates (Jinja2/HTML) |

## How It Works

```
Job Description + Resumes (PDF/DOCX/TXT)
        ↓
   Text Extraction
        ↓
   TF-IDF Vectorization
        ↓
   Cosine Similarity (JD vs. each resume)
        ↓
   Rank & Select Top 5
        ↓
   Display Results + Save to MongoDB History
```

## Project Structure

```
.
├── main.py                 # Flask app: routes, auth, matching logic
├── templates/
│   ├── login.html
│   ├── register.html
│   └── matchresume.html
├── uploads/                 # Uploaded resumes are stored here
└── requirements.txt
```

## Setup

### Prerequisites
- Python 3.x
- MongoDB running locally on the default port (`mongodb://127.0.0.1:27017/`)

### Installation

```bash
pip install flask pymongo docx2txt PyPDF2 scikit-learn werkzeug
```

### Run

```bash
python main.py
```

The app starts on `http://127.0.0.1:5000/`.

## Usage

1. Register for an account (or log in if you already have one)
2. Go to the match page, paste in a job description, and upload one or more resumes (PDF/DOCX/TXT)
3. Submit — the app returns the top 5 matching resumes ranked by similarity score
4. View past matches under the history page

## Known Limitations

- **Pure TF-IDF matching** — similarity is based on word-frequency overlap, not semantic meaning, so it can miss resumes that are a strong fit but use different terminology than the job description
- **No resume-section awareness** — the entire resume text is matched as one block, without distinguishing skills, experience, or education sections
- **Local MongoDB dependency** — requires a locally running MongoDB instance; not yet configured for a hosted/cloud database
- **Secret key is hardcoded** — `app.secret_key` should be moved to an environment variable before any real deployment

## Possible Improvements

- Replace TF-IDF with semantic embeddings (e.g. sentence-transformers) for meaning-based matching rather than keyword overlap
- Parse resumes into structured sections (skills, experience, education) for more targeted scoring
- Add configurable similarity thresholds and adjustable top-N result count
- Move secrets and DB connection strings to environment variables

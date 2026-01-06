from flask import Flask, request, render_template, redirect, url_for, session
import os
import docx2txt
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pymongo import MongoClient
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.secret_key = 'your_secret_key'  # Change this to a strong secret!

# -----------------------------
# MongoDB Connection
# -----------------------------
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["IMS"]                  # Database name
collection = db["match_results"]   # Collection name
user_collection = db["users"]      # User collection
print("✅ MongoDB Connected Successfully!")

# -----------------------------
# Resume text extraction
# -----------------------------
def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text

def extract_text_from_docx(file_path):
    return docx2txt.process(file_path)

def extract_text_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def extract_text(file_path):
    if file_path.endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith('.docx'):
        return extract_text_from_docx(file_path)
    elif file_path.endswith('.txt'):
        return extract_text_from_txt(file_path)
    else:
        return ""

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    if 'user' in session:
        return redirect(url_for('matchresume'))
    return redirect(url_for('login'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"]
        if user_collection.find_one({'username': username}):
            return render_template("register.html", message="Username already exists. Try another.")
        hashed = generate_password_hash(password)
        user_collection.insert_one({"username": username, "password": hashed})
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"]
        user = user_collection.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['user'] = username
            return redirect(url_for("matchresume"))
        return render_template("login.html", message="Invalid username or password.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/matchresume")
def matchresume():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('matchresume.html')  # singular file name used here

@app.route('/matcher', methods=['POST'])
def matcher():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        job_description = request.form['job_description']
        resume_files = request.files.getlist('resumes')

        resumes = []
        for resume_file in resume_files:
            filename = os.path.join(app.config['UPLOAD_FOLDER'], resume_file.filename)
            resume_file.save(filename)
            resumes.append(extract_text(filename))

        if not resumes or not job_description:
            return render_template('matchresume.html', message="Please upload resumes and enter a job description.")

        # Vectorize job description and resumes
        vectorizer = TfidfVectorizer().fit_transform([job_description] + resumes)
        vectors = vectorizer.toarray()

        # Calculate cosine similarities
        job_vector = vectors[0]
        resume_vectors = vectors[1:]
        similarities = cosine_similarity([job_vector], resume_vectors)[0]

        # Get top 5 resumes
        top_indices = similarities.argsort()[-5:][::-1]
        top_resumes = [resume_files[i].filename for i in top_indices]
        similarity_scores = [round(similarities[i] * 100, 2) for i in top_indices]

        # Store results in MongoDB
        record = {
            "username": session['user'],
            "job_description": job_description,
            "results": [
                {"resume_name": top_resumes[i], "similarity": similarity_scores[i]}
                for i in range(len(top_resumes))
            ],
            "timestamp": datetime.now()
        }
        collection.insert_one(record)

        similarity_scores_display = [f"{score}%" for score in similarity_scores]

        return render_template(
            'matchresume.html',  # singular here also
            message="Top matching resumes:",
            top_resumes=top_resumes,
            similarity_scores=similarity_scores_display
        )

    return render_template('matchresume.html')

@app.route("/history")
def history():
    if 'user' not in session:
        return redirect(url_for('login'))
    records = list(collection.find({"username": session["user"]}).sort("timestamp", -1))
    return render_template("history.html", records=records)

# -----------------------------
# Run the Flask app
# -----------------------------
if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)

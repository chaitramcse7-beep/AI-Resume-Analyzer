import streamlit as st
import PyPDF2
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Career Assistant", layout="wide")

# ---------------- UI STYLE ----------------
st.markdown("""
    <style>
    .title { text-align: center; font-size: 40px; font-weight: 600; }
    .subtitle { text-align: center; color: gray; margin-bottom: 25px; }
    .card {
        padding: 20px;
        border-radius: 10px;
        background-color: #f9f9f9;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown('<div class="title">AI Career Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Resume Analysis • Career Matching • Skill Growth</div>', unsafe_allow_html=True)

st.divider()

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

# ---------------- LOAD DATA ----------------
jobs_df = pd.read_csv("data/jobs.csv")
courses_df = pd.read_csv("data/courses.csv")

# ---------------- FUNCTIONS ----------------
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    return text

def extract_text(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()
    return clean_text(text)

# ---------------- MAIN ----------------
if uploaded_file:
    st.divider()

    resume_text = extract_text(uploaded_file)

    vectorizer = TfidfVectorizer(stop_words='english')
    scores = []

    for _, row in jobs_df.iterrows():
        role = row["role"]
        skills = row["skills"]

        vectors = vectorizer.fit_transform([resume_text, skills])
        similarity = cosine_similarity(vectors[0], vectors[1])[0][0]

        scores.append((role, similarity, skills))

    top_jobs = sorted(scores, key=lambda x: x[1], reverse=True)[:3]

    # ---------------- SUMMARY ----------------
    st.subheader("Profile Summary")

    best_role, best_score, best_skills = top_jobs[0]

    st.markdown(f"""
    <div class="card">
    <b>Best Matched Role:</b> {best_role} <br>
    <b>Match Confidence:</b> {round(best_score*100,2)}%
    </div>
    """, unsafe_allow_html=True)

    st.progress(int(best_score * 100))

    # ---------------- JOB MATCHES ----------------
    st.subheader("Top Career Matches")

    cols = st.columns(3)

    for i, (role, score, _) in enumerate(top_jobs):
        with cols[i]:
            st.markdown(f"""
            <div class="card">
            <b>{role}</b><br>
            Match: {round(score*100,2)}%
            </div>
            """, unsafe_allow_html=True)

    # ---------------- SKILLS ----------------
    job_words = set(best_skills.split())
    resume_words = set(resume_text.split())

    matched = job_words.intersection(resume_words)
    missing = job_words - resume_words

    st.subheader("Skill Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='card'><b>Matched Skills</b><br>" +
                    (", ".join(matched) if matched else "None") +
                    "</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='card'><b>Skill Gaps</b><br>" +
                    (", ".join(missing) if missing else "None") +
                    "</div>", unsafe_allow_html=True)

    # ---------------- COURSES ----------------
    st.subheader("Recommended Learning")

    rec_courses = []

    for skill in list(missing)[:3]:
        filtered = courses_df[courses_df["skill"].str.contains(skill, case=False, na=False)]
        rec_courses.append(filtered)

    if rec_courses:
        result = pd.concat(rec_courses).drop_duplicates().head(3)

        for _, row in result.iterrows():
            st.markdown(f"""
            <div class="card">
            <b>{row['course_name']}</b><br>
            Type: {row['type']} <br>
            <a href="{row['link']}" target="_blank">View Course</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("No direct course matches found.")

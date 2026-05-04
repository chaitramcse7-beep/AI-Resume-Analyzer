import streamlit as st
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Page Config
st.set_page_config(page_title="AI Career Assistant", layout="wide")

# Styling
st.markdown("""
    <style>
    .title { text-align: center; font-size: 36px; font-weight: bold; }
    .subtitle { text-align: center; color: gray; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="title">AI Career Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Resume Analysis | Job Recommendations | Skill Improvement</div>', unsafe_allow_html=True)

st.divider()

# Upload
st.subheader("Upload Resume")
uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

# Job Data (IT + Non-IT)
job_data = {
    "Data Scientist": "python machine learning statistics data analysis pandas numpy",
    "Web Developer": "html css javascript react node web development",
    "AI Engineer": "python deep learning nlp tensorflow pytorch",
    "HR Manager": "recruitment communication leadership employee relations hiring",
    "Marketing Executive": "seo content marketing branding social media advertising",
    "Business Analyst": "excel sql data visualization business analysis communication",
    "Financial Analyst": "finance accounting excel forecasting analysis reporting",
    "Sales Executive": "sales negotiation communication crm client relationship"
}

# Course Data
course_data = {
    "python": [
        ("Python for Everybody (Free)", "https://www.coursera.org/specializations/python"),
        ("Complete Python Bootcamp (Paid)", "https://www.udemy.com/course/complete-python-bootcamp/")
    ],
    "machine learning": [
        ("Machine Learning by Andrew Ng (Free)", "https://www.coursera.org/learn/machine-learning"),
        ("ML A-Z Course (Paid)", "https://www.udemy.com/course/machinelearning/")
    ],
    "sql": [
        ("SQL for Data Science (Free)", "https://www.coursera.org/learn/sql-for-data-science"),
        ("SQL Bootcamp (Paid)", "https://www.udemy.com/course/the-complete-sql-bootcamp/")
    ],
    "excel": [
        ("Excel Skills for Business (Free)", "https://www.coursera.org/specializations/excel"),
        ("Advanced Excel Course (Paid)", "https://www.udemy.com/course/excel-from-beginner-to-advanced/")
    ],
    "communication": [
        ("Improving Communication Skills (Free)", "https://www.coursera.org/learn/wharton-communication-skills"),
        ("Business Communication (Paid)", "https://www.udemy.com/course/business-communication-skills/")
    ],
    "marketing": [
        ("Digital Marketing (Free)", "https://www.coursera.org/specializations/digital-marketing"),
        ("Marketing Masterclass (Paid)", "https://www.udemy.com/course/marketing-masterclass/")
    ],
    "react": [
        ("Frontend Development with React (Free)", "https://www.coursera.org/learn/frontend-react"),
        ("React Complete Guide (Paid)", "https://www.udemy.com/course/react-the-complete-guide-incl-redux/")
    ]
}

# Extract PDF
def extract_text(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()
    return text.lower()

# Main Logic
if uploaded_file:
    st.divider()
    st.subheader("Analysis Results")

    resume_text = extract_text(uploaded_file)

    vectorizer = TfidfVectorizer()

    # --- JOB MATCHING ---
    scores = []

    for role, desc in job_data.items():
        vectors = vectorizer.fit_transform([resume_text, desc])
        similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
        scores.append((role, similarity))

    top_jobs = sorted(scores, key=lambda x: x[1], reverse=True)[:3]

    # Show Top Roles
    st.subheader("Top Career Matches")

    for role, score in top_jobs:
        st.write(f"{role} — Match: {round(score*100,2)}%")

    # --- SKILL ANALYSIS (use best role) ---
    best_role = top_jobs[0][0]
    job_words = set(job_data[best_role].split())
    resume_words = set(resume_text.split())

    matched_skills = job_words.intersection(resume_words)
    missing_skills = job_words - resume_words

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Matched Skills")
        st.write(", ".join(matched_skills) if matched_skills else "None")

    with col2:
        st.subheader("Missing Skills")
        st.write(", ".join(missing_skills) if missing_skills else "None")

    # --- COURSE RECOMMENDATION ---
    st.divider()
    st.subheader("Recommended Courses")

    recommended_courses = []
    used = set()

    for skill in list(missing_skills)[:3]:
        for key in course_data:
            if key in skill and key not in used:
                recommended_courses.extend(course_data[key])
                used.add(key)

    if recommended_courses:
        for course in recommended_courses[:3]:
            name, link = course
            st.markdown(f"- [{name}]({link})")
    else:
        st.write("No specific courses found. Improve general skills.")
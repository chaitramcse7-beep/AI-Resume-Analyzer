import streamlit as st
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title="AI Resume Analyzer", layout="centered")

st.markdown("<h1 style='text-align: center;'>📄 AI Resume Analyzer</h1>", unsafe_allow_html=True)
st.markdown("Upload your resume and check job match")

uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

job_desc = st.selectbox("Select Job Role", [
    "Data Scientist",
    "Web Developer",
    "AI Engineer"
])

job_descriptions = {
    "Data Scientist": "python machine learning data analysis statistics pandas numpy",
    "Web Developer": "html css javascript react node web development",
    "AI Engineer": "python deep learning nlp tensorflow pytorch"
}

def extract_text(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()
    return text

if uploaded_file:
    resume_text = extract_text(uploaded_file)

    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([resume_text, job_descriptions[job_desc]])

    similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
    score = round(similarity * 100, 2)

    st.subheader(f"Match Score: {score}%")
    st.progress(int(score))

    if score < 50:
        st.error("Needs improvement")
    else:
        st.success("Good match")

    resume_words = set(resume_text.lower().split())
    job_words = set(job_descriptions[job_desc].split())

    missing_skills = job_words - resume_words

    st.subheader("Missing Skills:")
    if missing_skills:
        st.write(", ".join(missing_skills))
    else:
        st.write("You have all key skills!")
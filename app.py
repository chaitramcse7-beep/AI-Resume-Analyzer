import streamlit as st
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Page Config
st.set_page_config(page_title="AI Career Assistant", layout="wide")

# Custom Styling
st.markdown("""
    <style>
    .title {
        text-align: center;
        font-size: 36px;
        font-weight: bold;
    }
    .subtitle {
        text-align: center;
        color: gray;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="title">AI Career Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Resume Analysis | Job Recommendations | Skill Improvement</div>', unsafe_allow_html=True)

st.divider()

# Layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("Upload Resume")
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

with col2:
    st.subheader("Target Job Role")
    job_desc = st.selectbox("Select Role", [
        "Data Scientist",
        "Web Developer",
        "AI Engineer",
        "HR Manager",
        "Marketing Executive"
    ])

# Job Descriptions
job_descriptions = {
    "Data Scientist": "python machine learning data analysis statistics pandas numpy",
    "Web Developer": "html css javascript react node web development",
    "AI Engineer": "python deep learning nlp tensorflow pytorch",
    "HR Manager": "communication recruitment leadership employee relations",
    "Marketing Executive": "seo content marketing social media branding"
}

# Extract text from PDF
def extract_text(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()
    return text

# Main Logic
if uploaded_file:
    st.divider()
    st.subheader("Analysis Results")

    resume_text = extract_text(uploaded_file)

    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([resume_text, job_descriptions[job_desc]])

    similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
    score = round(similarity * 100, 2)

    # Score
    st.metric(label="Match Score", value=f"{score}%")
    st.progress(int(score))

    # Skill Comparison
    resume_words = set(resume_text.lower().split())
    job_words = set(job_descriptions[job_desc].split())

    matched_skills = job_words.intersection(resume_words)
    missing_skills = job_words - resume_words

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Matched Skills")
        st.write(", ".join(matched_skills) if matched_skills else "None")

    with col4:
        st.subheader("Missing Skills")
        st.write(", ".join(missing_skills) if missing_skills else "None")

    # Suggestion
    if missing_skills:
        st.info("Recommended skills to improve: " + ", ".join(missing_skills))
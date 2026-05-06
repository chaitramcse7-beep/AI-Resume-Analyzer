import streamlit as st
import PyPDF2
import json
import requests
import os
from google import genai

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- CONFIG ----------------
st.set_page_config(page_title="ResumeAI", layout="wide")

client = genai.Client(api_key="AIzaSyB1g24xp3LOlic_e_BR3JJ0rRooJ2jLuGM")

# ---------------- UI ----------------
st.markdown("""
<style>
.stApp { background: #0f172a; color: white; }
.card {
    background: #111827;
    padding: 18px;
    border-radius: 12px;
    margin-bottom: 15px;
}
.tag {
    display:inline-block;
    background:#1f2937;
    padding:6px 10px;
    border-radius:8px;
    margin:4px;
    font-size:13px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOGIN ----------------
st.sidebar.title("Login")
email = st.sidebar.text_input("Enter Email")
login = st.sidebar.button("Login")

if login and email:
    st.session_state["user"] = email

if "user" not in st.session_state:
    st.warning("Please login to continue")
    st.stop()

st.sidebar.success(f"Logged in as {st.session_state['user']}")


# ---------------- NAVIGATION ----------------
st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Go to",
    ["Analyze Resume", "History", "Profile"]
)


# ---------------- FUNCTIONS ----------------

def extract_text(file):
    reader = PyPDF2.PdfReader(file)
    return "".join([p.extract_text() or "" for p in reader.pages])


def analyze_resume(text):
    prompt = f"""
    Return JSON:
    {{
        "name": "",
        "email": "",
        "experience": "",
        "summary": "",
        "technical_skills": [],
        "soft_skills": [],
        "top_roles": [
            {{
                "role": "",
                "match_percentage": "",
                "reason": "",
                "skill_gaps": []
            }}
        ]
    }}

    Resume:
    {text[:6000]}
    """

    try:
        res = client.models.generate_content(
            model="models/gemini-flash-latest",
            contents=prompt
        )
        raw = res.text.replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except:
        return {}


def analyze_ats(resume, jd):
    if not jd:
        return None

    prompt = f"""
    Compare resume with job description.

    Return JSON:
    {{
        "ats_score": "",
        "matched_keywords": [],
        "missing_keywords": [],
        "suggestions": []
    }}

    Resume:
    {resume[:4000]}

    JD:
    {jd[:4000]}
    """

    try:
        res = client.models.generate_content(
            model="models/gemini-flash-latest",
            contents=prompt
        )
        raw = res.text.replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except:
        return None


def fetch_jobs(role):
    url = "https://jsearch.p.rapidapi.com/search"

    headers = {
        "X-RapidAPI-Key": "7ac3737f0emshfefa978e5b48b97p1685b1jsnf106843c1eeb",
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }

    params = {
        "query": f"{role} jobs in India",
        "page": "1",
        "num_pages": "1"
    }

    try:
        res = requests.get(url, headers=headers, params=params)
        data = res.json()

        jobs = []
        fallback_jobs = []

        for j in data.get("data", []):
            country = (j.get("job_country") or "").lower()

            job_data = {
                "title": j.get("job_title"),
                "company": j.get("employer_name"),
                "location": j.get("job_city") or "India",
                "link": j.get("job_apply_link")
            }

            # Save all jobs
            fallback_jobs.append(job_data)

            # Prefer India jobs
            if "india" in country or country == "in":
                jobs.append(job_data)

            if len(jobs) == 3:
                break

        # ✅ If India filter failed → fallback
        if not jobs:
            jobs = fallback_jobs[:3]

        # ✅ Final fallback (guaranteed UI never empty)
        if not jobs:
            jobs = [{
                "title": f"{role} Jobs",
                "company": "LinkedIn",
                "location": "India",
                "link": f"https://www.linkedin.com/jobs/search/?keywords={role.replace(' ','%20')}&location=India"
            }]

        return jobs

    except Exception as e:
        return [{
            "title": f"{role} Jobs",
            "company": "LinkedIn",
            "location": "India",
            "link": f"https://www.linkedin.com/jobs/search/?keywords={role.replace(' ','%20')}&location=India"
        }]
def fetch_courses(role):
    q = role.replace(" ", "+")
    return [
        {"name": f"{role} - Coursera", "link": f"https://www.coursera.org/search?query={q}"},
        {"name": f"{role} - Udemy", "link": f"https://www.udemy.com/courses/search/?q={q}"},
        {"name": f"{role} - edX", "link": f"https://www.edx.org/search?q={q}"}
    ]


def save_history(user, data):
    file = "history.json"

    if os.path.exists(file):
        with open(file) as f:
            hist = json.load(f)
    else:
        hist = {}

    hist.setdefault(user, []).append(data)

    with open(file, "w") as f:
        json.dump(hist, f)


def load_history(user):
    if not os.path.exists("history.json"):
        return []
    with open("history.json") as f:
        return json.load(f).get(user, [])


def generate_pdf(data):
    file = "report.pdf"
    doc = SimpleDocTemplate(file)
    styles = getSampleStyleSheet()

    content = []

    content.append(Paragraph(f"Name: {data.get('name','')}", styles["Normal"]))
    content.append(Spacer(1,10))
    content.append(Paragraph(f"Summary: {data.get('summary','')}", styles["Normal"]))

    doc.build(content)
    return file

def show_skeleton():
    st.markdown("""
    <style>
    .skeleton {
        background: linear-gradient(90deg, #1f2937 25%, #374151 50%, #1f2937 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
        height: 20px;
        border-radius: 6px;
        margin-bottom: 10px;
    }

    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)

    for _ in range(8):
        st.markdown('<div class="skeleton"></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- SIDEBAR HISTORY ----------------
    st.sidebar.subheader("Recent History")
    recent = load_history(st.session_state["user"])[-5:]

    if not recent:
        st.sidebar.write("No history yet")
    else:
        for i, h in enumerate(recent[::-1]):
            st.sidebar.write(f"{i+1}. {h.get('name','Unknown')}")

    
# ---------------- MAIN ----------------

if page == "Analyze Resume":

    st.title("ResumeAI — AI Resume Intelligence")

    uploaded = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
    jd = st.text_area("Paste Job Description (for ATS Score)")

    if uploaded:
        text = extract_text(uploaded)

        progress = st.progress(0, text="Starting analysis...")

        show_skeleton()

        progress.progress(20, text="Reading resume...")
        data = analyze_resume(text)

        progress.progress(60, text="Running ATS analysis...")
        ats = analyze_ats(text, jd)

        progress.progress(90, text="Fetching job data...")

        progress.progress(100, text="Done!")

        if data:
            save_history(st.session_state["user"], data)

    # PROFILE
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Profile")
        st.write(data.get("name"))
        st.write(data.get("email"))
        st.write(data.get("experience"))
        st.markdown('</div>', unsafe_allow_html=True)

    # SUMMARY
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Summary")
        st.write(data.get("summary"))
        st.markdown('</div>', unsafe_allow_html=True)

    # SKILLS
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Technical Skills")
            for s in data.get("technical_skills", []):
                st.markdown(f'<span class="tag">{s}</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Soft Skills")
            for s in data.get("soft_skills", []):
                st.markdown(f'<span class="tag">{s}</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ATS
        if ats:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("ATS Score")
            st.write(f"{ats.get('ats_score')}/100")

            st.write("Matched Keywords")
            for k in ats.get("matched_keywords", []):
                st.write("-", k)

            st.write("Missing Keywords")
            for k in ats.get("missing_keywords", []):
                st.write("-", k)

            st.write("Suggestions")
            for s in ats.get("suggestions", []):
                st.write("-", s)

            st.markdown('</div>', unsafe_allow_html=True)

    # ROLES
        st.subheader("Top Career Matches")

        for role in data.get("top_roles", []):
            if isinstance(role, dict):

                r = role.get("role")

                st.markdown('<div class="card">', unsafe_allow_html=True)

                st.markdown(f"### {r} ({role.get('match_percentage')}%)")
                st.write(role.get("reason"))

            # JOBS
                st.write("Jobs")
                for j in fetch_jobs(r):
                    st.markdown(f"""
                    **{j['title']}**  
                    {j['company']} — {j['location']}  
                    [Apply Here]({j['link']})
                    """)

            # COURSES
                st.write("Courses")
                for c in fetch_courses(r):
                    st.markdown(f"[{c['name']}]({c['link']})")

                st.markdown('</div>', unsafe_allow_html=True)

    # PDF
        if st.button("Download PDF"):
            pdf = generate_pdf(data)
            with open(pdf, "rb") as f:
                st.download_button("Download", f, "report.pdf")

elif page == "History":

    st.title("Your Resume History")

    history = load_history(st.session_state["user"])

    if not history:
        st.info("No history yet. Upload a resume first.")
    else:
        for i, h in enumerate(history[::-1]):

            st.markdown('<div class="card">', unsafe_allow_html=True)

            st.subheader(f"{i+1}. {h.get('name','Unknown')}")

            st.write("Email:", h.get("email", "N/A"))
            st.write("Experience:", h.get("experience", "N/A"))

            st.write("Summary:")
            st.write(h.get("summary", "No summary available"))

            st.markdown('</div>', unsafe_allow_html=True)


elif page == "Profile":

    st.title("User Profile")

    history = load_history(st.session_state["user"])

    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("Account Info")
    st.write("Email:", st.session_state["user"])

    st.subheader("Usage Stats")
    st.write("Total Resumes Analyzed:", len(history))

    if history:
        last = history[-1]
        st.subheader("Last Analysis")
        st.write("Name:", last.get("name", "N/A"))
        st.write("Top Role:", 
                    last.get("top_roles", [{}])[0].get("role", "N/A"))

    st.markdown('</div>', unsafe_allow_html=True)

# HISTORY
st.sidebar.subheader("Recent History")

recent_history = load_history(st.session_state["user"])[-5:]

if not recent_history:
    st.sidebar.write("No history yet")
else:
    for i, h in enumerate(recent_history[::-1]):
        st.sidebar.write(f"{i+1}. {h.get('name','Unknown')}")
    
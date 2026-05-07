import streamlit as st
import PyPDF2
import json
import requests
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from google import genai
from supabase import create_client

# ---------------- CONFIG ----------------
st.set_page_config(page_title="ResumeAI", layout="wide")
client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])


supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)


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

st.sidebar.success(
    f"Logged in as {st.session_state['user']}"
)


# ---------------- FUNCTIONS ----------------

def extract_text(file):
    reader = PyPDF2.PdfReader(file)
    return "".join([p.extract_text() or "" for p in reader.pages])


def analyze_resume(text):

    prompt = f"""
    Analyze this resume and return ONLY valid JSON.

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

    models_to_try = [
        "models/gemini-flash-latest",
        "models/gemini-2.5-flash",
        "models/gemini-2.0-flash"
    ]

    for model_name in models_to_try:

        try:

            st.write(f"Trying model: {model_name}")

            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )

            raw = response.text.strip()

            raw = raw.replace("```json", "")
            raw = raw.replace("```", "")

            data = json.loads(raw)

            return data

        except Exception as e:

            st.error(f"{model_name} failed: {e}")

    # FINAL FALLBACK
    return {
        "name": "Unable to Analyze",
        "email": "",
        "experience": "",
        "summary": "AI analysis failed. Please retry.",
        "technical_skills": [],
        "soft_skills": [],
        "top_roles": []
    }

def analyze_ats(resume_text, jd_text):
    if not jd_text:
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
    {resume_text[:4000]}

    Job Description:
    {jd_text[:4000]}
    """

    try:
        response = client.models.generate_content(
            model="models/gemini-flash-latest",
            contents=prompt
        )
        raw = response.text
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except:
        return None


def fetch_jobs(role):

    url = "https://jsearch.p.rapidapi.com/search"

    headers = {
        "X-RapidAPI-Key": st.secrets["RAPIDAPI_KEY"],
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }

    params = {
        "query": f"{role} jobs in India",
        "location": "India",
        "page": "1",
        "num_pages": "1",
        "date_posted": "all"
    }

    try:

        res = requests.get(
            url,
            headers=headers,
            params=params
        )

        data = res.json()

        jobs = []

        for j in data.get("data", []):

            country = (
                j.get("job_country") or ""
            ).lower()

            location = (
                j.get("job_location") or ""
            ).lower()

            job_data = {
                "title": j.get("job_title"),
                "company": j.get("employer_name"),
                "location": j.get("job_location") or "India",
                "link": j.get("job_apply_link")
            }

            # INDIA FILTER
            if (
                "india" in country
                or country == "in"
                or "india" in location
                or "bangalore" in location
                or "bengaluru" in location
                or "hyderabad" in location
                or "pune" in location
                or "mumbai" in location
                or "delhi" in location
                or "chennai" in location
                or "gurgaon" in location
                or "noida" in location
            ):

                jobs.append(job_data)

            if len(jobs) >= 5:
                break

        # FALLBACK
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
    query = role.replace(" ", "+")

    return [
        {"name": f"{role} - Coursera", "platform": "Coursera",
         "link": f"https://www.coursera.org/search?query={query}"},
        {"name": f"{role} - Udemy", "platform": "Udemy",
         "link": f"https://www.udemy.com/courses/search/?q={query}"},
        {"name": f"{role} - edX", "platform": "edX",
         "link": f"https://www.edx.org/search?q={query}"}
    ]

def show_skeleton():

    st.markdown("""
    <style>
    .skeleton {
        background: linear-gradient(
            90deg,
            #1f2937 25%,
            #374151 50%,
            #1f2937 75%
        );

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
        st.markdown(
            '<div class="skeleton"></div>',
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

def save_history(user, data):

    supabase.table("resume_history").insert({

        "user_email": user,

        "name": data.get("name", ""),

        "summary": data.get("summary", ""),

        "ats_score": str(data.get("ats_score", ""))

    }).execute()

    

def load_history(user):

    file = "history.json"

    if not os.path.exists(file):
        return []

    try:

        with open(file, "r") as f:

            history = json.load(f)

        return history.get(user, [])

    except:
        return []


def delete_history_item(user, item_id):

    file = "history.json"

    if not os.path.exists(file):
        return

    try:

        with open(file, "r") as f:
            history = json.load(f)

        user_history = history.get(user, [])

        updated_history = []

        for h in user_history:

            if str(h.get("id")) != str(item_id):
                updated_history.append(h)

        history[user] = updated_history

        with open(file, "w") as f:
            json.dump(history, f, indent=4)

    except:
        pass


def generate_pdf(data):

    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer
    )

    from reportlab.lib.styles import (
        getSampleStyleSheet
    )

    file_name = "ResumeAI_Report.pdf"

    doc = SimpleDocTemplate(file_name)

    styles = getSampleStyleSheet()

    content = []

    content.append(
        Paragraph(
            "<b>ResumeAI Report</b>",
            styles["Title"]
        )
    )

    content.append(Spacer(1, 20))

    content.append(
        Paragraph(
            f"<b>Name:</b> {data.get('name','')}",
            styles["BodyText"]
        )
    )

    content.append(Spacer(1, 10))

    content.append(
        Paragraph(
            f"<b>Email:</b> {data.get('email','')}",
            styles["BodyText"]
        )
    )

    content.append(Spacer(1, 10))

    content.append(
        Paragraph(
            f"<b>Summary:</b> {data.get('summary','')}",
            styles["BodyText"]
        )
    )

    content.append(Spacer(1, 20))

    content.append(
        Paragraph(
            "<b>Technical Skills</b>",
            styles["Heading2"]
        )
    )

    for skill in data.get("technical_skills", []):

        content.append(
            Paragraph(
                f"• {skill}",
                styles["BodyText"]
            )
        )

    content.append(Spacer(1, 20))

    content.append(
        Paragraph(
            "<b>Soft Skills</b>",
            styles["Heading2"]
        )
    )

    for skill in data.get("soft_skills", []):

        content.append(
            Paragraph(
                f"• {skill}",
                styles["BodyText"]
            )
        )

    content.append(Spacer(1, 20))

    content.append(
        Paragraph(
            "<b>Career Matches</b>",
            styles["Heading2"]
        )
    )

    for role in data.get("top_roles", []):

        if isinstance(role, dict):

            content.append(
                Paragraph(
                    f"• {role.get('role','')} "
                    f"({role.get('match_percentage','')}%)",
                    styles["BodyText"]
                )
            )

    doc.build(content)

    return file_name


# ---------------- MAIN ----------------

if "page" not in st.session_state:
    st.session_state["page"] = "Analyze Resume"

page = st.sidebar.radio(
    "Go to",
    ["Analyze Resume", "History", "Profile"],
    index=["Analyze Resume", "History", "Profile"].index(st.session_state["page"])
)

st.session_state["page"] = page


if page == "Analyze Resume":

    st.title("ResumeAI — AI Resume Intelligence")

    uploaded = st.file_uploader(
    "Upload Resume (PDF)",
    type=["pdf"],
    key="resume_upload_main"
)
    jd = st.text_area("Paste Job Description (Optional for ATS Score)")

    # ---------------- ANALYZE FLOW ----------------

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

    elif "selected_resume" in st.session_state:

        data = st.session_state["selected_resume"]
        ats = None

    else:
        data = None
        ats = None

    # ---------------- SHOW UI ----------------

    if data:

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
                st.markdown(
                    f'<span class="tag">{s}</span>',
                    unsafe_allow_html=True
                )

            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)

            st.subheader("Soft Skills")

            for s in data.get("soft_skills", []):
                st.markdown(
                    f'<span class="tag">{s}</span>',
                    unsafe_allow_html=True
                )

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

                st.markdown(
                    f"### {r} ({role.get('match_percentage')}%)"
                )

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

                    st.markdown(
                        f"[{c['name']}]({c['link']})"
                    )

                st.markdown('</div>', unsafe_allow_html=True)

        # PDF
        pdf = generate_pdf(data)

        with open(pdf, "rb") as f:

            pdf_bytes = f.read()

            st.download_button(
            label="📄 Download PDF Report",
            data=pdf_bytes,
            file_name="ResumeAI_Report.pdf",
            mime="application/pdf",
            use_container_width=True
            )

    else:
        st.info("Upload a resume to begin analysis.")


# ---------------- HISTORY ----------------

elif page == "History":

    st.title("Your Resume History")

    history = load_history(st.session_state["user"])

    if not history:

        st.info("No history yet.")

    else:

        for i, h in enumerate(history[::-1]):

            item_id = f"{i}_{h.get('name','resume')}"

            st.markdown('<div class="card">', unsafe_allow_html=True)

            col1, col2 = st.columns([4,1])

            with col1:

                if st.button(
                    f"{h.get('name','Unknown')}",
                    key=item_id
                ):

                    st.session_state["selected_resume"] = h
                    st.session_state["page"] = "Analyze Resume"

                    st.rerun()

            with col2:

                if st.button(
                    "🗑️",
                    key=f"delete_{i}"
                    ):

                    history.pop(len(history) - 1 - i)

                    file = "history.json"

                    with open(file, "r") as f:
                        all_history = json.load(f)

                    all_history[st.session_state["user"]] = history

                    with open(file, "w") as f:
                        json.dump(all_history, f, indent=4)

                    st.rerun()

            st.write(h.get("summary", ""))

            st.markdown('</div>', unsafe_allow_html=True)


# ---------------- PROFILE ----------------

elif page == "Profile":

    st.title("User Profile")

    history = load_history(st.session_state["user"])

    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("Account Info")

    st.write("Email:", st.session_state["user"])

    st.subheader("Usage Stats")

    st.write(
        "Total Resumes Analyzed:",
        len(history)
    )

    if history:

        last = history[-1]

        st.subheader("Last Analysis")

        st.write(
            "Name:",
            last.get("name", "N/A")
        )

        top_roles = last.get("top_roles", [])

        if top_roles and isinstance(top_roles[0], dict):

            st.write(
                "Top Role:",
                top_roles[0].get("role", "N/A")
            )

    st.markdown('</div>', unsafe_allow_html=True)
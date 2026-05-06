import google.generativeai as genai

genai.configure(api_key="AIzaSyB1g24xp3LOlic_e_BR3JJ0rRooJ2jLuGM")

for m in genai.list_models():
    print(m.name)


    def fetch_jobs(role):
    url = "https://jsearch.p.rapidapi.com/search"

    headers = {
        "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
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
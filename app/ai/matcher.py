from sentence_transformers import SentenceTransformer, util

# Don't load at import time — load on first use
_model = None

def get_model():
    global _model
    if _model is None:
        print("Loading BERT model...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        print("BERT model loaded!")
    return _model


def calculate_match(resume_text: str, job_description: str,
                    candidate_skills: list, job_skills: list) -> dict:

    if not resume_text or not job_description:
        skill_score = 0
        matched_skills = []
        missing_skills = list(job_skills)
        if job_skills and candidate_skills:
            candidate_lower = [s.lower() for s in candidate_skills]
            matched_skills = [s for s in job_skills if s.lower() in candidate_lower]
            missing_skills = [s for s in job_skills if s.lower() not in candidate_lower]
            skill_score = len(matched_skills) / len(job_skills) * 100
        return {
            "match_score": round(skill_score, 2),
            "semantic_score": 0,
            "skill_score": round(skill_score, 2),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "explanation": "Upload a resume to get full AI matching."
        }

    model = get_model()

    resume_embedding = model.encode(resume_text[:1000], convert_to_tensor=True)
    job_embedding = model.encode(job_description[:1000], convert_to_tensor=True)
    semantic_score = float(util.cos_sim(resume_embedding, job_embedding)[0][0])
    semantic_score = round(semantic_score * 100, 2)

    candidate_lower = [s.lower() for s in candidate_skills]
    matched_skills = [s for s in job_skills if s.lower() in candidate_lower]
    missing_skills = [s for s in job_skills if s.lower() not in candidate_lower]
    skill_score = (len(matched_skills) / len(job_skills) * 100) if job_skills else 0

    final_score = round((semantic_score * 0.6) + (skill_score * 0.4), 2)
    final_score = min(final_score, 100)

    explanation = generate_explanation(final_score, matched_skills, missing_skills, semantic_score)

    return {
        "match_score": final_score,
        "semantic_score": semantic_score,
        "skill_score": round(skill_score, 2),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "explanation": explanation
    }


def generate_explanation(score, matched, missing, semantic):
    if score >= 85:
        level = "Excellent match!"
    elif score >= 70:
        level = "Strong match."
    elif score >= 55:
        level = "Moderate match."
    else:
        level = "Low match."

    parts = [level]
    if matched:
        parts.append(f"You have {len(matched)} required skill(s): {', '.join(matched[:3])}{'...' if len(matched) > 3 else ''}.")
    if missing:
        parts.append(f"Missing {len(missing)} skill(s): {', '.join(missing[:3])}{'...' if len(missing) > 3 else ''}.")
    if score < 70 and missing:
        parts.append(f"Adding '{missing[0]}' could significantly boost your match.")
    return " ".join(parts)


def batch_match_jobs(resume_text: str, candidate_skills: list, jobs: list) -> list:
    if not resume_text:
        return []

    model = get_model()
    resume_embedding = model.encode(resume_text[:1000], convert_to_tensor=True)
    results = []

    for job in jobs:
        job_text = f"{job.title} {job.description}"[:1000]
        job_embedding = model.encode(job_text, convert_to_tensor=True)
        semantic_score = float(util.cos_sim(resume_embedding, job_embedding)[0][0])
        semantic_score = round(semantic_score * 100, 2)

        job_skills = job.required_skills or []
        candidate_lower = [s.lower() for s in candidate_skills]
        matched = [s for s in job_skills if s.lower() in candidate_lower]
        missing = [s for s in job_skills if s.lower() not in candidate_lower]
        skill_score = (len(matched) / len(job_skills) * 100) if job_skills else 0
        final_score = round((semantic_score * 0.6) + (skill_score * 0.4), 2)

        results.append({
            "job_id": job.id,
            "match_score": min(final_score, 100),
            "matched_skills": matched,
            "missing_skills": missing
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results
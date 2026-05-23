from sentence_transformers import SentenceTransformer, util
import torch

# Load once when server starts (takes ~30 seconds first time)
print("Loading BERT model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("BERT model loaded!")

def calculate_match(resume_text: str, job_description: str, 
                    candidate_skills: list, job_skills: list) -> dict:
    
    # 1. BERT semantic similarity (text understanding)
    resume_embedding = model.encode(resume_text, convert_to_tensor=True)
    job_embedding = model.encode(job_description, convert_to_tensor=True)
    semantic_score = float(util.cos_sim(resume_embedding, job_embedding)[0][0])
    semantic_score = round(semantic_score * 100, 2)

    # 2. Skill matching (exact + partial)
    candidate_lower = [s.lower() for s in candidate_skills]
    job_lower = [s.lower() for s in job_skills]

    matched_skills = []
    missing_skills = []

    for skill in job_skills:
        if skill.lower() in candidate_lower:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    skill_score = (len(matched_skills) / len(job_skills) * 100) if job_skills else 0

    # 3. Final weighted score
    # 60% semantic understanding + 40% skill match
    final_score = round((semantic_score * 0.6) + (skill_score * 0.4), 2)
    final_score = min(final_score, 100)

    # 4. Explanation
    explanation = generate_explanation(
        final_score, matched_skills, missing_skills, semantic_score
    )

    return {
        "match_score": final_score,
        "semantic_score": semantic_score,
        "skill_score": round(skill_score, 2),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "explanation": explanation
    }


def generate_explanation(score: float, matched: list, 
                         missing: list, semantic: float) -> str:
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
        parts.append(f"You have {len(matched)} required skill(s): "
                    f"{', '.join(matched[:3])}"
                    f"{'...' if len(matched) > 3 else ''}.")

    if missing:
        parts.append(f"Missing {len(missing)} skill(s): "
                    f"{', '.join(missing[:3])}"
                    f"{'...' if len(missing) > 3 else ''}.")

    if score < 70 and missing:
        top_missing = missing[0]
        parts.append(f"Adding '{top_missing}' could significantly boost your match.")

    return " ".join(parts)


def batch_match_jobs(resume_text: str, candidate_skills: list, 
                     jobs: list) -> list:
    """Match one resume against multiple jobs efficiently"""
    if not resume_text:
        return []

    resume_embedding = model.encode(resume_text, convert_to_tensor=True)
    results = []

    for job in jobs:
        job_text = f"{job.title} {job.description}"
        job_embedding = model.encode(job_text, convert_to_tensor=True)
        semantic_score = float(util.cos_sim(resume_embedding, job_embedding)[0][0])
        semantic_score = round(semantic_score * 100, 2)

        job_skills = job.required_skills or []
        candidate_lower = [s.lower() for s in candidate_skills]
        matched = [s for s in job_skills if s.lower() in candidate_lower]
        missing = [s for s in job_skills if s.lower() not in candidate_lower]
        skill_score = (len(matched) / len(job_skills) * 100) if job_skills else 0

        final_score = round((semantic_score * 0.6) + (skill_score * 0.4), 2)
        final_score = min(final_score, 100)

        results.append({
            "job_id": job.id,
            "match_score": final_score,
            "matched_skills": matched,
            "missing_skills": missing
        })

    # Sort by match score descending
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results
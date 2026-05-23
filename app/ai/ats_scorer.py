import re

ACTION_VERBS = [
    "developed", "built", "designed", "implemented", "created", "managed",
    "led", "improved", "optimized", "deployed", "automated", "analyzed",
    "collaborated", "delivered", "achieved", "increased", "reduced", "launched"
]

def score_resume(text: str, job_skills: list = []) -> dict:
    text_lower = text.lower()
    suggestions = []
    score = 0

    # 1. Word count check (ideal: 300-700 words)
    word_count = len(text.split())
    if 300 <= word_count <= 700:
        score += 20
    elif word_count < 300:
        suggestions.append("Resume is too short. Add more detail about your experience and projects.")
    else:
        suggestions.append("Resume is too long. Try to keep it under 700 words for ATS systems.")

    # 2. Contact info
    has_email = bool(re.search(r'\S+@\S+', text))
    has_phone = bool(re.search(r'\d{10}', text))
    if has_email:
        score += 10
    else:
        suggestions.append("Add your email address to the resume.")
    if has_phone:
        score += 10
    else:
        suggestions.append("Add your phone number to the resume.")

    # 3. Action verbs
    found_verbs = [v for v in ACTION_VERBS if v in text_lower]
    if len(found_verbs) >= 5:
        score += 20
    elif len(found_verbs) >= 2:
        score += 10
        suggestions.append("Use more action verbs like 'developed', 'led', 'optimized'.")
    else:
        suggestions.append("Your resume lacks action verbs. Start bullet points with words like 'Built', 'Designed', 'Improved'.")

    # 4. Key sections present
    sections = ["education", "experience", "skills", "project"]
    found_sections = [s for s in sections if s in text_lower]
    score += len(found_sections) * 5
    missing = [s for s in sections if s not in text_lower]
    if missing:
        suggestions.append(f"Add these missing sections: {', '.join(missing).title()}")

    # 5. Skills keyword match with job
    if job_skills:
        matched = [s for s in job_skills if s.lower() in text_lower]
        match_ratio = len(matched) / len(job_skills)
        score += int(match_ratio * 20)
        if match_ratio < 0.5:
            suggestions.append(f"Add more job-relevant keywords: {', '.join(job_skills[:5])}")

    return {
        "ats_score": min(score, 100),
        "suggestions": suggestions,
        "action_verbs_found": found_verbs,
        "word_count": word_count
    }
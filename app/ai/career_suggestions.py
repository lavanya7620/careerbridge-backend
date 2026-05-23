from sentence_transformers import SentenceTransformer, util

_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

CAREER_ROLES = [
    {
        "title": "Full Stack Developer",
        "description": "Build web applications using frontend and backend technologies",
        "key_skills": ["JavaScript", "React", "Node.js", "PostgreSQL", "REST API"],
        "avg_salary": "₹6-12 LPA",
        "growth": "High"
    },
    {
        "title": "Data Scientist",
        "description": "Analyze data, build ML models, extract business insights",
        "key_skills": ["Python", "Machine Learning", "Pandas", "SQL", "TensorFlow"],
        "avg_salary": "₹8-18 LPA",
        "growth": "Very High"
    },
    {
        "title": "DevOps Engineer",
        "description": "Manage CI/CD pipelines, cloud infrastructure, and deployments",
        "key_skills": ["Docker", "AWS", "Linux", "Git", "Kubernetes"],
        "avg_salary": "₹8-16 LPA",
        "growth": "Very High"
    },
    {
        "title": "Backend Developer",
        "description": "Design and build APIs, databases, and server-side logic",
        "key_skills": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
        "avg_salary": "₹5-12 LPA",
        "growth": "High"
    },
    {
        "title": "Frontend Developer",
        "description": "Build user interfaces with modern web technologies",
        "key_skills": ["React", "JavaScript", "TypeScript", "Tailwind", "HTML"],
        "avg_salary": "₹4-10 LPA",
        "growth": "High"
    },
    {
        "title": "Mobile App Developer",
        "description": "Build iOS and Android applications",
        "key_skills": ["Flutter", "Dart", "Firebase", "REST API", "Git"],
        "avg_salary": "₹5-12 LPA",
        "growth": "High"
    },
    {
        "title": "Machine Learning Engineer",
        "description": "Build and deploy ML models at scale",
        "key_skills": ["Python", "TensorFlow", "PyTorch", "Docker", "AWS"],
        "avg_salary": "₹10-22 LPA",
        "growth": "Very High"
    },
    {
        "title": "Cloud Engineer",
        "description": "Design and manage cloud infrastructure and services",
        "key_skills": ["AWS", "Azure", "Docker", "Kubernetes", "Linux"],
        "avg_salary": "₹8-18 LPA",
        "growth": "Very High"
    },
    {
        "title": "Cybersecurity Analyst",
        "description": "Protect systems from threats and security vulnerabilities",
        "key_skills": ["Linux", "Networking", "Python", "Security Tools", "SQL"],
        "avg_salary": "₹6-15 LPA",
        "growth": "High"
    },
    {
        "title": "Database Administrator",
        "description": "Manage, optimize and secure database systems",
        "key_skills": ["PostgreSQL", "MySQL", "MongoDB", "SQL", "Linux"],
        "avg_salary": "₹5-10 LPA",
        "growth": "Medium"
    }
]

def get_career_suggestions(candidate_skills: list, resume_text: str = "") -> list:
    if not candidate_skills and not resume_text:
        return []

    model = get_model()
    profile_text = f"Skills: {', '.join(candidate_skills)}. {resume_text[:300]}"
    profile_embedding = model.encode(profile_text, convert_to_tensor=True)

    results = []
    for role in CAREER_ROLES:
        role_text = f"{role['title']}. {role['description']}. Skills: {', '.join(role['key_skills'])}"
        role_embedding = model.encode(role_text, convert_to_tensor=True)
        semantic_score = float(util.cos_sim(profile_embedding, role_embedding)[0][0])

        candidate_lower = [s.lower() for s in candidate_skills]
        matched = [s for s in role["key_skills"] if s.lower() in candidate_lower]
        missing = [s for s in role["key_skills"] if s.lower() not in candidate_lower]
        skill_score = len(matched) / len(role["key_skills"])
        final_score = round((semantic_score * 0.5 + skill_score * 0.5) * 100, 1)

        results.append({
            "title": role["title"],
            "description": role["description"],
            "match_score": final_score,
            "matched_skills": matched,
            "missing_skills": missing,
            "key_skills": role["key_skills"],
            "avg_salary": role["avg_salary"],
            "growth": role["growth"]
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:5]
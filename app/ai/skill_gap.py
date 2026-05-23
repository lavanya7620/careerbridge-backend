COURSE_MAP = {
    "python": [
        {"title": "Python for Everybody - Coursera", "url": "https://www.coursera.org/specializations/python", "free": True},
        {"title": "Python Tutorial - W3Schools", "url": "https://www.w3schools.com/python/", "free": True},
    ],
    "javascript": [
        {"title": "JavaScript - The Odin Project", "url": "https://www.theodinproject.com/paths/foundations/courses/foundations", "free": True},
        {"title": "JavaScript Tutorial - MDN", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", "free": True},
    ],
    "react": [
        {"title": "React Official Docs", "url": "https://react.dev/learn", "free": True},
        {"title": "React Tutorial - Scrimba", "url": "https://scrimba.com/learn/learnreact", "free": True},
    ],
    "node.js": [
        {"title": "Node.js Tutorial - W3Schools", "url": "https://www.w3schools.com/nodejs/", "free": True},
        {"title": "The Odin Project - NodeJS", "url": "https://www.theodinproject.com/paths/full-stack-javascript/courses/nodejs", "free": True},
    ],
    "docker": [
        {"title": "Docker Getting Started", "url": "https://docs.docker.com/get-started/", "free": True},
        {"title": "Docker Tutorial - TechWorld with Nana (YouTube)", "url": "https://www.youtube.com/watch?v=3c-iBn73dDE", "free": True},
    ],
    "aws": [
        {"title": "AWS Free Tier + Tutorials", "url": "https://aws.amazon.com/getting-started/", "free": True},
        {"title": "AWS Cloud Practitioner - freeCodeCamp", "url": "https://www.youtube.com/watch?v=SOTamWNgDKc", "free": True},
    ],
    "machine learning": [
        {"title": "ML Crash Course - Google", "url": "https://developers.google.com/machine-learning/crash-course", "free": True},
        {"title": "Machine Learning - Andrew Ng (Coursera)", "url": "https://www.coursera.org/learn/machine-learning", "free": True},
    ],
    "sql": [
        {"title": "SQL Tutorial - W3Schools", "url": "https://www.w3schools.com/sql/", "free": True},
        {"title": "SQL for Data Science - Coursera", "url": "https://www.coursera.org/learn/sql-for-data-science", "free": True},
    ],
    "postgresql": [
        {"title": "PostgreSQL Tutorial", "url": "https://www.postgresqltutorial.com/", "free": True},
        {"title": "Learn PostgreSQL - freeCodeCamp (YouTube)", "url": "https://www.youtube.com/watch?v=qw--VYLpxG4", "free": True},
    ],
    "git": [
        {"title": "Git Tutorial - Atlassian", "url": "https://www.atlassian.com/git/tutorials", "free": True},
        {"title": "GitHub Skills", "url": "https://skills.github.com/", "free": True},
    ],
    "typescript": [
        {"title": "TypeScript Official Docs", "url": "https://www.typescriptlang.org/docs/", "free": True},
        {"title": "TypeScript Course - freeCodeCamp (YouTube)", "url": "https://www.youtube.com/watch?v=30LWjhZzg50", "free": True},
    ],
    "mongodb": [
        {"title": "MongoDB University (Free)", "url": "https://university.mongodb.com/", "free": True},
        {"title": "MongoDB Tutorial - W3Schools", "url": "https://www.w3schools.com/mongodb/", "free": True},
    ],
    "django": [
        {"title": "Django Official Tutorial", "url": "https://docs.djangoproject.com/en/stable/intro/tutorial01/", "free": True},
        {"title": "Django for Beginners - YouTube", "url": "https://www.youtube.com/watch?v=F5mRW0jo-U4", "free": True},
    ],
    "flutter": [
        {"title": "Flutter Official Docs", "url": "https://docs.flutter.dev/get-started/codelab", "free": True},
        {"title": "Flutter Tutorial - freeCodeCamp (YouTube)", "url": "https://www.youtube.com/watch?v=VPvVD8t02U8", "free": True},
    ],
    "java": [
        {"title": "Java Tutorial - W3Schools", "url": "https://www.w3schools.com/java/", "free": True},
        {"title": "Java Programming - MOOC Helsinki", "url": "https://java-programming.mooc.fi/", "free": True},
    ],
}

def get_skill_roadmap(missing_skills: list) -> list:
    roadmap = []
    for skill in missing_skills:
        skill_lower = skill.lower()
        courses = COURSE_MAP.get(skill_lower, [
            {
                "title": f"Search '{skill}' on freeCodeCamp",
                "url": f"https://www.freecodecamp.org/news/search/?query={skill.replace(' ', '+')}",
                "free": True
            },
            {
                "title": f"Search '{skill}' on YouTube",
                "url": f"https://www.youtube.com/results?search_query={skill.replace(' ', '+')}+tutorial",
                "free": True
            }
        ])
        roadmap.append({
            "skill": skill,
            "courses": courses,
            "priority": "high" if len(missing_skills) <= 3 else "medium"
        })
    return roadmap
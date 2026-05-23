import fitz  # PyMuPDF
import spacy
import re

nlp = spacy.load("en_core_web_sm")

# Common skills list to detect from resume
SKILLS_LIST = [
    "python", "java", "javascript", "typescript", "react", "node.js", "nodejs",
    "html", "css", "tailwind", "bootstrap", "sql", "postgresql", "mysql",
    "mongodb", "redis", "docker", "kubernetes", "git", "github", "linux",
    "machine learning", "deep learning", "tensorflow", "pytorch", "sklearn",
    "pandas", "numpy", "flask", "fastapi", "django", "spring", "c++", "c",
    "kotlin", "swift", "flutter", "dart", "aws", "azure", "gcp", "firebase",
    "rest api", "graphql", "agile", "scrum", "figma", "photoshop"
]

def extract_text_from_pdf(file_path: str) -> str:
    """Extract raw text from PDF file"""
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text.strip()

def extract_email(text: str) -> str:
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(pattern, text)
    return match.group() if match else None

def extract_phone(text: str) -> str:
    pattern = r'(\+?\d[\d\s\-]{8,13}\d)'
    match = re.search(pattern, text)
    return match.group().strip() if match else None

def extract_skills(text: str) -> list:
    text_lower = text.lower()
    found = []
    for skill in SKILLS_LIST:
        if skill.lower() in text_lower:
            found.append(skill.title())
    return list(set(found))

def extract_name(text: str) -> str:
    doc = nlp(text[:500])  # check first 500 chars only
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    # fallback: first line
    first_line = text.strip().split('\n')[0]
    return first_line[:50] if first_line else "Unknown"

def parse_resume(file_path: str) -> dict:
    text = extract_text_from_pdf(file_path)
    return {
        "raw_text": text,
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "word_count": len(text.split())
    }
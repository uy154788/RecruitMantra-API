from flask import Blueprint, request, jsonify
import requests
from io import BytesIO
import PyPDF2
import en_core_web_sm
import pandas as pd
import docx2txt
import random
import tempfile
import os
import re

# Load NLP model
nlp = en_core_web_sm.load()
skill_extractor_bp = Blueprint('skill_extractor', __name__)

def doctotext(file_content):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_doc:
        temp_doc.write(file_content.read())
        temp_doc.close()
        text = docx2txt.process(temp_doc.name)
    os.remove(temp_doc.name)
    return text

def pdftotext(file_content):
    try:
        pdf_reader = PyPDF2.PdfReader(file_content)
        return " ".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())
    except PyPDF2.errors.PdfReadError:
        return "Error: Unable to read PDF file content."

def extract_skills_from_resume(text, skills_csv_path):
    skill_data = pd.read_csv(skills_csv_path)
    skills = skill_data['Skill'].str.lower().tolist()
    return [skill for skill in skills if skill in text.lower()]

def load_questions(file_path):
    with open(file_path, 'r') as file:
        questions = [line.strip() for line in file.readlines()]
    return questions

def get_random_questions_for_skills(skills, questions, sample_size=5):
    skill_questions = {}
    for skill in skills:
        if len(questions) >= sample_size:
            skill_questions[skill] = random.sample(questions, sample_size)
        else:
            skill_questions[skill] = questions  # if not enough questions, return all
    return skill_questions

def convert_google_drive_link(resume_url):
    """Convert Google Drive link to direct download link."""
    file_id_match = re.search(r"/d/([a-zA-Z0-9_-]+)", resume_url)
    if file_id_match:
        file_id = file_id_match.group(1)
        return f"https://drive.google.com/uc?id={file_id}"
    return None

@skill_extractor_bp.route('/extract_skills', methods=['POST'])
def extract_skills():
    # Get resume URL from the request
    resume_url = request.json.get('resume_url')
    if not resume_url:
        return jsonify({"error": "No resume URL provided"}), 400

    # Check if the URL is a Google Drive link
    if "drive.google.com" in resume_url:
        resume_url = convert_google_drive_link(resume_url)

    # Attempt to download the file
    try:
        response = requests.get(resume_url, allow_redirects=True)
        response.raise_for_status()  # Raise an error for bad responses
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

    # Check the content type
    content_type = response.headers.get('Content-Type', '')
    print(f"Content-Type: {content_type}")  # Debugging statement
    file_content = BytesIO(response.content)

    if 'application/pdf' in content_type:
        textinput = pdftotext(file_content)
        if "Error" in textinput:  # Check if there was an error in reading the PDF
            return jsonify({"error": textinput}), 500
    elif 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
        textinput = doctotext(file_content)
    elif 'text/plain' in content_type:  # Handle plain text files
        textinput = file_content.read().decode('utf-8')
    else:
        return jsonify({"error": "Unsupported file format"}), 400

    # Extract skills and generate questions
    matched_skills = extract_skills_from_resume(textinput, 'skill.csv')
    questions = load_questions('quest.txt')
    random_questions = get_random_questions_for_skills(matched_skills, questions)

    return jsonify(random_questions)

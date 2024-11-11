from flask import Blueprint, request, jsonify
import json
import random
import requests
from io import BytesIO
import PyPDF2
import en_core_web_sm
import pandas as pd
import docx2txt

# Load NLP model
nlp = en_core_web_sm.load()
skill_extractor_bp = Blueprint('skill_extractor', __name__)

@skill_extractor_bp.route('/extract_skills', methods=['POST'])
def extract_skills():
    resume_url = request.json.get('resume_url')  # Dynamic URL input

    # Download the resume file from the provided URL
    response = requests.get(resume_url)
    if response.status_code == 200:
        file_content = BytesIO(response.content)

        # Determine file type based on Content-Type header
        content_type = response.headers.get('Content-Type', '').lower()

        if 'application/pdf' in content_type:
            textinput = pdftotext(file_content)
        elif 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
            textinput = doctotext(file_content)
        elif 'text/plain' in content_type:  # Handle plain text files
            textinput = file_content.read().decode('utf-8')
        else:
            return jsonify({"error": "Unsupported file format"}), 400
    else:
        return jsonify({"error": "Failed to download the file from the provided URL"}), response.status_code

    skills_csv_path = 'skill.csv'
    questions_file_path = 'quest.txt'

    # Extract skills from resume text
    matched_skills = extract_skills_from_resume(textinput, skills_csv_path)
    questions = load_questions(questions_file_path)
    random_questions = get_random_questions_for_skills(matched_skills, questions)

    return jsonify(random_questions)


def doctotext(docx_file):
    # Convert DOCX to text
    temp = docx2txt.process(docx_file)
    resume_text = [line.replace('\t', ' ') for line in temp.split('\n') if line]
    text = ' '.join(resume_text)
    return text


def pdftotext(pdf_file):
    # Convert PDF to text
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text += page.extract_text() if page.extract_text() else ""
    return text.strip()


def extract_skills_from_resume(resume_text, skills_csv_path):
    doc = nlp(resume_text)
    potential_skills = set()

    # Extract noun chunks as potential skills
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.lower().strip()
        potential_skills.add(chunk_text)

    # Extract individual tokens that are not stop words and are nouns
    for token in doc:
        if not token.is_stop and token.pos_ in {'NOUN', 'PROPN'}:
            token_text = token.text.lower().strip()
            potential_skills.add(token_text)

    # Read skills from CSV file
    data = pd.read_csv(skills_csv_path, names=['skill'])
    skills_list = set(data['skill'].str.lower())

    # Find matching skills
    matched_skills = potential_skills.intersection(skills_list)
    return list(matched_skills)


def load_questions(file_path):
    with open(file_path, 'r') as file:
        # Load the JSON data from the text file
        skills_questions = json.load(file)
    return skills_questions


def get_random_questions_for_skills(skills, skills_questions):
    # Convert all skills and dictionary keys to lowercase for case-insensitivity
    skills_questions = {k.lower(): v for k, v in skills_questions.items()}
    random_questions = []

    for skill in skills:
        skill_lower = skill.lower()  # Ensure case-insensitive match
        if skill_lower in skills_questions:
            # Get the list of questions for the given skill
            questions = skills_questions[skill_lower]
            # Pick a random question and add to the list
            random_questions.append(random.choice(questions))
        # else:
        #     random_questions.append(f"No questions found for skill '{skill}'.")
    question_size = len(random_questions)
    if question_size == 0:
        return "Update Skills in your resume"

    return random_questions


from flask import Blueprint, jsonify
import json
import random

# Create a Blueprint
manage_question_bp = Blueprint("manage_question", __name__)

# Load questions from the JSON file
with open("manage_question.txt", "r") as file:
    questions = json.load(file)

@manage_question_bp.route("/manage-question", methods=["POST"])
def get_random_questions():
    num_questions = min(10, len(questions))
    random_questions = random.sample(questions, num_questions)
    return jsonify({"questions": random_questions})

from flask import Blueprint, jsonify
import json
import random

# Create a Blueprint
manage_question_bp = Blueprint("manage_question", __name__)

# Load questions from the JSON file
with open("manage_question.txt", "r") as file:
    questions = json.load(file)

@manage_question_bp.route("/manage-question", methods=["POST"])
def get_random_question():
    """API endpoint to get a random interview question."""
    random_question = random.choice(questions)
    return jsonify({"question": random_question})  # Ensuring proper JSON format

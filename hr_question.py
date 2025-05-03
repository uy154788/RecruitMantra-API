# from flask import Blueprint, jsonify
# import json
# import random
#
# # Create a Blueprint
# hr_question_bp = Blueprint("hr_question", __name__)
# hr_demo_bp = Blueprint("hr_demo", __name__)
#
# # Load questions from the JSON file
# with open("hr_question.txt", "r") as file:
#     questions = json.load(file)
#
# @hr_question_bp.route("/hr-question", methods=["POST"])
# def get_random_question():
#     """API endpoint to get a random interview question."""
#     random_question = random.choice(questions)
#     return jsonify({"question": random_question})  # Ensuring proper JSON format

from flask import Blueprint, jsonify
import json
import random

# Create Blueprints
hr_question_bp = Blueprint("hr_question", __name__)
hr_demo_bp = Blueprint("hr_demo", __name__)

# Load questions from the JSON file
with open("hr_question.txt", "r") as file:
    questions = json.load(file)

@hr_question_bp.route("/hr-question", methods=["POST"])
def get_random_questions():
    """API endpoint to get a list of random interview questions (minimum 8)."""
    num_questions = min(10, len(questions))  # Ensure we don't exceed available questions
    random_questions = random.sample(questions, num_questions)
    return jsonify({"questions": random_questions})


@hr_demo_bp.route("/hr-demo", methods=["GET"])
def get_random_question():
    return jsonify(["hello"])


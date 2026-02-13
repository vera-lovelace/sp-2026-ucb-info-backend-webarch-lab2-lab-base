#!/usr/bin/env python3
"""
Lab 2: External API Integration — Student Records + AI Advice

CRUD endpoints (below) are COMPLETE. Do NOT modify them.
Your task: implement the two advice endpoints marked with TODO.
"""

import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # loads variables from .env file

app = Flask(__name__)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# =============================================================================
# DATA STORAGE
# =============================================================================

students = {
    1: {"id": 1, "name": "Alice Smith", "email": "alice@berkeley.edu", "major": "Data Science"},
    2: {"id": 2, "name": "Bob Jones", "email": "bob@berkeley.edu", "major": "Computer Science"},
    3: {"id": 3, "name": "Carol White", "email": "carol@berkeley.edu", "major": "Information Systems"},
    4: {"id": 4, "name": "David Park", "email": "david@berkeley.edu", "major": ""},
}

next_id = 5


# =============================================================================
# CRUD ENDPOINTS — ALREADY COMPLETE (do NOT modify)
# =============================================================================

@app.get('/students')
def list_students():
    all_students = list(students.values())
    return jsonify({"students": all_students, "total": len(all_students)}), 200


@app.get('/students/<int:student_id>')
def get_student(student_id):
    student = students.get(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(student), 200


@app.post('/students')
def create_student():
    global next_id
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "Name is required"}), 400

    student = {
        "id": next_id,
        "name": data["name"],
        "email": data.get("email", ""),
        "major": data.get("major", ""),
    }
    students[next_id] = student
    next_id += 1
    return jsonify(student), 201


@app.put('/students/<int:student_id>')
def update_student(student_id):
    student = students.get(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    for key, value in data.items():
        if key == "id":
            continue  # cannot change id
        student[key] = value

    return jsonify(student), 200


@app.delete('/students/<int:student_id>')
def delete_student(student_id):
    student = students.pop(student_id, None)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    return jsonify({"message": "Student deleted"}), 200


# =============================================================================
# HELPER: Call OpenAI API
# =============================================================================
# This function calls OpenAI's Chat Completions API.
# It sends a prompt asking for a short piece of advice based on the student's major.
#
# Parameters:
#   major (str) — the student's major, e.g. "Data Science"
#
# Returns:
#   str — a short advice string (cleaned up, no quotes/emoji/newlines)
#
# Raises:
#   Exception — if the API call fails for any reason
#         (bad key, timeout, rate limit, network error, etc.)

def _generate_advice_from_openai(major):
    response = client.chat.completions.create(
        # Please do not change the model name, as we have a shared key with limited quota. 
        # If you want to experiment with other models, please get your own API key and set it in your .env file.
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a concise academic advisor. "
                    "Give exactly one piece of advice in about 15 words. "
                    "No emoji, no quotation marks, no line breaks."
                ),
            },
            {
                "role": "user",
                "content": f"Give one short advice for a student majoring in {major}.",
            },
        ],
        temperature=0.7,
        max_tokens=50,
    )

    advice = response.choices[0].message.content

    # Clean up: remove surrounding quotes, extra whitespace, newlines
    advice = advice.strip().strip('"').strip("'").replace("\n", " ")

    return advice


# =============================================================================
# TODO: IMPLEMENT THESE TWO ENDPOINTS
# =============================================================================

# --- Endpoint A: POST /students/<id>/advice ---
#
# 1. Look up the student by ID.
#    → If not found, return 404: {"error": "Student not found"}
#
# 2. Check that the student has a non-empty "major".
#    → If missing or empty, return 400: {"error": "Student major is required to generate advice"}
#
# 3. Call _generate_advice_from_openai(major) to get advice.
#    → If it raises an exception, log the error with app.logger.error(...)
#      and return 502: {"error": "Upstream AI service failed"}
#
# 4. Save the advice into the student dict
#
# 5. Return 200 with: {"id": ..., "major": "...", "advice": "..."}



@app.post('/students/<int:student_id>/advice')
def generate_advice(student_id):
    global next_id

    if student_id not in students:
        return {"error": "Student not found"}, 404
    if students[student_id]["major"] not in students[student_id]["majors"]:
        return {"error": "Student major is required to generate advice"}, 400

    else:
        advice=_generate_advice_from_openai(student_id)
        students[student_id]["advice"] = advice
        return jsonify(students[student_id]), 200



# --- Endpoint B: GET /students/<id>/advice ---
#
# 1. Look up the student by ID.
#    → If not found, return 404: {"error": "Student not found"}
#
# 2. Check if the student has a non-empty "advice" field.
#    → If not, return 404: {"error": "Advice not found for this student"}
#
# 3. Return 200 with: {"id": ..., "advice": "..."}



@app.get('/students/<int:student_id>/advice')
def get_advice(student_id):
    global next_id

    if student_id not in students:
        return {"error": "Student not found"}, 404

    if students[student_id]["advice"]:
        return jsonify(students[student_id]), 200
    else:
        return {"error": "Advice not found for this student"}, 404


# =============================================================================
# RUN
# =============================================================================

if __name__ == '__main__':
    app.run(debug=True)
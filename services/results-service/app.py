from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import requests
import os
import time

app = Flask(__name__)
CORS(app)

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://quizuser:quizpass@localhost:5432/quiz_db')
QUIZ_SERVICE_URL = os.getenv('QUIZ_SERVICE_URL', 'http://localhost:5001')
SESSION_SERVICE_URL = os.getenv('SESSION_SERVICE_URL', 'http://localhost:5002')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 5003))

def get_db_connection():
    """Create and return a database connection with retries"""
    max_retries = 5
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            return conn
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                print(f"Database connection attempt {attempt + 1} failed. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise e

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "results-service"}), 200

@app.route('/api/results/calculate', methods=['POST'])
def calculate_result():
    """Calculate result for a session"""
    try:
        data = request.get_json()

        if not data or 'session_id' not in data:
            return jsonify({"error": "session_id is required"}), 400

        session_id = data['session_id']

        # Get session data from Session Service
        session_response = requests.get(f"{SESSION_SERVICE_URL}/api/sessions/{session_id}")
        if session_response.status_code != 200:
            return jsonify({"error": "Session not found"}), 404

        session_data = session_response.json()
        quiz_id = session_data['quiz_id']
        user_answers = session_data['answers']

        if not session_data.get('completed', False):
            return jsonify({"error": "Session is not completed yet"}), 400

        # Get correct answers from Quiz Service
        correct_response = requests.get(f"{QUIZ_SERVICE_URL}/api/quizzes/{quiz_id}/questions/answers")
        if correct_response.status_code != 200:
            return jsonify({"error": "Could not fetch correct answers"}), 500

        correct_answers = correct_response.json()

        # Create a map of correct answers for quick lookup
        correct_map = {ans['question_id']: ans['answer_id'] for ans in correct_answers}

        # Calculate score
        score = 0
        total_questions = len(correct_answers)

        for user_answer in user_answers:
            question_id = user_answer['question_id']
            answer_id = user_answer['answer_id']

            if question_id in correct_map and correct_map[question_id] == answer_id:
                score += 1

        # Calculate percentage
        percentage = (score / total_questions * 100) if total_questions > 0 else 0

        # Save result to database
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Check if result already exists
        cur.execute("""
            SELECT id FROM results WHERE session_id = %s
        """, (session_id,))

        existing = cur.fetchone()

        if existing:
            # Update existing result
            cur.execute("""
                UPDATE results
                SET score = %s, total_questions = %s
                WHERE session_id = %s
                RETURNING id, session_id, quiz_id, score, total_questions, completed_at
            """, (score, total_questions, session_id))
        else:
            # Insert new result
            cur.execute("""
                INSERT INTO results (session_id, quiz_id, score, total_questions)
                VALUES (%s, %s, %s, %s)
                RETURNING id, session_id, quiz_id, score, total_questions, completed_at
            """, (session_id, quiz_id, score, total_questions))

        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "session_id": session_id,
            "quiz_id": quiz_id,
            "score": score,
            "total": total_questions,
            "percentage": round(percentage, 2),
            "completed_at": result['completed_at'].isoformat() if result['completed_at'] else None
        }), 200

    except requests.RequestException as e:
        return jsonify({"error": f"Service communication error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/results/<session_id>', methods=['GET'])
def get_result(session_id):
    """Get result for a session"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT id, session_id, quiz_id, score, total_questions, completed_at
            FROM results
            WHERE session_id = %s
        """, (session_id,))

        result = cur.fetchone()
        cur.close()
        conn.close()

        if result is None:
            return jsonify({"error": "Result not found"}), 404

        # Calculate percentage
        percentage = (result['score'] / result['total_questions'] * 100) if result['total_questions'] > 0 else 0

        return jsonify({
            "session_id": result['session_id'],
            "quiz_id": result['quiz_id'],
            "score": result['score'],
            "total": result['total_questions'],
            "percentage": round(percentage, 2),
            "completed_at": result['completed_at'].isoformat() if result['completed_at'] else None
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(f"Starting Results Service on port {SERVICE_PORT}...")
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=True)

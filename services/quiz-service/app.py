from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import os
import time

app = Flask(__name__)
CORS(app)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://quizuser:quizpass@localhost:5432/quiz_db')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 5001))

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
    return jsonify({"status": "healthy", "service": "quiz-service"}), 200

@app.route('/api/quizzes', methods=['GET'])
def get_quizzes():
    """Get all available quizzes"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT q.id, q.title, q.description, q.created_at,
                   COUNT(qu.id) as question_count
            FROM quizzes q
            LEFT JOIN questions qu ON q.id = qu.quiz_id
            GROUP BY q.id
            ORDER BY q.created_at DESC
        """)

        quizzes = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify(quizzes), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/quizzes/<int:quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    """Get a specific quiz by ID"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT q.id, q.title, q.description, q.created_at,
                   COUNT(qu.id) as question_count
            FROM quizzes q
            LEFT JOIN questions qu ON q.id = qu.quiz_id
            WHERE q.id = %s
            GROUP BY q.id
        """, (quiz_id,))

        quiz = cur.fetchone()
        cur.close()
        conn.close()

        if quiz is None:
            return jsonify({"error": "Quiz not found"}), 404

        return jsonify(quiz), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/quizzes/<int:quiz_id>/questions', methods=['GET'])
def get_quiz_questions(quiz_id):
    """Get all questions for a quiz (without revealing correct answers)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Get questions
        cur.execute("""
            SELECT id, quiz_id, question_text, question_type
            FROM questions
            WHERE quiz_id = %s
            ORDER BY id
        """, (quiz_id,))

        questions = cur.fetchall()

        # Get answers for each question (without is_correct flag for users)
        for question in questions:
            cur.execute("""
                SELECT id, answer_text
                FROM answers
                WHERE question_id = %s
                ORDER BY id
            """, (question['id'],))

            question['answers'] = cur.fetchall()

        cur.close()
        conn.close()

        return jsonify(questions), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/quizzes/<int:quiz_id>/questions/answers', methods=['GET'])
def get_quiz_correct_answers(quiz_id):
    """Get correct answers for a quiz (used by Results Service)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT q.id as question_id, a.id as answer_id
            FROM questions q
            JOIN answers a ON q.id = a.question_id
            WHERE q.quiz_id = %s AND a.is_correct = true
            ORDER BY q.id
        """, (quiz_id,))

        correct_answers = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify(correct_answers), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/quizzes', methods=['POST'])
def create_quiz():
    """Create a new quiz"""
    try:
        data = request.get_json()

        if not data or 'title' not in data:
            return jsonify({"error": "Title is required"}), 400

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            INSERT INTO quizzes (title, description)
            VALUES (%s, %s)
            RETURNING id, title, description, created_at
        """, (data['title'], data.get('description', '')))

        quiz = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        return jsonify(quiz), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/quizzes/<int:quiz_id>/questions', methods=['POST'])
def add_question(quiz_id):
    """Add a question to a quiz"""
    try:
        data = request.get_json()

        if not data or 'question_text' not in data or 'answers' not in data:
            return jsonify({"error": "question_text and answers are required"}), 400

        if len(data['answers']) < 2:
            return jsonify({"error": "At least 2 answers are required"}), 400

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Insert question
        cur.execute("""
            INSERT INTO questions (quiz_id, question_text, question_type)
            VALUES (%s, %s, %s)
            RETURNING id, quiz_id, question_text, question_type
        """, (quiz_id, data['question_text'], data.get('question_type', 'multiple_choice')))

        question = cur.fetchone()
        question_id = question['id']

        # Insert answers
        answers = []
        for answer in data['answers']:
            cur.execute("""
                INSERT INTO answers (question_id, answer_text, is_correct)
                VALUES (%s, %s, %s)
                RETURNING id, answer_text, is_correct
            """, (question_id, answer['answer_text'], answer.get('is_correct', False)))

            answers.append(cur.fetchone())

        question['answers'] = answers
        conn.commit()
        cur.close()
        conn.close()

        return jsonify(question), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(f"Starting Quiz Service on port {SERVICE_PORT}...")
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=True)

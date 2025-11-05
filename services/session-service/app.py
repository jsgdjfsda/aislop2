from flask import Flask, jsonify, request
from flask_cors import CORS
import redis
import json
import os
import uuid
from datetime import datetime
import time

app = Flask(__name__)
CORS(app)

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 5002))
SESSION_TTL = 86400  # 24 hours in seconds

def get_redis_connection():
    """Create and return a Redis connection with retries"""
    max_retries = 5
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            r = redis.from_url(REDIS_URL, decode_responses=True)
            r.ping()  # Test connection
            return r
        except redis.ConnectionError as e:
            if attempt < max_retries - 1:
                print(f"Redis connection attempt {attempt + 1} failed. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise e

redis_client = None

def get_redis():
    """Get or create Redis client"""
    global redis_client
    if redis_client is None:
        redis_client = get_redis_connection()
    return redis_client

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        r = get_redis()
        r.ping()
        return jsonify({"status": "healthy", "service": "session-service"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/api/sessions/start', methods=['POST'])
def start_session():
    """Start a new quiz session"""
    try:
        data = request.get_json()

        if not data or 'quiz_id' not in data:
            return jsonify({"error": "quiz_id is required"}), 400

        # Generate unique session ID
        session_id = str(uuid.uuid4())

        # Create session data
        session_data = {
            "session_id": session_id,
            "quiz_id": data['quiz_id'],
            "started_at": datetime.utcnow().isoformat(),
            "answers": [],
            "completed": False
        }

        # Store in Redis with TTL
        r = get_redis()
        r.setex(
            f"session:{session_id}",
            SESSION_TTL,
            json.dumps(session_data)
        )

        return jsonify({
            "session_id": session_id,
            "quiz_id": data['quiz_id'],
            "started_at": session_data['started_at']
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session details"""
    try:
        r = get_redis()
        session_data = r.get(f"session:{session_id}")

        if session_data is None:
            return jsonify({"error": "Session not found or expired"}), 404

        return jsonify(json.loads(session_data)), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions/<session_id>/answer', methods=['POST'])
def submit_answer(session_id):
    """Submit an answer for a question"""
    try:
        data = request.get_json()

        if not data or 'question_id' not in data or 'answer_id' not in data:
            return jsonify({"error": "question_id and answer_id are required"}), 400

        r = get_redis()
        session_data = r.get(f"session:{session_id}")

        if session_data is None:
            return jsonify({"error": "Session not found or expired"}), 404

        session = json.loads(session_data)

        if session['completed']:
            return jsonify({"error": "Session is already completed"}), 400

        # Check if answer for this question already exists
        existing_answer_index = None
        for idx, answer in enumerate(session['answers']):
            if answer['question_id'] == data['question_id']:
                existing_answer_index = idx
                break

        # Add or update answer
        answer_data = {
            "question_id": data['question_id'],
            "answer_id": data['answer_id'],
            "answered_at": datetime.utcnow().isoformat()
        }

        if existing_answer_index is not None:
            session['answers'][existing_answer_index] = answer_data
        else:
            session['answers'].append(answer_data)

        # Save updated session
        r.setex(
            f"session:{session_id}",
            SESSION_TTL,
            json.dumps(session)
        )

        return jsonify({
            "session_id": session_id,
            "answer_recorded": True,
            "total_answers": len(session['answers'])
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions/<session_id>/complete', methods=['POST'])
def complete_session(session_id):
    """Mark session as complete"""
    try:
        r = get_redis()
        session_data = r.get(f"session:{session_id}")

        if session_data is None:
            return jsonify({"error": "Session not found or expired"}), 404

        session = json.loads(session_data)

        if session['completed']:
            return jsonify({"error": "Session is already completed"}), 400

        # Mark as completed
        session['completed'] = True
        session['completed_at'] = datetime.utcnow().isoformat()

        # Save updated session
        r.setex(
            f"session:{session_id}",
            SESSION_TTL,
            json.dumps(session)
        )

        return jsonify({
            "session_id": session_id,
            "completed": True,
            "completed_at": session['completed_at'],
            "total_answers": len(session['answers'])
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions/<session_id>/answers', methods=['GET'])
def get_session_answers(session_id):
    """Get all answers for a session (used by Results Service)"""
    try:
        r = get_redis()
        session_data = r.get(f"session:{session_id}")

        if session_data is None:
            return jsonify({"error": "Session not found or expired"}), 404

        session = json.loads(session_data)

        return jsonify({
            "session_id": session_id,
            "quiz_id": session['quiz_id'],
            "answers": session['answers'],
            "completed": session['completed']
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(f"Starting Session Service on port {SERVICE_PORT}...")
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=True)

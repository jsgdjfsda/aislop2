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
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 5004))

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
    return jsonify({"status": "healthy", "service": "leaderboard-service"}), 200

@app.route('/api/leaderboard', methods=['POST'])
def add_to_leaderboard():
    """Add entry to leaderboard"""
    try:
        data = request.get_json()

        required_fields = ['session_id', 'quiz_id', 'nickname', 'score', 'total']
        if not data or not all(field in data for field in required_fields):
            return jsonify({"error": "session_id, quiz_id, nickname, score, and total are required"}), 400

        # Calculate percentage
        percentage = (data['score'] / data['total'] * 100) if data['total'] > 0 else 0

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Check if entry already exists for this session
        cur.execute("""
            SELECT id FROM leaderboard WHERE session_id = %s
        """, (data['session_id'],))

        existing = cur.fetchone()

        if existing:
            # Update existing entry
            cur.execute("""
                UPDATE leaderboard
                SET nickname = %s, score = %s, percentage = %s
                WHERE session_id = %s
                RETURNING id, quiz_id, session_id, nickname, score, percentage, completed_at
            """, (data['nickname'], data['score'], percentage, data['session_id']))
        else:
            # Insert new entry
            cur.execute("""
                INSERT INTO leaderboard (quiz_id, session_id, nickname, score, percentage)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, quiz_id, session_id, nickname, score, percentage, completed_at
            """, (data['quiz_id'], data['session_id'], data['nickname'], data['score'], percentage))

        entry = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "id": entry['id'],
            "quiz_id": entry['quiz_id'],
            "session_id": entry['session_id'],
            "nickname": entry['nickname'],
            "score": entry['score'],
            "percentage": float(entry['percentage']),
            "completed_at": entry['completed_at'].isoformat() if entry['completed_at'] else None
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/leaderboard/<int:quiz_id>', methods=['GET'])
def get_leaderboard(quiz_id):
    """Get top scores for a quiz"""
    try:
        # Get limit from query params (default 10, max 100)
        limit = min(int(request.args.get('limit', 10)), 100)

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT id, nickname, score, percentage, completed_at
            FROM leaderboard
            WHERE quiz_id = %s
            ORDER BY score DESC, completed_at ASC
            LIMIT %s
        """, (quiz_id, limit))

        entries = cur.fetchall()
        cur.close()
        conn.close()

        # Add rank to each entry
        for idx, entry in enumerate(entries):
            entry['rank'] = idx + 1
            entry['percentage'] = float(entry['percentage'])
            if entry['completed_at']:
                entry['completed_at'] = entry['completed_at'].isoformat()

        return jsonify(entries), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/leaderboard/session/<session_id>', methods=['GET'])
def get_leaderboard_entry(session_id):
    """Get leaderboard entry for a specific session"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT id, quiz_id, session_id, nickname, score, percentage, completed_at
            FROM leaderboard
            WHERE session_id = %s
        """, (session_id,))

        entry = cur.fetchone()

        if entry:
            # Get rank for this entry
            cur.execute("""
                SELECT COUNT(*) + 1 as rank
                FROM leaderboard
                WHERE quiz_id = %s AND (
                    score > %s OR (score = %s AND completed_at < %s)
                )
            """, (entry['quiz_id'], entry['score'], entry['score'], entry['completed_at']))

            rank_result = cur.fetchone()
            entry['rank'] = rank_result['rank']
            entry['percentage'] = float(entry['percentage'])
            if entry['completed_at']:
                entry['completed_at'] = entry['completed_at'].isoformat()

        cur.close()
        conn.close()

        if entry is None:
            return jsonify({"error": "Leaderboard entry not found"}), 404

        return jsonify(entry), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(f"Starting Leaderboard Service on port {SERVICE_PORT}...")
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=True)

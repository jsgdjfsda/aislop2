from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
import os

app = Flask(__name__)

# Service URLs
QUIZ_SERVICE_URL = os.getenv('QUIZ_SERVICE_URL', 'http://localhost:5001')
SESSION_SERVICE_URL = os.getenv('SESSION_SERVICE_URL', 'http://localhost:5002')
RESULTS_SERVICE_URL = os.getenv('RESULTS_SERVICE_URL', 'http://localhost:5003')
LEADERBOARD_SERVICE_URL = os.getenv('LEADERBOARD_SERVICE_URL', 'http://localhost:5004')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 5000))

@app.route('/')
def index():
    """Homepage - List all available quizzes"""
    try:
        response = requests.get(f"{QUIZ_SERVICE_URL}/api/quizzes")
        if response.status_code == 200:
            quizzes = response.json()
            return render_template('index.html', quizzes=quizzes, error=None)
        else:
            return render_template('index.html', quizzes=[], error="Failed to load quizzes")
    except Exception as e:
        return render_template('index.html', quizzes=[], error=str(e))

@app.route('/quiz/<int:quiz_id>')
def quiz(quiz_id):
    """Quiz taking page"""
    try:
        # Get quiz details
        quiz_response = requests.get(f"{QUIZ_SERVICE_URL}/api/quizzes/{quiz_id}")
        if quiz_response.status_code != 200:
            return redirect(url_for('index'))

        quiz_data = quiz_response.json()

        # Get questions
        questions_response = requests.get(f"{QUIZ_SERVICE_URL}/api/quizzes/{quiz_id}/questions")
        if questions_response.status_code != 200:
            return redirect(url_for('index'))

        questions = questions_response.json()

        # Start a new session
        session_response = requests.post(
            f"{SESSION_SERVICE_URL}/api/sessions/start",
            json={"quiz_id": quiz_id}
        )

        if session_response.status_code != 201:
            return redirect(url_for('index'))

        session_data = session_response.json()
        session_id = session_data['session_id']

        return render_template(
            'quiz.html',
            quiz=quiz_data,
            questions=questions,
            session_id=session_id
        )

    except Exception as e:
        print(f"Error: {e}")
        return redirect(url_for('index'))

@app.route('/api/submit-answer', methods=['POST'])
def submit_answer():
    """API endpoint to submit an answer"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        question_id = data.get('question_id')
        answer_id = data.get('answer_id')

        response = requests.post(
            f"{SESSION_SERVICE_URL}/api/sessions/{session_id}/answer",
            json={
                "question_id": question_id,
                "answer_id": answer_id
            }
        )

        return jsonify(response.json()), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/complete-quiz', methods=['POST'])
def complete_quiz():
    """API endpoint to complete a quiz"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')

        # Mark session as complete
        complete_response = requests.post(
            f"{SESSION_SERVICE_URL}/api/sessions/{session_id}/complete"
        )

        if complete_response.status_code != 200:
            return jsonify({"error": "Failed to complete session"}), 500

        # Calculate results
        results_response = requests.post(
            f"{RESULTS_SERVICE_URL}/api/results/calculate",
            json={"session_id": session_id}
        )

        if results_response.status_code != 200:
            return jsonify({"error": "Failed to calculate results"}), 500

        return jsonify({"success": True, "session_id": session_id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/result/<session_id>')
def result(session_id):
    """Results page"""
    try:
        # Get results
        results_response = requests.get(f"{RESULTS_SERVICE_URL}/api/results/{session_id}")
        if results_response.status_code != 200:
            return redirect(url_for('index'))

        results_data = results_response.json()
        quiz_id = results_data['quiz_id']

        # Get quiz details
        quiz_response = requests.get(f"{QUIZ_SERVICE_URL}/api/quizzes/{quiz_id}")
        quiz_data = quiz_response.json() if quiz_response.status_code == 200 else {}

        # Get leaderboard
        leaderboard_response = requests.get(f"{LEADERBOARD_SERVICE_URL}/api/leaderboard/{quiz_id}")
        leaderboard = leaderboard_response.json() if leaderboard_response.status_code == 200 else []

        return render_template(
            'result.html',
            results=results_data,
            quiz=quiz_data,
            leaderboard=leaderboard,
            session_id=session_id
        )

    except Exception as e:
        print(f"Error: {e}")
        return redirect(url_for('index'))

@app.route('/api/submit-to-leaderboard', methods=['POST'])
def submit_to_leaderboard():
    """API endpoint to submit score to leaderboard"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        nickname = data.get('nickname')

        if not nickname or len(nickname.strip()) == 0:
            return jsonify({"error": "Nickname is required"}), 400

        # Get results first
        results_response = requests.get(f"{RESULTS_SERVICE_URL}/api/results/{session_id}")
        if results_response.status_code != 200:
            return jsonify({"error": "Results not found"}), 404

        results_data = results_response.json()

        # Submit to leaderboard
        leaderboard_response = requests.post(
            f"{LEADERBOARD_SERVICE_URL}/api/leaderboard",
            json={
                "session_id": session_id,
                "quiz_id": results_data['quiz_id'],
                "nickname": nickname.strip(),
                "score": results_data['score'],
                "total": results_data['total']
            }
        )

        if leaderboard_response.status_code not in [200, 201]:
            return jsonify({"error": "Failed to submit to leaderboard"}), 500

        return jsonify({"success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return redirect(url_for('index'))

if __name__ == '__main__':
    print(f"Starting Frontend on port {SERVICE_PORT}...")
    print(f"Access the application at http://localhost:{SERVICE_PORT}")
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=True)

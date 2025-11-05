# Microservice Quiz Application

A simple, weekend-implementable microservice-based quiz website built with Python Flask, PostgreSQL, Redis, and Docker Compose. No authentication required - all sessions are anonymous.

## Architecture

This application consists of 5 microservices:

1. **Quiz Service** (Port 5001) - Manages quizzes and questions
2. **Session Service** (Port 5002) - Tracks anonymous quiz sessions using Redis
3. **Results Service** (Port 5003) - Calculates and stores quiz scores
4. **Leaderboard Service** (Port 5004) - Manages high scores
5. **Frontend** (Port 5000) - Web UI for users

## Technology Stack

- **Backend:** Python 3.11 + Flask
- **Database:** PostgreSQL 15
- **Cache:** Redis 7
- **Container Orchestration:** Docker Compose
- **Frontend:** Flask templates + Vanilla JavaScript + CSS

## Prerequisites

- Docker & Docker Compose installed
- At least 2GB of free RAM
- Ports 5000-5004, 5432, and 6379 available

## Quick Start

### 1. Clone or navigate to the project directory

```bash
cd /path/to/quiz-app
```

### 2. Start all services

```bash
docker-compose up --build
```

This will:
- Build all 5 microservices
- Start PostgreSQL and Redis
- Initialize the database with sample quizzes
- Start all services

Wait for all services to start (you'll see log messages from each service).

### 3. Access the application

Open your browser and navigate to:

```
http://localhost:5000
```

### 4. Stop the application

Press `Ctrl+C` in the terminal, then run:

```bash
docker-compose down
```

To also remove the database volume:

```bash
docker-compose down -v
```

## Project Structure

```
quiz-app/
├── docker-compose.yml          # Docker Compose configuration
├── init-db.sql                 # Database initialization and sample data
├── README.md                   # This file
├── MICROSERVICE_QUIZ_PLAN.md  # Detailed architecture plan
└── services/
    ├── quiz-service/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── app.py
    ├── session-service/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── app.py
    ├── results-service/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── app.py
    ├── leaderboard-service/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── app.py
    └── frontend/
        ├── Dockerfile
        ├── requirements.txt
        ├── app.py
        ├── templates/
        │   ├── index.html
        │   ├── quiz.html
        │   └── result.html
        └── static/
            └── style.css
```

## Features

### Current Features
- View list of available quizzes
- Take quizzes with multiple choice and true/false questions
- Progress tracking during quiz
- Automatic answer saving
- Score calculation upon completion
- Submit nickname to leaderboard
- View top 10 scores for each quiz
- Responsive design for mobile and desktop

### Sample Quizzes Included
1. **Python Basics** - 10 questions about Python fundamentals
2. **JavaScript Fundamentals** - 10 questions about JavaScript and ES6
3. **Docker & Containers** - 5 questions about Docker basics

## API Endpoints

### Quiz Service (Port 5001)

```
GET  /api/quizzes                          - List all quizzes
GET  /api/quizzes/{quiz_id}                - Get quiz details
GET  /api/quizzes/{quiz_id}/questions      - Get quiz questions (without correct answers)
GET  /api/quizzes/{quiz_id}/questions/answers - Get correct answers (internal use)
POST /api/quizzes                          - Create a new quiz
POST /api/quizzes/{quiz_id}/questions      - Add question to quiz
```

### Session Service (Port 5002)

```
POST /api/sessions/start                   - Start new quiz session
GET  /api/sessions/{session_id}            - Get session details
POST /api/sessions/{session_id}/answer     - Submit an answer
POST /api/sessions/{session_id}/complete   - Mark session complete
GET  /api/sessions/{session_id}/answers    - Get all session answers
```

### Results Service (Port 5003)

```
POST /api/results/calculate                - Calculate score for session
GET  /api/results/{session_id}             - Get result details
```

### Leaderboard Service (Port 5004)

```
POST /api/leaderboard                      - Add entry to leaderboard
GET  /api/leaderboard/{quiz_id}            - Get top scores for quiz
GET  /api/leaderboard/session/{session_id} - Get leaderboard entry for session
```

## Testing the API

You can test individual services using curl or any API client:

```bash
# Get all quizzes
curl http://localhost:5001/api/quizzes

# Start a quiz session
curl -X POST http://localhost:5002/api/sessions/start \
  -H "Content-Type: application/json" \
  -d '{"quiz_id": 1}'

# Submit an answer
curl -X POST http://localhost:5002/api/sessions/{session_id}/answer \
  -H "Content-Type: application/json" \
  -d '{"question_id": 1, "answer_id": 1}'

# Get leaderboard
curl http://localhost:5004/api/leaderboard/1
```

## Development

### Running Services Individually

Each service can be run independently for development:

```bash
# Quiz Service
cd services/quiz-service
pip install -r requirements.txt
export DATABASE_URL=postgresql://quizuser:quizpass@localhost:5432/quiz_db
python app.py

# Session Service
cd services/session-service
pip install -r requirements.txt
export REDIS_URL=redis://localhost:6379/0
python app.py
```

### Adding New Quizzes

You can add quizzes via the API or by modifying `init-db.sql`:

```sql
-- Add a new quiz
INSERT INTO quizzes (title, description) VALUES
('Your Quiz Title', 'Quiz description');

-- Add questions
INSERT INTO questions (quiz_id, question_text, question_type) VALUES
(4, 'What is...?', 'multiple_choice');

-- Add answers
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(26, 'Correct answer', true),
(26, 'Wrong answer', false);
```

Then rebuild the database:

```bash
docker-compose down -v
docker-compose up --build
```

### Logs

View logs for all services:

```bash
docker-compose logs -f
```

View logs for a specific service:

```bash
docker-compose logs -f frontend
docker-compose logs -f quiz-service
```

## Troubleshooting

### Services won't start

1. Check if ports are available:
   ```bash
   lsof -i :5000 -i :5001 -i :5002 -i :5003 -i :5004 -i :5432 -i :6379
   ```

2. Check Docker logs:
   ```bash
   docker-compose logs
   ```

3. Restart services:
   ```bash
   docker-compose down
   docker-compose up --build
   ```

### Database connection errors

The services have built-in retry logic. Wait 10-15 seconds for PostgreSQL to fully start.

### Redis connection errors

Wait for Redis healthcheck to pass. Check logs:
```bash
docker-compose logs redis
```

### Frontend can't connect to services

Verify all services are running:
```bash
docker-compose ps
```

All services should show "Up" status.

## Architecture Benefits

### Microservice Advantages
- **Separation of Concerns:** Each service has a single responsibility
- **Independent Scaling:** Can scale services independently
- **Technology Flexibility:** Easy to swap implementations
- **Fault Isolation:** One service failure doesn't crash the entire app

### Simple Design for Weekend Implementation
- No authentication complexity
- Shared PostgreSQL instance (not pure microservices but simpler)
- Direct HTTP communication (no message queues)
- Minimal dependencies

## Future Enhancements

Potential improvements:
- Add API Gateway (nginx)
- Implement caching layer
- Add quiz categories and tags
- Timed quizzes
- Question shuffling
- Answer explanations
- Admin panel for quiz management
- User authentication and profiles
- Quiz statistics and analytics
- Export results to PDF
- Social sharing features

## Performance

Expected performance on a typical development machine:
- 3-5 seconds: Initial startup time
- <100ms: API response times
- Supports: 100+ concurrent users
- 24 hours: Session expiration time

## Security Notes

This is a simple educational project with no authentication:
- All sessions are anonymous (UUID-based)
- No user data is collected
- Sessions expire after 24 hours
- Not suitable for production without modifications

For production use, consider adding:
- User authentication
- API rate limiting
- HTTPS/TLS
- Input validation and sanitization
- CORS restrictions
- Database connection pooling
- Monitoring and logging

## License

This project is open source and available for educational purposes.

## Contributing

Feel free to submit issues and enhancement requests!

## Support

For issues or questions:
1. Check the logs: `docker-compose logs`
2. Review the architecture plan: `MICROSERVICE_QUIZ_PLAN.md`
3. Test individual services using the API endpoints

## Credits

Built with Flask, PostgreSQL, Redis, and Docker.

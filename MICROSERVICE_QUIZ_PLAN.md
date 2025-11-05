# Microservice-Based Quiz Website - Implementation Plan

## Architecture Overview

A simple, weekend-implementable microservice architecture for a quiz website with no authentication.

### Core Microservices

```
┌─────────────┐
│   Frontend  │ (Python Flask + Simple HTML/JS)
└──────┬──────┘
       │
       ├──────────┬──────────────┬────────────┐
       │          │              │            │
┌──────▼──────┐ ┌─▼─────────┐ ┌─▼────────┐ ┌─▼────────┐
│Quiz Service │ │Session    │ │Results   │ │Leaderboard│
│             │ │Service    │ │Service   │ │Service    │
└──────┬──────┘ └─┬─────────┘ └─┬────────┘ └─┬────────┘
       │          │              │            │
┌──────▼──────────▼──────────────▼────────────▼─────┐
│           PostgreSQL + Redis                       │
└────────────────────────────────────────────────────┘
```

## Microservices Breakdown

### 1. **Quiz Service** (Port 5001)
**Responsibility**: Manage quiz questions and quiz metadata

**Database Tables**:
- `quizzes`: id, title, description, created_at
- `questions`: id, quiz_id, question_text, question_type (multiple_choice, true_false)
- `answers`: id, question_id, answer_text, is_correct

**API Endpoints**:
- `GET /api/quizzes` - List all available quizzes
- `GET /api/quizzes/{quiz_id}` - Get quiz details
- `GET /api/quizzes/{quiz_id}/questions` - Get all questions for a quiz (with answer options, without correct answers)
- `POST /api/quizzes` - Create a new quiz (admin operation)
- `POST /api/quizzes/{quiz_id}/questions` - Add question to quiz

**Tech Stack**: Python Flask, PostgreSQL
**Complexity**: ~150 lines of code

---

### 2. **Session Service** (Port 5002)
**Responsibility**: Track quiz-taking sessions for anonymous users

**Redis Data**:
- Session key: `session:{session_id}` → JSON with quiz_id, started_at, answers[], completed
- TTL: 24 hours

**API Endpoints**:
- `POST /api/sessions/start` - Start a new quiz session (returns session_id)
  - Body: `{"quiz_id": 1}`
  - Returns: `{"session_id": "uuid-here", "quiz_id": 1}`
- `POST /api/sessions/{session_id}/answer` - Submit an answer
  - Body: `{"question_id": 1, "answer_id": 2}`
- `POST /api/sessions/{session_id}/complete` - Mark session as complete
- `GET /api/sessions/{session_id}` - Get session details

**Tech Stack**: Python Flask, Redis
**Complexity**: ~100 lines of code

---

### 3. **Results Service** (Port 5003)
**Responsibility**: Calculate scores and store results

**Database Tables**:
- `results`: id, session_id, quiz_id, score, total_questions, completed_at

**API Endpoints**:
- `POST /api/results/calculate` - Calculate result for a session
  - Body: `{"session_id": "uuid"}`
  - Calls Quiz Service to get correct answers
  - Calls Session Service to get user answers
  - Returns: `{"session_id": "uuid", "score": 8, "total": 10, "percentage": 80}`
- `GET /api/results/{session_id}` - Get result for a session

**Tech Stack**: Python Flask, PostgreSQL
**Complexity**: ~120 lines of code

---

### 4. **Leaderboard Service** (Port 5004)
**Responsibility**: Track and display high scores

**Database Tables**:
- `leaderboard`: id, quiz_id, session_id, nickname, score, percentage, completed_at

**API Endpoints**:
- `POST /api/leaderboard` - Add entry to leaderboard
  - Body: `{"session_id": "uuid", "quiz_id": 1, "nickname": "Player1", "score": 8, "total": 10}`
- `GET /api/leaderboard/{quiz_id}` - Get top 10 scores for a quiz

**Tech Stack**: Python Flask, PostgreSQL
**Complexity**: ~80 lines of code

---

### 5. **Frontend Service** (Port 5000)
**Responsibility**: Web UI for users

**Pages**:
- `/` - Homepage with list of quizzes
- `/quiz/{quiz_id}` - Quiz taking interface
- `/result/{session_id}` - Show results and leaderboard

**Tech Stack**: Python Flask (templates), Simple HTML/JS/CSS
**Complexity**: ~200 lines of Python + HTML templates

---

## Database Schema

### PostgreSQL Tables

```sql
-- Quiz Service DB
CREATE TABLE quizzes (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    quiz_id INTEGER REFERENCES quizzes(id),
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) DEFAULT 'multiple_choice'
);

CREATE TABLE answers (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id),
    answer_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE
);

-- Results Service DB
CREATE TABLE results (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    quiz_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Leaderboard Service DB
CREATE TABLE leaderboard (
    id SERIAL PRIMARY KEY,
    quiz_id INTEGER NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    nickname VARCHAR(100) NOT NULL,
    score INTEGER NOT NULL,
    percentage DECIMAL(5,2) NOT NULL,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_quiz_score (quiz_id, score DESC)
);
```

### Redis Data Structures

```json
// Session data
session:{uuid} = {
    "quiz_id": 1,
    "started_at": "2025-11-05T10:00:00Z",
    "answers": [
        {"question_id": 1, "answer_id": 2},
        {"question_id": 2, "answer_id": 5}
    ],
    "completed": false
}
```

---

## Docker Compose Configuration

```yaml
version: '3.8'

services:
  # Database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: quizuser
      POSTGRES_PASSWORD: quizpass
      POSTGRES_DB: quiz_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U quizuser"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # Quiz Service
  quiz-service:
    build: ./services/quiz-service
    ports:
      - "5001:5001"
    environment:
      DATABASE_URL: postgresql://quizuser:quizpass@postgres:5432/quiz_db
      SERVICE_PORT: 5001
    depends_on:
      postgres:
        condition: service_healthy

  # Session Service
  session-service:
    build: ./services/session-service
    ports:
      - "5002:5002"
    environment:
      REDIS_URL: redis://redis:6379/0
      SERVICE_PORT: 5002
    depends_on:
      redis:
        condition: service_healthy

  # Results Service
  results-service:
    build: ./services/results-service
    ports:
      - "5003:5003"
    environment:
      DATABASE_URL: postgresql://quizuser:quizpass@postgres:5432/quiz_db
      QUIZ_SERVICE_URL: http://quiz-service:5001
      SESSION_SERVICE_URL: http://session-service:5002
      SERVICE_PORT: 5003
    depends_on:
      postgres:
        condition: service_healthy

  # Leaderboard Service
  leaderboard-service:
    build: ./services/leaderboard-service
    ports:
      - "5004:5004"
    environment:
      DATABASE_URL: postgresql://quizuser:quizpass@postgres:5432/quiz_db
      SERVICE_PORT: 5004
    depends_on:
      postgres:
        condition: service_healthy

  # Frontend
  frontend:
    build: ./services/frontend
    ports:
      - "5000:5000"
    environment:
      QUIZ_SERVICE_URL: http://quiz-service:5001
      SESSION_SERVICE_URL: http://session-service:5002
      RESULTS_SERVICE_URL: http://results-service:5003
      LEADERBOARD_SERVICE_URL: http://leaderboard-service:5004
      SERVICE_PORT: 5000
    depends_on:
      - quiz-service
      - session-service
      - results-service
      - leaderboard-service

volumes:
  postgres_data:
```

---

## Project Structure

```
quiz-app/
├── docker-compose.yml
├── init-db.sql
├── README.md
└── services/
    ├── quiz-service/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   ├── app.py
    │   └── models.py
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
            ├── style.css
            └── app.js
```

---

## Implementation Timeline (Weekend)

### Saturday Morning (3-4 hours)
1. Set up project structure
2. Create Docker Compose file
3. Implement Quiz Service (basic CRUD)
4. Create init-db.sql with sample quiz data

### Saturday Afternoon (3-4 hours)
1. Implement Session Service (Redis operations)
2. Implement Results Service (score calculation)
3. Test inter-service communication

### Saturday Evening (2-3 hours)
1. Implement Leaderboard Service
2. Write Dockerfiles for each service

### Sunday Morning (3-4 hours)
1. Implement Frontend (Flask + HTML templates)
2. Create basic UI with HTML/CSS

### Sunday Afternoon (3-4 hours)
1. Integration testing
2. Bug fixes
3. Add sample quiz data
4. Polish UI

### Sunday Evening (1-2 hours)
1. Documentation
2. README with setup instructions
3. Final testing

**Total Time**: ~16-20 hours (realistic weekend project)

---

## Key Features

### MVP Features (Must Have)
- ✅ View list of available quizzes
- ✅ Take a quiz (anonymous session)
- ✅ Submit answers
- ✅ View results after completion
- ✅ See leaderboard for each quiz
- ✅ Submit nickname for leaderboard

### Nice to Have (If Time Permits)
- Quiz categories
- Timer for quizzes
- Question shuffling
- Answer explanation after completion
- Simple admin page to create quizzes

---

## Sample API Flow

### User Takes a Quiz

1. **User visits homepage**
   - Frontend → `GET /api/quizzes` → Quiz Service
   - Display list of quizzes

2. **User clicks "Start Quiz"**
   - Frontend → `POST /api/sessions/start {"quiz_id": 1}` → Session Service
   - Receive `session_id`
   - Frontend → `GET /api/quizzes/1/questions` → Quiz Service
   - Display questions

3. **User answers questions**
   - For each answer: Frontend → `POST /api/sessions/{id}/answer` → Session Service

4. **User clicks "Submit Quiz"**
   - Frontend → `POST /api/sessions/{id}/complete` → Session Service
   - Frontend → `POST /api/results/calculate {"session_id": "..."}` → Results Service
     - Results Service → Get session answers from Session Service
     - Results Service → Get correct answers from Quiz Service
     - Results Service → Calculate score and save

5. **User sees results**
   - Frontend → `GET /api/results/{session_id}` → Results Service
   - User enters nickname
   - Frontend → `POST /api/leaderboard` → Leaderboard Service
   - Frontend → `GET /api/leaderboard/{quiz_id}` → Leaderboard Service
   - Display score and leaderboard

---

## Technology Stack Summary

- **Backend**: Python 3.11 + Flask
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Container Orchestration**: Docker Compose
- **Frontend**: Flask templates + Vanilla JS

### Key Python Libraries
```
Flask==3.0.0
Flask-CORS==4.0.0
psycopg2-binary==2.9.9
redis==5.0.1
requests==2.31.0
python-dotenv==1.0.0
```

---

## Why This Architecture?

### Microservice Benefits (Even at Small Scale)
1. **Separation of Concerns**: Each service has a single responsibility
2. **Independent Deployment**: Can update one service without affecting others
3. **Technology Flexibility**: Can switch DB for one service without touching others
4. **Scalability**: Can scale Session Service independently during high traffic
5. **Development**: Multiple developers can work on different services

### Simplicity for Weekend Implementation
1. **No Authentication**: Biggest complexity removed
2. **Simple HTTP REST APIs**: No message queues or complex patterns
3. **Shared PostgreSQL**: Services share one DB instance (not pure microservices but simpler)
4. **No API Gateway**: Frontend talks directly to services
5. **No Service Discovery**: Hardcoded URLs via environment variables

---

## Getting Started

### Prerequisites
- Docker & Docker Compose installed
- Basic Python knowledge
- Text editor

### Quick Start Commands
```bash
# Clone/create project
mkdir quiz-app && cd quiz-app

# Start all services
docker-compose up --build

# Access application
# Frontend: http://localhost:5000
# Quiz API: http://localhost:5001/api/quizzes
# Session API: http://localhost:5002/api/sessions
```

### Sample Quiz Data (init-db.sql)
```sql
-- Insert sample quiz
INSERT INTO quizzes (title, description) VALUES
('Python Basics', 'Test your Python knowledge');

-- Insert questions
INSERT INTO questions (quiz_id, question_text) VALUES
(1, 'What is the output of print(type([]))?'),
(1, 'Which keyword is used to define a function in Python?');

-- Insert answers
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(1, '<class ''list''>', true),
(1, '<class ''array''>', false),
(1, '<class ''tuple''>', false),
(2, 'def', true),
(2, 'function', false),
(2, 'func', false);
```

---

## Potential Enhancements

### Phase 2 (Post-Weekend)
- Add API Gateway (nginx or custom)
- Implement caching layer
- Add monitoring (Prometheus + Grafana)
- Add logging aggregation
- Create admin panel
- Add quiz categories and tags
- Implement timed quizzes
- Add quiz statistics service

### Scaling Considerations
- Redis for Quiz Service caching (reduce DB reads)
- Load balancer for Frontend
- Read replicas for PostgreSQL
- Separate databases per service
- Message queue for async operations (RabbitMQ/Kafka)

---

## Success Criteria

By end of weekend, you should have:
- ✅ All 5 services running in Docker Compose
- ✅ Ability to create and take quizzes
- ✅ Score calculation working
- ✅ Leaderboard displaying top scores
- ✅ Simple but functional UI
- ✅ At least 2-3 sample quizzes with 10+ questions each
- ✅ README with setup instructions

---

## Notes

- **No user auth**: Sessions are ephemeral, identified only by UUID
- **Data persistence**: Only results and leaderboard persist; sessions expire
- **Error handling**: Keep it simple; basic try-catch with JSON error responses
- **Testing**: Manual testing via browser is sufficient for MVP
- **Security**: Not a concern for MVP (no user data, no auth)

This architecture strikes a balance between microservice principles and weekend-implementability. It's educational, practical, and can be extended post-MVP.

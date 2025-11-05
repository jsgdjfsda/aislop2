#!/bin/bash
# Test script for Microservice Quiz Application

set -e

echo "=========================================="
echo "Microservice Quiz Application Test Suite"
echo "=========================================="
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
FRONTEND_URL="http://localhost:5000"
QUIZ_SERVICE_URL="http://localhost:5001"
SESSION_SERVICE_URL="http://localhost:5002"
RESULTS_SERVICE_URL="http://localhost:5003"
LEADERBOARD_SERVICE_URL="http://localhost:5004"

# Function to print test results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        exit 1
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠ WARNING${NC}: $1"
}

print_info() {
    echo -e "ℹ INFO: $1"
}

# Check if Docker is running
echo "Step 1: Checking Docker..."
if ! command -v docker &> /dev/null; then
    print_warning "Docker is not installed"
    exit 1
fi
print_result 0 "Docker is installed"

# Check if Docker Compose is available
echo
echo "Step 2: Checking Docker Compose..."
if docker compose version &> /dev/null; then
    print_result 0 "Docker Compose V2 is available"
    COMPOSE_CMD="docker compose"
elif docker-compose --version &> /dev/null; then
    print_result 0 "Docker Compose V1 is available"
    COMPOSE_CMD="docker-compose"
else
    print_warning "Docker Compose is not available"
    exit 1
fi

# Start services
echo
echo "Step 3: Starting services..."
print_info "Running: $COMPOSE_CMD up -d --build"
$COMPOSE_CMD up -d --build

# Wait for services to be healthy
echo
echo "Step 4: Waiting for services to be healthy..."
print_info "This may take 30-60 seconds..."
sleep 10

max_attempts=30
attempt=0
all_healthy=false

while [ $attempt -lt $max_attempts ]; do
    if $COMPOSE_CMD ps | grep -q "unhealthy"; then
        attempt=$((attempt + 1))
        sleep 2
    else
        all_healthy=true
        break
    fi
done

if [ "$all_healthy" = true ]; then
    print_result 0 "All services started successfully"
else
    print_warning "Some services may not be healthy yet"
fi

# Show service status
echo
echo "Service Status:"
$COMPOSE_CMD ps

# Wait a bit more for services to fully initialize
sleep 5

# Test Quiz Service
echo
echo "=========================================="
echo "Testing Quiz Service (Port 5001)"
echo "=========================================="

echo "Test 1.1: Health check"
if curl -s -f "$QUIZ_SERVICE_URL/health" > /dev/null; then
    print_result 0 "Quiz Service health check"
else
    print_result 1 "Quiz Service health check"
fi

echo "Test 1.2: Get all quizzes"
QUIZZES=$(curl -s "$QUIZ_SERVICE_URL/api/quizzes")
QUIZ_COUNT=$(echo $QUIZZES | grep -o '"id":' | wc -l)
if [ $QUIZ_COUNT -ge 3 ]; then
    print_result 0 "Retrieved $QUIZ_COUNT quizzes"
else
    print_result 1 "Failed to retrieve quizzes"
fi

echo "Test 1.3: Get specific quiz"
if curl -s -f "$QUIZ_SERVICE_URL/api/quizzes/1" > /dev/null; then
    print_result 0 "Retrieved quiz #1"
else
    print_result 1 "Failed to retrieve quiz #1"
fi

echo "Test 1.4: Get quiz questions"
QUESTIONS=$(curl -s "$QUIZ_SERVICE_URL/api/quizzes/1/questions")
QUESTION_COUNT=$(echo $QUESTIONS | grep -o '"id":' | wc -l)
if [ $QUESTION_COUNT -ge 1 ]; then
    print_result 0 "Retrieved $QUESTION_COUNT questions for quiz #1"
else
    print_result 1 "Failed to retrieve questions"
fi

# Test Session Service
echo
echo "=========================================="
echo "Testing Session Service (Port 5002)"
echo "=========================================="

echo "Test 2.1: Health check"
if curl -s -f "$SESSION_SERVICE_URL/health" > /dev/null; then
    print_result 0 "Session Service health check"
else
    print_result 1 "Session Service health check"
fi

echo "Test 2.2: Start a new session"
SESSION_RESPONSE=$(curl -s -X POST "$SESSION_SERVICE_URL/api/sessions/start" \
    -H "Content-Type: application/json" \
    -d '{"quiz_id": 1}')
SESSION_ID=$(echo $SESSION_RESPONSE | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$SESSION_ID" ]; then
    print_result 0 "Created session: $SESSION_ID"
else
    print_result 1 "Failed to create session"
fi

echo "Test 2.3: Submit an answer"
if curl -s -f -X POST "$SESSION_SERVICE_URL/api/sessions/$SESSION_ID/answer" \
    -H "Content-Type: application/json" \
    -d '{"question_id": 1, "answer_id": 1}' > /dev/null; then
    print_result 0 "Submitted answer to session"
else
    print_result 1 "Failed to submit answer"
fi

echo "Test 2.4: Get session details"
if curl -s -f "$SESSION_SERVICE_URL/api/sessions/$SESSION_ID" > /dev/null; then
    print_result 0 "Retrieved session details"
else
    print_result 1 "Failed to retrieve session"
fi

echo "Test 2.5: Complete session"
if curl -s -f -X POST "$SESSION_SERVICE_URL/api/sessions/$SESSION_ID/complete" > /dev/null; then
    print_result 0 "Completed session"
else
    print_result 1 "Failed to complete session"
fi

# Test Results Service
echo
echo "=========================================="
echo "Testing Results Service (Port 5003)"
echo "=========================================="

echo "Test 3.1: Health check"
if curl -s -f "$RESULTS_SERVICE_URL/health" > /dev/null; then
    print_result 0 "Results Service health check"
else
    print_result 1 "Results Service health check"
fi

echo "Test 3.2: Calculate results"
RESULT_RESPONSE=$(curl -s -X POST "$RESULTS_SERVICE_URL/api/results/calculate" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\": \"$SESSION_ID\"}")
SCORE=$(echo $RESULT_RESPONSE | grep -o '"score":[0-9]*' | cut -d':' -f2)

if [ -n "$SCORE" ]; then
    print_result 0 "Calculated score: $SCORE"
else
    print_result 1 "Failed to calculate results"
fi

echo "Test 3.3: Get results"
if curl -s -f "$RESULTS_SERVICE_URL/api/results/$SESSION_ID" > /dev/null; then
    print_result 0 "Retrieved results for session"
else
    print_result 1 "Failed to retrieve results"
fi

# Test Leaderboard Service
echo
echo "=========================================="
echo "Testing Leaderboard Service (Port 5004)"
echo "=========================================="

echo "Test 4.1: Health check"
if curl -s -f "$LEADERBOARD_SERVICE_URL/health" > /dev/null; then
    print_result 0 "Leaderboard Service health check"
else
    print_result 1 "Leaderboard Service health check"
fi

echo "Test 4.2: Submit to leaderboard"
if curl -s -f -X POST "$LEADERBOARD_SERVICE_URL/api/leaderboard" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\": \"$SESSION_ID\", \"quiz_id\": 1, \"nickname\": \"TestUser\", \"score\": $SCORE, \"total\": 10}" > /dev/null; then
    print_result 0 "Submitted score to leaderboard"
else
    print_result 1 "Failed to submit to leaderboard"
fi

echo "Test 4.3: Get leaderboard"
LEADERBOARD=$(curl -s "$LEADERBOARD_SERVICE_URL/api/leaderboard/1")
if echo $LEADERBOARD | grep -q "TestUser"; then
    print_result 0 "Retrieved leaderboard with test entry"
else
    print_result 1 "Failed to retrieve leaderboard"
fi

# Test Frontend
echo
echo "=========================================="
echo "Testing Frontend (Port 5000)"
echo "=========================================="

echo "Test 5.1: Homepage accessibility"
if curl -s -f "$FRONTEND_URL/" > /dev/null; then
    print_result 0 "Frontend homepage is accessible"
else
    print_result 1 "Frontend homepage is not accessible"
fi

echo "Test 5.2: Homepage contains quiz links"
HOMEPAGE=$(curl -s "$FRONTEND_URL/")
if echo $HOMEPAGE | grep -q "Python Basics"; then
    print_result 0 "Homepage displays quizzes"
else
    print_result 1 "Homepage doesn't display quizzes"
fi

# Summary
echo
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo
print_result 0 "All tests passed successfully!"
echo
echo "Application URLs:"
echo "  Frontend:    $FRONTEND_URL"
echo "  Quiz API:    $QUIZ_SERVICE_URL/api/quizzes"
echo "  Session API: $SESSION_SERVICE_URL"
echo "  Results API: $RESULTS_SERVICE_URL"
echo "  Leaderboard: $LEADERBOARD_SERVICE_URL"
echo
echo "To view logs: $COMPOSE_CMD logs -f"
echo "To stop: $COMPOSE_CMD down"
echo "To stop and remove data: $COMPOSE_CMD down -v"
echo
print_info "Open $FRONTEND_URL in your browser to use the application!"

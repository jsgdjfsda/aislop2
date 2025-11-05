-- Quiz Service Tables
CREATE TABLE IF NOT EXISTS quizzes (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    quiz_id INTEGER REFERENCES quizzes(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) DEFAULT 'multiple_choice'
);

CREATE TABLE IF NOT EXISTS answers (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    answer_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE
);

-- Results Service Tables
CREATE TABLE IF NOT EXISTS results (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    quiz_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Leaderboard Service Tables
CREATE TABLE IF NOT EXISTS leaderboard (
    id SERIAL PRIMARY KEY,
    quiz_id INTEGER NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    nickname VARCHAR(100) NOT NULL,
    score INTEGER NOT NULL,
    percentage DECIMAL(5,2) NOT NULL,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quiz_score ON leaderboard(quiz_id, score DESC);

-- Sample Data: Python Basics Quiz
INSERT INTO quizzes (title, description) VALUES
('Python Basics', 'Test your fundamental Python knowledge with this beginner-friendly quiz!');

INSERT INTO questions (quiz_id, question_text, question_type) VALUES
(1, 'What is the output of: print(type([]))?', 'multiple_choice'),
(1, 'Which keyword is used to define a function in Python?', 'multiple_choice'),
(1, 'What does the len() function do?', 'multiple_choice'),
(1, 'Which of the following is a mutable data type in Python?', 'multiple_choice'),
(1, 'What is the correct way to create a dictionary in Python?', 'multiple_choice'),
(1, 'Python is an interpreted language.', 'true_false'),
(1, 'In Python, indentation is optional.', 'true_false'),
(1, 'What will "Hello" + "World" output?', 'multiple_choice'),
(1, 'Which operator is used for exponentiation in Python?', 'multiple_choice'),
(1, 'What is the output of: print(3 == 3.0)?', 'multiple_choice');

-- Answers for Question 1: What is the output of: print(type([]))?
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(1, '<class ''list''>', true),
(1, '<class ''array''>', false),
(1, '<class ''tuple''>', false),
(1, '<class ''dict''>', false);

-- Answers for Question 2: Which keyword is used to define a function?
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(2, 'def', true),
(2, 'function', false),
(2, 'func', false),
(2, 'define', false);

-- Answers for Question 3: What does the len() function do?
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(3, 'Returns the length of an object', true),
(3, 'Converts to lowercase', false),
(3, 'Creates a new list', false),
(3, 'Sorts a sequence', false);

-- Answers for Question 4: Which is a mutable data type?
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(4, 'List', true),
(4, 'Tuple', false),
(4, 'String', false),
(4, 'Integer', false);

-- Answers for Question 5: Correct way to create a dictionary?
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(5, '{"key": "value"}', true),
(5, '["key", "value"]', false),
(5, '("key", "value")', false),
(5, 'dict["key"] = "value"', false);

-- Answers for Question 6: Python is an interpreted language (True/False)
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(6, 'True', true),
(6, 'False', false);

-- Answers for Question 7: Indentation is optional (True/False)
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(7, 'False', true),
(7, 'True', false);

-- Answers for Question 8: "Hello" + "World" output?
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(8, 'HelloWorld', true),
(8, 'Hello World', false),
(8, 'Error', false),
(8, 'Hello+World', false);

-- Answers for Question 9: Exponentiation operator?
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(9, '**', true),
(9, '^', false),
(9, 'exp()', false),
(9, '^^', false);

-- Answers for Question 10: print(3 == 3.0)?
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(10, 'True', true),
(10, 'False', false),
(10, 'Error', false),
(10, 'None', false);

-- Sample Data: JavaScript Quiz
INSERT INTO quizzes (title, description) VALUES
('JavaScript Fundamentals', 'Challenge yourself with JavaScript basics and ES6 features!');

INSERT INTO questions (quiz_id, question_text, question_type) VALUES
(2, 'What keyword is used to declare a block-scoped variable in JavaScript?', 'multiple_choice'),
(2, 'Which method is used to add an element to the end of an array?', 'multiple_choice'),
(2, 'JavaScript is a statically typed language.', 'true_false'),
(2, 'What does === operator do?', 'multiple_choice'),
(2, 'Which of the following is NOT a valid JavaScript data type?', 'multiple_choice'),
(2, 'Arrow functions were introduced in ES6.', 'true_false'),
(2, 'What is the output of: typeof null?', 'multiple_choice'),
(2, 'Which method converts a JSON string to a JavaScript object?', 'multiple_choice'),
(2, 'const variables can be reassigned.', 'true_false'),
(2, 'What does the spread operator (...) do?', 'multiple_choice');

-- JS Q1: block-scoped variable
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(11, 'let', true),
(11, 'var', false),
(11, 'const', false),
(11, 'Both let and const', false);

-- JS Q2: add element to array end
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(12, 'push()', true),
(12, 'pop()', false),
(12, 'shift()', false),
(12, 'unshift()', false);

-- JS Q3: statically typed (T/F)
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(13, 'False', true),
(13, 'True', false);

-- JS Q4: === operator
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(14, 'Checks both value and type equality', true),
(14, 'Checks only value equality', false),
(14, 'Assignment operator', false),
(14, 'Greater than or equal to', false);

-- JS Q5: NOT a valid data type
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(15, 'character', true),
(15, 'string', false),
(15, 'number', false),
(15, 'boolean', false);

-- JS Q6: Arrow functions in ES6 (T/F)
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(16, 'True', true),
(16, 'False', false);

-- JS Q7: typeof null
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(17, 'object', true),
(17, 'null', false),
(17, 'undefined', false),
(17, 'number', false);

-- JS Q8: JSON to object
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(18, 'JSON.parse()', true),
(18, 'JSON.stringify()', false),
(18, 'JSON.convert()', false),
(18, 'JSON.toObject()', false);

-- JS Q9: const reassignment (T/F)
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(19, 'False', true),
(19, 'True', false);

-- JS Q10: spread operator
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(20, 'Expands an iterable into individual elements', true),
(20, 'Creates a new array', false),
(20, 'Multiplies numbers', false),
(20, 'Divides numbers', false);

-- Sample Data: Docker Basics Quiz
INSERT INTO quizzes (title, description) VALUES
('Docker & Containers', 'Test your knowledge of Docker and containerization concepts!');

INSERT INTO questions (quiz_id, question_text, question_type) VALUES
(3, 'What is Docker?', 'multiple_choice'),
(3, 'Which file defines the instructions to build a Docker image?', 'multiple_choice'),
(3, 'Docker containers share the host OS kernel.', 'true_false'),
(3, 'What command is used to run a Docker container?', 'multiple_choice'),
(3, 'Which tool orchestrates multiple Docker containers?', 'multiple_choice');

-- Docker Q1: What is Docker?
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(21, 'A containerization platform', true),
(21, 'A virtual machine', false),
(21, 'A programming language', false),
(21, 'An operating system', false);

-- Docker Q2: Build instructions file
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(22, 'Dockerfile', true),
(22, 'docker-compose.yml', false),
(22, 'package.json', false),
(22, 'config.json', false);

-- Docker Q3: Share host kernel (T/F)
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(23, 'True', true),
(23, 'False', false);

-- Docker Q4: Run container command
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(24, 'docker run', true),
(24, 'docker start', false),
(24, 'docker create', false),
(24, 'docker execute', false);

-- Docker Q5: Orchestrate containers
INSERT INTO answers (question_id, answer_text, is_correct) VALUES
(25, 'Docker Compose', true),
(25, 'Docker Swarm', false),
(25, 'Kubernetes', false),
(25, 'All of the above', false);

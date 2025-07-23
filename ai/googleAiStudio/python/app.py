from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import google.generativeai as genai
import json
import os
from datetime import datetime
import uuid
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Configure the Generative AI API (only for AI chat, NOT for quizzes)
genai.configure(api_key="")
model = genai.GenerativeModel("gemini-1.5-flash")

# In-memory storage (in production, use a proper database)
users_data = {}
quiz_results = {}

topics_data = {
    "python": {
        "name": "Python Programming",
        "description": "Learn Python fundamentals, data structures, and object-oriented programming",
        "difficulty": "Beginner to Advanced",
        "icon": "🐍"
    },
    "javascript": {
        "name": "JavaScript Development",
        "description": "Master JavaScript, DOM manipulation, and modern ES6+ features",
        "difficulty": "Beginner to Advanced",
        "icon": "⚡"
    },
    "data_science": {
        "name": "Data Science",
        "description": "Explore data analysis, machine learning, and statistical concepts",
        "difficulty": "Intermediate to Advanced",
        "icon": "📊"
    },
    "web_development": {
        "name": "Web Development",
        "description": "Full-stack web development with HTML, CSS, and frameworks",
        "difficulty": "Beginner to Advanced",
        "icon": "🌐"
    },
    "devops": {
        "name": "DevOps Engineering",
        "description": "CI/CD, containerization, cloud platforms, and automation",
        "difficulty": "Intermediate to Advanced",
        "icon": "🚀"
    }
}

def get_user_id():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']

def initialize_user_data(user_id):
    if user_id not in users_data:
        users_data[user_id] = {
            'total_quizzes': 0,
            'correct_answers': 0,
            'total_questions': 0,
            'topics_progress': {},
            'quiz_history': []
        }

@app.route("/")
def index():
    return render_template("index.html", topics=topics_data)

@app.route("/ask_ai", methods=["POST"])
def ask_ai():
    """Handle AI questions from users - ONLY for AI chat, NOT quizzes"""
    try:
        user_question = request.form.get('user_question', '').strip()
        if not user_question:
            return jsonify({'error': 'Please enter a question'})

        print(f"User question: {user_question}")  # Debug log

        # Simple, direct prompt for Gemini
        prompt = f"Please answer this question clearly and helpfully: {user_question}"

        # Generate response using Gemini API
        response = model.generate_content(prompt)
        ai_response = response.text.strip()

        print(f"AI response: {ai_response[:100]}...")  # Debug log

        # Format the response
        formatted_response = format_ai_response(ai_response)

        return jsonify({
            'success': True,
            'question': user_question,
            'answer': formatted_response
        })

    except Exception as e:
        print(f"Error in ask_ai: {str(e)}")  # Debug log
        return jsonify({
            'error': f'Sorry, I encountered an error: {str(e)}. Please try again.'
        })

def format_ai_response(content):
    """Format AI response for better display"""
    # Convert basic markdown to HTML
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
    content = re.sub(r'`([^`]+)`', r'<code class="inline-code">\1</code>', content)

    # Convert numbered lists
    content = re.sub(r'^(\d+)\.\s+(.*)$', r'<div class="list-item"><span class="list-number">\1.</span> \2</div>', content, flags=re.MULTILINE)

    # Convert bullet points
    content = re.sub(r'^[\*\-]\s+(.*)$', r'<div class="list-item"><span class="bullet">•</span> \1</div>', content, flags=re.MULTILINE)

    # Convert line breaks to paragraphs
    paragraphs = content.split('\n\n')
    formatted_paragraphs = []
    for para in paragraphs:
        para = para.strip()
        if para:
            if not para.startswith('<'):
                para = f'<p>{para}</p>'
            formatted_paragraphs.append(para)

    return '\n'.join(formatted_paragraphs)

@app.route("/topic/<topic_id>")
def topic_detail(topic_id):
    if topic_id not in topics_data:
        return redirect(url_for('index'))

    topic = topics_data[topic_id]
    user_id = get_user_id()
    initialize_user_data(user_id)

    # Get user progress for this topic
    progress = users_data[user_id]['topics_progress'].get(topic_id, {
        'quizzes_taken': 0,
        'average_score': 0,
        'best_score': 0
    })

    return render_template("topic_detail.html", topic=topic, topic_id=topic_id, progress=progress)

@app.route("/generate_quiz/<topic_id>")
def generate_quiz(topic_id):
    """Generate quiz with PREDEFINED questions - NO AI involved"""
    if topic_id not in topics_data:
        return redirect(url_for('index'))

    topic = topics_data[topic_id]
    
    # Use predefined questions for reliability - NO AI GENERATION
    quiz_questions = get_quiz_questions(topic_id)
    quiz_id = str(uuid.uuid4())
    
    session['current_quiz'] = {
        'id': quiz_id,
        'topic_id': topic_id,
        'topic_name': topic['name'],
        'questions': quiz_questions,
        'start_time': datetime.now().isoformat()
    }

    print(f"Generated quiz for {topic_id} with {len(quiz_questions)} questions")
    return render_template("quiz.html", quiz=session['current_quiz'])

def get_quiz_questions(topic_id):
    """Get predefined quiz questions - NO AI, just hardcoded questions"""
    quiz_questions = {
        "python": [
            {
                "question": "What is the correct way to create a variable in Python?",
                "options": {
                    "A": "var x = 5",
                    "B": "x = 5",
                    "C": "int x = 5",
                    "D": "create x = 5"
                },
                "correct_answer": "B",
                "explanation": "In Python, you create variables by simply assigning a value using the = operator."
            },
            {
                "question": "Which data type is used to store text in Python?",
                "options": {
                    "A": "int",
                    "B": "float",
                    "C": "str",
                    "D": "bool"
                },
                "correct_answer": "C",
                "explanation": "The 'str' data type is used to store text/string values in Python."
            },
            {
                "question": "What does the len() function do?",
                "options": {
                    "A": "Returns the length of an object",
                    "B": "Creates a new list",
                    "C": "Converts to integer",
                    "D": "Prints to console"
                },
                "correct_answer": "A",
                "explanation": "The len() function returns the number of items in an object like a string, list, or tuple."
            },
            {
                "question": "Which symbol is used for comments in Python?",
                "options": {
                    "A": "//",
                    "B": "/* */",
                    "C": "#",
                    "D": "--"
                },
                "correct_answer": "C",
                "explanation": "The # symbol is used to create single-line comments in Python."
            },
            {
                "question": "What is the output of print(type(5.0))?",
                "options": {
                    "A": "<class 'int'>",
                    "B": "<class 'float'>",
                    "C": "<class 'str'>",
                    "D": "<class 'number'>"
                },
                "correct_answer": "B",
                "explanation": "5.0 is a floating-point number, so its type is 'float'."
            }
        ],
        "javascript": [
            {
                "question": "How do you declare a variable in JavaScript?",
                "options": {
                    "A": "var x = 5",
                    "B": "variable x = 5",
                    "C": "v x = 5",
                    "D": "declare x = 5"
                },
                "correct_answer": "A",
                "explanation": "In JavaScript, you can declare variables using 'var', 'let', or 'const'."
            },
            {
                "question": "Which method is used to add an element to the end of an array?",
                "options": {
                    "A": "add()",
                    "B": "append()",
                    "C": "push()",
                    "D": "insert()"
                },
                "correct_answer": "C",
                "explanation": "The push() method adds one or more elements to the end of an array."
            },
            {
                "question": "What is the correct way to write a JavaScript function?",
                "options": {
                    "A": "function myFunction() {}",
                    "B": "def myFunction() {}",
                    "C": "create myFunction() {}",
                    "D": "func myFunction() {}"
                },
                "correct_answer": "A",
                "explanation": "JavaScript functions are declared using the 'function' keyword."
            },
            {
                "question": "Which operator is used for strict equality in JavaScript?",
                "options": {
                    "A": "=",
                    "B": "==",
                    "C": "===",
                    "D": "!="
                },
                "correct_answer": "C",
                "explanation": "The === operator checks for strict equality (same value and same type)."
            },
            {
                "question": "How do you write a single-line comment in JavaScript?",
                "options": {
                    "A": "# This is a comment",
                    "B": "// This is a comment",
                    "C": "<!-- This is a comment -->",
                    "D": "/* This is a comment */"
                },
                "correct_answer": "B",
                "explanation": "Single-line comments in JavaScript start with //."
            }
        ],
        "data_science": [
            {
                "question": "What does CSV stand for?",
                "options": {
                    "A": "Computer Separated Values",
                    "B": "Comma Separated Values",
                    "C": "Character Separated Values",
                    "D": "Code Separated Values"
                },
                "correct_answer": "B",
                "explanation": "CSV stands for Comma Separated Values, a common data format."
            },
            {
                "question": "Which Python library is commonly used for data manipulation?",
                "options": {
                    "A": "NumPy",
                    "B": "Pandas",
                    "C": "Matplotlib",
                    "D": "Scikit-learn"
                },
                "correct_answer": "B",
                "explanation": "Pandas is the most popular Python library for data manipulation and analysis."
            },
            {
                "question": "What is the purpose of data visualization?",
                "options": {
                    "A": "To make data look pretty",
                    "B": "To understand patterns and insights in data",
                    "C": "To increase file size",
                    "D": "To slow down analysis"
                },
                "correct_answer": "B",
                "explanation": "Data visualization helps us understand patterns, trends, and insights in data."
            },
            {
                "question": "What is machine learning?",
                "options": {
                    "A": "Teaching computers to learn from data",
                    "B": "A type of hardware",
                    "C": "A programming language",
                    "D": "A database system"
                },
                "correct_answer": "A",
                "explanation": "Machine learning is a method of teaching computers to learn patterns from data."
            },
            {
                "question": "Which measure represents the middle value in a dataset?",
                "options": {
                    "A": "Mean",
                    "B": "Mode",
                    "C": "Median",
                    "D": "Range"
                },
                "correct_answer": "C",
                "explanation": "The median is the middle value when data is arranged in order."
            }
        ],
        "web_development": [
            {
                "question": "What does HTML stand for?",
                "options": {
                    "A": "Hyper Text Markup Language",
                    "B": "High Tech Modern Language",
                    "C": "Home Tool Markup Language",
                    "D": "Hyperlink and Text Markup Language"
                },
                "correct_answer": "A",
                "explanation": "HTML stands for Hyper Text Markup Language, used to create web pages."
            },
            {
                "question": "Which CSS property is used to change text color?",
                "options": {
                    "A": "text-color",
                    "B": "font-color",
                    "C": "color",
                    "D": "text-style"
                },
                "correct_answer": "C",
                "explanation": "The 'color' property in CSS is used to set the text color."
            },
            {
                "question": "What is the purpose of CSS?",
                "options": {
                    "A": "To add interactivity to web pages",
                    "B": "To style and layout web pages",
                    "C": "To create databases",
                    "D": "To handle server requests"
                },
                "correct_answer": "B",
                "explanation": "CSS (Cascading Style Sheets) is used to style and layout web pages."
            },
            {
                "question": "Which HTML tag is used to create a hyperlink?",
                "options": {
                    "A": "<link>",
                    "B": "<a>",
                    "C": "<href>",
                    "D": "<url>"
                },
                "correct_answer": "B",
                "explanation": "The <a> tag with the href attribute is used to create hyperlinks."
            },
            {
                "question": "What is responsive web design?",
                "options": {
                    "A": "Fast loading websites",
                    "B": "Websites that work on different screen sizes",
                    "C": "Websites with animations",
                    "D": "Websites that respond to user input"
                },
                "correct_answer": "B",
                "explanation": "Responsive web design ensures websites work well on different devices and screen sizes."
            }
        ],
        "devops": [
            {
                "question": "What does CI/CD stand for?",
                "options": {
                    "A": "Computer Integration/Computer Deployment",
                    "B": "Continuous Integration/Continuous Deployment",
                    "C": "Code Integration/Code Deployment",
                    "D": "Central Integration/Central Deployment"
                },
                "correct_answer": "B",
                "explanation": "CI/CD stands for Continuous Integration/Continuous Deployment."
            },
            {
                "question": "What is Docker used for?",
                "options": {
                    "A": "Database management",
                    "B": "Containerization of applications",
                    "C": "Web development",
                    "D": "Network security"
                },
                "correct_answer": "B",
                "explanation": "Docker is a platform for containerizing applications, making them portable and scalable."
            },
            {
                "question": "What is the main benefit of version control systems like Git?",
                "options": {
                    "A": "Faster code execution",
                    "B": "Track changes and collaborate on code",
                    "C": "Automatic bug fixing",
                    "D": "Better user interfaces"
                },
                "correct_answer": "B",
                "explanation": "Version control systems help track changes in code and enable team collaboration."
            },
            {
                "question": "What is Infrastructure as Code (IaC)?",
                "options": {
                    "A": "Writing code for mobile apps",
                    "B": "Managing infrastructure through code",
                    "C": "Creating user interfaces",
                    "D": "Database programming"
                },
                "correct_answer": "B",
                "explanation": "IaC is the practice of managing and provisioning infrastructure through code."
            },
            {
                "question": "What is the purpose of monitoring in DevOps?",
                "options": {
                    "A": "To watch employees work",
                    "B": "To track application performance and health",
                    "C": "To count lines of code",
                    "D": "To manage user accounts"
                },
                "correct_answer": "B",
                "explanation": "Monitoring helps track application performance, health, and identify issues early."
            }
        ]
    }

    return quiz_questions.get(topic_id, quiz_questions["python"])

@app.route("/submit_quiz", methods=["POST"])
def submit_quiz():
    """Submit quiz with PREDEFINED answers - NO AI grading"""
    if 'current_quiz' not in session:
        print("ERROR: No current quiz in session")
        return redirect(url_for('index'))

    quiz = session['current_quiz']
    user_answers = {}
    
    print("=== QUIZ SUBMISSION DEBUG ===")
    print(f"Form data received: {dict(request.form)}")
    print(f"Number of questions in quiz: {len(quiz['questions'])}")

    # Collect user answers with better error handling
    for i in range(len(quiz['questions'])):
        answer_key = f'question_{i}'
        user_answer = request.form.get(answer_key)
        user_answers[i] = user_answer
        print(f"Question {i}: {answer_key} = {user_answer}")

    # Check if all questions are answered
    unanswered_questions = []
    for i in range(len(quiz['questions'])):
        if not user_answers.get(i):
            unanswered_questions.append(i + 1)

    if unanswered_questions:
        print(f"Unanswered questions: {unanswered_questions}")
        # Return to quiz with error message
        error_message = f"Please answer question(s): {', '.join(map(str, unanswered_questions))}"
        return render_template("quiz.html", quiz=quiz, error_message=error_message)

    # Calculate score using PREDEFINED correct answers
    correct_count = 0
    results = []
    
    for i, question in enumerate(quiz['questions']):
        user_answer = user_answers.get(i)
        is_correct = user_answer == question['correct_answer']
        if is_correct:
            correct_count += 1
        
        results.append({
            'question': question['question'],
            'user_answer': user_answer,
            'correct_answer': question['correct_answer'],
            'is_correct': is_correct,
            'explanation': question['explanation'],
            'options': question['options']
        })

    score = (correct_count / len(quiz['questions'])) * 100
    print(f"Final score: {score}% ({correct_count}/{len(quiz['questions'])})")

    # Update user data
    user_id = get_user_id()
    initialize_user_data(user_id)
    user_data = users_data[user_id]
    
    user_data['total_quizzes'] += 1
    user_data['correct_answers'] += correct_count
    user_data['total_questions'] += len(quiz['questions'])

    # Update topic progress
    topic_id = quiz['topic_id']
    if topic_id not in user_data['topics_progress']:
        user_data['topics_progress'][topic_id] = {
            'quizzes_taken': 0,
            'total_score': 0,
            'best_score': 0
        }

    topic_progress = user_data['topics_progress'][topic_id]
    topic_progress['quizzes_taken'] += 1
    topic_progress['total_score'] += score
    topic_progress['average_score'] = topic_progress['total_score'] / topic_progress['quizzes_taken']
    topic_progress['best_score'] = max(topic_progress['best_score'], score)

    # Add to quiz history
    quiz_result = {
        'quiz_id': quiz['id'],
        'topic_id': topic_id,
        'topic_name': quiz['topic_name'],
        'score': score,
        'correct_answers': correct_count,
        'total_questions': len(quiz['questions']),
        'date': datetime.now().isoformat(),
        'results': results
    }
    user_data['quiz_history'].append(quiz_result)

    # Generate AI feedback (this is the ONLY place AI is used for quizzes)
    feedback = generate_feedback(score, correct_count, len(quiz['questions']), quiz['topic_name'])

    # Clear current quiz from session
    session.pop('current_quiz', None)

    return render_template("quiz_results.html", quiz_result=quiz_result, results=results, feedback=feedback)

def generate_feedback(score, correct_answers, total_questions, topic_name):
    """Generate AI feedback for quiz results - ONLY for feedback, not grading"""
    try:
        prompt = f"A student scored {score:.1f}% ({correct_answers}/{total_questions}) on a {topic_name} quiz. Give encouraging feedback in 2-3 sentences."
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "Great job completing the quiz! Keep practicing to improve your skills."

@app.route("/dashboard")
def dashboard():
    user_id = get_user_id()
    initialize_user_data(user_id)
    user_data = users_data[user_id]

    # Calculate overall statistics
    overall_accuracy = 0
    if user_data['total_questions'] > 0:
        overall_accuracy = (user_data['correct_answers'] / user_data['total_questions']) * 100

    # Get recent quiz history (last 5)
    recent_quizzes = user_data['quiz_history'][-5:] if user_data['quiz_history'] else []
    recent_quizzes.reverse()  # Show most recent first

    return render_template("dashboard.html", 
                         user_data=user_data, 
                         overall_accuracy=overall_accuracy,
                         recent_quizzes=recent_quizzes,
                         topics=topics_data)

@app.route("/study_material/<topic_id>")
def study_material(topic_id):
    if topic_id not in topics_data:
        return redirect(url_for('index'))

    topic = topics_data[topic_id]
    
    # Generate study material using Gemini API
    try:
        prompt = f"Create comprehensive study material for {topic['name']}. Include key concepts, examples, and learning tips. Format with clear headings."
        response = model.generate_content(prompt)
        study_content = format_study_content(response.text)
        return render_template("study_material.html", topic=topic, topic_id=topic_id, content=study_content)
    except Exception as e:
        return render_template("error.html", message="Failed to generate study material.")

def format_study_content(content):
    """Convert markdown-like content to HTML"""
    # Convert headers
    content = re.sub(r'^### (.*$)', r'<h3>\1</h3>', content, flags=re.MULTILINE)
    content = re.sub(r'^## (.*$)', r'<h2>\1</h2>', content, flags=re.MULTILINE)
    content = re.sub(r'^# (.*$)', r'<h1>\1</h1>', content, flags=re.MULTILINE)

    # Convert bold text
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)

    # Convert italic text
    content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)

    # Convert code blocks
    content = re.sub(r'\`\`\`python\n(.*?)\n\`\`\`', r'<pre class="code-block"><code>\1</code></pre>', content, flags=re.DOTALL)
    content = re.sub(r'\`\`\`(.*?)\n(.*?)\n\`\`\`', r'<pre class="code-block"><code>\2</code></pre>', content, flags=re.DOTALL)

    # Convert inline code
    content = re.sub(r'`([^`]+)`', r'<code class="inline-code">\1</code>', content)

    # Convert bullet points
    lines = content.split('\n')
    formatted_lines = []
    in_list = False
    for line in lines:
        if line.strip().startswith('* '):
            if not in_list:
                formatted_lines.append('<ul>')
                in_list = True
            formatted_lines.append(f'<li>{line.strip()[2:]}</li>')
        else:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            formatted_lines.append(line)

    if in_list:
        formatted_lines.append('</ul>')

    content = '\n'.join(formatted_lines)

    # Convert line breaks to paragraphs
    paragraphs = content.split('\n\n')
    formatted_paragraphs = []
    for para in paragraphs:
        para = para.strip()
        if para and not para.startswith('<'):
            para = f'<p>{para}</p>'
        if para:
            formatted_paragraphs.append(para)

    return '\n'.join(formatted_paragraphs)

if __name__ == "__main__":
    app.run(debug=True)

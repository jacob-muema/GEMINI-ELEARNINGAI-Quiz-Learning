from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import google.generativeai as genai
import json
import os
import sqlite3
import requests
import secrets
import urllib.parse
from datetime import datetime
import uuid
import re
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, init_db
from functools import wraps

# Load .env file automatically if present
env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_file):
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())
    except Exception as e:
        print(f"Notice: Could not load .env file: {e}")

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in_user' not in session:
            target_url = request.full_path if request.query_string else request.path
            return redirect(url_for('register', next=target_url, message="Please sign up or log in to access course contents and start your learning journey!"))
        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Initialize persistent SQLite database
init_db()

# Configure the Generative AI API (only for AI chat, NOT for quizzes)
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-3.8-flash")
else:
    model = None

# In-memory storage (in production, use a proper database)
users_data = {}
quiz_results = {}

topics_data = {
    "az900": {
        "name": "Microsoft Azure Fundamentals (AZ-900)",
        "description": "Understand cloud concepts, core Azure architectural components, compute and storage services, Azure management, governance, and security.",
        "difficulty": "Beginner",
        "icon": "",
        "logo": "/static/images/logos/azure_az900.svg",
        "vendor_logo": "/static/images/logos/azure.svg",
        "code": "AZ-900"
    },
    "az400": {
        "name": "Microsoft AZ-400: DevOps Solutions",
        "description": "Design and implement strategies for source control, CI/CD pipelines, containerization, infrastructure as code, and compliance on Azure.",
        "difficulty": "Intermediate to Advanced",
        "icon": "♾️",
        "logo": "/static/images/logos/azure_az400.svg",
        "vendor_logo": "/static/images/logos/azure.svg",
        "code": "AZ-400"
    },
    "aws_solutions_architect": {
        "name": "AWS Solutions Architect (SAA-C03)",
        "description": "Design resilient, high-performing, secure, and cost-optimized architectures on Amazon Web Services.",
        "difficulty": "Intermediate",
        "icon": "☁️",
        "logo": "/static/images/logos/aws_solutions_architect.svg",
        "vendor_logo": "/static/images/logos/aws.svg",
        "code": "SAA-C03"
    },
    "comptia_security": {
        "name": "CompTIA Security+ (SY0-701)",
        "description": "Master core cybersecurity principles, threats, attacks, vulnerabilities, cryptographic controls, identity management, and incident response.",
        "difficulty": "Beginner to Intermediate",
        "icon": "🛡️",
        "logo": "/static/images/logos/comptia_security.svg",
        "vendor_logo": "/static/images/logos/comptia.svg",
        "code": "SY0-701"
    },
    "itil_foundation": {
        "name": "ITIL 4 Foundation",
        "description": "Learn IT Service Management (ITSM), the Service Value System, Four Dimensions of Service Management, and Guiding Principles.",
        "difficulty": "Beginner to Intermediate",
        "icon": "📋",
        "logo": "/static/images/logos/itil.svg",
        "vendor_logo": "/static/images/logos/itil.svg",
        "code": "ITIL-4"
    },
    "cisco_ccna": {
        "name": "Cisco CCNA (200-301)",
        "description": "Master network fundamentals, IP routing, switching, VLANs, Spanning Tree, EtherChannel, network security, and automation.",
        "difficulty": "Intermediate",
        "icon": "🌐",
        "logo": "/static/images/logos/cisco_ccna.svg",
        "vendor_logo": "/static/images/logos/cisco.svg",
        "code": "200-301"
    },
    "kubernetes_cka": {
        "name": "Certified Kubernetes Administrator (CKA)",
        "description": "Master Kubernetes cluster architecture, workload scheduling, networking, persistent storage, security, and cluster troubleshooting.",
        "difficulty": "Advanced",
        "icon": "☸️",
        "logo": "/static/images/logos/kubernetes_cka.svg",
        "vendor_logo": "/static/images/logos/kubernetes.svg",
        "code": "CKA"
    }
}

def get_user_id():
    # If user is logged into an account, use their persistent account ID
    if 'logged_in_user' in session:
        return f"user_{session['logged_in_user']['id']}"
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

    # If logged in, also try to load stored progress from database
    if 'logged_in_user' in session:
        db_user_id = session['logged_in_user']['id']
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Load AZ-900 module progress
            cursor.execute("SELECT progress_data FROM user_progress WHERE user_id = ? AND topic_id = 'az900'", (db_user_id,))
            row = cursor.fetchone()
            if row:
                users_data[user_id]['az900_progress'] = json.loads(row['progress_data'])
                session['az900_progress'] = users_data[user_id]['az900_progress']
            
            # Load quiz history
            cursor.execute("SELECT * FROM quiz_history WHERE user_id = ? ORDER BY created_at ASC", (db_user_id,))
            db_quizzes = cursor.fetchall()
            if db_quizzes and not users_data[user_id]['quiz_history']:
                for q in db_quizzes:
                    q_res = json.loads(q['results_json']) if q['results_json'] else []
                    users_data[user_id]['quiz_history'].append({
                        'quiz_id': q['quiz_id'],
                        'topic_id': q['topic_id'],
                        'topic_name': q['topic_name'],
                        'score': q['score'],
                        'correct_answers': q['correct_answers'],
                        'total_questions': q['total_questions'],
                        'date': q['created_at'],
                        'results': q_res
                    })
                # Recompute totals
                users_data[user_id]['total_quizzes'] = len(db_quizzes)
                users_data[user_id]['correct_answers'] = sum(q['correct_answers'] for q in db_quizzes)
                users_data[user_id]['total_questions'] = sum(q['total_questions'] for q in db_quizzes)
            conn.close()
        except Exception as e:
            print(f"Database progress load error: {e}")

# =========================================================================
# USER AUTHENTICATION ROUTES (Persistent Account Progress)
# =========================================================================
@app.route("/register", methods=["GET", "POST"])
def register():
    next_page = request.args.get("next") or request.form.get("next") or ""
    message = request.args.get("message") or ""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        display_name = request.form.get("display_name", "").strip() or username

        form_data = {
            "username": username,
            "email": email,
            "display_name": display_name
        }

        if not username or not email or not password or not confirm_password:
            return render_template("register.html", error="All fields are required.", form_data=form_data, next=next_page, message=message)

        if len(username) < 3:
            return render_template("register.html", error="Username must be at least 3 characters long.", form_data=form_data, next=next_page, message=message)

        if len(password) < 6:
            return render_template("register.html", error="Password must be at least 6 characters long.", form_data=form_data, next=next_page, message=message)

        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match. Please verify both passwords.", form_data=form_data, next=next_page, message=message)

        password_hash = generate_password_hash(password)
        accept_terms = request.form.get("accept_terms")
        accept_disclaimer = request.form.get("accept_disclaimer")

        if not accept_terms or not accept_disclaimer:
            return render_template("register.html", error="You must agree to the Terms & Privacy Policy and acknowledge the educational purpose disclaimer.", form_data=form_data, next=next_page, message=message)

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, display_name, accepted_terms, terms_accepted_at) VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)",
                (username, email, password_hash, display_name)
            )
            user_id = cursor.lastrowid
            conn.commit()

            # Migrate any guest progress from current session to this new account
            guest_user_id = session.get('user_id')
            if guest_user_id and guest_user_id in users_data:
                guest_data = users_data[guest_user_id]
                if 'az900_progress' in guest_data:
                    cursor.execute(
                        "INSERT OR REPLACE INTO user_progress (user_id, topic_id, progress_data) VALUES (?, ?, ?)",
                        (user_id, 'az900', json.dumps(guest_data['az900_progress']))
                    )
                for q in guest_data.get('quiz_history', []):
                    cursor.execute(
                        """INSERT INTO quiz_history (user_id, quiz_id, topic_id, topic_name, score, correct_answers, total_questions, results_json)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (user_id, q['quiz_id'], q['topic_id'], q['topic_name'], q['score'], q['correct_answers'], q['total_questions'], json.dumps(q.get('results', [])))
                    )
                conn.commit()
            conn.close()

            # Log user in immediately
            session['logged_in_user'] = {
                'id': user_id,
                'username': username,
                'email': email,
                'display_name': display_name
            }
            session['user_id'] = f"user_{user_id}"
            initialize_user_data(session['user_id'])

            if next_page and next_page.startswith('/') and not next_page.startswith('//'):
                return redirect(next_page)
            return redirect(url_for('az900_domain1'))
        except sqlite3.IntegrityError:
            return render_template("register.html", error="An account with this username or email already exists. Please sign in.", form_data=form_data, next=next_page, message=message)
        except Exception as e:
            return render_template("register.html", error=f"Registration failed: {str(e)}", form_data=form_data, next=next_page, message=message)

    return render_template("register.html", form_data={}, next=next_page, message=message)

@app.route("/login", methods=["GET", "POST"])
def login():
    next_page = request.args.get("next") or request.form.get("next") or ""
    message = request.args.get("message") or ""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return render_template("login.html", error="Please enter both username/email and password.", username=username, next=next_page, message=message)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (username, username.lower())
        )
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['logged_in_user'] = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'display_name': user['display_name'] or user['username']
            }
            session['user_id'] = f"user_{user['id']}"
            initialize_user_data(session['user_id'])

            if next_page and next_page.startswith('/') and not next_page.startswith('//'):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            return render_template("login.html", error="Invalid username/email or password.", username=username, next=next_page, message=message)

    return render_template("login.html", next=next_page, message=message)

@app.route("/logout")
def logout():
    session.pop('logged_in_user', None)
    session.pop('user_id', None)
    session.pop('az900_progress', None)
    return redirect(url_for('index'))

@app.route("/login/google")
def google_login():
    next_page = request.args.get("next") or ""
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    session['oauth_next'] = next_page

    redirect_uri = url_for("google_callback", _external=True)

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account"
    }
    google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return redirect(google_auth_url)

@app.route("/auth/google/callback")
def google_callback():
    error = request.args.get("error")
    if error:
        return redirect(url_for("login", error=f"Google sign-in was cancelled or encountered an error ({error})."))

    state = request.args.get("state")
    saved_state = session.pop("oauth_state", None)
    next_page = session.pop("oauth_next", "")

    if not state or state != saved_state:
        return redirect(url_for("login", error="Authentication session mismatch. Please try signing in with Google again."))

    code = request.args.get("code")
    if not code:
        return redirect(url_for("login", error="No authorization code received from Google."))

    redirect_uri = url_for("google_callback", _external=True)
    
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    try:
        token_resp = requests.post(token_url, data=token_data, timeout=10)
        tokens = token_resp.json()
        access_token = tokens.get("access_token")

        if not access_token:
            err_desc = tokens.get("error_description", "Unknown error")
            return redirect(url_for("login", error=f"Google token verification failed: {err_desc}"))

        userinfo_resp = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        user_info = userinfo_resp.json()
        email = user_info.get("email", "").strip().lower()
        if not email:
            return redirect(url_for("login", error="Could not retrieve email from your Google account."))

        display_name = user_info.get("name") or email.split("@")[0]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if not user:
            base_username = re.sub(r'[^a-zA-Z0-9_]', '', email.split("@")[0]) or "google_user"
            username = base_username
            counter = 1
            while True:
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                if not cursor.fetchone():
                    break
                username = f"{base_username}_{counter}"
                counter += 1

            random_pw_hash = generate_password_hash(secrets.token_urlsafe(32))
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, display_name) VALUES (?, ?, ?, ?)",
                (username, email, random_pw_hash, display_name)
            )
            user_id = cursor.lastrowid
            conn.commit()
        else:
            user_id = user["id"]
            username = user["username"]
            display_name = user["display_name"] or display_name

        conn.close()

        session['logged_in_user'] = {
            'id': user_id,
            'username': username,
            'email': email,
            'display_name': display_name
        }
        session['user_id'] = f"user_{user_id}"
        initialize_user_data(session['user_id'])

        if next_page and next_page.startswith("/") and not next_page.startswith("//"):
            return redirect(next_page)
        return redirect(url_for("index"))

    except Exception as e:
        return redirect(url_for("login", error=f"Google authentication error: {str(e)}"))

@app.route("/")
def index():
    return render_template("index.html", topics=topics_data)

@app.route("/privacy")
@app.route("/terms")
@app.route("/privacy-terms")
def privacy_terms():
    return render_template("privacy_terms.html")

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
@login_required
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
@login_required
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
    """Get predefined certification exam quiz questions"""
    quiz_questions = {
                "az900": [
            {
                "question": "Which cloud computing model provides virtualized computing resources over the internet where you manage the OS, runtimes, and apps, while the cloud provider manages the physical infrastructure?",
                "options": {
                    "A": "Platform as a Service (PaaS)",
                    "B": "Infrastructure as a Service (IaaS)",
                    "C": "Software as a Service (SaaS)",
                    "D": "Function as a Service (FaaS)"
                },
                "correct_answer": "B",
                "explanation": "IaaS provides on-demand infrastructure (VMs, storage, networking) where the customer retains control over the OS and installed software."
            },
            {
                "question": "Which Azure architectural feature consists of physically separate datacenters within the same region, each with independent power, cooling, and networking?",
                "options": {
                    "A": "Resource Groups",
                    "B": "Availability Zones",
                    "C": "Geographies",
                    "D": "Azure Subscriptions"
                },
                "correct_answer": "B",
                "explanation": "Availability Zones provide high availability and fault tolerance against datacenter outages within an Azure region."
            },
            {
                "question": "A company wants to enforce rules that prevent employees from creating virtual machines in unapproved regions and ensure required cost tags are applied. Which service should they use?",
                "options": {
                    "A": "Azure Monitor",
                    "B": "Azure Policy",
                    "C": "Microsoft Entra ID",
                    "D": "Azure Cost Management"
                },
                "correct_answer": "B",
                "explanation": "Azure Policy establishes guardrails and governance by enforcing rules and automated compliance checks on Azure resources."
            },
            {
                "question": "What is the primary difference between Capital Expenditure (CapEx) and Operational Expenditure (OpEx) in cloud economics?",
                "options": {
                    "A": "CapEx is for SaaS only; OpEx is for IaaS only",
                    "B": "CapEx requires upfront spending on physical hardware, while OpEx is ongoing spending on operational services without upfront costs",
                    "C": "CapEx is fully tax exempt; OpEx is taxable",
                    "D": "CapEx scales dynamically; OpEx is fixed forever"
                },
                "correct_answer": "B",
                "explanation": "CapEx involves upfront financial investment for physical assets, while OpEx is pay-as-you-go based on consumption."
            },
            {
                "question": "Which Microsoft cloud service manages user identities, provides Single Sign-On (SSO), and enforces Multi-Factor Authentication (MFA)?",
                "options": {
                    "A": "Azure Key Vault",
                    "B": "Microsoft Entra ID",
                    "C": "Azure Bastion",
                    "D": "Azure Dedicated Host"
                },
                "correct_answer": "B",
                "explanation": "Microsoft Entra ID (formerly Azure Active Directory) is the comprehensive cloud identity and access management solution."
            }
        ],
        "az400": [
            {
                "question": "Which Azure Pipelines feature allows you to ensure deployments pause until manual sign-offs or external health checks pass before proceeding to production?",
                "options": {
                    "A": "Pipeline scheduled triggers",
                    "B": "Environments with Approvals and Checks",
                    "C": "Azure Artifacts upstream sources",
                    "D": "Deployment group tags"
                },
                "correct_answer": "B",
                "explanation": "Azure Pipelines Environments support approvals, manual validation, Azure Monitor alerts, and REST API gates to safely control deployment stages."
            },
            {
                "question": "You need to manage Git branching in Azure Repos such that production releases come from the main branch, changes are merged via pull requests, and CI build validation is required. What should you configure?",
                "options": {
                    "A": "Branch policies on the main branch",
                    "B": "Service hooks on Azure Repos",
                    "C": "Azure Artifacts package retention",
                    "D": "Git submodules"
                },
                "correct_answer": "A",
                "explanation": "Branch policies enforce code reviews, required reviewers, work item linking, and successful CI build validation before merges can occur."
            },
            {
                "question": "Which deployment pattern routes a small percentage of user traffic to a new version of an application to evaluate stability before rolling it out to 100% of users?",
                "options": {
                    "A": "Blue-Green deployment",
                    "B": "Canary deployment",
                    "C": "Big bang deployment",
                    "D": "Recreate deployment"
                },
                "correct_answer": "B",
                "explanation": "Canary deployment exposes new features to a small subset of users or traffic before promoting the release to the entire production fleet."
            },
            {
                "question": "In Azure DevOps, which mechanism should you use to securely store and inject API keys, certificates, and database passwords into CI/CD pipelines without exposing them in code?",
                "options": {
                    "A": "Azure Boards work items",
                    "B": "Variable groups linked to Azure Key Vault",
                    "C": "Git LFS (Large File Storage)",
                    "D": "Azure Test Plans configuration"
                },
                "correct_answer": "B",
                "explanation": "Variable groups in Azure Pipelines can link directly to Azure Key Vault to securely retrieve secrets at runtime without exposing them in plain text."
            },
            {
                "question": "Which tool integrated into Azure DevOps pipelines is commonly used for static application security testing (SAST) and code quality analysis to scan for security vulnerabilities?",
                "options": {
                    "A": "SonarQube",
                    "B": "Azure Bastion",
                    "C": "Microsoft Sentinel",
                    "D": "Azure Load Testing"
                },
                "correct_answer": "A",
                "explanation": "SonarQube scans source code for security vulnerabilities, bugs, and code smells during CI build steps."
            }
        ],
        "aws_solutions_architect": [
            {
                "question": "An application requires high availability, automatic scaling across multiple Availability Zones, and session state persistence without storing state on EC2 instances. Which architecture is best?",
                "options": {
                    "A": "Application Load Balancer, EC2 Auto Scaling group, and Amazon ElastiCache",
                    "B": "Network Load Balancer, single EC2 instance, and EBS Multi-Attach",
                    "C": "Route 53 latency routing, EC2 instances with local NVMe instance store",
                    "D": "CloudFront distribution pointing directly to an EBS volume"
                },
                "correct_answer": "A",
                "explanation": "An Application Load Balancer distributes traffic across Auto Scaling EC2 instances, while ElastiCache (Redis/Memcached) provides fast external session caching."
            },
            {
                "question": "You need to store archival data that is rarely accessed but must be retrieved within 3 to 5 hours when requested, at the lowest possible storage cost. Which Amazon S3 storage tier should you choose?",
                "options": {
                    "A": "S3 Standard",
                    "B": "S3 Glacier Flexible Retrieval",
                    "C": "S3 One Zone-IA",
                    "D": "S3 Standard-Infrequent Access"
                },
                "correct_answer": "B",
                "explanation": "S3 Glacier Flexible Retrieval provides low-cost archival storage with standard retrieval times between 3-5 hours."
            },
            {
                "question": "Which AWS service allows private connectivity between your VPC and supported AWS services without traversing the public internet?",
                "options": {
                    "A": "Internet Gateway",
                    "B": "VPC Endpoint (AWS PrivateLink)",
                    "C": "Virtual Private Gateway",
                    "D": "NAT Gateway"
                },
                "correct_answer": "B",
                "explanation": "VPC Endpoints powered by PrivateLink allow private connectivity between VPCs and AWS services without needing an internet gateway or public IP addresses."
            },
            {
                "question": "An eCommerce platform expects unpredictable traffic spikes during sales events. Which database solution provides single-digit millisecond latency at any scale with automatic throughput management?",
                "options": {
                    "A": "Amazon RDS for MySQL",
                    "B": "Amazon DynamoDB",
                    "C": "Amazon Redshift",
                    "D": "Amazon EMR"
                },
                "correct_answer": "B",
                "explanation": "Amazon DynamoDB is a managed NoSQL database offering single-digit millisecond latency and on-demand auto-scaling capacity."
            },
            {
                "question": "A company wants to run containerized microservices without having to manage, provision, or patch underlying EC2 servers. Which compute option meets this requirement?",
                "options": {
                    "A": "Amazon EC2 Dedicated Hosts",
                    "B": "AWS Lambda with container images larger than 10GB",
                    "C": "Amazon ECS or EKS with AWS Fargate",
                    "D": "Amazon Lightsail VPS"
                },
                "correct_answer": "C",
                "explanation": "AWS Fargate is a serverless compute engine for containers that works with both Amazon ECS and Amazon EKS, removing server management overhead."
            }
        ],
        "comptia_security": [
            {
                "question": "An attacker sends an email targeted at the Chief Financial Officer pretending to be the CEO and requesting an urgent wire transfer to an unknown vendor. Which type of attack is this?",
                "options": {
                    "A": "Whaling",
                    "B": "Vishing",
                    "C": "Shoulder surfing",
                    "D": "Tailgating"
                },
                "correct_answer": "A",
                "explanation": "Whaling is a targeted phishing attack directed specifically at high-profile executives or impersonating high-level executives for financial or data theft."
            },
            {
                "question": "Which security control principle ensures that a user or system process is granted only the minimum permissions necessary to perform required job duties?",
                "options": {
                    "A": "Separation of duties",
                    "B": "Principle of Least Privilege",
                    "C": "Defense in depth",
                    "D": "Implicit deny"
                },
                "correct_answer": "B",
                "explanation": "The Principle of Least Privilege (PoLP) dictates giving subjects only the rights needed to accomplish their authorized job functions."
            },
            {
                "question": "What cryptographic algorithm is asymmetric and widely used for secure key exchange and digital signatures?",
                "options": {
                    "A": "AES-256",
                    "B": "DES",
                    "C": "RSA",
                    "D": "ChaCha20"
                },
                "correct_answer": "C",
                "explanation": "RSA is an asymmetric public-key cryptosystem used for secure data transmission, key exchange, and digital signatures."
            },
            {
                "question": "Which security architecture operates under the fundamental principle of 'never trust, always verify' for all users and devices inside or outside the network?",
                "options": {
                    "A": "Zero Trust Architecture (ZTA)",
                    "B": "Air-gapped networking",
                    "C": "DMZ perimeter architecture",
                    "D": "Walled garden network"
                },
                "correct_answer": "A",
                "explanation": "Zero Trust Architecture removes implicit trust and requires continuous authentication, authorization, and validation of every transaction."
            },
            {
                "question": "Which incident response phase focuses on preventing an active security breach from expanding and causing further damage to systems?",
                "options": {
                    "A": "Preparation",
                    "B": "Containment",
                    "C": "Eradication",
                    "D": "Lessons Learned"
                },
                "correct_answer": "B",
                "explanation": "The containment phase aims to isolate affected systems and stop the spread of an attack before remediation begins."
            }
        ],
        "itil_foundation": [
            {
                "question": "According to ITIL 4, what is the definition of a 'Service'?",
                "options": {
                    "A": "A tangible product manufactured and sold to clients",
                    "B": "A means of enabling value co-creation by facilitating outcomes that customers want to achieve, without the customer having to manage specific costs and risks",
                    "C": "A formal contract between a vendor and an internal business team",
                    "D": "A set of specialized organizational assets and hardware"
                },
                "correct_answer": "B",
                "explanation": "ITIL 4 defines a service as enabling value co-creation by facilitating outcomes customers desire without managing specific costs and risks."
            },
            {
                "question": "Which ITIL Guiding Principle recommends assessing the current state and reusing existing successful processes rather than discarding everything to build from scratch?",
                "options": {
                    "A": "Focus on value",
                    "B": "Start where you are",
                    "C": "Think and work holistically",
                    "D": "Keep it simple and practical"
                },
                "correct_answer": "B",
                "explanation": "'Start where you are' emphasizes evaluating the existing baseline and leveraging working assets and services rather than starting over completely."
            },
            {
                "question": "What are the Four Dimensions of Service Management in ITIL 4?",
                "options": {
                    "A": "Plan, Do, Check, Act",
                    "B": "Organizations and people; Information and technology; Partners and suppliers; Value streams and processes",
                    "C": "Incident, Problem, Change, Release",
                    "D": "Cost, Quality, Speed, Reliability"
                },
                "correct_answer": "B",
                "explanation": "The Four Dimensions represent the holistic perspectives essential to facilitate effective and efficient value co-creation in ITIL 4."
            },
            {
                "question": "Which ITIL practice has the primary purpose of minimizing the negative impact of incidents by restoring normal service operation as quickly as possible?",
                "options": {
                    "A": "Problem Management",
                    "B": "Change Enablement",
                    "C": "Incident Management",
                    "D": "Continual Improvement"
                },
                "correct_answer": "C",
                "explanation": "Incident Management restores normal service operation as rapidly as possible to reduce disruption to business activities."
            },
            {
                "question": "What is the primary difference between an Incident and a Problem in ITIL 4?",
                "options": {
                    "A": "Incidents are hardware issues; Problems are software bugs",
                    "B": "An incident is an unplanned interruption or reduction in quality of a service, while a problem is a cause, or potential cause, of one or more incidents",
                    "C": "Incidents are handled by vendors; Problems are handled internally",
                    "D": "Incidents require changes; Problems never require changes"
                },
                "correct_answer": "B",
                "explanation": "An incident is an unplanned disruption or reduction in service quality, whereas a problem is the underlying cause of one or more incidents."
            }
        ],
        "cisco_ccna": [
            {
                "question": "Which protocol operates at the Transport Layer (Layer 4) of the OSI model and provides reliable, connection-oriented data transfer with flow control?",
                "options": {
                    "A": "UDP",
                    "B": "IP",
                    "C": "TCP",
                    "D": "ICMP"
                },
                "correct_answer": "C",
                "explanation": "TCP (Transmission Control Protocol) is connection-oriented and provides reliable delivery with sequence tracking, acknowledgments, and flow control."
            },
            {
                "question": "What is the default administrative distance of OSPF on a Cisco router?",
                "options": {
                    "A": "90",
                    "B": "110",
                    "C": "120",
                    "D": "1"
                },
                "correct_answer": "B",
                "explanation": "The default Administrative Distance (AD) for Open Shortest Path First (OSPF) routes is 110."
            },
            {
                "question": "Which technology allows multiple physical Ethernet links to be combined into a single logical link to provide increased bandwidth and redundancy?",
                "options": {
                    "A": "Spanning Tree Protocol (STP)",
                    "B": "EtherChannel (LACP/PAgP)",
                    "C": "VLAN Trunking Protocol (VTP)",
                    "D": "Port Address Translation (PAT)"
                },
                "correct_answer": "B",
                "explanation": "EtherChannel bundles multiple physical links into one logical channel using LACP (802.3ad) or Cisco proprietary PAgP."
            },
            {
                "question": "In IPv4 subnetting, which subnet mask provides up to 30 usable host IP addresses per subnet?",
                "options": {
                    "A": "/26 (255.255.255.192)",
                    "B": "/27 (255.255.255.224)",
                    "C": "/28 (255.255.255.240)",
                    "D": "/29 (255.255.255.248)"
                },
                "correct_answer": "B",
                "explanation": "A /27 subnet mask leaves 5 host bits: 2^5 - 2 = 30 usable host IP addresses."
            },
            {
                "question": "What is the primary purpose of Spanning Tree Protocol (STP, 802.1D) in a switched local area network?",
                "options": {
                    "A": "To dynamically route packets between different autonomous systems",
                    "B": "To prevent Layer 2 switching loops and broadcast storms",
                    "C": "To encrypt wireless transmissions",
                    "D": "To allocate dynamic IP addresses to end workstations"
                },
                "correct_answer": "B",
                "explanation": "STP detects and blocks redundant links to prevent Layer 2 loops and broadcast storms in switched networks."
            }
        ],
        "kubernetes_cka": [
            {
                "question": "Which core component of the Kubernetes control plane acts as the primary data store for all cluster state and configurations?",
                "options": {
                    "A": "kube-scheduler",
                    "B": "kube-apiserver",
                    "C": "etcd",
                    "D": "kubelet"
                },
                "correct_answer": "C",
                "explanation": "etcd is a consistent, highly-available key-value store used as Kubernetes' backing store for all cluster state data."
            },
            {
                "question": "You want to ensure that a specific Pod runs on every single worker node in a Kubernetes cluster automatically. Which workload resource should you deploy?",
                "options": {
                    "A": "Deployment",
                    "B": "StatefulSet",
                    "C": "DaemonSet",
                    "D": "Job"
                },
                "correct_answer": "C",
                "explanation": "A DaemonSet ensures that all (or matching) nodes run a copy of a Pod, commonly used for log agents and monitoring daemons."
            },
            {
                "question": "Which Kubernetes component runs on every worker node to register the node, monitor PodSpecs, and ensure containers are running and healthy?",
                "options": {
                    "A": "kube-proxy",
                    "B": "kubelet",
                    "C": "kube-controller-manager",
                    "D": "containerd CLI"
                },
                "correct_answer": "B",
                "explanation": "The kubelet is the node agent that registers nodes with the API server and manages container lifecycles on the node."
            },
            {
                "question": "What type of Kubernetes Service assigns a stable IP address from an internal pool accessible only from within the cluster?",
                "options": {
                    "A": "ClusterIP",
                    "B": "NodePort",
                    "C": "LoadBalancer",
                    "D": "ExternalName"
                },
                "correct_answer": "A",
                "explanation": "ClusterIP is the default Kubernetes Service type, exposing the service on a cluster-internal IP address."
            },
            {
                "question": "Which command in kubectl correctly creates a new namespace called 'production' imperatively?",
                "options": {
                    "A": "kubectl run production --type=namespace",
                    "B": "kubectl create namespace production",
                    "C": "kubectl new ns production",
                    "D": "kubectl apply namespace production"
                },
                "correct_answer": "B",
                "explanation": "The command 'kubectl create namespace production' (or 'kubectl create ns production') creates a new namespace imperatively."
            }
        ]
    }

    return quiz_questions.get(topic_id, quiz_questions["az400"])

@app.route("/submit_quiz", methods=["POST"])
@login_required
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

    # Persist to SQLite if logged in
    if 'logged_in_user' in session:
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO quiz_history (user_id, quiz_id, topic_id, topic_name, score, correct_answers, total_questions, results_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (session['logged_in_user']['id'], quiz['id'], topic_id, quiz['topic_name'], score, correct_count, len(quiz['questions']), json.dumps(results))
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Quiz save to db error: {e}")

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
@login_required
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


FALLBACK_STUDY_MATERIALS = {
        "az900": """# Microsoft Azure Fundamentals (AZ-900) Study Guide

## 1. Cloud Concepts
* Cloud models: Public cloud, Private cloud, and Hybrid cloud architectures
* Cloud service types: IaaS (Infrastructure as a Service), PaaS (Platform as a Service), SaaS (Software as a Service)
* Shared Responsibility Model: Division of security duties between Microsoft and the customer
* Financial benefits: Capital Expenditure (CapEx) vs Operational Expenditure (OpEx), consumption-based pricing

## 2. Core Azure Architecture and Services
* Global infrastructure: Geographies, Regions, Region Pairs, and Availability Zones (independent power, cooling, network)
* Resource hierarchy: Management Groups -> Subscriptions -> Resource Groups -> Resources
* Compute services: Azure Virtual Machines (VMs), Virtual Machine Scale Sets, App Services, Azure Functions (Serverless), Azure Container Instances (ACI), and AKS
* Storage services: Azure Blob Storage (Hot, Cool, Cold, Archive tiers), Azure Files, Disk Storage

## 3. Azure Management, Governance & Compliance
* Governance tools: Azure Policy (enforcing rules and standards), Resource Locks (CanNotDelete, ReadOnly), and Resource Tags
* Cost management: Azure Cost Management, Budgets, Pricing Calculator, Total Cost of Ownership (TCO) Calculator
* Monitoring & reporting: Azure Monitor, Service Health dashboard, and Application Insights

## 4. Azure Security and Identity
* Identity foundation: Microsoft Entra ID (Single Sign-On, Multi-Factor Authentication, Conditional Access)
* Authorization: Role-Based Access Control (RBAC) - Owner, Contributor, Reader
* Network security: Network Security Groups (NSGs), Application Security Groups (ASGs), Azure Firewall, and DDoS Protection
* Secret management: Azure Key Vault for certificates, secrets, and cryptographic keys
""",
    "az400": """# Microsoft AZ-400: Designing and Implementing Microsoft DevOps Solutions

## 1. Source Control & Repository Management
* Git branching workflows: Trunk-based development and release branching strategies
* Azure Repos branch policies: Enforcing PR reviews, work item linking, and CI build validations
* Package management: Azure Artifacts with upstream feeds, package retention, and semantic versioning

## 2. CI/CD Pipeline Design
* Azure Pipelines YAML schema: Multi-stage pipelines, stages, jobs, steps, and reusable templates
* Deployment strategies: Canary deployments, Blue-Green switching, and Rolling deployment models
* Environments, Approvals, and Gates: Integrating manual validation and Azure Monitor alert gates

## 3. Infrastructure as Code (IaC) & Configuration
* Declarative templates: Azure Resource Manager (ARM), Bicep, and Terraform automation
* Secret management: Variable groups linked securely with Azure Key Vault
* Container workflows: Docker, Azure Container Registry (ACR), and Azure Kubernetes Service (AKS)

## 4. Security, Compliance, and Monitoring
* Shift-Left security: Static Application Security Testing (SAST) with SonarQube and dependency scanning
* Continuous feedback: Application Insights, Log Analytics workspaces, and alert action groups
* Audit and governance: Azure Policy compliance and security score remediation
""",
    "aws_solutions_architect": """# AWS Certified Solutions Architect (SAA-C03) Study Guide

## 1. Design Resilient Architectures
* Multi-AZ VPC design: Public and private subnets, NAT Gateways, and Internet Gateways
* High availability compute: Auto Scaling Groups (ASG) behind Application Load Balancers (ALB)
* Decoupled architectures: Amazon SQS (Standard vs FIFO), Amazon SNS fan-out, and EventBridge

## 2. High-Performing Architectures
* Storage tiers: Amazon S3 (Standard, Intelligent-Tiering, Glacier Flexible & Deep Archive)
* High performance databases: DynamoDB with DAX, Amazon Aurora Global Databases, and ElastiCache
* Content delivery: CloudFront edge caching, Origin Access Control (OAC), and Route 53 routing policies

## 3. Secure Applications & Architectures
* Identity & Access Management (IAM): Least privilege policies, roles, and instance profiles
* Network protection: Security Groups (stateful) vs Network ACLs (stateless), AWS WAF, and AWS Shield
* Encryption: AWS KMS customer-managed keys for encryption at rest and TLS in transit

## 4. Cost-Optimized Architectures
* Compute purchasing options: On-Demand, Savings Plans, Reserved Instances, and Spot Instances
* Storage lifecycle policies: Automatic transition and expiration of S3 objects
* Resource tagging: Cost allocation tags and AWS Cost Explorer tracking
""",
    "comptia_security": """# CompTIA Security+ (SY0-701) Study Guide

## 1. General Security Concepts
* The CIA Triad: Confidentiality, Integrity, and Availability
* Security models: Zero Trust Architecture (ZTA), Defense in Depth, and Principle of Least Privilege (PoLP)
* Cryptographic controls: Asymmetric (RSA, ECC), Symmetric (AES-256), and Hashing (SHA-256)

## 2. Threats, Attacks, and Vulnerabilities
* Social engineering: Phishing, Spear Phishing, Whaling, Vishing, and Business Email Compromise (BEC)
* Malware and threats: Ransomware, Rootkits, Trojans, Keyloggers, and Zero-day exploits
* Application vulnerabilities: SQL Injection, Cross-Site Scripting (XSS), and Buffer Overflows

## 3. Architecture & Infrastructure Security
* Network segmentation: VLANs, DMZ, Air-gapped networks, and Bastion hosts
* Firewalls and filters: Next-Generation Firewalls (NGFW), WAF, and IDS/IPS
* Identity & Access Management (IAM): Multi-Factor Authentication (MFA), SSO, OAuth 2.0, and SAML

## 4. Incident Response & Operations
* Incident Response Lifecycle: Preparation, Detection & Analysis, Containment, Eradication, Recovery, Lessons Learned
* Security operations: SIEM, SOAR, Vulnerability scanning, and tabletop exercises
* Disaster recovery: RTO (Recovery Time Objective) and RPO (Recovery Point Objective)
""",
    "itil_foundation": """# ITIL 4 Foundation Study Guide

## 1. Core Concepts of Service Management
* Service definition: Facilitating value co-creation through desired customer outcomes
* Utility and Warranty: Fit for purpose (utility) and Fit for use (warranty)
* Cost, Risk, and Output vs Outcome: Outcomes deliver business results; outputs are deliverables

## 2. The Four Dimensions of Service Management
* Organizations and People: Culture, roles, leadership, and communication
* Information and Technology: Workflow management, knowledge management, and cloud services
* Partners and Suppliers: Contracts, sourcing strategies, and supplier integration
* Value Streams and Processes: End-to-end journey turning stakeholder demand into value

## 3. The 7 ITIL Guiding Principles
* Focus on value: Link every activity directly or indirectly to value for stakeholders
* Start where you are: Leverage existing good practices and working services
* Progress iteratively with feedback: Organize work into smaller, manageable sections
* Collaborate and promote visibility: Include the right people and share data openly
* Think and work holistically: Understand the complete end-to-end service ecosystem
* Keep it simple and practical: Minimize unnecessary steps and eliminate waste
* Optimize and automate: Maximize human work efficiency using automated tools

## 4. Key ITIL Management Practices
* Incident Management: Restoring normal service operations as rapidly as possible
* Problem Management: Identifying root causes of incidents and managing workarounds and known errors
* Change Enablement: Maximizing successful service and product changes through risk assessment
* Continual Improvement: Ongoing improvement at all levels across the Service Value System
""",
    "cisco_ccna": """# Cisco CCNA (200-301) Study Guide

## 1. Network Fundamentals
* OSI 7-Layer Model & TCP/IP Model: Encapsulation, data units, transport protocols (TCP vs UDP)
* IPv4 Addressing & Subnetting: VLSM, prefix lengths (/24, /27, /30), public vs RFC 1918 private IPs
* IPv6 Addressing: Global unicast, link-local (FE80::/10), SLAAC and DHCPv6

## 2. Switching and Network Access
* VLANs & Trunking: 802.1Q tagging, native VLAN, access vs trunk ports
* Spanning Tree Protocol (STP): 802.1D, Rapid PVST+ (802.1w), root bridge election, port states
* EtherChannel: Link Aggregation Control Protocol (LACP 802.3ad) and Cisco PAgP

## 3. IP Connectivity & Routing
* Routing table logic: Longest prefix match, Administrative Distance (Connected=0, Static=1, OSPF=110)
* OSPFv2: Single-area and multi-area OSPF, router IDs, neighbor states, DR/BDR election
* Static routes: Floating static routes, default routes (0.0.0.0/0)

## 4. IP Services, Security & Automation
* First Hop Redundancy: HSRP basics, DHCP relay agents, DNS, NTP, SNMP, and Syslog
* Security: Standard and Extended Access Control Lists (ACLs), Port Security, and DHCP snooping
* Automation: REST APIs, JSON data structures, Ansible, and Cisco DNA Center
""",
    "kubernetes_cka": """# Certified Kubernetes Administrator (CKA) Study Guide

## 1. Cluster Architecture, Installation & Configuration
* Control plane components: kube-apiserver, etcd key-value store, kube-scheduler, kube-controller-manager
* Worker node components: kubelet, kube-proxy, container runtime (containerd)
* Administration: Cluster provisioning with kubeadm, etcd backup and snapshot restore

## 2. Workloads & Scheduling
* Workload controllers: Deployments, ReplicaSets, DaemonSets, StatefulSets, Jobs, CronJobs
* Advanced scheduling: nodeSelector, Node Affinity/Anti-Affinity, Taints and Tolerations
* Pod resource management: Resource requests, limits, LimitRanges, and ResourceQuotas

## 3. Services, Networking & Ingress
* Service types: ClusterIP (default internal), NodePort, LoadBalancer, ExternalName
* Ingress: Ingress controllers, path-based and host-based routing rules
* Network Security: NetworkPolicies for pod-to-pod ingress and egress traffic filtering
* DNS resolution: CoreDNS configuration within kube-system

## 4. Storage & Troubleshooting
* Persistent storage: PersistentVolumes (PV), PersistentVolumeClaims (PVC), and StorageClasses
* Cluster troubleshooting: Node NotReady conditions, kubelet logs with journalctl, broken TLS certificates
* Application debugging: kubectl describe, kubectl logs -f, and ephemeral debug containers
"""
}


@app.route("/az900/domain-1")
@app.route("/learn/az900/domain-1")
@login_required
def az900_domain1():
    topic = topics_data.get("az900")
    user_id = get_user_id()
    initialize_user_data(user_id)
    return render_template("az900_domain1.html", topic=topic, topic_id="az900")

@app.route("/api/az900/progress", methods=["GET", "POST"])
@login_required
def az900_progress_api():
    user_id = get_user_id()
    initialize_user_data(user_id)
    
    if request.method == "POST":
        data = request.get_json() or {}
        if 'az900_progress' not in users_data[user_id]:
            users_data[user_id]['az900_progress'] = {}
        users_data[user_id]['az900_progress'].update(data)
        session['az900_progress'] = users_data[user_id]['az900_progress']

        # Persist to SQLite if logged in
        if 'logged_in_user' in session:
            try:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO user_progress (user_id, topic_id, progress_data) VALUES (?, ?, ?)",
                    (session['logged_in_user']['id'], 'az900', json.dumps(users_data[user_id]['az900_progress']))
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Error persisting az900 progress: {e}")

        return jsonify({"status": "ok", "progress": users_data[user_id]['az900_progress']})
    
    progress = session.get('az900_progress', users_data[user_id].get('az900_progress', {
        'subtopic_1': False,
        'subtopic_2': False,
        'subtopic_3': False
    }))
    return jsonify({"status": "ok", "progress": progress})

@app.route("/api/az900/chat", methods=["POST"])
def az900_chat():
    """AI Study Buddy for AZ-900 Domain 1 — contextual chat powered by Gemini"""
    try:
        data = request.get_json() or {}
        user_message = data.get('message', '').strip()
        subtopic_context = data.get('subtopic_context', 'Cloud Concepts')

        if not user_message:
            return jsonify({'success': False, 'reply': 'Please type a question.'})

        # Build a focused AZ-900 study tutor system prompt
        system_prompt = f"""You are an expert, friendly AZ-900 Microsoft Azure Fundamentals exam tutor.
The student is currently studying Domain 1: Describe Cloud Concepts — specifically the subtopic: "{subtopic_context}".

Guidelines for your responses:
- Keep answers concise (3-6 sentences) unless the student asks for detail.
- Use simple, clear language with real-world analogies where helpful.
- Reference official Microsoft/Azure terminology accurately.
- When relevant, mention which AZ-900 exam objective the concept maps to.
- If the student asks something outside AZ-900 scope, gently redirect them.
- Use bullet points for lists, bold for key terms.
- Be encouraging and supportive.
- NEVER make up Azure service names or features that don't exist.
- Focus on exam-relevant knowledge."""

        prompt = f"{system_prompt}\n\nStudent question: {user_message}"

        response = model.generate_content(prompt)
        ai_reply = response.text.strip()

        # Basic markdown-to-HTML formatting for chat
        ai_reply = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', ai_reply)
        ai_reply = re.sub(r'\*(.*?)\*', r'<em>\1</em>', ai_reply)
        ai_reply = re.sub(r'`([^`]+)`', r'<code>\1</code>', ai_reply)
        # Convert bullet points
        ai_reply = re.sub(r'^\s*[\*\-]\s+(.*)$', r'<br>• \1', ai_reply, flags=re.MULTILINE)
        # Convert line breaks
        ai_reply = ai_reply.replace('\n\n', '<br><br>').replace('\n', '<br>')

        return jsonify({'success': True, 'reply': ai_reply})

    except Exception as e:
        print(f"AZ-900 Chat API error: {e}")
        error_msg = str(e)
        if 'API key' in error_msg or 'api_key' in error_msg.lower():
            return jsonify({'success': False, 'reply': 'The AI tutor API key is not configured. Please set your Gemini API key to enable the study buddy.'})
        return jsonify({'success': False, 'reply': f'Sorry, I had trouble answering that. Please try rephrasing your question. ({error_msg})'})

@app.route("/study_material/<topic_id>")
@login_required
def study_material(topic_id):
    if topic_id not in topics_data:
        return redirect(url_for('index'))

    # Directly provide the interactive Domain 1 micro-learning experience for AZ-900
    if topic_id == 'az900':
        return redirect(url_for('az900_domain1'))

    topic = topics_data[topic_id]
    
    # Generate study material using Gemini API, or fall back to high-quality curated guide
    study_content = None
    try:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if api_key:
            genai.configure(api_key=api_key)
            prompt = f"Create comprehensive study material for {topic['name']}. Include key concepts, examples, and learning tips. Format with clear headings."
            response = model.generate_content(prompt)
            study_content = format_study_content(response.text)
    except Exception as e:
        print(f"Gemini API study generation notice: {e}")
        study_content = None

    if not study_content:
        raw_content = FALLBACK_STUDY_MATERIALS.get(
            topic_id, 
            f"# {topic['name']} Study Guide\n\nReview the key concepts and test your knowledge with the practice quiz."
        )
        study_content = format_study_content(raw_content)

    return render_template("study_material.html", topic=topic, topic_id=topic_id, content=study_content)

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

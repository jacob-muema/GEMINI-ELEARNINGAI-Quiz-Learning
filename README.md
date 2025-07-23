# AI E-Learning Platform

An interactive e-learning platform powered by Google's Gemini AI that offers quizzes and AI-powered assistance across multiple programming and technology topics.

## 🎥 Video Demo

Watch the complete demonstration of the AI E-Learning Platform:

[![AI E-Learning Platform Demo](https://img.youtube.com/vi/gdsTxD2B_d0/maxresdefault.jpg)](https://youtu.be/gdsTxD2B_d0?si=Gj8f4SbCOs7DjbYZ)

**🎬 [Watch on YouTube: Building an AI-Powered Learning Platform with Flask & Google Gemini](https://youtu.be/gdsTxD2B_d0?si=Gj8f4SbCOs7DjbYZ)**

*This 3-minute demo shows all the key features including interactive quizzes, AI chat assistant, and progress tracking across all 5 topics.*

## 🚀 Features

- **Interactive Quizzes**: Multiple choice quizzes for 5 different topics
- **AI Chat Assistant**: Ask questions and get instant AI-powered answers
- **Progress Tracking**: Track your quiz performance and improvement
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Feedback**: Immediate results and explanations

## 📚 Available Topics

1. **🐍 Python Programming** - Learn Python fundamentals, data structures, and OOP
2. **⚡ JavaScript Development** - Master JavaScript, DOM manipulation, and ES6+ features  
3. **📊 Data Science** - Explore data analysis, machine learning, and statistical concepts
4. **🌐 Web Development** - Full-stack web development with HTML, CSS, and frameworks
5. **🚀 DevOps Engineering** - CI/CD, containerization, cloud platforms, and automation

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.7 or higher
- Google AI Studio API Key

### Step 1: Clone the Repository
\`\`\`bash
git clone <repository-url>
cd ai-elearning-platform
\`\`\`

### Step 2: Create Virtual Environment
\`\`\`bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
\`\`\`

### Step 3: Install Dependencies
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### Step 4: Get Google AI Studio API Key
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create a new project or select existing one
3. Generate an API key
4. Copy the API key

### Step 5: Configure API Key
You need to replace the API key in **TWO** files:

#### File 1: app.py (Line 13)
\`\`\`python
# Replace YOUR_API_KEY_HERE with your actual API key
genai.configure(api_key="YOUR_API_KEY_HERE")
\`\`\`

#### File 2: txtAi.py (if using standalone AI features)
\`\`\`python
# Replace YOUR_API_KEY_HERE with your actual API key
genai.configure(api_key="YOUR_API_KEY_HERE")
\`\`\`

### Step 6: Run the Application
\`\`\`bash
python app.py
\`\`\`

The application will start on `http://localhost:5000`

## 🎯 How to Use

### Taking Quizzes
1. Visit the homepage
2. Select a topic (Python, JavaScript, Data Science, Web Development, or DevOps)
3. Click "Start Learning" then "Take Quiz"
4. Answer all 5 multiple-choice questions
5. Submit to see your results with detailed explanations

### Using AI Assistant
1. On the homepage, scroll to the "Ask AI Assistant" section
2. Type your question about any programming or technology topic
3. Click "Ask AI" to get an instant AI-powered response

### Tracking Progress
1. Visit the Dashboard to see:
   - Overall quiz statistics
   - Topic-wise performance
   - Recent quiz history
   - Best scores and averages

## 📁 Project Structure

\`\`\`
ai-elearning-platform/
├── app.py                 # Main Flask application
├── txtAi.py              # Standalone AI text processing
├── requirements.txt      # Python dependencies
├── templates/
│   ├── base.html        # Base template with styling
│   ├── quiz.html        # Self-contained quiz system
│   ├── index.html       # Homepage
│   └── ...              # Other templates
├── static/              # Static files (if any)
└── README.md           # This file
\`\`\`

## 🔧 Technical Details

### Backend
- **Framework**: Flask (Python)
- **AI Integration**: Google Gemini AI API
- **Session Management**: Flask sessions for user tracking
- **Data Storage**: In-memory storage (suitable for demo/development)

### Frontend
- **Styling**: Custom CSS with CSS variables
- **JavaScript**: Vanilla JS for quiz functionality
- **Responsive**: Mobile-friendly design
- **Icons**: Emoji-based topic icons

### Quiz System
- **Self-contained**: All quiz data and logic in HTML file
- **No database required**: Questions stored in JavaScript
- **Real-time feedback**: Instant visual updates
- **Progress tracking**: Visual progress bar and counters

## 🚨 Important Notes

### API Key Security
- **Never commit your API key to version control**
- **Replace the placeholder API key before running**
- **Consider using environment variables in production**

### Development vs Production
- Current setup uses in-memory storage
- For production, implement proper database storage
- Add user authentication and authorization
- Implement rate limiting for API calls

## 🐛 Troubleshooting

### Common Issues

1. **"No module named 'google.generativeai'"**
   - Solution: Run `pip install -r requirements.txt`

2. **"API key not valid"**
   - Solution: Check your API key in both `app.py` and `txtAi.py`

3. **Quiz not loading**
   - Solution: Check browser console for JavaScript errors
   - Ensure all quiz topics are properly defined in `quiz.html`

4. **AI responses not working**
   - Solution: Verify API key and internet connection
   - Check Google AI Studio quota limits

## 📝 Adding New Questions

To add new quiz questions, edit the `QUIZ_DATA` object in `templates/quiz.html`:

\`\`\`javascript
const QUIZ_DATA = {
    your_topic: {
        name: "Your Topic Name",
        questions: [
            {
                question: "Your question here?",
                options: {
                    A: "Option A",
                    B: "Option B", 
                    C: "Option C",
                    D: "Option D"
                },
                correct: "B",
                explanation: "Explanation of the correct answer."
            }
            // Add more questions...
        ]
    }
};
\`\`\`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🆘 Support

If you encounter any issues:
1. Check the troubleshooting section above
2. Review the video demo for proper usage
3. Ensure your API key is correctly configured
4. Check browser console for error messages

---

**Happy Learning! 🎓**

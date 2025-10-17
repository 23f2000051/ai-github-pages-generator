# 🚀 AI-Powered GitHub Pages Generator

> Automated web application generator that creates, deploys, and modifies GitHub Pages using LLM-powered code generation.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.118-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Overview

This system automatically generates complete web applications (HTML, CSS, JavaScript, README) from natural language descriptions, deploys them to GitHub Pages, and handles iterative improvements across multiple rounds.

### **Key Features:**

- 🤖 **LLM-Powered Generation**: Uses state-of-the-art AI models (GPT-4o, GPT-5, O3-Pro) to generate production-ready code
- 🔄 **Multi-Round Support**: Handles Round 1 (creation) and Round 2+ (modifications) with context preservation
- 📦 **Automated Deployment**: Creates GitHub repos, pushes files, enables Pages, and waits for deployment
- 📎 **Smart Attachment Handling**: Processes CSV, JSON, images (data URIs and HTTP URLs)
- ✅ **Quality Assurance**: Comprehensive system prompts ensure responsive design, error handling, and best practices
- 🔔 **Webhook Integration**: Posts results to evaluation endpoints with retry logic
- ⚡ **Async Processing**: Non-blocking background workers for efficient request handling

---

## 🏗️ Architecture

```
┌─────────────────┐
│   Instructor    │
│  (POST Request) │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         FastAPI Server (Port 8000)       │
│  ┌───────────────────────────────────┐  │
│  │   POST /handle_task               │  │
│  │   - Validates secret              │  │
│  │   - Returns 200 immediately       │  │
│  │   - Spawns background worker      │  │
│  └───────────────────────────────────┘  │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│      Background Worker (Async)          │
│  ┌───────────────────────────────────┐  │
│  │ 1. Parse attachments              │  │
│  │ 2. Generate content previews      │  │
│  │ 3. Call LLM API (AIPipe)          │  │
│  │ 4. Create/Update GitHub repo      │  │
│  │ 5. Push files (HTML/CSS/JS/imgs)  │  │
│  │ 6. Enable GitHub Pages            │  │
│  │ 7. Wait for deployment (10 min)   │  │
│  │ 8. POST results to webhook        │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│           GitHub Pages                   │
│  https://user.github.io/repo/            │
└─────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### **Prerequisites**

- Python 3.11+
- GitHub account with Personal Access Token
- AIPipe API key (for LLM access)

### **Installation**

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd Project1
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

Create a `.env` file in the project root:

```env
# GitHub Configuration
GITHUB_USER=your-github-username
GITHUB_TOKEN=ghp_your_personal_access_token

# LLM Configuration
AIPIPE_API_KEY=your-aipipe-api-key
AIPIPE_MODEL=gpt-4o  # or gpt-5, o3-pro

# API Security (optional)
API_SECRET=your-secret-key

# Development Flags
SKIP_GITHUB=0  # Set to 1 to skip GitHub operations (testing)
SKIP_LLM=0     # Set to 1 to use mock LLM responses (testing)

# Repository Settings
DEFAULT_REPO_PRIVATE=0  # Set to 1 for private repos
```

4. **Run the server**
```bash
cd app
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Server will start at: **http://localhost:8000**

---

## 📖 Usage

### **API Endpoint**

**POST** `/handle_task`

#### Request Body:
```json
{
  "email": "student@example.com",
  "secret": "your-secret",
  "task": "study-session-tracker",
  "round": 1,
  "nonce": "20251017-01",
  "brief": "Create an interactive study session tracker...",
  "checks": [
    "Repo has MIT license",
    "README.md contains Usage section",
    "Page contains #total-hours element"
  ],
  "evaluation_url": "https://example.com/notify",
  "attachments": [
    {
      "name": "data.csv",
      "url": "data:text/csv;base64,..."
    }
  ]
}
```

#### Response (Immediate):
```json
{
  "status": "accepted",
  "email": "student@example.com",
  "task": "study-session-tracker",
  "round": 1,
  "nonce": "20251017-01"
}
```

#### Webhook Callback (After Completion):
```json
{
  "email": "student@example.com",
  "task": "study-session-tracker",
  "round": 1,
  "nonce": "20251017-01",
  "repo_url": "https://github.com/user/study-session-tracker_20251017-01",
  "commit_sha": "abc123...",
  "pages_url": "https://user.github.io/study-session-tracker_20251017-01/",
  "status": "success"
}
```

---

## 🧪 Testing

### **Using the Test Server**

1. **Start the main API server** (port 8000)
```bash
cd app
python -m uvicorn app:app --reload
```

2. **Start the test server** (port 9001)
```bash
cd grader
python test_server.py
```

3. **Open browser**: http://localhost:9001

4. **Trigger workflows**:
   - Click **"Trigger Round 1"** - Creates new GitHub repo with generated app
   - Click **"Trigger Round 2"** - Modifies existing repo

### **Manual Testing with cURL**

```bash
curl -X POST http://localhost:8000/handle_task \
  -H "Content-Type: application/json" \
  -d @payload.json
```

---

## 📁 Project Structure

```
Project1/
├── app/
│   ├── app.py                    # Main FastAPI application
│   ├── config.py                 # Configuration loader
│   ├── models/
│   │   └── schema.py             # Pydantic models (TaskRequest)
│   └── services/
│       ├── attachments.py        # Attachment parsing (data URIs, HTTP URLs)
│       ├── evaluation.py         # Webhook posting with retry logic
│       ├── github_service.py     # GitHub API operations
│       ├── llm_generator.py      # LLM integration + system prompts
│       └── storage.py            # Context storage (Round 1 → Round 2)
│
├── grader/
│   └── test_server.py            # FastAPI test server (port 9001)
│
├── data/
│   └── llm_context/              # Stored Round 1 outputs for Round 2
│       └── task_nonce.json
│
├── .env                          # Environment variables (gitignored)
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## 🔧 Configuration

### **Environment Variables**

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `GITHUB_USER` | ✅ | GitHub username | - |
| `GITHUB_TOKEN` | ✅ | Personal access token with `repo` scope | - |
| `AIPIPE_API_KEY` | ✅ | AIPipe API key for LLM access | - |
| `AIPIPE_MODEL` | ⚠️ | LLM model (gpt-4o, gpt-5, o3-pro) | `gpt-4o` |
| `API_SECRET` | ❌ | Secret for `/handle_task` authentication | None |
| `SKIP_GITHUB` | ❌ | Skip GitHub operations (testing) | `0` |
| `SKIP_LLM` | ❌ | Use mock LLM responses (testing) | `0` |
| `DEFAULT_REPO_PRIVATE` | ❌ | Create private repos | `0` |

### **GitHub Token Permissions**

Your GitHub Personal Access Token needs:
- ✅ `repo` (full control of private repositories)
- ✅ `workflow` (update GitHub Actions workflows)

[Create token here](https://github.com/settings/tokens/new)

---

## 🎨 System Prompt Features

The LLM is guided by comprehensive system prompts that ensure:

### **Code Quality**
- ✅ Modern ES6+ JavaScript (async/await, arrow functions)
- ✅ Proper error handling (try/catch blocks)
- ✅ Loading states and user feedback
- ✅ Input validation and sanitization

### **Design Standards**
- ✅ Bootstrap 5.3 for responsive layouts
- ✅ Chart.js 4.4 for data visualizations
- ✅ Mobile-first responsive design
- ✅ Smooth animations and transitions
- ✅ Professional color schemes (gradients, cards, shadows)

### **Data Handling**
- ✅ Fetches CSV/JSON from relative paths (no hardcoding)
- ✅ Parses ALL data rows (no arbitrary limits)
- ✅ Displays images from relative paths
- ✅ Content previews sent to LLM (CSV structure, JSON keys)

### **Round 2 Behavior**
- ✅ Preserves existing good code
- ✅ Makes minimal targeted changes
- ✅ Loads previous context automatically
- ✅ Adds features without breaking old ones

---

## 🔄 Workflow Details

### **Round 1: Create New Application**

1. **Receive Task Request**: Validates secret, returns 200
2. **Parse Attachments**: Extracts CSV/JSON content, downloads images
3. **Generate Content Previews**: Shows CSV columns, JSON structure to LLM
4. **Call LLM**: Sends comprehensive prompt with task + attachments
5. **Create GitHub Repo**: `task-name_nonce` with MIT license
6. **Push Files**: HTML, CSS, JS, README, attachments
7. **Enable GitHub Pages**: Deploys from `main` branch
8. **Wait for Deployment**: Polls every 15s for up to 10 minutes
9. **Post Results**: Sends webhook with repo_url, pages_url, commit_sha

### **Round 2: Modify Existing Application**

1. **Load Round 1 Context**: Retrieves previous files from `data/llm_context/`
2. **Show Previous Code to LLM**: Complete files with "KEEP WHAT'S GOOD" warnings
3. **Generate Modifications**: LLM makes minimal changes
4. **Push Updated Files**: Only changed files (or all files with new content)
5. **Wait for Redeployment**: Verifies timestamp comment in HTML
6. **Post Results**: Updated commit_sha and pages_url

---

## 🐛 Debugging

### **Enable Verbose Logging**

The application already has extensive logging. Watch the terminal for:

```
[ROUND 1] Starting background worker...
[ROUND 1] Parsing 3 attachments...
[ROUND 1] ===== CALLING LLM =====
[LLM] Got 12450 chars
[LLM] Cost today: $0.4104 / $1
[LLM] ✅ Generated 4 files
[GitHub] Creating repo: study-tracker_20251017-01
[GitHub] Enabling GitHub Pages...
[GitHub] ✅ Pages deployed successfully after 45s
[ROUND 1] ✅ Posting results to webhook
```

### **Common Issues**

**❌ "content is not valid Base64"**
- **Cause**: Whitespace in base64 data
- **Fixed**: Attachment parser strips all whitespace

**❌ "GitHub Pages deployment timeout"**
- **Cause**: GitHub Pages taking >10 minutes to deploy
- **Solution**: Wait is logged, webhook still sent, page will work later

**❌ "LLM JSON parse error"**
- **Cause**: Model returned malformed JSON
- **Debug**: Check logs for first/last 500 chars of LLM response
- **Solution**: Improved error handling shows exact error

**❌ "Failed to put file: 409"**
- **Cause**: File already exists with different SHA
- **Solution**: GitHub service handles this automatically

---

## 🧩 Extending the System

### **Adding New LLM Providers**

Edit `app/services/llm_generator.py`:

```python
# Example: Add OpenAI support
import openai

def generate_files_openai(task_payload: Dict) -> Dict:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, ...]
    )
    # Parse response...
```

### **Custom Evaluation Checks**

The system supports any checks the instructor defines:

```json
"checks": [
  "Custom check: Page uses dark mode by default",
  "Performance: Page loads in <2 seconds",
  "Accessibility: All images have alt text"
]
```

LLM receives these as requirements in the prompt.

---

## 📊 Performance

- **API Response Time**: <50ms (immediate 200 response)
- **Background Processing**: 30-180 seconds (depends on LLM speed)
- **GitHub Pages Deployment**: 1-10 minutes
- **Total Time (Round 1)**: 2-12 minutes
- **Total Time (Round 2)**: 2-12 minutes (with redeployment wait)

---

## 🔒 Security

- ✅ API secret validation (optional)
- ✅ GitHub token stored in environment (never committed)
- ✅ Input validation with Pydantic models
- ✅ Safe base64 decoding (handles malformed data)
- ✅ HTTP timeout limits (prevent hanging requests)

**⚠️ Security Note**: This is an educational project. For production:
- Add rate limiting
- Implement proper authentication (OAuth, JWT)
- Validate all user inputs
- Add CORS configuration
- Use secrets management (AWS Secrets Manager, Azure Key Vault)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [AIPipe](https://aipipe.org/) - LLM API platform
- [GitHub API](https://docs.github.com/en/rest) - Repository and Pages management
- [Bootstrap](https://getbootstrap.com/) - Frontend framework
- [Chart.js](https://www.chartjs.org/) - Data visualization library

---

## 📞 Support

For issues, questions, or contributions:
- 📧 Email: your-email@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/your-username/your-repo/issues)

---

**Built with ❤️ for automated web app generation**

"""
Simple test server for triggering Round 1 and Round 2 tasks.

Usage:
    python test_server.py

Then visit:
    http://localhost:9001/round1  - Triggers Round 1 (creates new repo)
    http://localhost:9001/round2  - Triggers Round 2 (modifies existing repo)
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import requests
import uvicorn

app = FastAPI(title="Round Test Server")

# Your API endpoint
API_URL = "https://ai-github-pages-generator.onrender.com/handle_task"

# ngrok URL - REPLACE THIS with your actual ngrok URL!
# Get it by running: ngrok http 9001
# Example: https://abcd-1234-efgh-5678.ngrok-free.app
NGROK_URL = "https://unvivacious-runny-oswaldo.ngrok-free.dev"  # ← UPDATE THIS!

ROUND1_PAYLOAD = {
    "email": "kaishal.student@example.edu",
    "secret": "this-the-secret",
    "task": "minimal-calculator-app",
    "round": 1,
    "nonce": "20251017-03",
    "brief": """
Create a MINIMAL web-based calculator app with the following requirements:

REQUIREMENTS:
1. The app must allow users to perform basic arithmetic operations: addition, subtraction, multiplication, and division.
2. The UI should be clean and minimal, with a display area and buttons for 0-9, +, -, *, /, =, and C (clear).
3. All logic must be implemented in JavaScript (no external libraries).
4. The app must work in any modern browser.
5. Include a README.md with setup and usage instructions.

DESIGN:
- Use simple HTML and CSS only (no frameworks).
- Center the calculator on the page.
- Responsive for mobile and desktop.
- No unnecessary features or styling.

No external dependencies or assets required.
""",
    "checks": [
        "Repo has MIT license",
        "README.md contains 'Usage' or 'Setup' section",
        "Page contains a calculator display area",
        "Page contains buttons for 0-9, +, -, *, /, =, and C",
        "All calculator logic is in JavaScript (no libraries)",
        "No external CSS or JS frameworks used",
        "Calculator is centered and responsive"
    ],
    "evaluation_url": f"{NGROK_URL}/notify",
    "attachments": []
}

# Round 2 Payload - Modifies existing calculator app
ROUND2_PAYLOAD = {
    "email": "kaishal.student@example.edu",
    "secret": "this-the-secret",
    "task": "minimal-calculator-app",
    "round": 2,
    "nonce": "20251017-03",  # same repo as round 1
    "brief": """
ROUND 2 MODIFICATIONS:

Enhance the minimal calculator app with the following updates:

1. Add a dark mode toggle button.
2. Add keyboard support for all calculator functions.
3. Show the last calculation below the display area.
4. Update README.md to document new features and dark mode usage.

KEEP EXISTING:
- All existing features must remain functional.
- Maintain minimal, framework-free design.
- No external dependencies added.
""",
    "checks": [
        "Page contains button for dark mode toggle",
        "Calculator supports keyboard input for all operations",
        "Last calculation is displayed below the main display",
        "README.md mentions 'dark mode' or 'theme toggle'",
        "README.md documents keyboard support",
        "No external CSS or JS frameworks used"
    ],
    "evaluation_url": f"{NGROK_URL}/notify",
    "attachments": []
}



@app.get('/', response_class=HTMLResponse)
def home():
    """Home page with instructions"""
    return """
    <html>
    <head>
        <title>Round Test Server</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                max-width: 800px; 
                margin: 50px auto; 
                padding: 20px;
                background: #f5f5f5;
            }
            .card {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            h1 { color: #333; }
            h2 { color: #666; margin-top: 30px; }
            .btn {
                display: inline-block;
                padding: 15px 30px;
                margin: 10px 10px 10px 0;
                background: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            .btn:hover { background: #0056b3; }
            .btn-success { background: #28a745; }
            .btn-success:hover { background: #1e7e34; }
            code { 
                background: #f4f4f4; 
                padding: 2px 6px; 
                border-radius: 3px;
                color: #e83e8c;
            }
            pre {
                background: #f4f4f4;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
            }
            .info { 
                background: #d1ecf1; 
                padding: 15px; 
                border-radius: 5px;
                border-left: 4px solid #0c5460;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🧪 Round Test Server</h1>
            <p>Simple testing interface for Round 1 and Round 2 workflows.</p>
            
            <h2>📋 Test Endpoints</h2>
            <a href="/round1" class="btn">🚀 Trigger Round 1</a>
            <a href="/round2" class="btn btn-success">🔄 Trigger Round 2</a>
            
            <div class="info">
                <strong>⚠️ Before testing:</strong><br>
                1. Make sure your FastAPI server is running on <code>localhost:8000</code><br>
                2. Update <code>.env</code>: Set <code>SKIP_GITHUB=0</code> and <code>SKIP_LLM=0</code><br>
                3. Round 2 requires Round 1 to run first (creates the repo)
            </div>
            
            <h2>📖 What Each Round Does</h2>
            
            <h3>Round 1: Create New Dashboard</h3>
            <ul>
                <li>Creates new GitHub repo: <code>fitness-tracker-dashboard_20251015-01</code></li>
                <li>Generates fitness tracker with charts, tables, stats cards</li>
                <li>Includes Bootstrap 5 + Chart.js</li>
                <li>Processes CSV (workouts) and JSON (goals) attachments</li>
                <li>Enables GitHub Pages</li>
            </ul>
            
            <h3>Round 2: Modify Existing Dashboard</h3>
            <ul>
                <li>Updates existing repo (same name)</li>
                <li>Adds dark mode toggle</li>
                <li>Changes doughnut → bar chart</li>
                <li>Adds date filter and export button</li>
                <li>Adds personal best section</li>
                <li>Preserves all Round 1 functionality</li>
            </ul>
            
            <h2>🔍 Monitor Progress</h2>
            <p>Watch your FastAPI terminal for verbose logs:</p>
            <pre>[ROUND 1] Starting background worker...
[ROUND 1] Creating new GitHub repo...
[ROUND 1] ===== CALLING LLM =====
[ROUND 1] Generated 4 file(s)...
[ROUND 1] ✅ GitHub Pages is live</pre>
        </div>
    </body>
    </html>
    """


@app.get('/round1')
def trigger_round1():
    """Trigger Round 1 - Create new repo"""
    try:
        print("\n" + "=" * 60)
        print("🚀 TRIGGERING ROUND 1")
        print("=" * 60)
        print(f"Sending payload to: {API_URL}")
        print(f"Task: {ROUND1_PAYLOAD['task']}")
        print(f"Nonce: {ROUND1_PAYLOAD['nonce']}")
        print(f"Attachments: {len(ROUND1_PAYLOAD['attachments'])}")
        
        response = requests.post(API_URL, json=ROUND1_PAYLOAD, timeout=10)
        
        print(f"\n✅ Response Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        return {
            "status": "success",
            "message": "Round 1 triggered successfully!",
            "api_response": response.json() if response.headers.get('content-type') == 'application/json' else response.text,
            "note": "Check your FastAPI terminal for verbose logs. Background worker is processing..."
        }
        
    except requests.exceptions.ConnectionError:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Could not connect to FastAPI server",
                "hint": "Make sure your FastAPI server is running on localhost:8000"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )


@app.get('/round2')
def trigger_round2():
    """Trigger Round 2 - Modify existing repo"""
    try:
        print("\n" + "=" * 60)
        print("🔄 TRIGGERING ROUND 2")
        print("=" * 60)
        print(f"Sending payload to: {API_URL}")
        print(f"Task: {ROUND2_PAYLOAD['task']}")
        print(f"Nonce: {ROUND2_PAYLOAD['nonce']}")
        print(f"Modifications: Dark mode, bar chart, filters, export...")
        
        response = requests.post(API_URL, json=ROUND2_PAYLOAD, timeout=10)
        
        print(f"\n✅ Response Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        return {
            "status": "success",
            "message": "Round 2 triggered successfully!",
            "api_response": response.json() if response.headers.get('content-type') == 'application/json' else response.text,
            "note": "Check your FastAPI terminal for verbose logs. Background worker is modifying existing repo..."
        }
        
    except requests.exceptions.ConnectionError:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Could not connect to FastAPI server",
                "hint": "Make sure your FastAPI server is running on localhost:8000"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )


@app.get('/payload/round1')
def view_round1_payload():
    """View Round 1 payload as JSON"""
    return ROUND1_PAYLOAD


@app.get('/payload/round2')
def view_round2_payload():
    """View Round 2 payload as JSON"""
    return ROUND2_PAYLOAD


@app.post('/notify')
async def receive_notification(request: dict):
    """
    Receives evaluation webhook callbacks from the main API.
    Just prints the received data to terminal for debugging.
    """
    print("\n" + "=" * 70)
    print("📬 EVALUATION WEBHOOK RECEIVED")
    print("=" * 70)
    
    # Pretty print the received payload
    import json
    print(json.dumps(request, indent=2))
    
    print("\n" + "=" * 70)
    print("✅ Notification acknowledged")
    print("=" * 70 + "\n")
    
    return {
        "status": "received",
        "message": "Notification logged successfully"
    }


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🧪 Round Test Server Starting...")
    print("=" * 60)
    print("\n📍 Visit: http://localhost:9001")
    print("\n🚀 Endpoints:")
    print("   GET  /           - Home page with instructions")
    print("   GET  /round1     - Trigger Round 1 (create repo)")
    print("   GET  /round2     - Trigger Round 2 (modify repo)")
    print("   GET  /payload/round1  - View Round 1 JSON")
    print("   GET  /payload/round2  - View Round 2 JSON")
    print("\n⚠️  Make sure FastAPI is running on https://ai-github-pages-generator.onrender.com/")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host='0.0.0.0', port=9001)

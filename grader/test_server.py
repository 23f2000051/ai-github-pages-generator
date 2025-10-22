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
    "task": "weather-widget",
    "round": 1,
    "nonce": "20251022-06",
    "brief": """
Create a simple weather information widget with the following requirements:

REQUIREMENTS:
1. Display weather data from the provided weather_data.json file
2. Show current temperature, conditions, humidity, wind speed
3. Display a 5-day forecast with daily highs and lows
4. Show weather icons/emojis for different conditions (sunny ☀️, rainy 🌧️, cloudy ☁️)
5. Include location info from the JSON file
6. Include a README.md with setup and usage instructions

DESIGN:
- Use simple HTML and CSS (no frameworks required, but Bootstrap optional)
- Clean, card-based layout
- Center the widget on the page
- Responsive for mobile and desktop
- Use appropriate colors (blue for cool, orange for warm, etc.)

DATA FILE:
- weather_data.json: Contains current weather and 5-day forecast

CRITICAL:
- Fetch and parse the JSON file dynamically (no hardcoding)
- Display all forecast days
- Show loading state while fetching
- Handle fetch errors gracefully
""",
    "checks": [
        "Repo has MIT license",
        "README.md contains 'Usage' or 'Setup' section",
        "Page fetches weather_data.json dynamically",
        "Current temperature displayed",
        "Current conditions displayed",
        "Humidity and wind speed shown",
        "5-day forecast displayed",
        "Weather icons/emojis used",
        "Location info shown",
        "Loading state displayed while fetching",
        "Error handling for failed fetch",
        "Page is responsive"
    ],
    "evaluation_url": f"{NGROK_URL}/notify",
    "attachments": [
        {
            "name": "weather_data.json",
            "url": "data:application/json;base64,eyJsb2NhdGlvbiI6IlNhbiBGcmFuY2lzY28sIENBIiwiY3VycmVudCI6eyJ0ZW1wZXJhdHVyZSI6NjgsImNvbmRpdGlvbiI6InN1bm55IiwiaHVtaWRpdHkiOjY1LCJ3aW5kX3NwZWVkIjoxMn0sImZvcmVjYXN0IjpbeyJkYXkiOiJNb25kYXkiLCJoaWdoIjo3MiwibG93Ijo1OCwiY29uZGl0aW9uIjoic3VubnkifSx7ImRheSI6IlR1ZXNkYXkiLCJoaWdoIjo2OSwibG93Ijo1NSwiY29uZGl0aW9uIjoiY2xvdWR5In0seyJkYXkiOiJXZWRuZXNkYXkiLCJoaWdoIjo2NSwibG93Ijo1MywiY29uZGl0aW9uIjoicmFpbnkifSx7ImRheSI6IlRodXJzZGF5IiwiaGlnaCI6NjcsImxvdyI6NTQsImNvbmRpdGlvbiI6ImNsb3VkeSJ9LHsiZGF5IjoiRnJpZGF5IiwiaGlnaCI6NzAsImxvdyI6NTYsImNvbmRpdGlvbiI6InN1bm55In1dfQ=="
        }
    ]
}

# Round 2 Payload - Modifies existing weather widget
ROUND2_PAYLOAD = {
    "email": "kaishal.student@example.edu",
    "secret": "this-the-secret",
    "task": "weather-widget",
    "round": 2,
    "nonce": "20251022-06",  # same repo as round 1
    "brief": """
ROUND 2 MODIFICATIONS:

Enhance the weather widget with the following updates:

1. Add a dark mode toggle button
2. Add temperature unit toggle (Fahrenheit ↔ Celsius)
3. Add hourly forecast section (use sample data if not in JSON)
4. Add "feels like" temperature
5. Update README.md to document new features

KEEP EXISTING:
- All existing weather display features must remain functional
- Keep data fetching from JSON file
- Maintain responsive design
""",
    "checks": [
        "Page has dark mode toggle button",
        "Temperature unit toggle present (F/C)",
        "Hourly forecast section displayed",
        "Feels like temperature shown",
        "README.md documents new features",
        "All original weather data still displayed",
        "JSON file still fetched dynamically"
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

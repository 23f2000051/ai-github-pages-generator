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
API_URL = "http://localhost:8000/handle_task"

ROUND1_PAYLOAD = {
    "email": "kaishal.student@example.edu",
    "secret": "this-the-secret",
    "task": "study-planner-pro",
    "round": 1,
    "nonce": "20251017-01",
    "brief": """Create an interactive Study Planner web app that helps students plan, track, and visualize their daily and weekly study goals.

CRITICAL DATA REQUIREMENTS:
- The study_sessions.csv file contains 20 rows of session data
- You MUST parse and display ALL 20 sessions in the table
- Do NOT hardcode data — fetch and parse study_sessions.csv dynamically
- Use JavaScript fetch('study_sessions.csv') to load and process data
- Parse all rows properly using: text.trim().split('\\n').slice(1).map(row => row.split(','))
- The icon.webp file MUST be displayed at the top-left corner with <img src="icon.webp">

REQUIREMENTS:
1. Beautiful modern UI using Bootstrap 5 cards, gradients, and icons
2. Display total study time (sum of durations) in #total-hours with animated counter
3. Show a pie chart (#chart) using Chart.js displaying subject-wise time allocation
4. Sortable and searchable study log table (#study-table) showing ALL 20 rows
5. Daily progress bar for total target hours from goals.json
6. Cards for "Total Sessions", "Average Duration", "Favorite Subject"
7. Smooth transitions and hover effects for interactivity
8. Fully responsive layout for mobile and desktop
9. Color-coded subjects (Math=blue, Science=green, Literature=purple, History=orange)
10. Include README.md with setup and usage guide

DESIGN SPECS:
- Use Bootstrap 5.3 via CDN
- Load Chart.js 4.4 for the pie chart
- Pastel gradient theme
- Grid layout with card shadows
- Meta viewport tag for responsiveness
- Loading animation while fetching data

DATA FILES TO FETCH:
- study_sessions.csv (20 rows — all must be displayed)
- goals.json (study targets)
- icon.webp (app icon)""",
    "checks": [
        "Repo has MIT license",
        "README.md contains 'Usage' or 'Setup' section",
        "Page contains #total-hours element with number displayed",
        "Page contains canvas element with id='chart'",
        "Page contains table with id='study-table' with at least 20 rows",
        "Page loads Bootstrap CSS from CDN",
        "Page loads Chart.js from CDN",
        "Table includes thead and tbody",
        "Page contains at least 3 Bootstrap cards",
        "Page includes meta viewport tag",
        "JavaScript fetches study_sessions.csv (no hardcoding)",
        "Icon image is displayed (img src='icon.webp')"
    ],
    "evaluation_url": "http://127.0.0.1:9001/notify",
    "attachments": [
        {
            "name": "study_sessions.csv",
            "url": "data:text/csv;base64,ZGF0ZSxzdWJqZWN0LGR1cmF0aW9uX2hvdXJzLGRhdGUsY29tbWVudHMKMjAyNS0xMC0wMSxNYXRoLDEuNSwyMDI1LTEwLTAxLEZpbmlzaGVkIGludGVncmFscyBzZXQKMjAyNS0xMC0wMixTY2llbmNlLDIsMjAyNS0xMC0wMixDaGVtaXN0cnkgcmV2aWV3CjIwMjUtMTAtMDMsTGl0ZXJhdHVyZSwyLCAyMDI1LTEwLTAzLFRvpicuLi4="  # (short example; replace with your full base64 CSV)
        },
        {
            "name": "goals.json",
            "url": "data:application/json;base64,eyJ3ZWVrbHlfdGFyZ2V0X2hvdXJzIjogMjUsICJkYWlseV9nb2FsX2hvdXJzIjogNSwgImZhdm9yaXRlX3N1YmplY3QiOiAiTWF0aCJ9"
        },
        {
            "name": "icon.webp",
            "url": "data:image/webp;base64,UklGRiQSAABXRUJQVlA4WAoAAAAgAAAA/wAAqgAASUNDUAwCAAAAAAIMbGNtcwIQAABtbnRyUkdCIFhZWiAH3AABABkAAwApADlhY3NwQVBQTAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA9tYAAQAAAADTLWxjbXMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAApkZXNjAAAA/AAAAF5jcHJ0AAABXAAAAAt3dHB0AAABaAAAABRia3B0AAABfAAAABRyWFlaAAABkAAAABRnWFlaAAABpAAAABRiWFlaAAABuAAAABRyVFJDAAABzAAAAEBnVFJDAAABzAAAAEBiVFJDAAABzAAAAEBkZXNjAAAAAAAAAANjMgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB0ZXh0AAAAAElYAABYWVogAAAAAAAA9tYAAQAAAADTLVhZWiAAAAAAAAADFgAAAzMAAAKkWFlaIAAAAAAAAG+iAAA49QAAA5BYWVogAAAAAAAAYpkAALeFAAAY2lhZWiAAAAAAAAAkoAAAD4QAALbPY3VydgAAAAAAAAAaAAAAywHJA2MFkghrC/YQPxVRGzQh8SmQMhg7kkYFUXdd7WtwegWJsZp8rGm/fdPD6TD//1ZQOCDyDwAAUFIAnQEqAAGrAD7ZUqBQKCSmoz5fe4kAGwlnbeswDWR7vbO7hHuv25y92Hmn4apN5K8URdszgKxVownyGKv8ckEydjqHv8KfVq9zR/5J5zvK8v2Y1iuNn37TmNbgsBKByeSNi9Hu8g7X8npEmH7hhm75K1g5CBKevJJ5txkYXmBanuAx8PN3y53MrxDNxOQ3U5AOtxNnpetdTbXIBqwc2p+Er1FuHbAdZ3Jx98Dqc3Lq21r8Mv5lyipuaQ4MME5GVgEIFHtJ5eBB0eAUB6t8FlKeZWIAkD6SkAliPncL++J7f4LvC4Va28Dp+ZHmTQY3JciSux30/iSyz3R6cG0TQQ0lFihVZ/pIPPY3PcO/sMbl68XmDo2og2cHgbJWsXO916aYSBSy24uimYf99VaD4VGXtTDT8luO9x5GQuocsmDWeg/4o3CZzj3QevX8qkIcJ+oE32RxdFB0j43USkcuX3nSU3UzEmHZamdrXkYR03ynnJ8CVFYDw+ojAY/HivqF4yF54h7uRfjqPeyWd8PM1ZF/FKrGxDjggIhMx5iXvwSB/81pr+q7W2edrl3vlTX73U1me5GvQ1WiQxztFQ3bLoBRq+oUZ4YAdxa5YIq+PRfe3HWaSKT9T93Rs4yxflDoo1Uzjeb2eLPWBDrYivttCkJbq76EUgF31kfIIka3E0puWGE4jLRq588ObmfBsGT2hpfFrPsYMG48Zl1WPqDvT7UjIAbqlMfmUGQB4uf1tCgRO/gdGm9UWkzZGfG76W/aBw0cLGp6Ae6jF2b5ptO8VimPNMJbv+FKPOEjzoTSX/PZLX1ui64UiDwxkXAaXpHGD4Y932MI91BBxmRe520PyPr/GEisB3g5lUkBdSzckXecwYsKCWrEPGcXmAD+78kS+jnljBxTvT+PK1fvOqeRuFndJXxoYWyPgVY8xOHzzTHhMR19EmyXDkqBYnvw8yZZYiJtZVDVUOrDBMuLwW2xWUPn1HoArKarg+nDMT540RYdiNGzZBledYfyFVDrbH3ZuaPA7ElZPGx+NWj3Un9Mcm4UfzZHMglS42kBUa867U32lLq+zLjOUowyy5Cb3mTNywPBiiHDSZDoIM+zkOzVh1cmCae0P9boLyxcKDfyv+/o6FJpjGDhXncJvaNZFI51R+8fev/V6BhRe5NcCru45HPbMleqCNx1bhvBIxHE8idDBrN/yUZ+4niI4vwulH+eYBIC+p2RqvdIQyTNvEF6ZShcc/Hw6miv56ygZCfMeIxPS5AJNpvyn6Z1yXZtJqSqWPXL4Rmy6MDnI14rGByMUpgceG2kfvs4iXH/YGIcT5xOCxjoQxzX6imeckAw0w3y42ZCjGcAcG+tPtT1GWKEmgkpFn7kDdQMGmM+ac2E5HOBptbo0JCUxx62ERHcxWbL82e7FPR725FLpIaza5IrsAN2sTqLygashU7lW/m33U7NiqClvyiGcAz/yolqf7eIw61hyTVcJTMoRmiVmlma+CODOuEYPH0Pa5+56V03vDw4ymqwKzSodbNivybI9GycfH+pbb2UQjKU31cW5sR63s0P+il0K9GIa9pO9HenAiyuE/7JjmAxDYtG260ho1ZKPn5D76rRXdd3TT/Z/oJdMLsmYk6gyyeolRkFq1mOM3oBv4y8SFGMASsITHU+0qwF67PMtecgi8IJsVyTp8gLeosh381sGXrul5CMkMd46a+3T2+GyzmHiyWQwfjN1k+Q74lp7gbDjVtKUaWX8UbkADtSEDQ3xnDz0+5M2o/2whVco99d+03yjWN3J123XHjV8HLge8a6ZulgemDf3F6C+LLMQNd0waQp8N2UbAU2V/BQ7YLYHhjK7xKlJDyDl9Nzv8FgoiHfEBveaO89wehgD8NJ7QwB5en0/n1rJf4wmLFzeVqdgSvVKZaTHmUEnf78cnhBVDO2RKdrOYU4I9/4zbKhXWYchlSPhaxlzwhf7Dnj5eckOMM4+f6quZFmVdJxFmqDnAuD6ksqJ/sRf1OE9qI85vi/4FyOklDFJSGujiyHjHk9mBurdVepSTtSKY+nQVvY4oxHCs6DwGiSwr4CSNkwFMLW8nvlPWd7wYGuLpuE5UiDnzg+Ps43YtAM+Xw5jZoHBXBTDNhbCYUuVJV0vnQCFo6ZIM3uYIo+bxblMY/e3VMVYSiIUHb7kW+GamiC5t52U4zcTzxdCDyILZCWSP89TqZfOmDEEAhu4S2KEPBViGlON1uu4UrcWxBm7AHzMb7HtfPSRNd6yrNjJxHbaFGkRB7bEY1ECPIcYO8TpnbKBpTdFJPG9Qi2Oczog0dKNKMv4N5l+o/gpqtT+SgKm2O4GJ/60ObNjPzMonI4dG/HrtC6RHtyW4A4+tPrY9TWtIQLwR+ElgkaladxNlec9eleMkxAOut1sygy690IwN/ZWrfw9cPEjUlWXekzTG235x/OsWvRzqSuO/n6/UEw2X2LzJ01udRPC2+Gi1x2xpPnFtM0osf+GfkcZTJxjNWBX7DKDTx9mGsQ3Wiw1+KGj+4M1RxCqZxVWC6MQ7JeU4uzz3UGzzX5B157KJqim67dhtIbWK5maqljUw7BGzMLU+SftxAuaaceSI2P17hwXeko0t0XAjzLzftL7kLovkRXSl27pBE5cn88A9ODA2Suh/f2fgHK5BoXp0wR2WSY/mB8ji2TwOUQ9Lfm6nJ6heAV5eWgJSKat8ed38h1Jbsj7XIWbf348h84LyWI/jIR3PvAOZljENUQZKYbF8ABW24iJ5A2SxDp0wcHDGOYFJaUfxujgWRug3WG0bhPq+qDuCtlSf2Jyt7J9Ix45Osp7OeNH8ctlqNBRnrLAONVRx4lSWDiPu5RBMa7x6dNQpVRqPhA87I9LdEiPRbdZdzKBTz4sqrNfqZdEPgNGYN3euGqxz2Exp117h6yTuUTkybfLYDSXvHnclC7te0HSpoPzsP68iTuIxuU7H+dDzYnAMoU2Y63+k6yrcaeLOhwYWzcGm1e0oXHGQRKEIb7XC9DjQmcDj1WmSKMMDwF6Kgn3fLafHApcZE3OFDzdkS7/poIT/XWyK8jB5YGBw20rsVSSf0P4oxFE9M7HTDNqLim7crfMHEyEL71MaYh0Y+u6Ho11sPu+6UZszb48S1q8C+WfkwuWg2Mlut3k6Qoj9fyMp3NwrJrkF3l3h2bn2R4RH1UvHaZuHED2uvXDmVsbHg20pqd4SjhquhFt268UvsJloJrhtZpP9Przx6Thfhim6jsdh9X8cI05UhhgpTx6NhNMsge8Tp73GuwUvp0mzhz57ZumXyUljxiFbdjeJ0VF6Hd26XSC0bBlUEVCNir5sq6d3rkH4JW+o+BzFDDSOWGP5UJnX1I+YelI+fyDB4rbeSg53QpwAR2dGsJvv4BfB8dgxCF8Nk0+fKLdrOST7nDaK5iDpJGq5wXvFpRxVq/pAgOjKkE67o06bxS/HCtPHq1jcPpZ5OZMWr5E2vqnvnxraK2BOIdXVke/Bou3K80FitKtyz82gouOxbW7I04GHLsA2BHEV9yfhTUMfyvruMx6DloaEW05KOVoH3A16S5tT9q6dWohKjVang73zkMw6IorLXT8euIp4ODFnDUgWaLOgj9hFittON5WDaXB9IgR+8wmOdfeLd4fWg1z7lhxGkywFUewwimCvT3/RiOQj1lFg04Q0stnGB/v18jGm+N7ZQCgXBBwtc9YPmlq85h+29OG1t6O+GprNYU6iM2lbr4f/6a2ZFQU65xG06ioL5iJSAe5TzvAVAyWkk8nUKLO5vzP/2iFdZn+sOr0mkm8SPwvQkzSk0TOt8HYp2u7wgE4pwEXKPWJOldoQ6K1FpTW4l7KXVXvQZtXDq985DiYggHtB0SUgIZgzEMqi1p3v55ephfUU6g5UX8OKIdEYWfCp4cpPFzcvbF186lDceVCKTO881QP+RuMtYAJd+aPp8saucl5r092pySa2VxZuT1LVLWhWZkWKpiHsRHqvAfhmuyTX2N3qbOJLTWT/wfoh4+B9KUTHTP79ENZ2quvDU0pOw/qlYWbweUT07WOxFOR9YmqkOfHFTxIu4EJzH03eed94ttiRbQbhO/tsWIq3LiqRmcjRZKdLNXLJIho+jos/xQbuDXttBo+t3ZOORc8yPnmoXz79HPXeB4GWQDp5vJP+lkv9KMF92aCf41QUNqWOVenXqA4HDkSLC1MrkN6CrmHD/7HVgvrjnLJMyNFQoXyHRFLyQSobRN/CI076RjLOPVgfjtzJlJgKaso6NpRQmff2bYLU1EK7kePzEJV5h/10iaC6HRkHSf7R7F5tsVXgyIHmtYAEpYbq9jz2RA7vgbM576VQBNRt0z2saifVJKr1bn7EI4pRCcmZQE3ercMVD+IxiaIwBwKLtBfPVMfiL0uBsAcFM7sjkD0XIcFyysBijKI0zYyq2S7Wxvue+p/xnu4Mns0u1Cvi0Xo5qdelL2wEnDPHhQ/2Cd8CozmdAsfYRK6Olr9BNha4S2FptUQFTyQ+fCArDChcL62VbkbeBYUS4Mf0FeiAHsTLZl2U9zMjtOBMmh9/Muw/4D0FTLTXPY2PQ6tdRz25ONkhfUC5DYvE4EL2xD1zdQK4iEhspV/xI8dICL6Skec6JdZV5w5piVxs6rCiho+etaD5qP9BUutMirOzQahXcNYwUDNdOE3AFE+U/kpnGHqAT0hOuIeR7f2y1p8kmITPCnAFcv6YcU80ixUasU5z/IOxt97M0sGXIidrMhVqfYIVwTk/mDCadeYB/OpSirDVacTgMpqTWqc7Qp5SMw1ieKL28RYldKTHaYQewkf3kdyD8aZq6i9dnbZdH10WgPlw1YL0+fv2oixUROpUEPpKQj3KAAyPuENb6m+FGP4T3fyf+/v9zjIby7AYEKIH0B9rZzvKBQWztiNdQkZIk2VAsFXiOcKNnZ4TJBtlUj5FHWMevTHUAGrVBoAJRhEodVa4z/3B6Itu2YkXKz6mFnu6VAg9gEQzAh1mgbkSJ8f3+TGegGJpKAyuBRoxUroMdRpp2hjCmJXHsCYe3qErYBeOGTvvm+FqQbG3R9+8BlPo3ESSc8Azu+vHFQWLUWffiHpz+oEhcWNbkdkoWOFxemiZGTqZz2Zj5t1Hrff2BFnqRXhtc94oq88ct761QCYno/VGqa7XSukNU1cTQ+wFi89NBrnYjR8NiUEU55XIfhhg7Lzx4xBlolk7bgN293DRjPMKKun1Ws8JsaDK/6QeAo6/kWZfZ14iSixNJCaZWsQK77i5gcLF3RfKTsPkddOahseD6pvBwpeVwIDOwhzaShVoByZPXZS/229sNFOLqFw+bsttF5IfyEKyNioBjEoXMcL81Sh3gEi30HELOiYXLuVeACg5dA8AdsXyqTakBqMMAo9zBk47KtTjSdklt6CLA4UW3hxDg1Py9EBXA1Qu9Cd/CMWnI6rAPBjQcT3BoTAAA="
        }
    ]
}

# Round 2 Payload - Modifies existing dashboard
ROUND2_PAYLOAD = {
    "email": "kaishal.student@example.edu",
    "secret": "this-the-secret",
    "task": "study-planner-pro",
    "round": 2,
    "nonce": "20251017-01",  # same repo
    "brief": """ROUND 2 MODIFICATIONS:

Enhance the Study Planner app with the following updates:

1. Add dark mode toggle button (#dark-mode-toggle) in the navbar
2. Change the pie chart to a bar chart for clearer subject comparison
3. Add date range filter (#date-filter) for sessions
4. Add export button (#export-btn) to download session data as CSV
5. Add a “Top Subject” card showing the subject with highest total hours
6. Add smooth scroll-to-top button when scrolling down
7. Improve table design — striped rows, centered text, larger font
8. Update README.md to document new features and dark mode usage

KEEP EXISTING:
- All existing features must remain functional
- Maintain all previous IDs, structure, and Chart.js dependency
- Keep Bootstrap 5.3 and responsive layout intact""",
    "checks": [
        "Page contains button with id='dark-mode-toggle'",
        "Page contains select or input with id='date-filter'",
        "Page contains button with id='export-btn'",
        "README.md mentions 'dark mode' or 'theme toggle'",
        "README.md mentions 'export' functionality",
        "Page still has #total-hours element (from Round 1)",
        "Page still has #study-table element (from Round 1)",
        "Page still has #chart element (now a bar chart)",
        "CSS includes dark theme or color variables",
        "JavaScript has event listener for theme toggle"
    ],
    "evaluation_url": "http://127.0.0.1:9001/notify",
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
    print("\n⚠️  Make sure FastAPI is running on http://localhost:8000")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host='0.0.0.0', port=9001)

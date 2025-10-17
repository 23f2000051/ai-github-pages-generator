
import requests
import threading
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import time


payload = {
  "email": "alice.student@example.edu",
  "secret": "this-the-secret",
  "task": "fitness-tracker-dashboard",
  "round": 1,
  "nonce": "20251015-01",
  "brief": """Create an interactive fitness tracker dashboard that visualizes workout data from attached CSV and nutrition goals from JSON. 

REQUIREMENTS:
1. Beautiful, modern UI with Bootstrap 5 cards and gradients
2. Display total calories burned in #total-calories with animated counter
3. Interactive doughnut chart (#chart) showing exercise type breakdown using Chart.js
4. Sortable workout history table (#workout-table) with hover effects
5. Progress bars showing weekly goals completion
6. Stats cards with icons for: Total Workouts, Average Duration, Calories/Day
7. Responsive design that works on mobile and desktop
8. Smooth animations and transitions
9. Color-coded workout types (Cardio=blue, Strength=red, Yoga=green, Sports=orange)
10. README.md with setup and usage instructions

DESIGN SPECS:
- Use Bootstrap 5.3 from CDN
- Load Chart.js 4.4 for the doughnut chart
- Modern color palette with gradients
- Card-based layout with shadows
- Hover effects on interactive elements
- Loading state while processing data""",
  "checks": [
    "Repo has MIT license",
    "README.md contains a 'Usage' or 'Setup' section",
    "Page contains element with id='total-calories' displaying a number",
    "Page contains canvas element with id='chart'",
    "Page contains table with id='workout-table' with at least 3 rows",
    "Page loads Bootstrap CSS from CDN (link[href*='bootstrap'])",
    "Page loads Chart.js from CDN (script[src*='chart.js'])",
    "Table has thead and tbody elements",
    "Page contains at least 3 Bootstrap cards (class='card')",
    "Page is mobile responsive (has meta viewport tag)"
  ],
  "evaluation_url": "http://127.0.0.1:9000/notify",
  "attachments": [
    {
      "name": "workouts.csv",
      "url": "data:text/csv;base64,ZGF0ZSxleGVyY2lzZSx0eXBlLGR1cmF0aW9uLGNhbG9yaWVzCjIwMjUtMTAtMDEsTW9ybmluZyBSdW4sQ2FyZGlvLDQ1LDQyMAoyMDI1LTEwLTAyLFdlaWdodCBUcmFpbmluZyxTdHJlbmd0aCw2MCw0ODAKMjAyNS0xMC0wMyxZb2dhLFlvZ2EsOTAsMTgwCjIwMjUtMTAtMDQsQ3ljbGluZyxDYXJkaW8sNjAsNTQwCjIwMjUtMTAtMDUsQmVuY2ggUHJlc3MsU3RyZW5ndGgsNDUsMzYwCjIwMjUtMTAtMDYsU3dpbW1pbmcsQ2FyZGlvLDMwLDMyMAoyMDI1LTEwLTA3LFBpbGF0ZXMsWW9nYSw2MCwxNTAKMjAyNS0xMC0wOCxCYXNrZXRiYWxsLFNwb3J0cyw5MCw2MzAKMjAyNS0xMC0wOSxFbGxpcHRpY2FsLENhcmRpbyw0MCwzODAKMjAyNS0xMC0xMCxTcXVhdHMsU3RyZW5ndGgsNTAsNDAwCjIwMjUtMTAtMTEsTW9ybmluZyBXYWxrLENhcmRpbywyMCwxNjAKMjAyNS0xMC0xMixIb3QgWW9nYSxZb2dhLDYwLDIyMAoyMDI1LTEwLTEzLFRlbm5pcyxTcG9ydHMsNzUsNTcwCjIwMjUtMTAtMTQsSElJVCxDYXJkaW8sNDUsNTUwCjIwMjUtMTAtMTUsRGVhZGxpZnRzLFN0cmVuZ3RoLDU1LDQ0MA=="
    },
    {
      "name": "goals.json",
      "url": "data:application/json;base64,eyJ3ZWVrbHlfd29ya291dHMiOiA1LCAid2Vla2x5X2NhbG9yaWVzIjogMzUwMCwgImRhaWx5X2NhbG9yaWVzIjogNTAwLCAiZmF2b3JpdGVfdHlwZXMiOiBbIkNhcmRpbyIsICJTdHJlbmd0aCJdfQ=="
    },
    {
      "name": "icon.png",
      # small placeholder PNG (1x1)
      "url": "data:image/webp;base64,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"
    }
  ]
}



def send_task(payload):

    response = requests.post("http://localhost:8000/handle_task", json=payload)
    print("Response status code:", response.status_code)
    print("Response text:", response.text)


class EvalHandler(BaseHTTPRequestHandler):
  # class-level placeholders that will be set before server starts
  event: threading.Event = None
  received_payload: dict = None

  def do_POST(self):
    if self.path != "/notify":
      self.send_response(404)
      self.end_headers()
      return
    length = int(self.headers.get('content-length', 0))
    body = self.rfile.read(length)
    try:
      data = json.loads(body.decode('utf-8'))
    except Exception:
      data = body.decode('utf-8')
    print("\n=== Evaluation webhook received ===")
    try:
      print(json.dumps(data, indent=2))
    except Exception:
      print(str(data))
    # store payload and notify main thread
    EvalHandler.received_payload = data
    if EvalHandler.event:
      EvalHandler.event.set()
    self.send_response(200)
    self.end_headers()


def run_eval_server(server: HTTPServer):
  print("Evaluation server listening on http://127.0.0.1:9000/notify")
  try:
    server.serve_forever()
  except Exception as e:
    print("Eval server stopped:", e)


if __name__ == "__main__":
  # Prepare synchronization primitives
  done_event = threading.Event()
  EvalHandler.event = done_event

  server = HTTPServer(('127.0.0.1', 9000), EvalHandler)
  server_thread = threading.Thread(target=run_eval_server, args=(server,), daemon=False)
  server_thread.start()

  # Send task
  send_task(payload)
  print("Task sent — waiting up to 10 minutes for evaluation webhook...")

  # Wait up to 10 minutes for the webhook to arrive
  got = done_event.wait(timeout=10 * 60)
  if got:
    print("Received evaluation payload:")
    try:
      print(json.dumps(EvalHandler.received_payload, indent=2))
    except Exception:
      print(EvalHandler.received_payload)
  else:
    print("Timed out waiting for evaluation webhook (10 minutes)")

  # Shutdown server gracefully
  try:
    server.shutdown()
    server.server_close()
  except Exception:
    pass
  # Give thread a moment to exit
  time.sleep(0.2)
  print("Evaluation server stopped. Exiting.")






  







# payload = {
#   "id": "sum-of-sales",
#   "brief": "Publish a single-page site that fetches data.csv from attachments, sums its sales column, sets the title to \"Sales Summary ${seed}\", displays the total inside #total-sales, and loads Bootstrap 5 from jsdelivr.",
#   "attachments": [
#     {
#       "name": "data.csv",
#       "url": "data:text/csv;base64,${seed}"
#     }
#   ],
#   "checks": [
#     "document.title === `Sales Summary ${seed}`",
#     "!!document.querySelector(\"link[href*='bootstrap']\")",
#     "Math.abs(parseFloat(document.querySelector(\"#total-sales\").textContent) - ${result}) < 0.01"
#   ],
#   "round2": [
#     {
#       "brief": "Add a Bootstrap table #product-sales that lists each product with its total sales and keeps #total-sales accurate after render.",
#       "checks": [
#         "document.querySelectorAll(\"#product-sales tbody tr\").length >= 1",
#         "(() => {\n  const rows = [...document.querySelectorAll(\"#product-sales tbody tr td:last-child\")];\n  const sum = rows.reduce((acc, cell) => acc + parseFloat(cell.textContent), 0);\n  return Math.abs(sum - ${result}) < 0.01;\n})()"
#       ]
#     },
#     {
#       "brief": "Introduce a currency select #currency-picker that converts the computed total using rates.json from attachments and mirrors the active currency inside #total-currency.",
#       "attachments": [
#         {
#           "name": "rates.json",
#           "url": "data:application/json;base64,${seed}"
#         }
#       ],
#       "checks": [
#         "!!document.querySelector(\"#currency-picker option[value='USD']\")",
#         "!!document.querySelector(\"#total-currency\")"
#       ]
#     },
#     {
#       "brief": "Allow filtering by region via #region-filter, update #total-sales with the filtered sum, and set data-region on that element to the active choice.",
#       "checks": [
#         "document.querySelector(\"#region-filter\").tagName === \"SELECT\"",
#         "document.querySelector(\"#total-sales\").dataset.region !== undefined"
#       ]
#     }
#   ]
# }
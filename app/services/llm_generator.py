import os
import json
import requests
from typing import Dict, List
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

AIPIPE_API_KEY = os.getenv("AIPIPE_API_KEY")
AIPIPE_MODEL = os.getenv("AIPIPE_MODEL")
SKIP_LLM = os.getenv("SKIP_LLM") == "1"

def _get_context_dir() -> Path:
  """Get directory for storing LLM context between rounds"""
  context_dir = Path(__file__).resolve().parents[2] / "data" / "llm_context"
  context_dir.mkdir(parents=True, exist_ok=True)
  return context_dir

def _save_round_context(task: str, nonce: str, round_num: int, files: List[Dict], prompt: str, response: str):
  """Save LLM context for future rounds"""
  try:
    context_file = _get_context_dir() / f"{task}_{nonce}_round{round_num}.json"
    context = {
      "task": task,
      "nonce": nonce,
      "round": round_num,
      "files": files,
      "prompt": prompt,
      "response": response
    }
    context_file.write_text(json.dumps(context, indent=2))
    print(f"[LLM] Saved context to {context_file.name}")
  except Exception as e:
    print(f"[LLM] Warning: Failed to save context: {e}")

def _load_previous_context(task: str, nonce: str, round_num: int) -> Dict:
  """Load context from previous round"""
  try:
    prev_round = round_num - 1
    context_file = _get_context_dir() / f"{task}_{nonce}_round{prev_round}.json"
    if context_file.exists():
      context = json.loads(context_file.read_text())
      print(f"[LLM] Loaded previous context from round {prev_round}")
      return context
  except Exception as e:
    print(f"[LLM] Warning: Failed to load previous context: {e}")
  return None

def _mock_response(brief: str) -> Dict[str, List[Dict]]:
  """Return mock LLM response for testing"""
  print("[LLM] MOCK MODE - Skipping real API call")
  
  return {
    "files": [
      {
        "path": "index.html",
        "content": f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{brief[:50]}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="container mt-5">
    <h1>Mock App: {brief[:50]}</h1>
    <p class="lead">This is a mock response for testing. Set SKIP_LLM=0 to use real LLM.</p>
    <div id="app"></div>
  </div>
  <script src="script.js"></script>
</body>
</html>"""
      },
      {
        "path": "style.css",
        "content": """body {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.container {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 30px;
  backdrop-filter: blur(10px);
}"""
      },
      {
        "path": "script.js",
        "content": """console.log('Mock app loaded');
document.getElementById('app').innerHTML = '<div class=\"alert alert-info\">Mock data displayed here</div>';"""
      }
    ]
  }

# SYSTEM PROMPT - Edit this to fine-tune LLM behavior
SYSTEM_PROMPT = """
You are an elite full-stack developer specializing in creating production-ready web applications.

## YOUR MISSION
Create COMPLETE, FULLY FUNCTIONAL web apps that users can actually use. Not demos. Not prototypes. REAL apps.

## CORE PRINCIPLES
1. **QUALITY OVER SPEED**: Write clean, well-structured, maintainable code
2. **USER EXPERIENCE FIRST**: Beautiful UI, smooth interactions, responsive design
3. **DATA-DRIVEN**: Actually parse and use ALL provided data - never hardcode sample data
4. **ERROR-PROOF**: Handle edge cases, loading states, empty data, fetch failures
5. **PRODUCTION-READY**: Code should work perfectly on first deployment

## TECHNICAL REQUIREMENTS

### File Structure (ALWAYS include these 4 files):
1. **index.html** - Semantic HTML5, proper meta tags, accessible
2. **style.css** - Modern CSS, responsive, organized by sections
3. **script.js** - Clean JavaScript, async/await, proper error handling
4. **README.md** - Professional documentation (Summary, Setup, Usage, Code Explanation, License)

### HTML Standards:
- Use semantic tags: <header>, <main>, <section>, <article>, <footer>
- Include proper meta tags: viewport, charset, description
- Accessibility: alt text, ARIA labels, keyboard navigation
- Load external resources from CDN (Bootstrap 5.3, Chart.js 4.4, etc.)

### CSS Standards:
- Modern layout: Flexbox or Grid
- Smooth transitions and animations
- Consistent spacing and typography
- Dark mode support when appropriate
- Do not use CSS libraries like Bootstrap or Tailwind unless explicitly requested
- This is the bootstrap css imports if needed:
```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-sRIl4kxILFvY47J16cr9ZwB07vP4J8+LH7qKQnuqkuIAvNWLzeN8tE5YBujZqJLB" crossorigin="anonymous">
<script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.8/dist/umd/popper.min.js" integrity="sha384-I7E8VVD/ismYTF4hNIPjVp/Zjvgyol6VFvRkX/vR+Vc4jQkC+hVqc2pM8ODewa9r" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.min.js" integrity="sha384-G/EV+4j2dNv+tEPo3++6LCgdCROaejBqfUeNjuKAiuXbjrxilcCdDz6ZAVfHWe1Y" crossorigin="anonymous"></script>
```
- This is chart js import if needed:
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
```

## ⚠️ YOUR RESPONSIBILITY: DELIVER WORKING CODE

**You are generating production code that will be deployed immediately.**
**Zero tolerance for:**
- Syntax errors
- Undefined variables/functions
- Missing null checks on DOM elements
- Broken event listeners
- Non-existent element IDs referenced in JavaScript
- Vague error messages that don't help users
- Code that crashes instead of failing gracefully

**Before generating ANY code, verify:**
1. Every `getElementById()` in JS has matching `id=""` in HTML
2. Every function called is defined
3. Every library used is included via `<script>` tag
4. Every DOM manipulation has null check
5. Every error has a helpful, specific message
6. Code fails gracefully with user-friendly messages

**If you generate broken code, the user gets a broken website. TAKE RESPONSIBILITY.**

### CRITICAL STYLING RULES (MUST FOLLOW):

**Layout & Spacing:**
- Use proper containers: max-width: 1200px with padding
- Consistent spacing: use rem units (1rem, 1.5rem, 2rem, 3rem)
- Breathing room: Don't cram elements together
- Grid layouts: Use CSS Grid or Bootstrap grid system properly

**Charts & Visualizations:**
- Chart containers: Set reasonable dimensions (max-width: 600px, max-height: 400px)
- Responsive charts: Use `maintainAspectRatio: true` and `responsive: true`
- Chart positioning: Center charts, don't let them take full width
- Multiple charts: Use grid layout with proper gaps

**Colors & Backgrounds:**
- Use modern color schemes (NOT plain white backgrounds)
- Gradients: Subtle, professional (e.g., `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`)
- Cards: Use shadows, borders, or subtle backgrounds to separate content
- Text contrast: Ensure readable text on all backgrounds
- Color palette: Define 3-5 main colors and use consistently

**Typography:**
- Font sizes: Base 16px, headings 1.5-3rem, body 1rem
- Line height: 1.6 for body text
- Font family: Use modern sans-serif (system fonts or Google Fonts)
- Hierarchy: Clear difference between h1, h2, h3, body text

**Components:**
- Cards: Add padding (1.5-2rem), border-radius (8-12px), box-shadow
- Buttons: Proper padding, hover states, focus states
- Tables: Striped rows, hover effects, proper spacing
- Forms: Clear labels, input styling, validation states

**Animations & Transitions:**
- Smooth transitions: Use `transition: all 0.3s ease`
- Hover effects: Scale, shadow, color changes
- Loading states: Spinners or skeleton screens
- Page load: Fade-in animations for content

**DO NOT:**
- ❌ Let charts occupy 100% width/height without constraints
- ❌ Use plain white background with no styling
- ❌ Cram multiple elements without spacing
- ❌ Use default browser styles (style everything!)
- ❌ Make tiny text or huge headings
- ❌ Forget mobile responsive breakpoints

### JavaScript Standards:
- Use modern ES6+: async/await, arrow functions, destructuring
- Proper error handling with try/catch
- Loading states: show spinners/messages while fetching
- Data validation: check for null/undefined/empty
- Event delegation for better performance
- Comments for complex logic

## ATTACHMENT HANDLING (CRITICAL!)

### Files Location:
All attachment files are in the SAME directory as index.html on GitHub Pages.

### Fetching Data:
```javascript
// ✅ CORRECT - Relative path
const response = await fetch('data.csv');
const text = await response.text();

// ❌ WRONG - Don't hardcode or use data URIs
const data = [/* hardcoded */];
```

### CSV Parsing:
```javascript
// ✅ CORRECT - Parse ALL rows properly
const rows = text.trim().split('\\n');
const headers = rows[0].split(',');
const data = rows.slice(1).map(row => {
    const values = row.split(',');
    return headers.reduce((obj, header, i) => {
        obj[header.trim()] = values[i]?.trim();
        return obj;
    }, {});
});

// ❌ WRONG - Don't limit rows arbitrarily
const data = rows.slice(0, 3); // Only 3 rows? NO!
```

### JSON Handling:
```javascript
// ✅ CORRECT
const response = await fetch('config.json');
const config = await response.json();
// Use ALL data from config
```

### Image Display:
```html
<!-- ✅ CORRECT - Relative path -->
<img src="user.png" alt="User Profile" class="profile-img">

<!-- ❌ WRONG - Don't use data URIs -->
<img src="data:image/png;base64,...">
```

### Error Handling:
```javascript
// ✅ ALWAYS handle errors
try {
    const response = await fetch('data.csv');
    if (!response.ok) throw new Error('Failed to load data');
    const text = await response.text();
    // Process data...
} catch (error) {
    console.error('Error loading data:', error);
    document.getElementById('error-message').textContent = 
        'Failed to load data. Please refresh the page.';
}
```

## DEFENSIVE CODING (CRITICAL!)

### ⚠️ ALWAYS Check Elements Exist Before Using Them!

```javascript
// ❌ WRONG - Will crash if element doesn't exist
document.getElementById('total-hours').textContent = '42';

// ✅ CORRECT - Safe with null check
const totalHoursEl = document.getElementById('total-hours');
if (totalHoursEl) {
    totalHoursEl.textContent = '42';
} else {
    console.error('Element #total-hours not found');
}

// ✅ EVEN BETTER - Use optional chaining
document.getElementById('total-hours')?.textContent = '42';
```

### Event Listeners Must Be Safe

```javascript
// ❌ WRONG - Crashes if button doesn't exist
document.getElementById('theme-toggle').addEventListener('click', toggleTheme);

// ✅ CORRECT - Check existence first
const themeToggle = document.getElementById('theme-toggle');
if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        // Save preference
        localStorage.setItem('theme', document.body.classList.contains('dark-mode') ? 'dark' : 'light');
    });
}
```

### DOM Queries in Functions

```javascript
// ✅ ALWAYS validate before using
function updateChart(data) {
    const canvas = document.getElementById('chart');
    if (!canvas) {
        console.error('Chart canvas not found');
        return; // Exit early
    }
    // Now safe to use canvas
    new Chart(canvas.getContext('2d'), { ... });
}
```

### Array/Object Safety

```javascript
// ✅ Check data exists before using
if (data && Array.isArray(data) && data.length > 0) {
    data.forEach(item => { /* process */ });
} else {
    console.warn('No data available');
    showEmptyState();
}
```

## CODE QUALITY ENFORCEMENT ⚠️

### YOU ARE RESPONSIBLE FOR WORKING CODE!

**NEVER generate code that:**
- References DOM elements without checking they exist
- Has undefined variable references
- Uses functions/libraries that aren't included in the HTML
- Contains syntax errors or typos
- Has logic errors that cause crashes

### Validation Checklist (Review Before Responding):

1. **✅ All element IDs used in JS exist in HTML**
   ```javascript
   // If script.js has: document.getElementById('my-button')
   // Then index.html MUST have: <button id="my-button">
   ```

2. **✅ All external libraries are loaded**
   ```html
   <!-- If using Chart.js, MUST include: -->
   <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
   ```

3. **✅ Every DOM query has null check**
   ```javascript
   // EVERY single getElementById/querySelector needs:
   const el = document.getElementById('something');
   if (!el) return; // or handle gracefully
   ```

4. **✅ Error messages are helpful**
   ```javascript
   // ❌ BAD: Generic/useless errors
   catch(e) { console.log('error'); }
   
   // ✅ GOOD: Specific, actionable errors
   catch(e) { 
       console.error('Failed to load expenses.csv:', e.message);
       alert('Could not load expense data. Please check that expenses.csv exists.');
   }
   ```

5. **✅ All variables are defined before use**
   ```javascript
   // Check: No undefined variables, all functions exist
   ```

### Test Your Code Mentally:

Before generating the response, **mentally walk through**:
- What happens if data file is missing? ✅ Shows error message
- What if user clicks button before data loads? ✅ Button disabled or checked
- What if CSV is malformed? ✅ try/catch with helpful error
- What if element ID doesn't exist? ✅ Null check prevents crash

## UI/UX REQUIREMENTS

### Must Have:
- ✅ Loading states (spinners/messages while data loads)
- ✅ Error messages (if data fails to load)
- ✅ Empty states (if no data available)
- ✅ Smooth animations (fade-in, slide, etc.)
- ✅ Hover effects on interactive elements
- ✅ Mobile responsive (test at 320px, 768px, 1024px widths)
- ✅ Fast load time (optimize images, minimize code)

### Bootstrap 5 Usage:
- Use cards, modals, alerts, badges effectively
- Responsive grid system (container, row, col)
- Utility classes for spacing (mt-3, p-4, etc.)
- Color system (primary, success, danger, etc.)

### Charts (if needed):
- Use Chart.js 4.4 from CDN
- Responsive charts (maintainAspectRatio: true)
- Proper colors and labels
- Interactive tooltips
- Legend positioning

## ROUND BEHAVIOR

### Round 1 (New Project):
- Create all 4 required files from scratch
- Implement complete functionality
- Fetch and display ALL data from attachments
- Ensure all checks pass

### Round 2+ (Modifications):
⚠️ **CRITICAL: DO NOT REWRITE EVERYTHING!** ⚠️

**Your job in Round 2 is to make MINIMAL TARGETED CHANGES:**

1. **PRESERVE existing good code** - Don't touch what's already working
2. **Only modify** the specific parts mentioned in the feedback/checks
3. **Keep the same styling** unless specifically asked to change it
4. **Don't rewrite functions** that are already working
5. **Add new features** without removing old ones

**Example - If feedback says "Fix chart labels":**
- ✅ GOOD: Only change the chart labels configuration
- ❌ BAD: Rewrite entire HTML, CSS, and chart code

**Example - If feedback says "Add dark mode toggle":**
- ✅ GOOD: Add toggle button and CSS variables, keep everything else
- ❌ BAD: Completely redesign the whole UI

**How to approach Round 2:**
1. Look at the previous files you generated
2. Identify the SPECIFIC issue to fix
3. Make the SMALLEST change that fixes it
4. Return the COMPLETE files but with MINIMAL edits

**Remember:** If Round 1 code was good, keep it! Only fix what's broken or add what's requested.

Load previous context (automatically provided)
Modify ONLY necessary files
Preserve existing functionality
Add new features without breaking old ones
Update README with new features

## OUTPUT FORMAT

Return ONLY a valid JSON object. NO markdown fences, NO explanations, NO extra text.

IMPORTANT: In index.html, add this EXACT comment at the top of <body> tag:
<!-- Generated: TIMESTAMP -->
Replace TIMESTAMP with current Unix timestamp (e.g., 1234567890). This helps verify deployments.

```json
{
  "files": [
    {"path": "index.html", "content": "<!DOCTYPE html>..."},
    {"path": "style.css", "content": "/* Styles */..."},
    {"path": "script.js", "content": "// JavaScript..."},
    {"path": "README.md", "content": "# Project Title..."}
  ]
}
```

## QUALITY CHECKLIST (Verify before returning):
- [ ] All attachment files are fetched (not hardcoded)
- [ ] ALL data rows are parsed and displayed (no arbitrary limits)
- [ ] Loading states show while fetching
- [ ] Error handling catches fetch failures
- [ ] Mobile responsive (works on small screens)
- [ ] Images display correctly with proper paths
- [ ] All checks from the brief are satisfied
- [ ] Code is clean, commented, and maintainable
- [ ] README is complete and helpful
- [ ] No LICENSE file generated (already exists)

## REMEMBER:
You are creating apps that REAL USERS will use. Make them proud. Make them beautiful. Make them work perfectly.
"""


def generate_files(task_payload: Dict) -> Dict[str, List[Dict]]:
  """Generate files using AIPipe - dead simple"""
  
  # Mock mode for testing
  if SKIP_LLM:
    brief = task_payload.get("brief", "Test App")
    return _mock_response(brief)
  
  if not AIPIPE_API_KEY:
    raise ValueError("AIPIPE_API_KEY not set in .env")
  
  brief = task_payload.get("brief", "")
  checks = task_payload.get("checks", [])
  task_name = task_payload.get("task", "unknown")
  nonce = task_payload.get("nonce", "no-nonce")
  round_num = task_payload.get("round", 1)
  
  # Use parsed attachments if available (has mime_type), otherwise fall back to raw attachments
  attachments = task_payload.get("parsed_attachments") or task_payload.get("attachments", [])
  
  # Load previous round context if this is round 2+
  previous_context = None
  if round_num > 1:
    previous_context = _load_previous_context(task_name, nonce, round_num)
  
  # Build attachment info with content preview
  attachment_info = ""
  if attachments:
    attachment_info = "\n\n## AVAILABLE DATA FILES:\n"
    for att in attachments:
      path = att.get("path", "unknown")
      mime = att.get("mime_type", "unknown")
      preview = att.get("content_preview", "")
      
      attachment_info += f"\n### File: `{path}` (type: {mime})\n"
      
      # Show content preview if available
      if preview and preview != f"[Binary file: {mime}]":
        # Show structure for CSV/JSON
        if mime in ["text/csv", "application/csv"]:
          lines = preview.split('\n')[:10]  # First 10 lines
          attachment_info += "**Structure (first rows):**\n```csv\n"
          attachment_info += '\n'.join(lines)
          attachment_info += "\n```\n"
          if len(preview.split('\n')) > 10:
            attachment_info += f"*Note: File has more rows - fetch and parse ALL data*\n"
        elif mime == "application/json":
          attachment_info += "**Content:**\n```json\n"
          attachment_info += preview[:500]  # First 500 chars
          attachment_info += "\n```\n"
        else:
          # Plain text
          attachment_info += f"**Preview:**\n```\n{preview[:300]}\n```\n"
      else:
        # Binary file (image)
        attachment_info += f"*This is a binary file that will be available at the same location. Display using: `<img src=\"{path}\">`*\n"
  
  # Format checks as clear requirements
  checks_info = ""
  if checks:
    checks_info = "\n\nREQUIRED CHECKS (Your app MUST pass all these):\n"
    for idx, check in enumerate(checks, 1):
      checks_info += f"{idx}. {check}\n"
  
  # Add previous context for round 2+
  context_info = ""
  if previous_context and round_num > 1:
    context_info = f"""

═══════════════════════════════════════════════════════════════
PREVIOUS ROUND {round_num - 1} CODE (KEEP WHAT'S GOOD!)
═══════════════════════════════════════════════════════════════

⚠️ **IMPORTANT:** The code below was already generated and is working.
   Only change what needs to be fixed based on the feedback/checks.
   DO NOT rewrite everything from scratch!

"""
    prev_files = previous_context.get("files", [])
    for f in prev_files:
      path = f.get('path', 'unknown')
      content = f.get('content', '')
      context_info += f"\n### File: {path}\n"
      context_info += f"```\n{content}\n```\n"
    
    context_info += """
═══════════════════════════════════════════════════════════════
END OF PREVIOUS CODE
═══════════════════════════════════════════════════════════════

**Your task:** Make MINIMAL changes to fix issues or add features mentioned in the checks.
**Keep:** Everything that's already working well
**Change:** Only what's broken or missing
"""
  
  # Round instruction
  round_info = f"\n\nROUND: {round_num}"
  if round_num == 1:
    round_info += " (Create new files)"
  else:
    round_info += " (Modify existing files to fix issues/add features)"
  
  # Combine system prompt + round + task + checks + attachments + context
  prompt = f"""{SYSTEM_PROMPT}

{round_info}{context_info}

TASK: {brief}{checks_info}{attachment_info}

Generate the complete web app as JSON now:"""
  
  print(f"\n[LLM] Calling AIPipe ({AIPIPE_MODEL})...")
  
  # Call AIPipe
  response = requests.post(
    "https://aipipe.org/openai/v1/responses",
    headers={"Authorization": f"Bearer {AIPIPE_API_KEY}", "Content-Type": "application/json"},
    json={"model": AIPIPE_MODEL, "input": prompt},
    timeout=120
  )
  response.raise_for_status()
  data = response.json()
  
  # Extract text from response
  text = data["output"][0]["content"][0]["text"]
  print(f"[LLM] Got {len(text)} chars")
  
  # Show usage
  try:
    usage = requests.get("https://aipipe.org/usage", headers={"Authorization": f"Bearer {AIPIPE_API_KEY}"}, timeout=5).json()
    print(f"[LLM] Cost today: ${usage['usage'][-1]['cost']:.4f} / ${usage['limit']}")
  except:
    pass
  
  # Parse JSON with robust error handling
  try:
    # Remove markdown code fences if present
    if "```" in text:
      parts = text.split("```")
      for part in parts:
        if part.strip().startswith("json"):
          text = part[4:].strip()  # Remove "json" prefix
          break
        elif part.strip() and part.strip()[0] == "{":
          text = part.strip()
          break
    
    # Find JSON boundaries
    start = text.find("{")
    end = text.rfind("}") + 1
    
    if start == -1 or end == 0:
      print(f"[LLM] ❌ No JSON found in response!")
      print(f"[LLM] First 500 chars: {text[:500]}")
      raise ValueError("No JSON object found in LLM response")
    
    json_str = text[start:end]
    print(f"[LLM] Extracted JSON: {len(json_str)} chars")
    
    result = json.loads(json_str)
    
    if "files" not in result:
      print(f"[LLM] ❌ Response missing 'files' key!")
      print(f"[LLM] Keys found: {list(result.keys())}")
      raise ValueError("LLM response missing 'files' array")
    
    print(f"[LLM] ✅ Generated {len(result['files'])} files")
    
    # Save context for future rounds
    _save_round_context(task_name, nonce, round_num, result["files"], prompt, text)
    
    return {"files": result["files"]}
    
  except json.JSONDecodeError as e:
    print(f"[LLM] ❌ JSON parse error: {e}")
    print(f"[LLM] Full response text (first 1000 chars):")
    print(text[:1000])
    print(f"[LLM] Full response text (last 500 chars):")
    print(text[-500:])
    raise ValueError(f"Failed to parse LLM JSON response: {e}")


from fastapi import FastAPI, HTTPException
import asyncio
import os
from services.github_service import (
    create_github_repo,
    enable_github_pages,
    push_files,
    get_sha_of_latest_commit,
    wait_for_pages_deployment,
)
from models.schema import TaskRequest
from services.attachments import parse_attachments
from fastapi.encoders import jsonable_encoder
from services.llm_generator import generate_files
from services.evaluation import post_results
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root so we can read DEFAULT_REPO_PRIVATE without importing app.config
env_path = Path(__file__).resolve().parents[1] / ".env"
if env_path.exists():
    load_dotenv(env_path)


async def do_round1(data_dict: dict) -> None:
    """Async background worker: perform GitHub operations and notify evaluator.

    Blocking service calls are executed via asyncio.to_thread to avoid
    blocking the event loop.
    """
    try:
        # Reconstruct minimal fields
        repo_base = data_dict.get("task") or "generated-repo"
        nonce = data_dict.get("nonce") or data_dict.get("nounce")
        repo_name = f"{repo_base}_{nonce}" if nonce else repo_base

        # Prepare placeholders
        repo_info = None
        pages_info = None
        latest_sha = None
        errors: list[str] = []

        # Parse attachments and generate files (run in thread-safe manner)
        try:
            attachments = data_dict.get("attachments", []) or []
            parsed = await asyncio.to_thread(parse_attachments, attachments)
        except Exception as e:
            parsed = []
            errors.append(f"attachment_parse_error: {e}")
            print("do_round1: attachment parse error:", e)

        # === VERBOSE LLM CALL START ===
        print("\n" + "="*80)
        print("🤖 CALLING LLM API (GEMINI) TO GENERATE FILES")
        print("="*80)
        print(f"📋 Task: {data_dict.get('task', 'unknown')}")
        print(f"🔄 Round: {data_dict.get('round', 1)}")
        print(f"🎯 Nonce: {data_dict.get('nonce', 'N/A')}")
        print(f"📝 Brief: {data_dict.get('brief', 'N/A')[:100]}..." if len(str(data_dict.get('brief', ''))) > 100 else f"📝 Brief: {data_dict.get('brief', 'N/A')}")
        print(f"✅ Checks: {len(data_dict.get('checks', []))} checks provided")
        print(f"📎 Attachments: {len(attachments)} attachments parsed")
        print(f"⏳ Calling generate_files()...")
        print("="*80 + "\n")
        
        # Add parsed attachments info to data_dict for LLM
        data_dict_with_parsed = data_dict.copy()
        if parsed:
            # Include content for text files, preview for large files
            data_dict_with_parsed["parsed_attachments"] = []
            for p in parsed:
                att_info = {
                    "path": p.get("path"),
                    "mime_type": p.get("mime", "unknown"),
                    "encoding": p.get("encoding", "unknown")
                }
                
                # Include content for text/JSON/CSV (so LLM knows structure)
                content = p.get("content", "")
                mime = p.get("mime", "")
                if mime and (mime.startswith("text/") or mime in ["application/json", "application/csv"]):
                    # For CSV/JSON, include preview or full content
                    if len(content) < 5000:  # Small files: send full content
                        att_info["content_preview"] = content
                    else:  # Large files: send first 2000 chars
                        att_info["content_preview"] = content[:2000] + "\n... (file continues)"
                else:
                    # For binary files (images), just mention they exist
                    att_info["content_preview"] = f"[Binary file: {mime}]"
                
                data_dict_with_parsed["parsed_attachments"].append(att_info)
        
        try:
            generated = await asyncio.to_thread(generate_files, data_dict_with_parsed)
            gen_files = generated.get("files", [])
            
            # === VERBOSE LLM OUTPUT ===
            print("\n" + "="*80)
            print("✅ LLM API RESPONSE RECEIVED SUCCESSFULLY")
            print("="*80)
            print(f"📦 Number of files generated: {len(gen_files)}")
            print(f"📁 Generated files:")
            for idx, file in enumerate(gen_files, 1):
                file_path = file.get("path", "unknown")
                content_length = len(file.get("content", ""))
                print(f"   {idx}. {file_path} ({content_length} bytes)")
            print("\n📄 File Contents Preview:")
            for file in gen_files:
                file_path = file.get("path", "unknown")
                content = file.get("content", "")
                preview = content[:200] if len(content) > 200 else content
                print(f"\n   --- {file_path} ---")
                print(f"   {preview}...")
                if len(content) > 200:
                    print(f"   ... (+ {len(content) - 200} more bytes)")
            print("\n" + "="*80 + "\n")
            
        except Exception as e:
            gen_files = []
            errors.append(f"llm_generation_error: {e}")
            print("\n" + "="*80)
            print("❌ LLM API CALL FAILED")
            print("="*80)
            print(f"🚨 Error Type: {type(e).__name__}")
            print(f"🚨 Error Message: {str(e)}")
            print("="*80 + "\n")
            print("do_round1: LLM generation error:", e)

        attach_files = []
        for a in (parsed or []):
            try:
                attach_files.append({"path": a["path"], "content": a["content"], "encoding": a.get("encoding", "utf-8")})
            except Exception as e:
                errors.append(f"attachment_normalize_error: {e}")
                print("do_round1: attachment normalize error:", e)

        combined_files = (gen_files or []) + attach_files

        # Respect default privacy setting from the environment (.env)
        private = os.getenv("DEFAULT_REPO_PRIVATE", "0") == "1"

        # GitHub operations — each wrapped to collect errors but continue
        try:
            repo_info = await asyncio.to_thread(create_github_repo, repo_name, private)
            print(f"✅ GitHub repo created/retrieved: {repo_info}")
        except Exception as e:
            errors.append(f"create_repo_error: {e}")
            print("do_round1: create_github_repo error:", e)

        try:
            if combined_files:
                push_results = await asyncio.to_thread(
                    push_files,
                    repo_name,
                    combined_files,
                    commit_message_prefix=data_dict.get("task"),
                    round=data_dict.get("round", 1)
                )
            else:
                push_results = []
        except Exception as e:
            errors.append(f"push_files_error: {e}")
            print("do_round1: push_files error:", e)

        try:
            pages_info = await asyncio.to_thread(enable_github_pages, repo_name, "main")
            print(f"✅ GitHub Pages enabled: {pages_info}")
        except Exception as e:
            errors.append(f"enable_pages_error: {e}")
            print("do_round1: enable_github_pages error:", e)

        try:
            latest_sha = await asyncio.to_thread(get_sha_of_latest_commit, repo_name, "main")
        except Exception as e:
            errors.append(f"get_sha_error: {e}")
            print("do_round1: get_sha_of_latest_commit error:", e)

        # Build final evaluation payload with status
        eval_payload = {
            "email": data_dict.get("email"),
            "task": data_dict.get("task"),
            "round": data_dict.get("round"),
            "nonce": nonce,
            "repo_url": None,
            "commit_sha": latest_sha,
            "pages_url": None,
        }

        # repo_info may contain html_url or full_name
        if isinstance(repo_info, dict):
            eval_payload["repo_url"] = repo_info.get("html_url") or repo_info.get("svn_url") or repo_info.get("url")
            print(f"🔗 Extracted repo_url from repo_info: {eval_payload['repo_url']}")
        # pages_info may contain pages_url
        if isinstance(pages_info, dict):
            eval_payload["pages_url"] = pages_info.get("pages_url") or pages_info.get("html_url")
            print(f"🌐 Extracted pages_url from pages_info: {eval_payload['pages_url']}")

        # If we have errors, attach them (string-joined) so the evaluator can see what happened
        if errors:
            eval_payload["error"] = "; ".join(errors)

        # Fallback constructions
        if not eval_payload["repo_url"]:
            # try to infer owner from repo_info.full_name
            if isinstance(repo_info, dict) and repo_info.get("full_name"):
                eval_payload["repo_url"] = f"https://github.com/{repo_info.get('full_name')}"
                print(f"🔗 Constructed repo_url from full_name: {eval_payload['repo_url']}")
            elif isinstance(repo_info, dict) and repo_info.get("name"):
                # Handle mock response case (uses global os import from line 3)
                owner = os.getenv("GITHUB_USER", "your-github-username")
                eval_payload["repo_url"] = f"https://github.com/{owner}/{repo_info.get('name')}"
                print(f"🔗 Constructed repo_url from name (mock): {eval_payload['repo_url']}")
                
        if not eval_payload["pages_url"]:
            # Best effort: use owner from repo_url
            if eval_payload.get("repo_url"):
                try:
                    owner_repo = eval_payload["repo_url"].rstrip("/").split("github.com/")[-1]
                    owner = owner_repo.split("/")[0]
                    eval_payload["pages_url"] = f"https://{owner}.github.io/{repo_name}/"
                    print(f"🌐 Constructed pages_url from repo_url: {eval_payload['pages_url']}")
                except Exception as e:
                    print(f"⚠️ Failed to construct pages_url: {e}")
        
        # Wait for GitHub Pages to be deployed before sending final evaluation
        if eval_payload.get("pages_url") and not errors:
            print("\n" + "="*80)
            print("⏳ WAITING FOR GITHUB PAGES DEPLOYMENT")
            print("="*80)
            try:
                pages_ready = await asyncio.to_thread(
                    wait_for_pages_deployment, 
                    eval_payload["pages_url"],
                    timeout=300,  # 5 minutes max
                    check_interval=10  # Check every 10 seconds
                )
                if not pages_ready:
                    print("⚠️ GitHub Pages deployment timeout - URL may not be ready yet")
                    # Don't add to errors, just warn - the page might work later
            except Exception as e:
                print(f"⚠️ Error while waiting for pages deployment: {e}")
            print("="*80 + "\n")
        
        # Final verbose output before sending evaluation
        print("\n" + "="*80)
        print("📤 FINAL EVALUATION PAYLOAD")
        print("="*80)
        print(f"Email: {eval_payload.get('email')}")
        print(f"Task: {eval_payload.get('task')}")
        print(f"Round: {eval_payload.get('round')}")
        print(f"Status: {eval_payload.get('status')}")
        print(f"Repo URL: {eval_payload.get('repo_url')}")
        print(f"Pages URL: {eval_payload.get('pages_url')}")
        print(f"Commit SHA: {eval_payload.get('commit_sha')}")
        if eval_payload.get('error'):
            print(f"Errors: {eval_payload.get('error')}")
        print("="*80 + "\n")

        # Send to evaluation_url (best-effort) via thread
        eval_url = data_dict.get("evaluation_url") or data_dict.get("evaluation")
        if eval_url:
            try:
                await asyncio.to_thread(post_results, eval_url, eval_payload)
            except Exception as e:
                print("do_round1: failed to post final evaluation payload:", e)
    except Exception as e:
        # Catch any unexpected error in the background worker to ensure it doesn't crash silently
        print("do_round1: unexpected error:", e)


async def do_round2(data_dict: dict) -> None:
    """Async background worker for Round 2: modify existing repo files.
    
    In Round 2:
    - Repo already exists (created in Round 1)
    - LLM generates modifications based on feedback/checks
    - Only modified files are pushed (existing files preserved)
    - Pages are already enabled, just wait for new deployment
    """
    try:
        print("\n" + "=" * 60)
        print("[ROUND 2] Starting background worker")
        print("=" * 60)
        
        task_name = data_dict.get("task")
        nonce = data_dict.get("nonce") or data_dict.get("nounce")
        eval_url = data_dict.get("evaluation_url") or data_dict.get("evaluation")
        email = data_dict.get("email")
        repo_name = f"{task_name}_{nonce}"
        
        print(f"[ROUND 2] Task: {task_name}")
        print(f"[ROUND 2] Nonce: {nonce}")
        print(f"[ROUND 2] Repo: {repo_name} (existing)")
        
        # Parse attachments if provided
        attachments_raw = data_dict.get("attachments", [])
        parsed_attach = []
        if attachments_raw:
            print(f"[ROUND 2] Parsing {len(attachments_raw)} attachment(s)...")
            parsed_attach = await asyncio.to_thread(parse_attachments, attachments_raw)
            print(f"[ROUND 2] Parsed attachments: {[a['path'] for a in parsed_attach]}")
        
        # Prepare data for LLM (include parsed attachment metadata)
        data_dict_with_parsed = data_dict.copy()
        if parsed_attach:
            data_dict_with_parsed["parsed_attachments"] = [
                {"path": att["path"], "mime_type": att.get("mime")} 
                for att in parsed_attach
            ]
        
        print("\n[ROUND 2] ===== CALLING LLM =====")
        print(f"[ROUND 2] Task brief: {data_dict.get('brief', 'N/A')[:100]}...")
        print(f"[ROUND 2] Checks: {data_dict.get('checks', [])}")
        print(f"[ROUND 2] Round: 2 (modification mode)")
        print("[ROUND 2] Generating modified files...")
        
        # Generate modified files using LLM (it will load Round 1 context automatically)
        result = await asyncio.to_thread(generate_files, data_dict_with_parsed)
        gen_files = result.get("files", [])
        
        print(f"\n[ROUND 2] ===== LLM RESPONSE =====")
        print(f"[ROUND 2] Generated {len(gen_files)} file(s):")
        for f in gen_files:
            print(f"[ROUND 2]   - {f.get('path')} ({len(f.get('content', ''))} chars)")
        
        # Extract timestamp from generated HTML for deployment verification
        html_timestamp = None
        for f in gen_files:
            if f.get("path") == "index.html":
                import re
                match = re.search(r'<!-- Generated: (\d+) -->', f.get("content", ""))
                if match:
                    html_timestamp = match.group(1)
                    print(f"[ROUND 2] Found generation timestamp in HTML: {html_timestamp}")
                break
        
        # Combine LLM-generated files with any parsed attachments
        attach_files = [
            {"path": att["path"], "content": att["content"]}
            for att in parsed_attach
        ]
        combined_files = gen_files + attach_files
        
        print(f"\n[ROUND 2] Total files to push: {len(combined_files)}")
        
        # Skip GitHub operations if SKIP_GITHUB is set
        skip_github = os.getenv("SKIP_GITHUB", "0") == "1"
        if skip_github:
            print("[ROUND 2] SKIP_GITHUB=1, skipping all GitHub operations")
            return
        
        # Push modified files to existing repo (Round 2)
        print(f"\n[ROUND 2] Pushing {len(combined_files)} file(s) to existing repo: {repo_name}")
        await asyncio.to_thread(
            push_files,
            repo_name,
            combined_files,
            commit_message_prefix="Round 2: Updates based on feedback",
            round=2
        )
        print(f"[ROUND 2] Files pushed successfully")
        
        # Get latest commit SHA
        print(f"[ROUND 2] Fetching latest commit SHA...")
        commit_sha = await asyncio.to_thread(get_sha_of_latest_commit, repo_name)
        print(f"[ROUND 2] Latest commit SHA: {commit_sha}")
        
        # Construct URLs (repo already exists from Round 1)
        github_user = os.getenv("GITHUB_USER")
        repo_url = f"https://github.com/{github_user}/{repo_name}"
        pages_url = f"https://{github_user}.github.io/{repo_name}/"
        
        print(f"\n[ROUND 2] Repository: {repo_url}")
        print(f"[ROUND 2] Pages URL: {pages_url}")
        
        # Wait for new deployment to be live
        print(f"\n[ROUND 2] Waiting for GitHub Pages to redeploy (max 5 minutes)...")
        
        # If we have a timestamp, use it to verify new content is deployed
        expected_content = f"<!-- Generated: {html_timestamp} -->" if html_timestamp else None
        
        deployment_ready = await asyncio.to_thread(
            wait_for_pages_deployment,
            pages_url,
            300,  # 5 minute timeout
            10,   # Check every 10 seconds
            expected_content  # Verify this content is present
        )
        
        if deployment_ready:
            print(f"[ROUND 2] ✅ GitHub Pages is live at: {pages_url}")
        else:
            print(f"[ROUND 2] ⚠️ GitHub Pages deployment timed out, but continuing...")
        
        # Post final results to evaluator
        if eval_url:
            eval_payload = {
                "email": email,
                "task": task_name,
                "round": 2,
                "nonce": nonce,
                "repo_url": repo_url,
                "commit_sha": commit_sha,
                "pages_url": pages_url,
            }
            print(f"\n[ROUND 2] Posting results to evaluator: {eval_url}")
            print(f"[ROUND 2] Payload: {eval_payload}")
            
            try:
                await asyncio.to_thread(post_results, eval_url, eval_payload)
                print("[ROUND 2] ✅ Evaluation posted successfully")
            except Exception as e:
                print(f"[ROUND 2] ❌ Failed to post evaluation: {e}")
    except Exception as e:
        print(f"[ROUND 2] ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


app = FastAPI()


def verify_secret(provided: str | None) -> bool:
    expected = os.getenv("API_SECRET")
    if expected is None:
        return True
    return provided == expected

@app.post("/handle_task")
async def handle_task(data: TaskRequest):
    if not verify_secret(data.secret):
        raise HTTPException(status_code=403, detail="Invalid secret")

    # Immediate acknowledgement: copy required fields back to caller
    ack = {
        "status": "accepted",
        "email": getattr(data, "email", None),
        "task": data.task,
        "round": data.round,
        "nonce": getattr(data, "nonce", None) or getattr(data, "nounce", None),
    }

    # Immediately notify the evaluation URL that the task was accepted (fast ACK)
    eval_url = getattr(data, "evaluation_url", None) or getattr(data, "evaluation", None)
    if eval_url:
        init_payload = {
            "email": getattr(data, "email", None),
            "task": data.task,
            "round": data.round,
            "nonce": getattr(data, "nonce", None) or getattr(data, "nounce", None),
            "repo_url": None,
            "commit_sha": None,
            "pages_url": None,
            "status": "accepted",
        }
        # fire-and-forget the initial webhook so the handler stays fast
        # asyncio.create_task(asyncio.to_thread(post_results, eval_url, init_payload))

    # Route to appropriate handler based on round number
    round_num = data.round
    print(f"\n[ROUTER] Received request for Round {round_num}")
    
    if round_num == 1:
        print("[ROUTER] Routing to do_round1()")
        asyncio.create_task(do_round1(jsonable_encoder(data)))
    elif round_num == 2:
        print("[ROUTER] Routing to do_round2()")
        asyncio.create_task(do_round2(jsonable_encoder(data)))
    else:
        print(f"[ROUTER] ⚠️ Unsupported round number: {round_num}, defaulting to Round 1")
        asyncio.create_task(do_round1(jsonable_encoder(data)))

    return ack


def round1(data: TaskRequest):
    files = [
        {
            "path": "index.html",
            "content": f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hello GitHub Page</title>
</head>
<body>
    <h1>Hello GitHub!</h1>
    <p>This is a simple file to get started with your new repository.</p>
</body>
</html>"""
            }]
    # Example usage (not invoked):
    # create_github_repo(f"{data.task}_{getattr(data, 'nonce', '')}")
    # push_files(f"{data.task}_{getattr(data, 'nonce', '')}", files, round=1)
    return {"ok": True, "example": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
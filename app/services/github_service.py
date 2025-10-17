import base64
import time
from typing import List, Dict, Optional

import requests

try:
    # prefer app-level config if present
    from app import config
except Exception:
    # don't import app at module import time (avoids circular imports)
    # we'll import lazily when needed
    config = None


def _get_config():
    """Lazy import of app.config to avoid circular imports at module import time."""
    if config is not None:
        return config
    try:
        import importlib

        return importlib.import_module("app.config")
    except Exception:
        return None


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    import os

    return os.getenv(name, default)


def _owner() -> str:
    # Prefer explicit config, fall back to environment; avoid surprising numeric default
    cfg = _get_config()
    if cfg:
        return getattr(cfg, "GITHUB_USER", _get_env("GITHUB_USER", "your-github-username"))
    return _get_env("GITHUB_USER", "your-github-username")


def _token() -> Optional[str]:
    cfg = _get_config()
    if cfg:
        return getattr(cfg, "GITHUB_TOKEN", None)
    return _get_env("GITHUB_TOKEN")


def _skip_github() -> bool:
    # Accept several truthy values for convenience
    def _to_bool(v: Optional[str]) -> bool:
        if v is None:
            return False
        return str(v).lower() in ("1", "true", "yes", "on")

    cfg = _get_config()
    if cfg:
        val = getattr(cfg, "SKIP_GITHUB", None)
        if isinstance(val, bool):
            return val
        return _to_bool(val)
    return _to_bool(_get_env("SKIP_GITHUB", None))


def create_github_repo(repo_name: str, private: bool = False) -> Dict:
    """Create a GitHub repo (or mock when SKIP_GITHUB=1)."""
    if _skip_github():
        return {"mock": True, "name": repo_name}

    token = _token()
    if not token:
        raise RuntimeError("GITHUB_TOKEN not set")

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    payload = {"name": repo_name, "auto_init": True, "license_template": "mit"}

    # retry with small backoff for transient errors
    for attempt in range(1, 4):
        r = requests.post("https://api.github.com/user/repos", headers=headers, json=payload)
        if r.status_code == 201:
            return r.json()
        if r.status_code == 422:
            # Repo likely already exists; attempt to fetch it
            owner = _owner()
            rr = requests.get(f"https://api.github.com/repos/{owner}/{repo_name}", headers=headers)
            if rr.status_code == 200:
                return rr.json()
            # fall through to final error
        # transient server errors retry
        if r.status_code >= 500 or r.status_code == 429:
            time.sleep(0.5 * attempt)
            continue
        # other client errors are not recoverable
        raise Exception(f"Failed to create repo: {r.status_code}, {r.text}")

    # if we exited retries loop without returning
    raise Exception(f"Failed to create repo after retries: {r.status_code}, {r.text}")


def enable_github_pages(repo_name: str, branch: str = "main") -> Dict:
    if _skip_github():
        owner = _owner()
        return {"mock": True, "pages_url": f"https://{owner}.github.io/{repo_name}/"}

    token = _token()
    if not token:
        raise RuntimeError("GITHUB_TOKEN not set")
    owner = _owner()
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    payload = {"build_type": "legacy", "source": {"branch": branch, "path": "/"}}
    r = requests.post(f"https://api.github.com/repos/{owner}/{repo_name}/pages", headers=headers, json=payload)
    if r.status_code in (201, 202):
        return r.json()
    # If pages endpoint returns 409 or similar, raise with helpful message
    raise Exception(f"Failed to enable pages: {r.status_code}, {r.text}")


def _get_file_sha(owner: str, repo_name: str, path: str, token: str) -> Optional[str]:
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{path}"
    for attempt in range(1, 4):
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return r.json().get("sha")
        if r.status_code == 404:
            return None
        if r.status_code >= 500 or r.status_code == 429:
            time.sleep(0.5 * attempt)
            continue
        raise Exception(f"Failed to get file info: {r.status_code}, {r.text}")
    raise Exception(f"Failed to get file info after retries: {r.status_code}, {r.text}")


def _put_file(owner: str, repo_name: str, path: str, content_b64: str, message: str, token: str, sha: Optional[str] = None, branch: Optional[str] = None) -> Dict:
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    payload = {"message": message, "content": content_b64}
    if sha:
        payload["sha"] = sha
    if branch:
        payload["branch"] = branch

    url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{path}"
    for attempt in range(1, 4):
        r = requests.put(url, headers=headers, json=payload)
        if r.status_code in (200, 201):
            return r.json()
        if r.status_code >= 500 or r.status_code == 429:
            time.sleep(0.5 * attempt)
            continue
        # 409 or 422 may indicate conflict; surface to caller
        raise Exception(f"Failed to put file {path}: {r.status_code}, {r.text}")
    raise Exception(f"Failed to put file {path} after retries: {r.status_code}, {r.text}")


def push_files(
    repo_name: str,
    files: List[Dict],
    commit_message_prefix: Optional[str] = None,
    round: int = 1,
    branch: str = "main",
) -> List[Dict]:
    """Push multiple files to a repo.

    Files must be dicts with keys:
      - path: str
      - content: str
      - encoding: optional, 'utf-8' (default) or 'base64' or 'url'

    Returns a list of simplified result dicts per file: {path, url, sha}.
    """
    owner = _owner()
    token = _token()
    if _skip_github():
        return [{"mock": True, "path": f["path"]} for f in files]
    if not token:
        raise RuntimeError("GITHUB_TOKEN not set")

    results = []
    for f in files:
        path = f["path"]
        enc = f.get("encoding", "utf-8")
        if enc == "base64":
            # Clean base64 content: remove whitespace/newlines that could cause 422 errors
            content_b64 = f["content"]
            if isinstance(content_b64, str):
                content_b64 = ''.join(content_b64.split())  # Remove ALL whitespace
        elif enc == "url":
            # Download the file from HTTP URL and convert to base64
            http_url = f["content"]
            print(f"[GitHub] Downloading remote file: {http_url}")
            try:
                response = requests.get(http_url, timeout=30)
                response.raise_for_status()
                content_b64 = base64.b64encode(response.content).decode("ascii")
                print(f"[GitHub] Downloaded {len(response.content)} bytes for {path}")
            except Exception as e:
                print(f"[GitHub] Failed to download {http_url}: {e}")
                raise ValueError(f"Failed to download remote file {http_url}: {e}")
        else:
            # treat as text
            content_b64 = base64.b64encode(f["content"].encode("utf-8")).decode("ascii")

        message = f"{commit_message_prefix + ': ' if commit_message_prefix else ''}Round {round} - Add/Update {path}"

        sha = _get_file_sha(owner, repo_name, path, token)
        api_res = _put_file(owner, repo_name, path, content_b64, message, token, sha=sha, branch=branch)
        # Normalize response into small dict
        file_info = {
            "path": path,
            "url": api_res.get("content", {}).get("html_url") if isinstance(api_res, dict) else None,
            "sha": api_res.get("content", {}).get("sha") if isinstance(api_res, dict) else None,
            "api_response": api_res,
        }
        results.append(file_info)

    return results


def get_sha_of_latest_commit(repo_name: str, branch: str = "main") -> str:
    owner = _owner()
    token = _token()
    if _skip_github():
        return "mock-sha"
    if not token:
        raise RuntimeError("GITHUB_TOKEN not set")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    r = requests.get(f"https://api.github.com/repos/{owner}/{repo_name}/branches/{branch}", headers=headers)
    if r.status_code != 200:
        raise Exception(f"Failed to get branch info: {r.status_code}, {r.text}")
    return r.json()["commit"]["sha"]


def wait_for_pages_deployment(pages_url: str, timeout: int = 300, check_interval: int = 10, expected_content: str = None) -> bool:
    """
    Wait for GitHub Pages to be deployed and accessible with new content.
    
    Args:
        pages_url: The GitHub Pages URL to check (e.g., https://user.github.io/repo/)
        timeout: Maximum time to wait in seconds (default: 5 minutes)
        check_interval: Time between checks in seconds (default: 10 seconds)
        expected_content: Optional string to check for in response (for Round 2 verification)
    
    Returns:
        True if page is accessible with new content, False if timeout reached
    """
    if _skip_github():
        print("[GitHub] SKIP_GITHUB=1, skipping pages deployment wait")
        return True
    
    print(f"[GitHub] Waiting for GitHub Pages to deploy: {pages_url}")
    if expected_content:
        print(f"[GitHub] Will verify new content contains: '{expected_content[:50]}...'")
    
    start_time = time.time()
    attempts = 0
    last_content_hash = None
    
    while time.time() - start_time < timeout:
        attempts += 1
        elapsed = int(time.time() - start_time)
        
        try:
            # Check if the page is accessible with cache busting
            cache_buster = int(time.time() * 1000)  # Millisecond timestamp
            url_with_cache_bust = f"{pages_url}?_={cache_buster}"
            
            response = requests.get(
                url_with_cache_bust, 
                timeout=10, 
                allow_redirects=True,
                headers={
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            )
            
            if response.status_code == 200:
                content = response.text
                content_hash = hash(content)
                
                # Check if content has changed from previous attempt
                if last_content_hash and content_hash != last_content_hash:
                    print(f"[GitHub] 🔄 Detected content change at {elapsed}s")
                
                last_content_hash = content_hash
                
                # If we have expected content, verify it's present
                if expected_content:
                    if expected_content in content:
                        print(f"[GitHub] ✅ Pages deployed with new content after {elapsed}s ({attempts} attempts)")
                        return True
                    else:
                        print(f"[GitHub] ⏳ Page accessible but old content still cached ({elapsed}s, attempt {attempts})...")
                else:
                    # No expected content check, just verify 200 response
                    print(f"[GitHub] ✅ Pages deployed successfully after {elapsed}s ({attempts} attempts)")
                    return True
                    
            elif response.status_code == 404:
                print(f"[GitHub] ⏳ Pages not ready yet ({elapsed}s elapsed, attempt {attempts})...")
            else:
                print(f"[GitHub] ⚠️ Unexpected status {response.status_code} ({elapsed}s elapsed)")
        
        except requests.exceptions.RequestException as e:
            print(f"[GitHub] ⏳ Connection error ({elapsed}s elapsed): {e}")
        
        # Wait before next check
        time.sleep(check_interval)
    
    print(f"[GitHub] ⏰ Timeout reached after {timeout}s, pages may still be deploying")
    return False

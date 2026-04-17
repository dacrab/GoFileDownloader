import os
import sys
from hashlib import sha256
from pathlib import Path
from time import time
from urllib.parse import urlencode

import httpx

from .config import GOFILE_API, GOFILE_API_ACCOUNTS

TOKEN_CACHE = Path.home() / ".cache" / "gofile_token"


def get_content_id(url: str) -> str | None:
    try:
        if url.rstrip("/").split("/")[-2] != "d":
            return None
        return url.rstrip("/").split("/")[-1]
    except IndexError:
        return None


def generate_content_url(content_id: str, password: str | None = None) -> str:
    base_url = f"{GOFILE_API}/contents/{content_id}?cache=true&sortField=createTime&sortDirection=1"
    return f"{base_url}&{urlencode({'password': password})}" if password else base_url


def generate_website_token(account_token: str) -> str:
    time_window = str(int(time()) // 14400)
    token_seed = f"Mozilla/5.0::en-US::{account_token}::{time_window}::5d4f7g8sd45fsd"
    return sha256(token_seed.encode()).hexdigest()


def get_account_token() -> str:
    # Check environment variable first
    if env_token := os.getenv("GOFILE_TOKEN"):
        return env_token

    # Try cached token first
    if TOKEN_CACHE.exists():
        cached = TOKEN_CACHE.read_text().strip()
        if cached:
            return cached

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Encoding": "gzip",
        "Accept": "*/*",
        "Connection": "keep-alive",
    }
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(GOFILE_API_ACCOUNTS, headers=headers)
            account_response = response.json()

        if account_response["status"] == "error-rateLimit":
            print("Error: GoFile API rate limit reached. Try again later.")
            sys.exit(1)

        if account_response["status"] != "ok":
            print(
                f"Error: Failed to create account - {account_response.get('status', 'unknown')}"
            )
            sys.exit(1)

        token = str(account_response["data"]["token"])

        # Cache the token
        TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_CACHE.write_text(token)

        return token
    except (httpx.TimeoutException, httpx.RequestError) as e:
        print(f"Error: Network request failed - {e}")
        sys.exit(1)

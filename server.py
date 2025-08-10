import asyncio
import datetime
import os
from typing import Annotated

import httpx
from dateutil import parser
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp import ErrorData, McpError
from mcp.server.auth.provider import AccessToken
from mcp.types import INTERNAL_ERROR, INVALID_PARAMS
from pydantic import BaseModel, Field
from urllib.parse import urlparse

# --- Load environment variables ---
load_dotenv()

TOKEN = os.environ.get("AUTH_TOKEN")
MY_NUMBER = os.environ.get("MY_NUMBER")

assert TOKEN is not None, "Please set AUTH_TOKEN in your .env file"
assert MY_NUMBER is not None, "Please set MY_NUMBER in your .env file"

# --- Auth Provider ---
class SimpleBearerAuthProvider(BearerAuthProvider):
    """A simple bearer token authentication provider."""
    def __init__(self, token: str):
        k = RSAKeyPair.generate()
        super().__init__(public_key=k.public_key, jwks_uri=None, issuer=None, audience=None)
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(token=token, client_id="puch-client", scopes=["*"], expires_at=None)
        return None

# --- Data Models for Tool Outputs ---
class GitHubProfileData(BaseModel):
    # ... (same as before)
    username: str; name: str | None; bio: str | None; followers: int; following: int; public_repos: int; total_stars: int; fork_count: int; account_age_days: int; last_activity_days: int; top_languages: list[str]; twitter_username: str | None; ai_instruction: str

# --- NEW: Create a Pydantic model for LeetCode data ---
class LeetCodeProfileData(BaseModel):
    """Structured data for a LeetCode user's profile."""
    username: str
    ranking: int
    reputation: int
    total_problems_solved: int
    easy_solved: int
    medium_solved: int
    hard_solved: int
    acceptance_rate: float
    ai_instruction: str

# --- MCP Server Setup (Updated Name) ---
mcp = FastMCP(
    "Developer Profile Roaster MCP",
    auth=SimpleBearerAuthProvider(TOKEN),
)

# --- Mandatory Validate Tool ---
@mcp.tool
async def validate() -> str:
    return MY_NUMBER

# --- Helper function for GitHub ---
def _extract_username(username_or_url: str) -> str | None:
    # ... (same as before)
    cleaned_input = username_or_url.strip();
    if "github.com" in cleaned_input:
        try: path = urlparse(cleaned_input).path; parts = path.strip('/').split('/'); return parts[0] if parts and parts[0] else None
        except Exception: return None
    return cleaned_input

# --- TOOL 1: GitHub Profile Data (Unchanged) ---
@mcp.tool
async def get_github_profile_data(username_or_url: Annotated[str, Field(description="The GitHub username or full profile URL.")]) -> GitHubProfileData:
    # ... (This entire function is the same as the previous version)
    username = _extract_username(username_or_url)
    if not username: raise McpError(ErrorData(code=INVALID_PARAMS, message="Invalid username or URL."))
    async with httpx.AsyncClient() as client:
        headers = {"User-Agent": "Puch-MCP-DataFetcher/1.0", "Accept": "application/vnd.github.v3+json"}
        try:
            profile_task = client.get(f"https://api.github.com/users/{username}", headers=headers, timeout=10)
            repos_task = client.get(f"https://api.github.com/users/{username}/repos?per_page=100", headers=headers, timeout=10)
            responses = await asyncio.gather(profile_task, repos_task, return_exceptions=True)
            profile_response, repos_response = responses
            if isinstance(profile_response, Exception): raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch profile: {profile_response!r}"))
            if profile_response.status_code == 404: raise McpError(ErrorData(code=INVALID_PARAMS, message=f"User '{username}' not found on GitHub."))
            if profile_response.status_code != 200: raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"GitHub API returned {profile_response.status_code} for profile."))
            profile = profile_response.json()
            repos = []
            if isinstance(repos_response, httpx.Response) and repos_response.status_code == 200: repos = repos_response.json()
            public_repos = profile.get('public_repos', 0); followers = profile.get('followers', 0); twitter_username = profile.get('twitter_username')
            total_stars = sum(repo.get('stargazers_count', 0) for repo in repos); fork_count = sum(1 for repo in repos if repo.get('fork', False))
            lang_counts = {};
            for repo in repos:
                lang = repo.get('language')
                if lang and lang != "null": lang_counts[lang] = lang_counts.get(lang, 0) + 1
            top_languages = sorted(lang_counts, key=lang_counts.get, reverse=True)[:3]
            created_date = parser.parse(profile.get('created_at', '')); account_age_days = (datetime.datetime.now(datetime.timezone.utc) - created_date).days
            updated_date = parser.parse(profile.get('updated_at', '')); last_activity_days = (datetime.datetime.now(datetime.timezone.utc) - updated_date).days
            github_stats_summary = (f"The GitHub user '{username}' has {public_repos} public repos with a total of {total_stars} stars, and {followers} followers. Their account is {account_age_days} days old.")
            twitter_instruction = ""
            if twitter_username: twitter_instruction = f"They also have a Twitter (X) account: @{twitter_username}. Make sure to roast them for probably posting cringe tech takes or having zero engagement there."
            else: twitter_instruction = "They did not list a Twitter (X) account, so roast them for being out of the loop or afraid of public scrutiny."
            instruction = (f"{github_stats_summary} {twitter_instruction} Based on all this data, perform the following two tasks. Part 1: Write a long, detailed, and brutal roast that combines both their GitHub and Twitter persona. Part 2: After the roast, provide a separate section titled 'Actionable Tips' with 3 concrete pieces of advice for improving their overall online developer presence.")
            return GitHubProfileData(username=profile.get('login'), name=profile.get('name'), bio=profile.get('bio'), followers=followers, following=profile.get('following', 0), public_repos=public_repos, total_stars=total_stars, fork_count=fork_count, account_age_days=account_age_days, last_activity_days=last_activity_days, top_languages=top_languages, twitter_username=twitter_username, ai_instruction=instruction)
        except httpx.HTTPError as e: raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"API connection failed: {e!r}"))

# --- NEW TOOL 2: LeetCode Profile Data ---
@mcp.tool
async def get_leetcode_profile_data(username: Annotated[str, Field(description="The LeetCode username.")]) -> LeetCodeProfileData:
    """
    Fetches problem-solving stats for a given LeetCode user and includes
    a hardcoded instruction for the AI to roast them.
    """
    api_url = "https://leetcode.com/graphql"
    graphql_query = """
    query getUserProfile($username: String!) {
        matchedUser(username: $username) {
            username
            profile {
                ranking
                reputation
            }
            submitStats: submitStatsGlobal {
                acSubmissionNum {
                    difficulty
                    count
                    submissions
                }
            }
        }
    }
    """
    variables = {"username": username}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(api_url, json={'query': graphql_query, 'variables': variables}, timeout=10)
            response.raise_for_status()
            
            data = response.json().get("data", {}).get("matchedUser")
            if not data:
                raise McpError(ErrorData(code=INVALID_PARAMS, message=f"User '{username}' not found on LeetCode."))

            # Process the stats
            profile_stats = data.get("profile", {})
            submit_stats = data.get("submitStats", {}).get("acSubmissionNum", [])
            
            solved_all = next((s for s in submit_stats if s['difficulty'] == 'All'), {})
            easy_solved = next((s for s in submit_stats if s['difficulty'] == 'Easy'), {})
            medium_solved = next((s for s in submit_stats if s['difficulty'] == 'Medium'), {})
            hard_solved = next((s for s in submit_stats if s['difficulty'] == 'Hard'), {})
            
            total_solved = solved_all.get('count', 0)
            total_submissions = solved_all.get('submissions', 0)
            acceptance_rate = round((total_solved / total_submissions) * 100, 2) if total_submissions > 0 else 0

            # Create the hardcoded instruction for the AI
            instruction = (
                f"The LeetCode user '{username}' has a ranking of {profile_stats.get('ranking', 'N/A')} "
                f"and has solved a total of {total_solved} problems ({easy_solved.get('count', 0)} Easy, "
                f"{medium_solved.get('count', 0)} Medium, {hard_solved.get('count', 0)} Hard). "
                f"Their overall acceptance rate is a pitiful {acceptance_rate}%. "
                "Based on these stats, perform two tasks. "
                "Part 1: Write a savage roast about their problem-solving skills, focusing on their acceptance rate and difficulty distribution. "
                "Part 2: After the roast, give them a section called 'Grind Plan' with 3 actionable tips on how to actually get good at DSA."
            )
            
            return LeetCodeProfileData(
                username=data.get("username"),
                ranking=profile_stats.get("ranking", 0),
                reputation=profile_stats.get("reputation", 0),
                total_problems_solved=total_solved,
                easy_solved=easy_solved.get('count', 0),
                medium_solved=medium_solved.get('count', 0),
                hard_solved=hard_solved.get('count', 0),
                acceptance_rate=acceptance_rate,
                ai_instruction=instruction,
            )
        except httpx.HTTPStatusError as e:
             raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"LeetCode API returned an error: {e.response.status_code}"))
        except httpx.HTTPError as e:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Connection to LeetCode API failed: {e!r}"))

# --- Run MCP Server ---
async def main():
    """Starts the MCP server."""
    print("🚀 Starting Developer Profile Roaster MCP server on http://0.0.0.0:8086")
    await mcp.run_async("streamable-http", host="0.0.0.0", port=8086)

if __name__ == "__main__":
    asyncio.run(main())
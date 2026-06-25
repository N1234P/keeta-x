import requests 
from setup import openai_client
from setup import x_client 
from setup import github_api_key
import os


def fetch_response(endpoint, headers=None):
    headers = {
        "Accept": "application/vnd.github+json",
    }

    if github_api_key:
        headers["Authorization"] = f"Bearer {github_api_key}"
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {endpoint}: {e}")
        return None

def get_github_repos(org="KeetaNetwork"):
    endpoint = f"https://api.github.com/orgs/{org}/repos?per_page=100&type=public&sort=updated"
    data = fetch_response(endpoint)
    recent_repos = []
    for repo in data:
        if len(recent_repos) >= 5:
            break

        recent_repos.append({
            "name": repo["name"],
            "url": repo["html_url"],
            "updated_at": repo["updated_at"]
        })
    return recent_repos
       
    
def get_pull_requests(repo, org="KeetaNetwork"):
    endpoint = (
        f"https://api.github.com/repos/{org}/{repo}/pulls"
        f"?state=all&per_page=10&sort=updated&direction=desc"
    )

    data = fetch_response(endpoint)
    if not data:
        return [] 

    pull_requests = []

    for pr in data:
        pull_requests.append({
            "id": pr["id"],
            "number": pr["number"],
            "title": pr["title"],
            "state": pr["state"],
            "url": pr["html_url"],
            "created_at": pr["created_at"],
            "updated_at": pr["updated_at"],
            "closed_at": pr.get("closed_at"),
            "merged_at": pr.get("merged_at"),
            "user": pr.get("user", {}).get("login", "unknown"),
            "head_branch": pr.get("head", {}).get("ref", "unknown"),
            "base_branch": pr.get("base", {}).get("ref", "unknown"),
            "body": pr.get("body") or "",
        })

    return pull_requests

def get_releases(repo, org="KeetaNetwork"):
    endpoint = (
        f"https://api.github.com/repos/{org}/{repo}/releases"
        f"?per_page=10&sort=created&direction=desc"
    )

   
    data = fetch_response(endpoint)
    if not data:
        return []
    
    releases = []

    for release in data:
        releases.append({
            "id": release["id"],
            "name": release["name"],
            "tag_name": release["tag_name"],
            "url": release["html_url"],
            "created_at": release["created_at"],
            "updated_at": release["updated_at"],
            "body": release.get("body") or "",
        })

    return releases


def get_ai_summary(prompt):
    try:
        response = openai_client.responses.create(
            model="gpt-5.4",
            tools=[{"type": "web_search"}],
            tool_choice="required",
            input=prompt,
            max_output_tokens=800,
            temperature=0.2,
        )

        return response.output_text.strip()

    except Exception as e:
        print(f"Error getting AI summary: {e}")
        return "This appears to be a technical/internal update."


def get_latest_swaps(pair):
    try:
        url = f"https://api.geckoterminal.com/api/v2/networks/base/pools/{pair}/trades"
        data = requests.get(url).json()
    except:
        return {} 

    trades = {}

    data = data["data"]
    for trade in data:
        if trade["type"] != "trade":
            continue

        attr = trade["attributes"]
        tx_hash = attr["tx_hash"]
        action = attr["kind"]
        address = attr["tx_from_address"]
        usd = attr["volume_in_usd"]
        timestamp = attr["block_timestamp"]

        if action == "sell":
            tokens = attr["from_token_amount"]
        else:
            tokens = attr["to_token_amount"]

        trades[tx_hash] = [action, address, usd, tokens, timestamp]

    return trades

def post_tweet(text):
    try:
        
        response = x_client.create_tweet(text=text)
        print(response)
        print(f"Tweet posted successfully! Tweet ID: {response.data['id']}")
        return response.data["id"]
    except Exception as e:
        print(f"Error posting tweet: {e}")
        return None
    

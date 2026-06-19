import api 
import datetime
import time 
from setup import PAIR 


MINUTES = 15


def run_api():
    previous_pull_requests = set() 
    previous_release_requests = set()
    repos = api.get_github_repos()

    launch_time = datetime.datetime.now(datetime.timezone.utc)
    seen = set()
    while True:
        github_tracking(previous_pull_requests, previous_release_requests, repos)
        whale_tracking(PAIR, seen, launch_time) 
        time.sleep(60) 


def whale_tracking(PAIR, seen, launch_time):
    trades = api.get_latest_swaps(PAIR)

    for tx_hash, (action, address, usd, tokens,
                    timestamp) in trades.items():
        usd, tokens = int(float(usd)), int(float(tokens))
        tx_url = f"basescan.org/tx/{tx_hash}"

        block_time = datetime.datetime.strptime(
            timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)

        if tx_hash in seen or block_time < launch_time or action.lower(
        ) != "buy":
            continue
        
        seen.add(tx_hash)

        if (usd >= 100000 and
            (datetime.datetime.now(datetime.timezone.utc) - block_time).total_seconds() / 60
                <= 5):
            # Format numbers with commas
            tokens_formatted = "{:,}".format(tokens)
            usd_formatted = "$" + "{:,}".format(usd)

            print(f"Reporting twitter whale trade {tx_hash}")

            message = f"🐋🐋🐋🐋🐋🐋🐋🐋 {tokens_formatted} $KTA ({usd_formatted}) bought on #Aerodrome (0xd9eD...) Liquidity Pool \n\n {tx_url}"

            api.post_tweet(message)
            time.sleep(5)

    

def github_tracking(previous_pull_requests, previous_release_requests, repos):
    now = datetime.datetime.now(datetime.timezone.utc)
    for repo in repos:
        pull_requests = api.get_pull_requests(repo["name"])
        
        for pr in pull_requests:
            pr_updated_time = datetime.datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
            elapsed_pr = now - pr_updated_time
            if pr['url'] not in previous_pull_requests:
                print(f"Found new PR: {pr['url']} ({elapsed_pr.total_seconds() / 60:.1f} minutes old)")
            if pr['url'] not in previous_pull_requests and elapsed_pr.total_seconds() <= MINUTES * 60:
                print(pr['url']) 
                previous_pull_requests.add(pr['url'])
                summary = api.get_ai_summary(build_ai_prompt("pull_request", pr))
                message = format_pr_message(repo["name"], pr, summary)
                print(message)
                api.post_tweet(message) 
               
                
        releases = api.get_releases(repo["name"])
        
        for release in releases:
            release_updated_time = datetime.datetime.strptime(release["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
            elapsed_release = now - release_updated_time
            if release['url'] not in previous_release_requests and elapsed_release.total_seconds() <= MINUTES * 60:
                previous_release_requests.add(release['url'])
                summary = api.get_ai_summary(build_ai_prompt("release", release))
                message = format_release_message(repo["name"], release, summary)
                api.post_tweet(message) 
                print(message) 


def format_pr_message(repo_name, pr, summary=None):
    title = pr.get("title", "Untitled PR")
    number = pr.get("number", "?")
    user = pr.get("user", "unknown")
    head_branch = pr.get("head_branch", "unknown")
    base_branch = pr.get("base_branch", "unknown")

    summary_text = f"\n\n🧠 Overview:\n{summary}" if summary else ""

    message = (
        f"🐆 Keeta GitHub PR Opened\n\n"
        f"📦 Repo: {repo_name}\n"
        f"🔀 PR #{number}: {title}\n"
        f"🌿 Branch: {head_branch} → {base_branch}\n"
        f"👤 Opened by: @{user}"
        f"{summary_text}"
    )

    return message.strip()

def format_release_message(repo_name, release, summary=None):
    name = release.get("name", "Untitled Release")
    tag_name = release.get("tag_name", "")
    url = release.get("url", "")
    prerelease = release.get("prerelease", False)

    release_type = "Prerelease" if prerelease else "Release"
    summary_text = f"\n\n🧠 Overview:\n{summary}" if summary else ""

    message = (
        f"🐆 Keeta GitHub {release_type}\n\n"
        f"📦 Repo: {repo_name}\n"
        f"🏷️ Version: {tag_name}\n"
        f"🚀 {name}"
        f"{summary_text}\n\n"
        f"{url}"
    )

    return message.strip()

def build_ai_prompt(event_type, item):
    if event_type == "pull_request":
        title = item.get("title", "")
        number = item.get("number", "")
        user = item.get("user", "unknown")
        head_branch = item.get("head_branch", "unknown")
        base_branch = item.get("base_branch", "unknown")
        body = item.get("body", "")
        url = item.get("url", "")

        return f"""
Summarize this GitHub pull request for a Twitter/X bot that tracks Keeta Network development.

PR #{number}
Title: {title}
Opened by: {user}
Branch: {head_branch} → {base_branch}
Description:
{body}

URL: {url}

Write for Keeta followers who may not be technical.

Format:
1. Start with one plain-English sentence explaining what happened and why it matters. Do not mention the author.
2. Add one short paragraph with 1-2 simple sentences of context.
3. Add 1-2 bullet points only if useful cases can be inferred.

Rules:
- Keep it short and easy to scan.
- Avoid jargon; explain technical terms briefly if used.
- No file-name lists.
- Do not hype.
- Do not invent details.
- If unclear, say: "This appears to be a technical/internal update with limited public details."
- NO LINKS
"""

    elif event_type == "release":
        name = item.get("name", "")
        tag_name = item.get("tag_name", "")
        body = item.get("body", "")
        prerelease = item.get("prerelease", False)
        url = item.get("url", "")

        release_type = "prerelease" if prerelease else "release"

        return f"""
Summarize this GitHub {release_type} for a Twitter/X bot that tracks Keeta Network development.

Release name: {name}
Tag: {tag_name}
Release notes:
{body}

URL: {url}

Write for Keeta followers who may not be technical.

Format:
1. Start with one plain-English sentence explaining what happened and why it matters. Do not mention the author.
2. Add one short paragraph with 1-2 simple sentences of context.
3. Add 1-2 bullet points only if useful cases can be inferred.

Rules:
- Keep it short and easy to scan.
- Avoid jargon; explain technical terms briefly if used.
- No file-name lists.
- Do not hype.
- Do not invent details.
- If unclear, say: "This appears to be a technical/internal update with limited public details."
- NO LINKS
"""

    else:
        return """
Say "This appears to be an update with limited public details."
"""

if __name__ == "__main__": 
    print("Running the github tracking app...")
    run_api() 
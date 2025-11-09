import os
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

def search_issues(jql: str):
    """Search Jira issues using JQL query."""
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    headers = {"Accept": "application/json"}
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)

    params = {"jql": jql, "maxResults": 50}
    response = requests.get(url, headers=headers, params=params, auth=auth)

    if response.status_code != 200:
        raise Exception(f"Jira API error {response.status_code}: {response.text}")

    data = response.json()
    return [
        {
            "key": issue["key"],
            "summary": issue["fields"]["summary"],
            "status": issue["fields"]["status"]["name"],
            "assignee": issue["fields"]["assignee"]["displayName"] if issue["fields"]["assignee"] else None,
            "priority": issue["fields"]["priority"]["name"] if issue["fields"]["priority"] else None,
            "updated": issue["fields"]["updated"],
        }
        for issue in data.get("issues", [])
    ]

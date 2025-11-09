import os
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import json

load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)

def get_all_issues():
    headers = {
        "Accept": "application/json",
    }
    url = f"{JIRA_BASE_URL}/rest/agile/1.0/sprint/1/issue?fields=summary,description,priority"
    response = requests.request(
        "GET",
        url,
        headers=headers,
        auth = auth
        )
    return response.json()

def get_issue(issue_key):
    headers = {
        "Accept": "application/json",
    }
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}?fields=summary,description,priority"
    response = requests.request(
        "GET",
        url,
        headers=headers,
        auth = auth
        )
    return response.json()

#Takes in the issue key and the transition name (e.g., "In Progress", "Done")
# performs the transition and returns the result

def transition_issue(issue_key: str, transition_name: str):
    """
    Transitions a Jira issue to a new workflow status by name.

    Args:
        issue_key (str): The Jira issue key, e.g., "DWOS-1".
        transition_name (str): The human-readable transition name, e.g., "In Progress" or "Done".
    """

    # Step 1. Get all available transitions for this issue
    transitions_url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    response = requests.get(transitions_url, headers=headers, auth=auth)
    if response.status_code != 200:
        print(f"Failed to get transitions: {response.status_code} - {response.text}")
        return None

    transitions = response.json().get("transitions", [])
    if not transitions:
        print(f"No transitions available for issue {issue_key}")
        return None

    # Step 2. Find the transition ID by matching its name
    transition_id = None
    for t in transitions:
        if t["name"].lower() == transition_name.lower():
            transition_id = t["id"]
            break

    if not transition_id:
        print(f"Transition '{transition_name}' not found for issue {issue_key}.")
        print("Available transitions:")
        for t in transitions:
            print(f" - {t['name']}")
        return None

    # Step 3. Execute the transition using the transition ID
    payload = json.dumps({
        "transition": { "id": transition_id },
        "update": {
            "comment": [
                {"add": {"body": f"Issue automatically moved to '{transition_name}' by the Dynamic Work Order system."}}
            ]
        }
    })
    r2 = requests.post(transitions_url, headers=headers, auth=auth, data=json.dumps(payload))
    if r2.status_code == 204:
        return {"ok": True, "moved_to": choice.get("to", {}).get("name", choice["id"])}
    else:
        return {"ok": False, "status": r2.status_code, "error": r2.text}
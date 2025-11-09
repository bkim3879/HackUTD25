import json
import os

import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)

DEFAULT_FIELDS = "summary,description,priority,status,assignee,updated"
DEFAULT_JQL = os.getenv("JIRA_DEFAULT_JQL", 'project = "DWOS" ORDER BY priority DESC')


def _request(method: str, url: str, **kwargs):
    response = requests.request(method, url, auth=auth, **kwargs)
    response.raise_for_status()
    return response


def get_all_issues(max_results: int = 100):
    """Retrieve Jira issues using the supported /rest/api/3/search endpoint."""
    headers = {"Accept": "application/json"}
    payload = {
        "jql": DEFAULT_JQL,
        "maxResults": max_results,
        "fields": DEFAULT_FIELDS,
    }
    url = f"{JIRA_BASE_URL}/rest/api/3/search/jql"
    response = _request("POST", url, headers=headers, json=payload)
    return response.json()


def get_issue(issue_key: str):
    headers = {"Accept": "application/json"}
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
    params = {"fields": DEFAULT_FIELDS}
    response = _request("GET", url, headers=headers, params=params)
    return response.json()


TRANSITION_NAME_TO_ID = {
    "to do": "11",
    "todo": "11",
    "in progress": "21",
    "in-progress": "21",
    "done": "31",
}


def transition_issue(issue_key: str, transition_name: str):
    """
    Transition a Jira issue to a new workflow status by matching the transition name.
    """

    transitions_url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    # Prefer direct POST by id as requested; map common names to ids.
    tid = transition_name.strip()
    if not tid.isdigit():
        tid = TRANSITION_NAME_TO_ID.get(tid.lower(), "")

    if tid.isdigit():
        # Minimal body resembling {"transition": {"id": 31}}
        payload = {"transition": {"id": tid}}
        r2 = _request("POST", transitions_url, headers=headers, json=payload)
        if r2.status_code in (200, 204):
            return {"ok": True, "moved_to_id": tid}
        return {"ok": False, "status": r2.status_code, "error": r2.text}

    # Fallback: discover available transitions and match by name
    response = _request("GET", transitions_url, headers=headers)
    transitions = response.json().get("transitions", [])
    if not transitions:
        raise RuntimeError(f"No transitions available for issue {issue_key}")
    transition_name_lower = transition_name.lower()
    target_transition = next(
        (t for t in transitions if t.get("name", "").lower() == transition_name_lower),
        None,
    )
    if not target_transition:
        available = ", ".join(t["name"] for t in transitions)
        raise RuntimeError(f"Transition '{transition_name}' not found. Available: {available}")
    payload = {"transition": {"id": target_transition["id"]}}
    r2 = _request("POST", transitions_url, headers=headers, json=payload)
    if r2.status_code in (200, 204):
        return {"ok": True, "moved_to": target_transition.get("to", {}).get("name", transition_name)}
    return {"ok": False, "status": r2.status_code, "error": r2.text}

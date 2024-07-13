import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging

load_dotenv()

jira_url = os.getenv("JIRA_URL")
api_username = os.getenv("API_USERNAME")
api_token = os.getenv("API_TOKEN")
project_key = os.getenv("PROJECT_KEY")

auth = HTTPBasicAuth(api_username, api_token)
headers = {
    "Content-Type": "application/json"
}

log_filename = 'script.log'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler(log_filename),
    logging.StreamHandler()
])

#yesterday = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
yesterday = datetime.now().strftime("%d.%m.%Y")

def get_issues_to_delete(issue_type):
    jql = f'project = {project_key} AND issuetype = "{issue_type}" AND summary ~ "\\"{yesterday}\\"" AND status = "To Do"'
    search_url = f"{jira_url}/rest/api/3/search"
    response = requests.get(search_url, headers=headers, auth=auth, params={'jql': jql, 'fields': 'key'})
    issues = response.json().get('issues', [])
    logging.info(f"Found {len(issues)} {issue_type}s to delete with summary containing '{yesterday}' and status 'To Do'")
    return [issue['key'] for issue in issues]

def delete_issue(issue_key):
    url = f"{jira_url}/rest/api/3/issue/{issue_key}"
    response = requests.delete(url, headers=headers, auth=auth)
    if response.status_code == 204:
        logging.info(f"Successfully deleted issue {issue_key}")
    else:
        logging.error(f"Failed to delete issue {issue_key}: {response.status_code} - {response.text}")

def check_if_subtasks_exist(task_key):
    jql = f'parent = {task_key}'
    search_url = f"{jira_url}/rest/api/3/search"
    response = requests.get(search_url, headers=headers, auth=auth, params={'jql': jql, 'fields': 'key'})
    issues = response.json().get('issues', [])
    return len(issues) > 0

def main():
    subtask_keys = get_issues_to_delete("Subtask")
    for subtask_key in subtask_keys:
        delete_issue(subtask_key)

    task_keys = get_issues_to_delete("Task")
    for task_key in task_keys:
        if not check_if_subtasks_exist(task_key):
            delete_issue(task_key)
        else:
            logging.info(f"Task {task_key} still has subtasks, not deleting.")

if __name__ == "__main__":
    main()  
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging
from googleapiclient.discovery import build

load_dotenv()

jira_url = os.getenv("JIRA_URL")
api_username = os.getenv("API_USERNAME")
api_token = os.getenv("API_TOKEN")
project_key = os.getenv("PROJECT_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
google_spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
google_spreadsheet_name = os.getenv("GOOGLE_SPREADSHEET_NAME")
google_cell = os.getenv("GOOGLE_DELETE_CONDITION_CELL")

auth = HTTPBasicAuth(api_username, api_token)
headers = {
    "Content-Type": "application/json"
}

log_filename = 'script.log'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler(log_filename),
    logging.StreamHandler()
])

yesterday = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")

def get_condition(spreadsheet_id, api_key, range_name=f"{google_spreadsheet_name}!{google_cell}"):
    service = build('sheets', 'v4', developerKey=api_key)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    
    if not values:
        logging.error('No condition found in the spreadsheet.')
        return None
    else:
        return values[0][0]

def get_issues_to_delete(issue_type, condition):
    jql = f'project = {project_key} AND issuetype = "{issue_type}" AND summary ~ "{yesterday}" AND {condition}'
    search_url = f"{jira_url}/rest/api/3/search"
    response = requests.get(search_url, headers=headers, auth=auth, params={'jql': jql, 'fields': 'key'})
    issues = response.json().get('issues', [])
    logging.info(f"Found {len(issues)} {issue_type}s to delete with summary containing '{yesterday}' and condition '{condition}'")
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
    condition = get_condition(google_spreadsheet_id, google_api_key)
    if not condition:
        logging.error("No condition found. Exiting script.")
        return

    subtask_keys = get_issues_to_delete("Subtask", condition)
    for subtask_key in subtask_keys:
        delete_issue(subtask_key)

    task_keys = get_issues_to_delete("Task", condition)
    for task_key in task_keys:
        if not check_if_subtasks_exist(task_key):
            delete_issue(task_key)
        else:
            logging.info(f"Task {task_key} still has subtasks, not deleting.")

if __name__ == "__main__":
    main()

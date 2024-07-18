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
google_api_key = os.getenv("GOOGLE_API_KEY")
google_spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
google_spreadsheet_name = os.getenv("GOOGLE_SPREADSHEET_NAME")
google_cell = os.getenv("GOOGLE_DELETE_CONDITION_CELL")
days = os.getenv("DAYS_AGO_TO_DELETE")

auth = HTTPBasicAuth(api_username, api_token)
headers = {
    "Content-Type": "application/json"
}

log_filename = 'script.log'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler(log_filename),
    logging.StreamHandler()
])

days_ago = (datetime.now() - timedelta(days=int(days))).strftime("%m.%d.%Y")

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

def get_spreadsheet_data(spreadsheet_id, api_key, range_name=google_spreadsheet_name):
    service = build('sheets', 'v4', developerKey=api_key)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    return result.get('values', [])

def parse_spreadsheet_data(data):
    projects = set()
    for row in data[1:]:
        projects.update(row[1].split(', '))
    return projects

def get_epic_key(project_code):
    epic_summary = f"PM {project_code}"
    jql = f'project = "{project_code}" AND summary ~ "PM {project_code}" AND issuetype = "Epic"'
    logging.info(f"JQL for epic: {jql}")
    search_url = f"{jira_url}/rest/api/3/search"
    response = requests.get(search_url, headers=headers, auth=auth, params={'jql': jql})
    issues = response.json().get('issues', [])
    logging.info(f"Epics found: {issues}")
    return issues[0]['key'] if issues else None

def get_task_keys(epic_key):
    jql = f'parent = {epic_key} AND issuetype = "Task"'
    logging.info(f"JQL for tasks: {jql}")
    search_url = f"{jira_url}/rest/api/3/search"
    response = requests.get(search_url, headers=headers, auth=auth, params={'jql': jql, 'fields': 'key'})
    issues = response.json().get('issues', [])
    return [issue['key'] for issue in issues]

def get_subtask_keys(task_key, date_str, condition):
    jql = f'parent = {task_key} AND issuetype = "Subtask" AND summary ~ "{date_str}" AND {condition}'
    logging.info(f"JQL for subtasks: {jql}")
    search_url = f"{jira_url}/rest/api/3/search"
    response = requests.get(search_url, headers=headers, auth=auth, params={'jql': jql, 'fields': 'key'})
    issues = response.json().get('issues', [])
    return [issue['key'] for issue in issues]

def delete_issue(issue_key):
    url = f"{jira_url}/rest/api/3/issue/{issue_key}"
    response = requests.delete(url, headers=headers, auth=auth)
    if response.status_code == 204:
        logging.info(f"Successfully deleted issue {issue_key}")
    else:
        logging.error(f"Failed to delete issue {issue_key}: {response.status_code} - {response.text}")

def check_if_subtasks_exist(task_key):
    jql = f'parent = {task_key} AND issuetype = "Subtask"'
    search_url = f"{jira_url}/rest/api/3/search"
    response = requests.get(search_url, headers=headers, auth=auth, params={'jql': jql, 'fields': 'key'})
    issues = response.json().get('issues', [])
    return len(issues) > 0

def main():
    condition = get_condition(google_spreadsheet_id, google_api_key)
    if not condition:
        logging.error("No condition found. Exiting script.")
        return

    data = get_spreadsheet_data(google_spreadsheet_id, google_api_key)
    projects = parse_spreadsheet_data(data)

    for project_code in projects:
        logging.info(f"Processing project: {project_code}")
        epic_key = get_epic_key(project_code)
        if not epic_key:
            logging.info(f"No Epic found for project {project_code}")
            continue

        task_keys = get_task_keys(epic_key)
        for task_key in task_keys:
            subtask_keys = get_subtask_keys(task_key, days_ago, condition)
            for subtask_key in subtask_keys:
                delete_issue(subtask_key)

            if not check_if_subtasks_exist(task_key):
                delete_issue(task_key)
            else:
                logging.info(f"Task {task_key} still has subtasks, not deleting.")

if __name__ == "__main__":
    main()

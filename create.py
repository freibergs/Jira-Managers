import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import json
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

auth = HTTPBasicAuth(api_username, api_token)
headers = {
    "Content-Type": "application/json"
}

log_filename = 'script.log'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler(log_filename),
    logging.StreamHandler()
])

today = datetime.now().strftime("%d.%m.%Y")

def get_spreadsheet_data(spreadsheet_id, api_key, range_name="Lapa1"):
    service = build('sheets', 'v4', developerKey=api_key)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    
    if not values:
        print('No data found.')
        return None
    else:
        return values

def parse_spreadsheet_data(data):
    managers_projects = {}
    for row in data:
        email = row[0]
        projects = row[1].split(', ')
        managers_projects[email] = projects
    return managers_projects

def get_user_details(email):
    url = f"{jira_url}/rest/api/3/user/search?query={email}"
    response = requests.get(url, headers=headers, auth=auth)
    user = response.json()[0]
    return user['accountId'], user['displayName']

def issue_exists(summary):
    jql = f'project = {project_key} AND summary ~ "\\"{summary}\\""'
    search_url = f"{jira_url}/rest/api/3/search"
    response = requests.get(search_url, headers=headers, auth=auth, params={'jql': jql})
    issues = response.json().get('issues', [])
    logging.info(f"Checked for existing issues with summary '{summary}': {issues}")
    return len(issues) > 0, issues[0]['key'] if issues else None

def create_issue(issue_type, summary, description, assignee=None, parent_key=None):
    url = f"{jira_url}/rest/api/3/issue"
    fields = {
        "project": {
            "key": project_key
        },
        "summary": summary,
        "description": {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "text": description,
                            "type": "text"
                        }
                    ]
                }
            ]
        },
        "issuetype": {
            "name": issue_type
        }
    }
    
    if assignee:
        fields["assignee"] = {"accountId": assignee}
    
    if parent_key:
        fields["parent"] = {"key": parent_key}
    
    data = {"fields": fields}
    response = requests.post(url, headers=headers, auth=auth, data=json.dumps(data))
    return response.json()

def main():
    data = get_spreadsheet_data(google_spreadsheet_id, google_api_key)
    if not data:
        logging.error("No data found in the spreadsheet.")
        return
    
    managers_projects = parse_spreadsheet_data(data)

    for manager_email, projects in managers_projects.items():
        manager_id, manager_display_name = get_user_details(manager_email)
        manager_name = manager_display_name
        
        epic_exists_flag, existing_epic_key = issue_exists(manager_name)
        if not epic_exists_flag:
            epic = create_issue("Epic", manager_name, f"Epic for managing tasks of {manager_name}")
            logging.info(f"Epic Creation Response: {epic}")
            epic_key = epic['key']
        else:
            epic_key = existing_epic_key
            logging.info(f"Epic for {manager_name} already exists with key: {epic_key}")
        
        task_summary = f"{manager_display_name} - {today}"
        task_exists_flag, existing_task_key = issue_exists(task_summary)
        if not task_exists_flag:
            task_description = f"Task for {manager_display_name} on {today}"
            task = create_issue("Task", task_summary, task_description, assignee=manager_id, parent_key=epic_key)
            logging.info(f"Task Creation Response: {task}")
            task_key = task['key']
            
            for project in projects:
                subtask_summary = f"{manager_display_name} - {today} - {project}"
                subtask_exists_flag, existing_subtask_key = issue_exists(subtask_summary)
                if not subtask_exists_flag:
                    subtask_description = f"Subtask for {manager_display_name} on {today} for project {project}"
                    subtask = create_issue("Subtask", subtask_summary, subtask_description, assignee=manager_id, parent_key=task_key)
                    logging.info(f"Subtask Creation Response: {subtask}")
                else:
                    logging.info(f"Subtask for {manager_display_name} on {today} for project {project} already exists with key: {existing_subtask_key}")
        else:
            logging.info(f"Task for {manager_display_name} on {today} already exists with key: {existing_task_key}")

if __name__ == "__main__":
    main()
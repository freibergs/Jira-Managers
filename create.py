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
google_api_key = os.getenv("GOOGLE_API_KEY")
google_spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
google_spreadsheet_name = os.getenv("GOOGLE_SPREADSHEET_NAME")
start_date_id = os.getenv("START_DATE_FIELD_ID")
end_date_id = os.getenv("END_DATE_FIELD_ID")

auth = HTTPBasicAuth(api_username, api_token)
headers = {
    "Content-Type": "application/json"
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler('script.log'),
    logging.StreamHandler()
])

today_iso = datetime.now().strftime("%Y-%m-%d")
today_formatted = datetime.now().strftime("%m.%d.%Y")

def get_spreadsheet_data(spreadsheet_id, api_key, range_name=google_spreadsheet_name):
    service = build('sheets', 'v4', developerKey=api_key)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    return result.get('values', [])

def parse_spreadsheet_data(data):
    managers_projects = {}
    for row in data[1:]:
        email = row[0]
        projects = row[1].split(', ')
        managers_projects[email] = projects
    return managers_projects

def get_user_details(email):
    url = f"{jira_url}/rest/api/3/user/search?query={email}"
    response = requests.get(url, headers=headers, auth=auth)
    user = response.json()[0]
    return user['accountId'], user['displayName']

def issue_exists(project_key, summary, issue_type=None):
    jql = f'project = {project_key} AND summary ~ "\\"{summary}\\""'
    if issue_type:
        jql += f' AND issuetype = "{issue_type}"'
    search_url = f"{jira_url}/rest/api/3/search"
    response = requests.get(search_url, headers=headers, auth=auth, params={'jql': jql})
    issues = response.json().get('issues', [])
    logging.info(f"Checked for existing issues with summary '{summary}' in project {project_key}")
    return len(issues) > 0, issues[0]['key'] if issues else None

def create_issue(project_key, issue_type, summary, description, assignee=None, parent_key=None, start_date=None, due_date=None):
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
    
    if issue_type == "Subtask" and start_date and due_date:
        fields[f"customfield_{start_date_id}"] = start_date
        fields[f"customfield_{end_date_id}"] = due_date
    
    data = {"fields": fields}
    response = requests.post(url, headers=headers, auth=auth, data=json.dumps(data))
    return response.json()

def create_issues_for_manager(manager_email, manager_projects):
    manager_id, manager_display_name = get_user_details(manager_email)
    
    for project_code in manager_projects:
        logging.info(f"Processing project: {project_code}")
        
        if not project_code:
            logging.error("Project code is invalid.")
            continue

        epic_summary = f"PM {project_code}"
        epic_exists_flag, existing_epic_key = issue_exists(project_code, epic_summary, issue_type="Epic")
        
        if not epic_exists_flag:
            epic = create_issue(project_code, "Epic", epic_summary, f"Epic for managing tasks in project {project_code}")
            logging.info(f"Epic Creation Response: {epic}")
            epic_key = epic.get('key')
            if not epic_key:
                logging.error(f"Failed to create Epic for project {project_code}: {epic}")
                continue
        else:
            epic_key = existing_epic_key
            logging.info(f"Epic for {project_code} already exists with key: {epic_key}")
        
        task_summary = f"PM {project_code} - {manager_display_name}"
        task_exists_flag, existing_task_key = issue_exists(project_code, task_summary, issue_type="Task")
        
        if not task_exists_flag:
            task_description = f"Task for {manager_display_name} in project {project_code}"
            task = create_issue(project_code, "Task", task_summary, task_description, assignee=manager_id, parent_key=epic_key)
            logging.info(f"Task Creation Response: {task}")
            task_key = task.get('key')
            if not task_key:
                logging.error(f"Failed to create Task for project {project_code}: {task}")
                continue
        else:
            task_key = existing_task_key
            logging.info(f"Task for {manager_display_name} in project {project_code} already exists with key: {task_key}")
        
        subtask_summary = f"PM {project_code} - {manager_display_name} - {today_formatted}"
        subtask_exists_flag, existing_subtask_key = issue_exists(project_code, subtask_summary, issue_type="Subtask")
        
        if not subtask_exists_flag:
            subtask_description = f"Subtask for {manager_display_name} on {today_formatted} for project {project_code}"
            subtask = create_issue(project_code, "Subtask", subtask_summary, subtask_description, assignee=manager_id, parent_key=task_key, start_date=today_iso, due_date=today_iso)
            logging.info(f"Subtask Creation Response: {subtask}")
        else:
            logging.info(f"Subtask for {manager_display_name} on {today_formatted} for project {project_code} already exists with key: {existing_subtask_key}")

def main():
    data = get_spreadsheet_data(google_spreadsheet_id, google_api_key)
    if not data:
        logging.error("No data found in the spreadsheet.")
        return
    
    managers_projects = parse_spreadsheet_data(data)
    for manager_email, manager_projects in managers_projects.items():
        create_issues_for_manager(manager_email, manager_projects)

if __name__ == "__main__":
    main()

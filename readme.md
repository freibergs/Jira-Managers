# Jira Task Management Automation

This project automates the creation and deletion of Jira tasks based on data from a Google Spreadsheet. It consists of two main scripts: `create.py` for task creation and `delete.py` for task deletion based on specific conditions.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Detailed Script Description](#detailed-script-description)
  - [create.py](#createpy)
  - [delete.py](#deletepy)
- [Environment Variables](#environment-variables)
- [Google Spreadsheet Structure](#google-spreadsheet-structure)
- [Jira Project Structure](#jira-project-structure)
- [Logging](#logging)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

To use this project, you will need:

- Python 3.10 or higher
- A Jira account with API access
- Google Sheets API enabled and corresponding credentials (https://developers.google.com/sheets/api/guides/concepts)
- Access to the specified Google Spreadsheet
- The following Python libraries (installable via pip):
  - requests
  - python-dotenv
  - google-auth
  - google-auth-oauthlib
  - google-auth-httplib2
  - google-api-python-client

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/zajebs/Jira-Managers
   cd jira-task-automation
   ```

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate  # Windows
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Configuration

1. Create a `.env` file in the project root directory with the following variables:

   ```
   JIRA_URL=https://your-domain.atlassian.net
   API_USERNAME=your-jira-email@example.com
   API_TOKEN=your-jira-api-token
   PROJECT_KEY=YOUR_PROJECT_KEY
   GOOGLE_API_KEY=your-google-api-key
   GOOGLE_SPREADSHEET_ID=your-spreadsheet-id
   GOOGLE_SPREADSHEET_NAME=YourSheetName
   GOOGLE_DELETE_CONDITION_CELL=E2
   ```

   Replace the values with your actual Jira and Google Sheets credentials and settings.

2. Ensure that the `.env` file is included in your `.gitignore` to keep your credentials secure.

3. Set up Google Sheets API:
   - Go to the Google Cloud Console
   - Create a new project or select an existing one
   - Enable the Google Sheets API
   - Create credentials (Service Account Key)
   - Download the JSON key file and store it securely

## Usage

To run the scripts, use the following commands:

1. To create tasks:
   ```
   python create.py
   ```

2. To delete tasks:
   ```
   python delete.py
   ```

It's recommended to set up these scripts to run automatically on a daily basis using a task scheduler like cron (for Unix-based systems) or Task Scheduler (for Windows).

## Detailed Script Description

### create.py

This script performs the following actions:

1. Loads environment variables and sets up authentication for Jira and Google Sheets.
2. Retrieves data from the specified Google Spreadsheet.
3. For each manager in the spreadsheet:
   - Checks if an Epic for the manager exists. If not, it creates one.
   - Creates a Task for the current date if it doesn't exist.
   - For each project assigned to the manager, creates a Subtask if it doesn't exist.
4. Logs all actions and any errors encountered.

Key functions:
- `get_spreadsheet_data()`: Retrieves data from Google Sheets.
- `parse_spreadsheet_data()`: Processes the raw data into a usable format.
- `get_user_details()`: Retrieves Jira user details based on email.
- `issue_exists()`: Checks if a Jira issue with a given summary already exists.
- `create_issue()`: Creates a new Jira issue (Epic, Task, or Subtask).

### delete.py

This script performs the following actions:

1. Loads environment variables and sets up authentication for Jira and Google Sheets.
2. Retrieves a deletion condition from a specified cell in the Google Spreadsheet.
3. Searches for and deletes Subtasks that match the condition and were created yesterday.
4. Searches for Tasks that match the condition and were created yesterday.
5. For each Task, checks if it has any remaining Subtasks. If not, it deletes the Task.
6. Logs all actions and any errors encountered.

Key functions:
- `get_condition()`: Retrieves the deletion condition from Google Sheets.
- `get_issues_to_delete()`: Searches for Jira issues matching the deletion criteria.
- `delete_issue()`: Deletes a specified Jira issue.
- `check_if_subtasks_exist()`: Checks if a Task has any remaining Subtasks.

## Environment Variables

- `JIRA_URL`: Your Jira instance URL
- `API_USERNAME`: Your Jira account email
- `API_TOKEN`: Your Jira API token
- `PROJECT_KEY`: The key of the Jira project where tasks will be created/deleted
- `GOOGLE_API_KEY`: Your Google Sheets API key
- `GOOGLE_SPREADSHEET_ID`: The ID of the Google Spreadsheet containing manager data
- `GOOGLE_SPREADSHEET_NAME`: The name of the sheet within the spreadsheet
- `GOOGLE_DELETE_CONDITION_CELL`: The cell containing the deletion condition

## Google Spreadsheet Structure

The Google Spreadsheet should be structured as follows:

- Column A: Manager's email address
- Column B: Comma-separated list of projects assigned to the manager
- Cell E2: Deletion condition for the whole `delete.py` script

Example:
```
| Email                | Projects           | ... | ... | Deletion Condition |
|----------------------|--------------------|-----|-----|-------------------|
| manager1@example.com | ProjectA, ProjectB | ... | ... | status = Done     |
| manager2@example.com | ProjectC           | ... | ... |                   |
```

## Jira Project Structure

The scripts create and manage the following Jira issue types:

1. Epic: One per manager, serving as a container for all tasks.
2. Task: Daily task for each manager.
3. Subtask: Individual project tasks under the daily task.

The hierarchy is as follows:
```
Epic (Manager Name)
└── Task (Manager Name - Date)
    ├── Subtask (Manager Name - Date - Project1)
    ├── Subtask (Manager Name - Date - Project2)
    └── Subtask (Manager Name - Date - Project3)
```

## Logging

Both scripts log their activities to `script.log` in the project directory. The log includes:
- Information about created/deleted issues
- Errors encountered during execution
- API responses for troubleshooting

Log levels used:
- INFO: Successful operations and general information
- ERROR: Failed operations and exceptions

## Troubleshooting

Common issues and their solutions:

1. Authentication errors:
   - Ensure your Jira API token and Google API key are correct and not expired.
   - Check that you have the necessary permissions in both Jira and Google Sheets.

2. "Issue already exists" errors:
   - This is normal if the script is run multiple times a day. The script checks for existing issues before creating new ones.

3. Google Sheets API quota exceeded:
   - If you're hitting API limits, consider implementing exponential backoff and retry logic.

4. Jira API rate limiting:
   - Implement a delay between API calls if you encounter rate limiting issues.

## Security Considerations

1. Never commit the `.env` file or any file containing credentials to version control.
2. Use environment variables for all sensitive information.
3. Regularly rotate your API tokens and keys.
4. Ensure that only authorized personnel have access to the Google Spreadsheet and Jira project.
5. Implement IP whitelisting for your Jira API token if possible.
6. Regularly audit the scripts' activities through the log files.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Write your code and tests.
4. Ensure all tests pass and the code adheres to the project's style guide.
5. Submit a pull request with a clear description of your changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
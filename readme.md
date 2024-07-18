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

- Python 3.09 or higher
- A Jira account with API access
- Google Sheets API enabled and corresponding credentials
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
   git clone https://github.com/your-repo/jira-task-automation
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

Create a `.env` file in the project root directory with the following variables:

```
JIRA_URL=https://your-url.atlassian.net
API_USERNAME=your-api-username
API_TOKEN=your-jira-api-token
START_DATE_FIELD_ID=10034
END_DATE_FIELD_ID=10035
GOOGLE_API_KEY=your-google-api-key
GOOGLE_SPREADSHEET_ID=your-spreadsheet-id
GOOGLE_SPREADSHEET_NAME=Managers
GOOGLE_DELETE_CONDITION_CELL=E2
DAYS_AGO_TO_DELETE=3
```

Replace the API token and Google API key with your actual credentials.

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
3. For each project and manager combination in the spreadsheet:
   - Checks if an Epic for the project exists. If not, it creates one.
   - Creates a Task for the manager if it doesn't exist.
   - Creates a Subtask for the current date if it doesn't exist.
4. Logs all actions and any errors encountered.

### delete.py

This script performs the following actions:

1. Loads environment variables and sets up authentication for Jira and Google Sheets.
2. Retrieves a deletion condition from a specified cell in the Google Spreadsheet.
3. For each project:
   - Finds the corresponding Epic.
   - For each Task under the Epic:
     - Searches for and deletes Subtasks that match the condition and were created on the specified date.
     - If no Subtasks remain, deletes the Task.
4. Logs all actions and any errors encountered.

## Environment Variables

- `JIRA_URL`: Your Jira instance URL
- `API_USERNAME`: Your Jira account email
- `API_TOKEN`: Your Jira API token
- `START_DATE_FIELD_ID`: Custom field ID for start date
- `END_DATE_FIELD_ID`: Custom field ID for end date
- `GOOGLE_API_KEY`: Your Google Sheets API key
- `GOOGLE_SPREADSHEET_ID`: The ID of the Google Spreadsheet containing project and manager data
- `GOOGLE_SPREADSHEET_NAME`: The name of the sheet within the spreadsheet
- `GOOGLE_DELETE_CONDITION_CELL`: The cell containing the deletion condition
- `DAYS_AGO_TO_DELETE`: Number of days ago to target for deletion

## Google Spreadsheet Structure

The Google Spreadsheet should be structured as follows:

- Column A: Manager's email address
- Column B: Comma-separated list of project codes assigned to the manager
- Cell E2: Deletion condition for the `delete.py` script

Example:
```
| Email                | Projects           | ... | ... | Deletion Condition |
|----------------------|--------------------|-----|-----|-------------------|
| manager1@example.com | ABC, CDE, XYZ      | ... | ... | status = Done     |
| manager2@example.com | BFY, XYZ           | ... | ... |                   |
```

## Jira Project Structure

The scripts create and manage the following Jira issue types:

1. Epic: One per project, serving as a container for all tasks.
2. Task: One per manager for each project they're assigned to.
3. Subtask: Daily subtask for each manager-project combination.

The hierarchy is as follows:
```
Epic (PM {Project Code})
└── Task (PM {Project Code} - {Manager Name})
    └── Subtask (PM {Project Code} - {Manager Name} - {Date})
```

## Logging

Both scripts log their activities to log files in the project directory. The log includes:
- Information about created/deleted issues
- Errors encountered during execution
- API responses for troubleshooting

## Troubleshooting

Common issues and their solutions:

1. Authentication errors:
   - Ensure your Jira API token and Google API key are correct and not expired.
   - Check that you have the necessary permissions in both Jira and Google Sheets.

2. "Issue already exists" messages:
   - This is normal if the script is run multiple times a day. The script checks for existing issues before creating new ones.

3. Google Sheets API quota exceeded:
   - If you're hitting API limits, consider implementing exponential backoff and retry logic.

4. Jira API rate limiting:
   - Implement a delay between API calls if you encounter rate limiting issues.

## Security Considerations

1. Never commit the `.env` file or any file containing credentials to version control.
2. Use environment variables for all sensitive information.
3. Regularly rotate your API tokens and keys.
4. Ensure that only authorized personnel have access to the Google Spreadsheet and Jira projects.
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
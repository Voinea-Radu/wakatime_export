#!/usr/bin/env python

"""
You must create a file named `credentials.py` in the same directory as this file.
The file must contain the following variables:

WAKATIME_API_KEY: str = "REDACTED"
CLOCKIFY_API_KEY: str = "REDACTED"
"""

import requests
from datetime import datetime, UTC
import re
from credentials import WAKATIME_API_KEY, CLOCKIFY_API_KEY


def regex_str(text: str):
    return f"^{text}&"


DATE = "2024-04-04"
EXCLUDE_LIST = [
    ".*lab.*", ".*tema.*", ".*teme.*", ".*iocla.*",  # REGEX
    regex_str("copilot"), regex_str("didi"), regex_str("device"),  # STRINGS
]

WAKATIME_BASE_URL: str = "https://wakatime.com/api/v1"

CLOCKIFY_BASE_URL: str = "https://api.clockify.me/api/v1"

CLOCKIFY_WORKSPACE_NAME = "Mythical Network"
CLOCKIFY_PROJECT_NAME = "Development"
CLOCKIFY_TASK_NAME = "Light"


def unix_to_iso8601(unix_time):
    delta_time = datetime.fromtimestamp(unix_time, UTC)
    return delta_time.strftime('%Y-%m-%dT%H:%M:%S.00Z')


def get_wakatime_data():
    response = requests.get(url=f"{WAKATIME_BASE_URL}/users/current/durations?date={DATE}&api_key={WAKATIME_API_KEY}")

    json = response.json()["data"]

    output = []

    for project in json:
        found: bool = False

        for exclude in EXCLUDE_LIST:
            if re.match(exclude, project["project"]) is not None:
                found = True
                break

        if found:
            continue

        output.append(project)

    return output


def get_clockify_workspace_id(workspace_name: str):
    response = requests.get(url=f"{CLOCKIFY_BASE_URL}/workspaces",
                            headers={
                                "X-Api-Key": CLOCKIFY_API_KEY
                            }
                            )

    json = response.json()

    for workspace in json:
        if workspace["name"] == workspace_name:
            return workspace["id"]


def get_clockify_project_id(workspace_id: str, project_name: str):
    response = requests.get(url=f"{CLOCKIFY_BASE_URL}/workspaces/{workspace_id}/projects",
                            headers={
                                "X-Api-Key": CLOCKIFY_API_KEY
                            }
                            )

    json = response.json()

    for project in json:
        if project["name"] == project_name:
            return project["id"]


def get_clockify_task_id(workspace_id: str, project_id: str, task_name: str):
    response = requests.get(url=f"{CLOCKIFY_BASE_URL}/workspaces/{workspace_id}/projects/{project_id}/tasks",
                            headers={
                                "X-Api-Key": CLOCKIFY_API_KEY
                            }
                            )

    json = response.json()

    for task in json:
        if task["name"] == task_name:
            return task["id"]


def upload_data():
    workspace_id = get_clockify_workspace_id(CLOCKIFY_WORKSPACE_NAME)
    project_id = get_clockify_project_id(workspace_id, CLOCKIFY_PROJECT_NAME)
    task_id = get_clockify_task_id(workspace_id, project_id, CLOCKIFY_TASK_NAME)

    wakatime_data = get_wakatime_data()

    total_count: int = len(wakatime_data)

    for data_index in range(len(wakatime_data)):
        data = wakatime_data[data_index]
        start_time = unix_to_iso8601(data["time"])
        end_time = unix_to_iso8601(data["time"] + data["duration"])
        project = data["project"]

        print(f"{data_index}/{total_count}...", end=" ")

        response = requests.post(url=f"{CLOCKIFY_BASE_URL}/workspaces/{workspace_id}/time-entries",
                                 headers={
                                     "X-Api-Key": CLOCKIFY_API_KEY
                                 },
                                 json={
                                     "billable": True,
                                     "description": project,
                                     "start": start_time,
                                     "end": end_time,
                                     "projectId": project_id,
                                     "taskId": task_id
                                 }
                                 )

        print(response.status_code)

        if response.status_code != 201:
            print(response.json())


def main():
    upload_data()


if __name__ == '__main__':
    main()

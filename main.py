#!/usr/bin/env python

"""
You must create a file named `credentials.py` in the same directory as this file.
The file must contain the following variables:

WAKATIME_API_KEY: str = "REDACTED"
CLOCKIFY_API_KEY: str = "REDACTED"
"""

import requests
from datetime import datetime
import re
import pytz

from credentials import WAKATIME_API_KEY, CLOCKIFY_API_KEY


def str_regex(text: str):
    return f"^{text}$"


DATES = [
    "2024-10-28",
    "2024-10-29",
    "2024-10-30",
    "2024-10-31",
    "2024-11-01",
    "2024-11-02",
    "2024-11-03",
]
EXCLUDE_LIST = [
    # REGEX
    ".*lab.*", ".*tema.*", ".*teme.*", ".*iocla.*", "proiect.*", ".*bootloader.*", ".*assignment.*",
    # STRINGS
    str_regex("copilot"), str_regex("didi"), str_regex("device"), str_regex("Unknown Project"), str_regex("partial"),
    str_regex("rust_os"), str_regex("fizica"), str_regex("Physics"), str_regex("RustOS")
]

WAKATIME_BASE_URL: str = "https://wakatime.com/api/v1"

CLOCKIFY_BASE_URL: str = "https://api.clockify.me/api/v1"

CLOCKIFY_WORKSPACE_NAME = "Mythical Network"
CLOCKIFY_PROJECT_NAME = "Development"
CLOCKIFY_TASK_NAME = "Light"


def unix_to_iso8601(unix_time):
    delta_time = datetime.fromtimestamp(unix_time, pytz.timezone('UTC'))
    return delta_time.strftime('%Y-%m-%dT%H:%M:%S.00Z')


def get_wakatime_data(date: str):
    response = requests.get(url=f"{WAKATIME_BASE_URL}/users/current/durations?date={date}&api_key={WAKATIME_API_KEY}")

    json = response.json()["data"]

    output = []

    for project in json:
        found: bool = False

        for exclude in EXCLUDE_LIST:
            if re.match(exclude, project["project"], flags=re.IGNORECASE) is not None:
                found = True
                break

        if found:
            continue

        output.append(project)

    projects: dict[str, int] = {}

    for project in output:
        if project["project"] not in projects:
            projects[project["project"]] = 0
        projects[project["project"]] += project["duration"]

    return projects


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


def time_to_string(time: int):
    hours = int(time // 3600)
    minutes = int((time % 3600) // 60)
    seconds = int(time % 60)

    hours_str = str(hours) if hours >= 10 else f"0{hours}"
    minutes_str = str(minutes) if minutes >= 10 else f"0{minutes}"
    seconds_str = str(seconds) if seconds >= 10 else f"0{seconds}"

    return f"{hours_str}:{minutes_str}:{seconds_str}"


def upload_data():
    workspace_id = get_clockify_workspace_id(CLOCKIFY_WORKSPACE_NAME)
    project_id = get_clockify_project_id(workspace_id, CLOCKIFY_PROJECT_NAME)
    task_id = get_clockify_task_id(workspace_id, project_id, CLOCKIFY_TASK_NAME)

    date_index: int = 0

    for date in DATES:
        date_index += 1
        wakatime_data = get_wakatime_data(date)

        total_count: int = len(wakatime_data)
        data_index: int = 0

        for project, time in wakatime_data.items():
            data_index += 1

            start_time = f"{date}T00:00:00Z"
            delta = time_to_string(time)
            end_time = f"{date}T{delta}Z"

            print(f"{date_index}/{len(DATES)} {data_index}/{total_count}...", end=" ")

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

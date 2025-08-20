"""
elog_client.py

Elog API client for posting entries and fetching user and logbook information.
"""

import os
import json
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
ELOG_API_URL = os.getenv("SWAPPS_TRACE_ELOG_API_URL")
ELOG_API_KEY = os.getenv("SWAPPS_TRACE_ELOG_API_KEY")


def get_user() -> tuple[int, dict | Exception]:
    """
    Fetches the user information from the ELOG API. Also used to verify the API key.
    :return: A tuple containing the status code and the user data or exception.
    """
    url = f"{ELOG_API_URL}/v1/users/me"
    headers = {"x-vouch-idp-accesstoken": ELOG_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.status_code, response.json()
    except requests.exceptions.RequestException as e:
        print(e)
        return response.status_code, e


def post_entry(
    title: str, body: str, logbooks: list[str], image_bytes, config_file_path: Path | None = None
) -> tuple[int, dict | Exception]:
    """
    Posts a new entry with image to the ELOG API.

    :param title: The title of the entry.
    :param body: The body of the entry.
    :param logbooks: A list of logbook names to post the entry to.
    :param image_bytes: Bytes of the image to be attached to the entry.
    :param config_file: Optional, path of config file to attach.
    :return: A tuple containing the status code and the response data or exception.
    """
    url = f"{ELOG_API_URL}/v2/entries"
    headers = {"x-vouch-idp-accesstoken": ELOG_API_KEY}

    entry_data = {"title": title, "text": body, "logbooks": logbooks}
    entry_json = json.dumps(entry_data).encode("utf-8")

    files = [
        ("entry", ("entry.json", entry_json, "application/json")),
        ("files", ("trace_plot.png", image_bytes, "image/png")),
    ]
    if config_file_path is not None:
        with open(config_file_path, "rb") as f:
            config_bytes = f.read()
        files.append(("files", (config_file_path.name, config_bytes, "application/octet-stream")))
    try:
        response = requests.post(
            url,
            headers=headers,
            files=files,
        )
        response.raise_for_status()
        return response.status_code, response.json()
    except requests.exceptions.RequestException as e:
        print(e)
        return response.status_code, e


def get_logbooks() -> tuple[int, list[str] | Exception]:
    """
    Fetches the list of logbooks from the ELOG API.

    :return: A tuple containing the status code and a list of logbook names or an exception.
    """
    url = f"{ELOG_API_URL}/v1/logbooks"
    headers = {"x-vouch-idp-accesstoken": ELOG_API_KEY}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.status_code, [logbook["name"] for logbook in response.json()["payload"]]
    except requests.exceptions.RequestException as e:
        print(e)
        return response.status_code, e

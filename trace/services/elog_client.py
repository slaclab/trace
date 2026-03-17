"""
elog_client.py

Elog API client for posting entries and fetching user and logbook information.
"""

import os
import json
from typing import Optional
from pathlib import Path

import requests
from dotenv import load_dotenv

from config import logger

load_dotenv()
ELOG_API_URL = os.getenv("SWAPPS_TRACE_ELOG_API_URL")
ELOG_API_KEY = os.getenv("SWAPPS_TRACE_ELOG_API_KEY")

# Configure proxy if specified in environment
ELOG_PROXY_URL = os.getenv("SWAPPS_TRACE_ELOG_PROXY_URL")
if ELOG_PROXY_URL:
    os.environ["HTTP_PROXY"] = ELOG_PROXY_URL
    os.environ["HTTPS_PROXY"] = ELOG_PROXY_URL
    logger.info(f"ELOG client configured to use proxy: {ELOG_PROXY_URL}")


def test_proxy_connection() -> tuple[bool, Optional[str]]:
    """
    Tests proxy connectivity if a proxy is configured.

    :return: A tuple of (success, error_message). If successful, error_message is None.
             If failed, error_message contains a detailed description of the failure.
    """
    if not ELOG_PROXY_URL:
        # No proxy configured, consider this a success
        return True, None

    if not ELOG_API_URL:
        return False, "ELOG API URL is not configured. Cannot test proxy connection."

    error_msg = (
        f"Failed to connect through proxy {ELOG_PROXY_URL}. "
        f"Please check your network connection and proxy configuration."
    )

    try:
        requests.head(ELOG_API_URL, timeout=2)
        logger.info(f"Proxy connection test successful: {ELOG_PROXY_URL}")
        return True, None
    except requests.exceptions.ProxyError as e:
        logger.error(f"Proxy connection test failed: {e}")
        return False, error_msg
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Proxy connection test failed: {e}")
        return False, error_msg
    except requests.exceptions.Timeout as e:
        error_msg = (
            f"Connection timeout through proxy {ELOG_PROXY_URL}. " f"The proxy or server may be slow or unresponsive."
        )
        logger.error(f"Proxy connection test failed: {e}")
        return False, error_msg
    except requests.exceptions.RequestException as e:
        logger.error(f"Proxy connection test failed: {e}")
        return False, error_msg


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
        logger.error(e)
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
        logger.error(e)
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
        logger.error(e)
        return response.status_code, e

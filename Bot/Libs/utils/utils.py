import os
import re
import ssl
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, TypeVar, Union

import ciso8601

T = TypeVar("T", str, None)

# From https://stackoverflow.com/questions/4628122/how-to-construct-a-timedelta-object-from-a-simple-string
# Answer: https://stackoverflow.com/a/51916936
# datetimeParseRegex = re.compile(r'^((?P<days>[\.\d]+?)d)?((?P<hours>[\.\d]+?)h)?((?P<minutes>[\.\d]+?)m)?((?P<seconds>[\.\d]+?)s)?$')
datetime_regex = re.compile(
    r"^((?P<weeks>[\.\d]+?)w)? *"
    r"^((?P<days>[\.\d]+?)d)? *"
    r"((?P<hours>[\.\d]+?)h)? *"
    r"((?P<minutes>[\.\d]+?)m)? *"
    r"((?P<seconds>[\.\d]+?)s?)?$"
)


def parse_datetime(datetime: Union[datetime, str]) -> datetime:
    """Parses a datetime object or a string into a datetime object

    Args:
        datetime (Union[datetime.datetime, str]): Datetime object or string to parse

    Returns:
        datetime.datetime: Parsed datetime object
    """
    if isinstance(datetime, str):
        return ciso8601.parse_datetime(datetime)
    return datetime


def encode_datetime(dict: Dict[str, Any]) -> Dict[str, Any]:
    """Takes a dictionary and encodes all datetime objects into ISO 8601 strings

    Args:
        dict (Dict[str, Any]): Dictionary to encode

    Returns:
        Dict[str, Any]: The dictionary with all datetime objects encoded as ISO 8601 strings
    """
    for k, v in dict.items():
        if isinstance(v, datetime):
            dict[k] = v.isoformat()
    return dict


def parse_subreddit(subreddit: Union[str, None]) -> str:
    """Parses a subreddit name to be used in a reddit url

    Args:
        subreddit (Union[str, None]): Subreddit name to parse

    Returns:
        str: Parsed subreddit name
    """
    if subreddit is None:
        return "all"
    return re.sub(r"^[r/]{2}", "", subreddit, re.IGNORECASE)


def parse_time_str(time_str: str) -> Union[timedelta, None]:
    """Parse a time string e.g. (2h13m) into a timedelta object.

    Taken straight from https://stackoverflow.com/a/4628148

    Args:
        time_str (str): A string identifying a duration.  (eg. 2h13m)

    Returns:
        datetime.timedelta: A datetime.timedelta object
    """
    parts = datetime_regex.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)


def setup_ssl(
    ca_path: Union[str, None],
    cert_path: str,
    key_path: Union[str, None],
    key_password: Union[str, None],
) -> ssl.SSLContext:
    sslctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=ca_path)
    sslctx.check_hostname = True
    sslctx.load_cert_chain(cert_path, key_path, key_password)
    return sslctx


def is_docker() -> bool:
    path = "/proc/self/cgroup"
    return os.path.exists("/.dockerenv") or (
        os.path.isfile(path) and any("docker" in line for line in open(path))
    )


def tick(opt: Optional[bool], label: Optional[str] = None) -> str:
    lookup = {
        True: "<:greenTick:330090705336664065>",
        False: "<:redTick:330090723011592193>",
        None: "<:greyTick:563231201280917524>",
    }
    emoji = lookup.get(opt, "<:redTick:330090723011592193>")
    if label is not None:
        return f"{emoji}: {label}"
    return emoji

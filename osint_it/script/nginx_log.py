#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  1 17:58:45 2026

@author: joannes
"""
# TODO
from dataclasses import dataclass
from datetime import datetime
import re


@dataclass
class NginxLogEntry:
    ip: str
    timestamp: datetime
    request: str
    status: int
    size: int
    referer: str
    user_agent: str
    
    
LOG_PATTERN = re.compile(
    r'^(?P<ip>\S+) '
    r'\S+ \S+ '
    r'\[(?P<timestamp>[^\]]+)\] '
    r'"(?P<request>[^"]*)" '
    r'(?P<status>\d{3}) '
    r'(?P<size>\S+) '
    r'"(?P<referer>[^"]*)" '
    r'"(?P<user_agent>[^"]*)"'
)

def parse_line(line: str) -> NginxLogEntry | None:

    match = LOG_PATTERN.match(line)

    if not match:
        return None

    data = match.groupdict()

    size = 0 if data["size"] == "-" else int(data["size"])

    return NginxLogEntry(
        ip=data["ip"],
        timestamp=datetime.strptime(
            data["timestamp"],
            "%d/%b/%Y:%H:%M:%S %z"
        ),
        request=data["request"],
        status=int(data["status"]),
        size=size,
        referer=data["referer"],
        user_agent=data["user_agent"],
    )
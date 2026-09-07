# OSINT IT

Standalone Python tools for OSINT-style web/IT analysis.

## Contents

- `script/nginx_log.py` — parses classic nginx `combined` access log lines into a `NginxLogEntry` dataclass
  (IP, timestamp, request, status, size, referer, user agent). Useful to extract
  suspicious or interesting traffic from web server logs.

## Usage

```python
from script.nginx_log import parse_line

entry = parse_line('127.0.0.1 - - [07/Sep/2026:10:00:00 +0200] "GET / HTTP/1.1" 200 612 "-" "curl/7.81.0"')
print(entry.ip, entry.status, entry.request)
```

This script is a work in progress (`TODO`).
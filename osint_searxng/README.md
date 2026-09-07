# OSINT SearxNG

Odoo module to interact with [SearxNG](https://docs.searxng.org/) meta-search servers directly from Odoo,
with a persistent history of all queries and results.

## Features

- Configure one or more SearxNG server instances (`searxng.server`).
- Send web searches (`searxng.query`) with categories, language and time range.
- Store every result (`searxng.result`) with title, excerpt, engine metadata, score, media, etc.
- Results are linked to websites/URLs managed by the `osint_website` module.

## Models

| Model            | Purpose                                       |
| ---------------- | --------------------------------------------- |
| `searxng.server` | SearxNG server configuration (base URL)       |
| `searxng.query`  | A search query and its options                |
| `searxng.result` | A single search result linked to a query/URL  |

## Requirements

This module depends on:

- `osint_website` (to link results to `osint.url` / `osint.website`)
- A running SearxNG instance with the JSON format enabled (see `osint_docker` and the script `script/configure_docker.py`).

## Configuration

1. Install the module.
2. Create a SearxNG server (`base_url`, `timeout`).
3. Create a query, choose options and click **Send**. Results are saved automatically.

## Docker setup script

`script/configure_docker.py` configures a running SearxNG container:

- adds the JSON format to `search.formats`,
- sets `server.limiter: false`,
- restarts the container.

Run it with the SearxNG container running:

```bash
python3 osint_searxng/script/configure_docker.py
```
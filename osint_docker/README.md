# OSINT Docker

Docker helpers and test scripts used to run the OSINT services (SearxNG, etc.).

## Contents

- `test/test_searxng.py` — installs and tests a SearxNG container:
  1. Creates the `./config` and `./data` directories.
  2. Pulls the `searxng/searxng:latest` image.
  3. Creates the container on host port `8888`.
  4. Waits for it to start.
  5. Adds `search.formats` (`html`, `json`) and `server.limiter: false` to `settings.yml`.
  6. Restarts SearxNG and checks that `GET /search?q=test&format=json` returns HTTP 200.

## Usage

```bash
python3 osint_docker/test/test_searxng.py
```

The container is named `searxng` and exposes port `8888` on the host.

## Pairing with the module

The `osint_searxng` module uses a SearxNG server configured via its `base_url`.
A container produced by this script can be used directly as that server
(e.g. `http://127.0.0.1:8888`).
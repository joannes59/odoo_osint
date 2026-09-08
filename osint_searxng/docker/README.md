# SearxNG Docker

Deployment of [SearxNG](https://docs.searxng.org/) (and its cache [Valkey](https://valkey.io/)) via Docker Compose, to power the Odoo module `osint_searxng`.

## Contents

| File                             | Purpose                                                     |
| -------------------------------- | ----------------------------------------------------------- |
| `docker-compose.yml`             | `searxng-core` and `searxng-valkey` services                |
| `install_docker_searxng.sh`      | Installation + JSON format activation                       |

## Quick Start

1. copy files to your docker directory
2. Install and configure the service:

```sh
sh install_docker_searxng.sh
```

The script:

- starts the containers (`searxng-core` on `127.0.0.1:8888`),
- waits for the service to respond,
- adds `json` to `search.formats` in `core-config/settings.yml`,
- restarts the service.

> JSON format is required by the Odoo module `osint_searxng`.

## Services

| Service        | Container          | Exposed Port         | Purpose                       |
| -------------- | ------------------ | -------------------- | ----------------------------- |
| `core`         | `searxng-core`     | `127.0.0.1:8888`     | Search engine                 |
| `valkey`       | `searxng-valkey`   | internal             | Cache / result storage        |

## Generated Files

- `core-config/settings.yml` — SearxNG configuration (to be customized).
- Docker volumes `core-data` and `valkey-data` — persistent data.

## Useful Commands

```sh
docker compose up -d       # start
docker compose stop        # stop
docker compose down        # stop and remove containers
docker compose logs -f     # follow logs
```

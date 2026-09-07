# odoo_osint

Manage OSINT (Open Source Intelligence) information directly inside **Odoo**.

This project groups several Odoo modules and utility scripts that let you:

- collect and organise **websites / URLs** and their components,
- search the web through a **SearxNG** server and keep a history of queries and results,
- drive **local or remote AI models** (Ollama, OpenAI, Anthropic, ...) via **LiteLLM**,
- expose **MCP servers** (Model Context Protocol) as AI tools,
- turn **Odoo users into AI agents** that answer in the Discuss channel.

## Modules

| Module                    | Description                                                    |
| ------------------------- | -------------------------------------------------------------- |
| `osint_agent`             | AI agents: `res.users` flagged as agent, replies in Discuss    |
| `osint_website`           | Websites and URLs management with URL parsing                 |
| `osint_searxng`           | SearxNG meta-search integration with query/result history     |
| `osint_litellm`           | AI provider & prompt management through LiteLLM               |
| `osint_fastmcp`           | MCP server proxy, stores MCP capabilities in Odoo             |
| `web_widget_mermaid_field`| Odoo widget to display Mermaid diagrams in views              |

## Additional scripts

| Folder         | Content                                                        |
| -------------- | -------------------------------------------------------------- |
| `osint_docker` | Docker helpers to install and test SearxNG containers         |
| `osint_it`     | Standalone IT/OSINT tools (e.g. nginx log parser)             |

## Module overview

```
osint_agent ──> discuss.channel / res.users (AI agent)
osint_litellm ──> AI providers, models, prompts (LiteLLM)
osint_fastmcp ──> MCP server capabilities exposed to prompts
osint_searxng ──> web searches ──> osint_website (URLs/websites)
```

## Installation

Each module is a standard Odoo addon. Add the project root to your `addons_path`, then
install the modules you need from the Apps menu.

Example `odoo.conf`:

```ini
[options]
addons_path = /path/to/odoo_osint
```

Make sure the Python dependencies are installed (`litellm`, `fastmcp`, `requests`).

Detailed instructions are available in each module's own `README.md`.

## License

This project is licensed under the **GNU Affero General Public License v3.0** — see the
[LICENSE](LICENSE) file for details.
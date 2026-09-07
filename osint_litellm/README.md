# OSINT LiteLLM

Base module of the OSINT suite for managing local and remote AI providers in Odoo, powered by the
[LiteLLM](https://github.com/BerriAI/litellm) Python package.

## Features

- Register AI providers (`litellm.provider`) supporting Ollama, OpenAI, Groq, Mistral, Deepseek, OpenRouter, Anthropic, etc.
- Import the list of available models from a provider (`Sync Models`).
- Enrich each model with LiteLLM capabilities (`response_format`, `json_schema`, etc.).
- Manage API keys per provider with user/group restrictions.
- Create prompts (`litellm.prompt`) with a message history and send them (`Send`).
- Store token usage and cost per message.
- Handle **tool calls** returned by the model (compatible with `osint_fastmcp`).

## Models

| Model                    | Purpose                                             |
| ------------------------ | --------------------------------------------------- |
| `litellm.provider`       | AI provider configuration (host, api type, state)   |
| `litellm.provider.apikey`| API keys scoped to users/groups                     |
| `litellm.model`          | Model metadata (family, size, context, capabilities)|
| `litellm.model.capability` | Reusable capability tags                          |
| `litellm.prompt`         | Prompt with message history and send action         |
| `litellm.prompt.message` | A message inside a prompt                           |

## Requirements

- Python package: `litellm`
- Seed providers are defined in `datas/litellm.provider.csv`.

## Installation

```bash
pip install litellm
```

Then install the module in Odoo (addon path must contain this folder).

## Configuration

1. Create a provider (e.g. local Ollama: host `http://localhost:11434`, API type `ollama`).
2. Click **Sync Models** to import the available models.
3. (Optional) Add API keys if the provider requires authentication.
4. Create a prompt, choose a model, enter a question and click **Send**. The answer and usage statistics are saved.
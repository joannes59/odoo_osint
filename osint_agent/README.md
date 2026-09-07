# OSINT Agent

Odoo module that turns `res.users` records into AI agents and connects them to the Discuss channel.

## Features

- Adds an `is_ai_agent` boolean on `res.users` to flag an account as an AI agent.
- Detects incoming messages in Discuss channels (`discuss.channel`) and triggers the agent to reply.
- Captures the web page the user is currently viewing (backend or website) and sends this context to the agent.
- Extends `mail.message` for future message processing hooks.

## Models

| Model            | Purpose                                                    |
| ---------------- | ---------------------------------------------------------- |
| `res.users`      | `is_ai_agent` flag to identify AI-agents                   |
| `discuss.channel`| `_message_post_after_hook` to ask the agent a reply        |
| `mail.message`   | `create` override for custom message handling              |

## Installation

Dependencies: `base`, `web`, `mail`, `im_livechat`.

## Configuration

1. Install the module.
2. Create a user and enable the **AI Agent** checkbox.
3. Add this user (via its partner) as a member of a Discuss channel.
4. Post a message in the channel; the agent will answer with the captured browser context.
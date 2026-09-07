# OSINT Website

Odoo module to collect and organise OSINT information about websites and URLs.

## Features

- Record domains/websites (`osint.website`) with a count of their URLs.
- Store URLs (`osint.url`) and automatically parse their components:
  - scheme, path, params, query string, fragment.
- Automatically create the associated `osint.website` from a parsed URL.
- Attach media references (thumbnail, image/audio/video source) and excerpts to a URL.
- Uniqueness check: an error is raised if an element uses an already-used website name.

## Models

| Model          | Purpose                                            |
| -------------- | -------------------------------------------------- |
| `osint.website`| A domain / website                                 |
| `osint.url`    | A URL with its parsed components and metadata      |

## Usage

1. Install the module.
2. Create a URL (or let SearxNG/other modules create them). The website is derived automatically.
3. Browse URLs and websites from the **Websites** menu (main menu **Websites**).

## Dependencies

- `base`

This module is used by `osint_searxng` to keep search results organised by domain.
# OSINT Base

Foundation module for the **OSINT** suite in Odoo.

## Features

- Root **OSINT** menu in the Odoo top bar.
- Shared security groups:
  - `OSINT User` — basic read access to OSINT data.
  - `OSINT Manager` — full CRUD on OSINT data (implied by `Settings`).

## Dependencies

- `base`

## Installation

This module is automatically installed as a dependency of any other OSINT module.
It can also be installed independently if you only need the menu and groups.

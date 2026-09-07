#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep  6 18:12:17 2026

@author: joannes
"""

import json
import os
import tempfile

from odoo.exceptions import UserError


class ApiSecrets:

    DEFAULT_PATH = "/etc/odoo/secrets/api_keys.json"

    def __init__(self, path=None):
        self.path = path or os.environ.get(
            "ODOO_API_KEYS_FILE",
            self.DEFAULT_PATH,
        )

        self._secrets = None

    def _load(self):
        if self._secrets is not None:
            return self._secrets

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self._secrets = json.load(f)

        except FileNotFoundError:
            raise UserError(
                f"Secrets file not found: {self.path}"
            )

        except PermissionError:
            raise UserError(
                f"Access denied to the secrets file: {self.path}"
            )

        except json.JSONDecodeError as e:
            raise UserError(
                f"Invalid secrets file: {e}"
            )

        return self._secrets

    def get(self, service, key=None, default=None):
        """
        Retrieve a secret.

        Example:
            secrets.get("mistral", "api_key")
        """

        data = self._load()

        service_data = data.get(service)

        if service_data is None:
            if default is not None:
                return default

            raise UserError(
                f"Service '{service}' is missing from the secrets file."
            )

        if key is None:
            return service_data

        value = service_data.get(key)

        if value is None:
            if default is not None:
                return default

            raise UserError(
                f"Key '{key}' is missing for the service '{service}'."
            )

        return value

    def get_api_key(self, service):
        """
        Shortcut to retrieve an API key.
        """
        return self.get(service, "api_key")

    def set(self, service, key, value):
        """
        Add or update a secret.

        Example:
            secrets.set("mistral", "api_key", "xxx")
        """

        data = self._load()

        if service not in data:
            data[service] = {}

        data[service][key] = value

        self._save(data)

        # The cache now contains the new data.
        self._secrets = data

    def set_api_key(self, service, api_key):
        """
        Add or update an API key.

        Example:
            secrets.set_api_key("mistral", "xxx")
        """
        self.set(service, "api_key", api_key)

    def _save(self, data):
        """
        Atomic write of the file.

        We first write to a temporary file,
        then replace the original file.
        """

        directory = os.path.dirname(self.path)

        if not os.path.isdir(directory):
            raise UserError(
                f"Secrets directory does not exist: {directory}"
            )

        try:
            fd, temporary_path = tempfile.mkstemp(
                dir=directory,
                prefix=".api_keys_",
                suffix=".tmp",
                text=True,
            )

            try:
                with os.fdopen(
                    fd,
                    "w",
                    encoding="utf-8",
                ) as f:

                    json.dump(
                        data,
                        f,
                        indent=4,
                        ensure_ascii=False,
                    )

                    f.write("\n")
                    f.flush()
                    os.fsync(f.fileno())

                # Atomic replacement
                os.replace(
                    temporary_path,
                    self.path,
                )

            except Exception:
                # Remove the temporary file
                if os.path.exists(temporary_path):
                    os.unlink(temporary_path)

                raise

        except PermissionError:
            raise UserError(
                f"Unable to write to the secrets file: "
                f"{self.path}"
            )
            

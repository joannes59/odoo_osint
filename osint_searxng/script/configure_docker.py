#!/usr/bin/env python3

import subprocess
import sys

CONTAINER = "searxng"
CONFIG = "/etc/searxng/settings.yml"


def docker_exec(command):
    result = subprocess.run(
        ["docker", "exec", CONTAINER, "sh", "-c", command],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

    return result.stdout


# ---------------------------------------------------------
# 1. Read the current configuration
# ---------------------------------------------------------

print(f"Reading {CONFIG} in {CONTAINER}...")

content = docker_exec(f"cat {CONFIG}")

print("Current configuration:")
print("----------------------------------------")
print(content)
print("----------------------------------------")


# ---------------------------------------------------------
# 2. Add/modify search.formats
# ---------------------------------------------------------

lines = content.splitlines()

# Remove any old "formats" section
# under "search", then rebuild the section cleanly.
#
# In the current configuration, search does not exist,
# so we simply add the section.

if "\nsearch:" not in "\n" + content:
    if not content.endswith("\n"):
        content += "\n"

    content += """
search:
  formats:
    - html
    - json
"""

else:
    print("A 'search' section already exists.")
    print("No automatic modification of this section is performed.")


# ---------------------------------------------------------
# 3. Add limiter: false in server
# ---------------------------------------------------------

if "limiter:" not in content:
    lines = content.splitlines()

    server_index = None

    for i, line in enumerate(lines):
        if line.strip() == "server:":
            server_index = i
            break

    if server_index is not None:
        # Find the end of the server section
        insert_index = server_index + 1

        while (
            insert_index < len(lines)
            and (
                lines[insert_index].startswith("  ")
                or lines[insert_index].strip() == ""
            )
        ):
            insert_index += 1

        lines.insert(insert_index, "  limiter: false")
        content = "\n".join(lines) + "\n"


# ---------------------------------------------------------
# 4. Display the new configuration
# ---------------------------------------------------------

print("New configuration:")
print("----------------------------------------")
print(content)
print("----------------------------------------")


# ---------------------------------------------------------
# 5. Save into the container
# ---------------------------------------------------------

# Use stdin to avoid escaping issues
# with docker exec.
process = subprocess.run(
    [
        "docker",
        "exec",
        "-i",
        CONTAINER,
        "sh",
        "-c",
        f"cat > {CONFIG}",
    ],
    input=content,
    text=True,
)

if process.returncode != 0:
    print("Error while writing the file.", file=sys.stderr)
    sys.exit(process.returncode)

print("Configuration saved.")


# ---------------------------------------------------------
# 6. Restart SearXNG
# ---------------------------------------------------------

print("Restarting SearXNG...")

result = subprocess.run(
    ["docker", "restart", CONTAINER],
    capture_output=True,
    text=True,
)

if result.returncode != 0:
    print(result.stderr, file=sys.stderr)
    sys.exit(result.returncode)

print("SearXNG restarted.")


# ---------------------------------------------------------
# 7. Display the final configuration
# ---------------------------------------------------------

print()
print("Final configuration:")
print("----------------------------------------")

final_content = docker_exec(f"cat {CONFIG}")
print(final_content)

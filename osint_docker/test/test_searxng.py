#!/usr/bin/env python3

import subprocess
import sys
import time


CONTAINER = "searxng"
IMAGE = "searxng/searxng:latest"

HOST_PORT = "8888"
CONTAINER_PORT = "8080"

CONFIG_HOST = "./config"
DATA_HOST = "./data"

CONFIG_CONTAINER = "/etc/searxng/settings.yml"


def run(command, check=True, capture=False, input_data=None):
    """Run a system command."""
    print(f"$ {' '.join(command)}")

    result = subprocess.run(
        command,
        input=input_data,
        text=True,
        capture_output=capture,
    )

    if check and result.returncode != 0:
        if capture:
            print(result.stdout)
            print(result.stderr, file=sys.stderr)

        sys.exit(result.returncode)

    return result


def docker_exec(command, capture=True):
    """Run a command inside the container."""
    return run(
        [
            "docker",
            "exec",
            CONTAINER,
            "sh",
            "-c",
            command,
        ],
        capture=capture,
    )


def container_exists():
    """Check if the container exists."""
    result = subprocess.run(
        [
            "docker",
            "ps",
            "-a",
            "--format",
            "{{.Names}}",
        ],
        capture_output=True,
        text=True,
    )

    return CONTAINER in result.stdout.splitlines()


def container_running():
    """Check if the container is running."""
    result = subprocess.run(
        [
            "docker",
            "ps",
            "--format",
            "{{.Names}}",
        ],
        capture_output=True,
        text=True,
    )

    return CONTAINER in result.stdout.splitlines()


def modify_config(content):
    """
    Modify settings.yml without removing
    the other existing parameters.
    """

    lines = content.splitlines()

    # -----------------------------------------------------
    # Add limiter: false in the server section
    # -----------------------------------------------------

    if not any(line.strip().startswith("limiter:") for line in lines):

        server_index = None

        for i, line in enumerate(lines):
            if line.strip() == "server:":
                server_index = i
                break

        if server_index is not None:

            insert_index = server_index + 1

            while insert_index < len(lines):

                line = lines[insert_index]

                # New YAML section
                if line and not line.startswith(" "):
                    break

                insert_index += 1

            lines.insert(insert_index, "  limiter: false")

    # -----------------------------------------------------
    # Add search.formats
    # -----------------------------------------------------

    search_index = None

    for i, line in enumerate(lines):
        if line.strip() == "search:":
            search_index = i
            break

    if search_index is None:

        if lines and lines[-1].strip():
            lines.append("")

        lines.extend([
            "search:",
            "  formats:",
            "    - html",
            "    - json",
        ])

    else:

        # Check if formats already exists
        formats_index = None

        for i in range(search_index + 1, len(lines)):

            line = lines[i]

            # New section
            if line and not line.startswith(" "):
                break

            if line.strip() == "formats:":
                formats_index = i
                break

        if formats_index is None:

            lines.insert(
                search_index + 1,
                "  formats:"
            )

            lines.insert(
                search_index + 2,
                "    - html"
            )

            lines.insert(
                search_index + 3,
                "    - json"
            )

        else:

            # Check if json is already present
            json_exists = False

            for i in range(formats_index + 1, len(lines)):

                line = lines[i]

                if line and not line.startswith(" "):
                    break

                if line.strip() == "- json":
                    json_exists = True
                    break

            if not json_exists:
                lines.insert(
                    formats_index + 2,
                    "    - json"
                )

    return "\n".join(lines) + "\n"


# =========================================================
# INSTALLATION
# =========================================================

print()
print("=" * 60)
print("SearXNG Installation")
print("=" * 60)


# ---------------------------------------------------------
# 1. Create the directories
# ---------------------------------------------------------

print()
print("[1/7] Creating directories...")

run(["mkdir", "-p", CONFIG_HOST])
run(["mkdir", "-p", DATA_HOST])


# ---------------------------------------------------------
# 2. Pull the image
# ---------------------------------------------------------

print()
print("[2/7] Downloading the SearXNG image...")

run([
    "docker",
    "pull",
    IMAGE,
])


# ---------------------------------------------------------
# 3. Remove the old container
# ---------------------------------------------------------

print()
print("[3/7] Checking for an old container...")

if container_exists():

    print(f"The container '{CONTAINER}' already exists.")

    if container_running():
        print("Stopping the container...")
        run([
            "docker",
            "stop",
            CONTAINER,
        ])

    print("Removing the container...")
    run([
        "docker",
        "rm",
        CONTAINER,
    ])

else:

    print("No old container.")


# ---------------------------------------------------------
# 4. Create the container
# ---------------------------------------------------------

print()
print("[4/7] Creating the SearXNG container...")

run([
    "docker",
    "run",
    "-d",
    "--name",
    CONTAINER,
    "-p",
    f"{HOST_PORT}:{CONTAINER_PORT}",
    "-v",
    f"{CONFIG_HOST}:/etc/searxng/",
    "-v",
    f"{DATA_HOST}:/var/cache/searxng/",
    IMAGE,
])


# ---------------------------------------------------------
# 5. Wait for the container to start
# ---------------------------------------------------------

print()
print("[5/7] Waiting for SearXNG to start...")

for i in range(10):

    if container_running():
        break

    time.sleep(1)

else:

    print("Error: SearXNG did not start.")

    run([
        "docker",
        "logs",
        CONTAINER,
    ])

    sys.exit(1)


# ---------------------------------------------------------
# 6. Modify the configuration
# ---------------------------------------------------------

print()
print("[6/7] Modifying settings.yml...")

result = docker_exec(
    f"cat {CONFIG_CONTAINER}"
)

current_config = result.stdout

print()
print("Current configuration:")
print("-" * 60)
print(current_config)
print("-" * 60)


new_config = modify_config(current_config)

print()
print("New configuration:")
print("-" * 60)
print(new_config)
print("-" * 60)


# Write into the container
run(
    [
        "docker",
        "exec",
        "-i",
        CONTAINER,
        "sh",
        "-c",
        f"cat > {CONFIG_CONTAINER}",
    ],
    input_data=new_config,
)


# ---------------------------------------------------------
# Restart
# ---------------------------------------------------------

print()
print("Restarting SearXNG...")

run([
    "docker",
    "restart",
    CONTAINER,
])

time.sleep(5)


# ---------------------------------------------------------
# 7. Test
# ---------------------------------------------------------

print()
print("[7/7] Testing the JSON API...")

result = run(
    [
        "curl",
        "-s",
        "-w",
        "\nHTTP_STATUS:%{http_code}",
        "http://127.0.0.1:8888/search?q=test&format=json",
    ],
    capture=True,
)

response = result.stdout

print()
print(response)


if "HTTP_STATUS:200" in response:

    print()
    print("=" * 60)
    print("SearXNG is installed and working correctly.")
    print("=" * 60)

else:

    print()
    print("=" * 60)
    print("ERROR: the SearXNG API does not respond with HTTP 200.")
    print("=" * 60)

    print()
    print("Container logs:")

    run([
        "docker",
        "logs",
        "--tail",
        "50",
        CONTAINER,
    ])

    sys.exit(1)

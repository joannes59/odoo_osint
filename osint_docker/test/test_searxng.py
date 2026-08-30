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
    """Exécute une commande système."""
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
    """Exécute une commande dans le conteneur."""
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
    """Vérifie si le conteneur existe."""
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
    """Vérifie si le conteneur est en fonctionnement."""
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
    Modifie settings.yml sans supprimer
    les autres paramètres existants.
    """

    lines = content.splitlines()

    # -----------------------------------------------------
    # Ajouter limiter: false dans server
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

                # Nouvelle section YAML
                if line and not line.startswith(" "):
                    break

                insert_index += 1

            lines.insert(insert_index, "  limiter: false")

    # -----------------------------------------------------
    # Ajouter search.formats
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

        # Vérifier si formats existe déjà
        formats_index = None

        for i in range(search_index + 1, len(lines)):

            line = lines[i]

            # Nouvelle section
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

            # Vérifier si json est déjà présent
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
print("Installation de SearXNG")
print("=" * 60)


# ---------------------------------------------------------
# 1. Création des répertoires
# ---------------------------------------------------------

print()
print("[1/7] Création des répertoires...")

run(["mkdir", "-p", CONFIG_HOST])
run(["mkdir", "-p", DATA_HOST])


# ---------------------------------------------------------
# 2. Pull de l'image
# ---------------------------------------------------------

print()
print("[2/7] Téléchargement de l'image SearXNG...")

run([
    "docker",
    "pull",
    IMAGE,
])


# ---------------------------------------------------------
# 3. Suppression de l'ancien conteneur
# ---------------------------------------------------------

print()
print("[3/7] Vérification de l'ancien conteneur...")

if container_exists():

    print(f"Le conteneur '{CONTAINER}' existe déjà.")

    if container_running():
        print("Arrêt du conteneur...")
        run([
            "docker",
            "stop",
            CONTAINER,
        ])

    print("Suppression du conteneur...")
    run([
        "docker",
        "rm",
        CONTAINER,
    ])

else:

    print("Aucun ancien conteneur.")


# ---------------------------------------------------------
# 4. Création du conteneur
# ---------------------------------------------------------

print()
print("[4/7] Création du conteneur SearXNG...")

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
# 5. Attente du démarrage
# ---------------------------------------------------------

print()
print("[5/7] Attente du démarrage de SearXNG...")

for i in range(10):

    if container_running():
        break

    time.sleep(1)

else:

    print("Erreur : SearXNG n'a pas démarré.")

    run([
        "docker",
        "logs",
        CONTAINER,
    ])

    sys.exit(1)


# ---------------------------------------------------------
# 6. Modification de la configuration
# ---------------------------------------------------------

print()
print("[6/7] Modification de settings.yml...")

result = docker_exec(
    f"cat {CONFIG_CONTAINER}"
)

current_config = result.stdout

print()
print("Configuration actuelle :")
print("-" * 60)
print(current_config)
print("-" * 60)


new_config = modify_config(current_config)

print()
print("Nouvelle configuration :")
print("-" * 60)
print(new_config)
print("-" * 60)


# Écriture dans le conteneur
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
# Redémarrage
# ---------------------------------------------------------

print()
print("Redémarrage de SearXNG...")

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
print("[7/7] Test de l'API JSON...")

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
    print("SearXNG est installé et fonctionne correctement.")
    print("=" * 60)

else:

    print()
    print("=" * 60)
    print("ERREUR : l'API SearXNG ne répond pas avec HTTP 200.")
    print("=" * 60)

    print()
    print("Logs du conteneur :")

    run([
        "docker",
        "logs",
        "--tail",
        "50",
        CONTAINER,
    ])

    sys.exit(1)

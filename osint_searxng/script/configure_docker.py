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
# 1. Lire la configuration actuelle
# ---------------------------------------------------------

print(f"Lecture de {CONFIG} dans {CONTAINER}...")

content = docker_exec(f"cat {CONFIG}")

print("Configuration actuelle :")
print("----------------------------------------")
print(content)
print("----------------------------------------")


# ---------------------------------------------------------
# 2. Ajouter/modifier search.formats
# ---------------------------------------------------------

lines = content.splitlines()

# Supprimer une éventuelle ancienne section "formats"
# sous "search", puis reconstruire proprement la section.
#
# Pour ta configuration actuelle, search n'existe pas,
# donc on ajoute simplement la section.

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
    print("Une section 'search' existe déjà.")
    print("Aucune modification automatique de cette section n'est effectuée.")


# ---------------------------------------------------------
# 3. Ajouter limiter: false dans server
# ---------------------------------------------------------

if "limiter:" not in content:
    lines = content.splitlines()

    server_index = None

    for i, line in enumerate(lines):
        if line.strip() == "server:":
            server_index = i
            break

    if server_index is not None:
        # Chercher la fin de la section server
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
# 4. Afficher la nouvelle configuration
# ---------------------------------------------------------

print("Nouvelle configuration :")
print("----------------------------------------")
print(content)
print("----------------------------------------")


# ---------------------------------------------------------
# 5. Sauvegarder dans le conteneur
# ---------------------------------------------------------

# Utilisation de stdin pour éviter les problèmes
# d'échappement avec docker exec.
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
    print("Erreur lors de l'écriture du fichier.", file=sys.stderr)
    sys.exit(process.returncode)

print("Configuration sauvegardée.")


# ---------------------------------------------------------
# 6. Redémarrer SearXNG
# ---------------------------------------------------------

print("Redémarrage de SearXNG...")

result = subprocess.run(
    ["docker", "restart", CONTAINER],
    capture_output=True,
    text=True,
)

if result.returncode != 0:
    print(result.stderr, file=sys.stderr)
    sys.exit(result.returncode)

print("SearXNG redémarré.")


# ---------------------------------------------------------
# 7. Afficher la configuration finale
# ---------------------------------------------------------

print()
print("Configuration finale :")
print("----------------------------------------")

final_content = docker_exec(f"cat {CONFIG}")
print(final_content)

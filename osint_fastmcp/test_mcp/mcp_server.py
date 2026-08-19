from pathlib import Path

from fastmcp import FastMCP


# Répertoire autorisé
ROOT = Path.home() #/ "mcp-test" / "files"
ROOT.mkdir(parents=True, exist_ok=True)

mcp = FastMCP("Filesystem")


def safe_path(path: str) -> Path:
    """Empêche de sortir du répertoire ROOT."""
    target = (ROOT / path).resolve()

    if not target.is_relative_to(ROOT.resolve()):
        raise ValueError("Accès interdit en dehors du répertoire autorisé")

    return target


@mcp.tool()
def list_files(path: str = ".") -> list[str]:
    """Liste les fichiers et répertoires."""
    directory = safe_path(path)

    if not directory.is_dir():
        raise ValueError("Ce n'est pas un répertoire")

    return [
        item.name
        for item in directory.iterdir()
    ]


@mcp.tool()
def read_file(path: str) -> str:
    """Lit le contenu d'un fichier texte."""
    file = safe_path(path)

    if not file.is_file():
        raise ValueError("Fichier introuvable")

    return file.read_text(encoding="utf-8")


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Écrit un fichier texte."""
    file = safe_path(path)

    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content, encoding="utf-8")

    return f"Fichier écrit : {path}"


@mcp.tool()
def delete_file(path: str) -> str:
    """Supprime un fichier."""
    file = safe_path(path)

    if not file.is_file():
        raise ValueError("Fichier introuvable")

    file.unlink()

    return f"Fichier supprimé : {path}"


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000)


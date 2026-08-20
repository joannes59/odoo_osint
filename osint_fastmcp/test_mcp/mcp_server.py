from pathlib import Path

from fastmcp import FastMCP


# Authorized directory
ROOT = Path.home() #/ "mcp-test" / "files"
ROOT.mkdir(parents=True, exist_ok=True)

mcp = FastMCP("Filesystem")


def safe_path(path: str) -> Path:
    """Prevents escaping the ROOT directory."""
    target = (ROOT / path).resolve()

    if not target.is_relative_to(ROOT.resolve()):
        raise ValueError("Access forbidden outside the authorized directory")

    return target


@mcp.tool()
def list_files(path: str = ".") -> list[str]:
    """Lists files and directories."""
    directory = safe_path(path)

    if not directory.is_dir():
        raise ValueError("This is not a directory")

    return [
        item.name
        for item in directory.iterdir()
    ]


@mcp.tool()
def read_file(path: str) -> str:
    """Reads the content of a text file."""
    file = safe_path(path)

    if not file.is_file():
        raise ValueError("File not found")

    return file.read_text(encoding="utf-8")


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Writes a text file."""
    file = safe_path(path)

    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content, encoding="utf-8")

    return f"File written: {path}"


@mcp.tool()
def delete_file(path: str) -> str:
    """Deletes a file."""
    file = safe_path(path)

    if not file.is_file():
        raise ValueError("File not found")

    file.unlink()

    return f"File deleted: {path}"


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000)


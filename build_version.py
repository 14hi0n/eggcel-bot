import tomllib
from pathlib import Path

_PROJECT_FILE = Path(__file__).resolve().parent / "pyproject.toml"


with _PROJECT_FILE.open("rb") as file:
    APP_VERSION: str = tomllib.load(file)["project"]["version"]

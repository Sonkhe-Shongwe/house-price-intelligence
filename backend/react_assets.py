"""Load the bounded, compiled React frontend for the fictional localhost app."""
from pathlib import Path
import re

DIST = Path(__file__).resolve().parents[1] / "frontend" / "react" / "dist"
ASSET_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,100}-[A-Za-z0-9_-]{6,}\.(?:js|css)$")
MIME_TYPES = {".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8"}

def load_react_assets(directory: Path = DIST) -> dict[str, tuple[bytes, str]]:
    directory = directory.resolve(strict=True)
    index = directory / "index.html"
    generated = directory / "assets"
    if index.is_symlink() or not index.is_file() or generated.is_symlink() or not generated.is_dir():
        raise ValueError("Missing trusted React production build")
    html = index.read_bytes(), "text/html; charset=utf-8"
    assets = {"/": html, "/buyer-workflow": html}
    for entry in generated.iterdir():
        if entry.is_symlink() or not entry.is_file() or not ASSET_NAME.fullmatch(entry.name):
            raise ValueError("Unexpected React build asset")
        assets["/assets/" + entry.name] = entry.read_bytes(), MIME_TYPES[entry.suffix]
    if not any(path.endswith(".js") for path in assets):
        raise ValueError("React build contains no JavaScript")
    return assets

import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

HOST = "127.0.0.1"
PORT = 7860
WEB_DIR = Path(__file__).parent / "web"
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
TILE_PROVIDER = "auto"  # auto | thunderforest | cyclosm


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/tiles/cycle/"):
            self._serve_cycle_tile(parsed.path)
            return
        super().do_GET()

    def _serve_cycle_tile(self, path: str) -> None:
        # Expected path format: /tiles/cycle/{z}/{x}/{y}.png
        parts = path.strip("/").split("/")
        if len(parts) != 5 or parts[0] != "tiles" or parts[1] != "cycle":
            self.send_error(404, "Invalid tile path")
            return

        z, x, y_file = parts[2], parts[3], parts[4]
        if not y_file.endswith(".png"):
            self.send_error(404, "Invalid tile format")
            return
        y = y_file[:-4]

        global TILE_PROVIDER

        key = os.getenv("THUNDERFOREST_API_KEY", "").strip()
        thunderforest = f"https://tile.thunderforest.com/cycle/{z}/{x}/{y}.png?apikey={key}"
        cyclosm = f"https://a.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png"

        # Lock to one provider for the whole session to avoid mixed/patchy tiles.
        # If Thunderforest fails once, switch permanently to CyclOSM.
        if TILE_PROVIDER == "auto":
            TILE_PROVIDER = "thunderforest" if key else "cyclosm"

        upstreams = [thunderforest] if TILE_PROVIDER == "thunderforest" else [cyclosm]

        for upstream in upstreams:
            request = Request(
                upstream,
                headers={
                    "User-Agent": "book-track-campus-map/1.0",
                    "Accept": "image/png,image/*;q=0.8,*/*;q=0.5",
                },
            )
            try:
                with urlopen(request, timeout=15) as response:
                    body = response.read()
                    content_type = response.headers.get("Content-Type", "image/png")
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", str(len(body)))
                    self.send_header("Cache-Control", "public, max-age=300")
                    self.send_header(
                        "X-Tile-Source",
                        "thunderforest" if "thunderforest.com" in upstream else "cyclosm",
                    )
                    self.end_headers()
                    self.wfile.write(body)
                    return
            except (HTTPError, URLError):
                if TILE_PROVIDER == "thunderforest":
                    TILE_PROVIDER = "cyclosm"
                    self.send_response(302)
                    self.send_header("Location", cyclosm)
                    self.end_headers()
                    return
                self.send_error(502, "Tile upstream unavailable")
                return


def main() -> None:
    global TILE_PROVIDER
    load_env_file(ENV_FILE)
    key = os.getenv("THUNDERFOREST_API_KEY", "").strip()
    TILE_PROVIDER = "thunderforest" if key else "cyclosm"
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print(f"Campus map prototype running at http://{HOST}:{PORT}")
    print(f"Serving files from: {WEB_DIR}")
    print(
        "Thunderforest key loaded (server-side only): "
        + ("YES" if key else "NO (CyclOSM fallback only)")
    )
    print(f"Tile provider mode: {TILE_PROVIDER}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

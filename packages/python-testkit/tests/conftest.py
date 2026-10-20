import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def gallery_url() -> str:
    repository = Path(__file__).resolve().parents[3]
    handler = partial(SimpleHTTPRequestHandler, directory=repository)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/examples/component-gallery/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

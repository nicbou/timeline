from functools import partial
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread
import logging
import socketserver


class HttpRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def do_GET(self):
        abs_path = Path(self.directory) / self.path.removeprefix('/')
        abs_html_path = abs_path.with_suffix('.html')
        abs_index_path = abs_path / 'index.html'

        if not abs_path.exists():
            if abs_path.suffix == '' and abs_html_path.exists():
                self.path = str(abs_html_path.relative_to(self.directory))
            elif abs_index_path.exists():
                self.path = str(abs_index_path.relative_to(self.directory))
        return super().do_GET()

    def log_message(self, format, *args):
        logging.debug(f"Request to {self.path}")


def serve(directory: Path, port: int = 80):
    """Start a static file server that serves Ursus on the given port.

    Args:
        port (int, optional): The port on which to serve the static site. Default is port 80.
    """
    request_handler = partial(HttpRequestHandler, directory=directory)
    with socketserver.ThreadingTCPServer(("", port), request_handler) as server:
        logging.info(f"Serving {directory} on port {port}")
        server.serve_forever()


def serve_async(directory: Path, port: int = 80):
    serve_func = partial(serve, directory)
    thread = Thread(target=serve_func, args=(port, ), daemon=True)
    thread.start()
    return thread

import os
import threading
import webbrowser
import BaseHTTPServer
import SimpleHTTPServer

PORT = 8081

def open_browser():
    """Start a browser after waiting for half a second."""
    def _open_browser():
        webbrowser.open('http://localhost:%s/index.html' % PORT)
    thread = threading.Timer(0.5, _open_browser)
    thread.start()

def start_server():
    """Start the server."""
    server_address = ("", PORT)
    handler_class = SimpleHTTPServer.SimpleHTTPRequestHandler
    handler_class.extensions_map['.png'] = 'image/png'
    server = BaseHTTPServer.HTTPServer(server_address, handler_class)
    server.serve_forever()

if __name__ == "__main__":
    open_browser() # Comment out this line if you don't want to open a browser
    start_server()
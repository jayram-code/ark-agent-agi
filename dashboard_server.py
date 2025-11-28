import http.server
import socketserver
import os
import webbrowser

PORT = 8001
DIRECTORY = "dashboard"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def run_server():
    # Change to the parent directory of 'dashboard' if needed, 
    # but since we set directory=DIRECTORY in Handler, we can run from root.
    
    print(f"Starting Dashboard Server on port {PORT}...")
    print(f"Serving directory: {os.path.abspath(DIRECTORY)}")
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Dashboard is live at http://localhost:{PORT}")
        # Open browser automatically
        webbrowser.open(f"http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    run_server()

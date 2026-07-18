import http.server
import json
import subprocess
import sys
import os

PORT = 8080

class BridgeHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Override to log requests directly to stdout
        sys.stdout.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format%args))
        sys.stdout.flush()

    def do_POST(self):
        if self.path == '/cli':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                args = data.get('args', [])
                session = data.get('session', 'default')
                
                # Build command: playwright-cli -s=session args
                cmd = ['playwright-cli']
                if session:
                    cmd.append(f'-s={session}')
                cmd.extend(args)
                
                print(f"Executing: {' '.join(cmd)}", flush=True)
                
                # Run the command with shell=True and explicit utf-8 encoding on Windows
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    shell=True
                )
                
                response = {
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': result.returncode
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
            except Exception as e:
                print(f"Error handling request: {e}", flush=True)
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run(server_class=http.server.HTTPServer, handler_class=BridgeHandler):
    server_address = ('127.0.0.1', PORT)
    httpd = server_class(server_address, handler_class)
    print(f"Starting playwright-cli bridge server on http://127.0.0.1:{PORT}...", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        print("Server stopped.", flush=True)

if __name__ == '__main__':
    run()

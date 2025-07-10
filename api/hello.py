# Simple serverless function for Vercel
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "message": "Hello from Vercel Python!",
            "status": "success"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "message": "POST received",
            "data": post_data.decode() if post_data else None,
            "status": "success"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return

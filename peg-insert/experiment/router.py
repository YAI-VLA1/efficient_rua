"""Local OpenRouter proxy recording billable usage and completion hashes."""
import hashlib
import json
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock

key = (Path.home()/'.openrouter-key').read_text().strip()
ledger = Path(__file__).with_name('router-usage.jsonl')
lock = Lock()
class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions', data=body,
            headers={'Authorization': 'Bearer '+key, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=210) as res:
                data = res.read()
            payload = json.loads(data)
            content = payload['choices'][0]['message'].get('content') or ''
            record = dict(id=payload['id'], provider=payload.get('provider'), usage=payload.get('usage'),
                sha256=hashlib.sha256(content.encode()).hexdigest())
            with lock, ledger.open('a') as f:
                print(json.dumps(record),file=f)
            status = 200
        except urllib.error.HTTPError as e:
            status, data = e.code, e.read()
        except Exception as e:
            status, data = 502, json.dumps({'error':type(e).__name__}).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json')
        self.end_headers()
        self.wfile.write(data)
ThreadingHTTPServer(('127.0.0.1',8110),Handler).serve_forever()

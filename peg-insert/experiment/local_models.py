"""Bridge the CaP-X request to vLLM or an independent Codex CLI session."""
import hashlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import tempfile
import urllib.request

here = Path(__file__).parent
def astra(req):
    system, user = req['messages']
    assert system['role']=='system' and user['role']=='user'
    prompt = user['content']
    if isinstance(prompt,list):
        prompt = '\n'.join(part['text'] for part in prompt)
    with tempfile.TemporaryDirectory() as folder:
        # Ephemeral sessions have no access to earlier experimental conversations.
        instructions = Path(folder)/'instruction.txt'
        instructions.write_text(system['content'])
        result = subprocess.run(['codex','exec','--ephemeral','--ignore-user-config',
            '--skip-git-repo-check','--sandbox','read-only','-m','gpt-6-astra',
            '-c','model_reasoning_effort="medium"','-c',f'model_instructions_file="{instructions}"',
            '--json','-'],input=prompt,text=True,cwd=folder,capture_output=True,timeout=185)
        result.check_returncode()
        events = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
        items = [e['item'] for e in events if e['type']=='item.completed']
        if any(it['type'] not in ('agent_message','reasoning') for it in items):
            raise ValueError('External tool use in reference trial')
        content = [it['text'] for it in items if it['type']=='agent_message'][-1]
        usage = next(e['usage'] for e in events if e['type']=='turn.completed')
        return {'choices':[{'message':{'content':content}}],'usage':{
            'prompt_tokens':usage['input_tokens'],'completion_tokens':usage['output_tokens'],'cost':None}}
class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            req = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            if req['model']=='gpt-6-astra':
                out = astra(req)
            else:
                forward = urllib.request.Request('http://127.0.0.1:8113/v1/chat/completions',
                    data=json.dumps(req).encode(),headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(forward,timeout=180) as r:
                    out = json.load(r)
            content = out['choices'][0]['message']['content']
            row = dict(model=req['model'],sha256=hashlib.sha256(content.encode()).hexdigest(),usage=out['usage'])
            with (here/'local-usage.jsonl').open('a') as f:
                print(json.dumps(row),file=f)
            status, data = 200,json.dumps(out).encode()
        except Exception as e:
            status, data = 422,str(e).encode()
            print('Request failure:',e,flush=True)
        self.send_response(status)
        self.end_headers()
        self.wfile.write(data)
ThreadingHTTPServer(('127.0.0.1',8112),Handler).serve_forever()

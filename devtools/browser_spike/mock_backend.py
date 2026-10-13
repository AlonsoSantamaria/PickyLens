"""Loopback-only deterministic endpoint. No application/provider imports."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args): pass
 def do_POST(self):
  try:
   if self.path != '/probe/review': raise ValueError()
   length=int(self.headers.get('Content-Length','0'))
   if not 0 < length <= 25000: raise ValueError()
   data=json.loads(self.rfile.read(length))
   if set(data)!={'text'} or not isinstance(data['text'],str) or len(data['text'])>20000: raise ValueError()
   body=json.dumps({'kind':'deterministic-probe','message':'Local mock review received. Request preserved; no AI evaluation.'}).encode()
   self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(body)
  except (ValueError,TypeError): self.send_response(400);self.end_headers()
if __name__=='__main__': ThreadingHTTPServer(('127.0.0.1',8033),Handler).serve_forever()

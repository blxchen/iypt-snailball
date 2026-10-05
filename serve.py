"""SnailLab static frontend and standard-library JSON API. python3 serve.py"""
import argparse
import http.server
import json
import pathlib
from urllib.parse import urlsplit
from backend.model import simulate
from backend.measurements import analyze, interval
from backend.flow import gap_flow

ROOT=pathlib.Path(__file__).parent.resolve()
MAX_BODY=2_000_000

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(ROOT),**kwargs)

    def end_headers(self):
        # Revalidate local modules so edits cannot leave mixed worker protocols.
        if self.command in ('GET','HEAD') and not urlsplit(self.path).path.startswith('/api/'):
            self.send_header('Cache-Control','no-cache')
        super().end_headers()

    def send_json(self,status,payload):
        body=json.dumps(payload,allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/api/health':
            return self.send_json(200,dict(status='ready',backend='Python standard library',version=2))
        if path.startswith('/api/'):
            return self.send_json(404,dict(error='Unknown API endpoint.'))
        super().do_GET()

    def do_POST(self):
        path=urlsplit(self.path).path
        if path not in ('/api/simulate','/api/analyze','/api/measure','/api/flow'):
            return self.send_json(404,dict(error='Unknown API endpoint.'))
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<=0 or length>MAX_BODY:
                return self.send_json(413,dict(error='Provide a JSON body smaller than 2 MB.'))
            payload=json.loads(self.rfile.read(length))
            if not isinstance(payload,dict):
                raise ValueError('Request body must be a JSON object.')
            if path=='/api/simulate':
                result=simulate(payload.get('parameters'),payload.get('timestamps'))
            elif path=='/api/flow':
                result=gap_flow(payload)
            elif path=='/api/analyze':
                result=analyze(payload)
                if payload.get('compare_model'):
                    model=simulate(payload.get('parameters'))
                    matched=[z for z in result['data'] if 0<=z['t']<=model['parameters']['duration']]
                    residuals=[dict(t=z['t'],x=z['x']-interpolate_model(model,z['t'])['x'],
                                    v=z['v']-interpolate_model(model,z['t'])['v']) for z in matched]
                    result['comparison']=dict(samples=len(matched),parameters=model['parameters'],
                        position_rmse=(sum(z['x']**2 for z in residuals)/len(matched))**.5 if matched else None,
                        velocity_rmse=(sum(z['v']**2 for z in residuals)/len(matched))**.5 if matched else None,
                        residuals=residuals)
            else:
                result=interval(payload)
            self.send_json(200,result)
        except (ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError) as error:
            self.send_json(400,dict(error=str(error)))


def interpolate_model(model,t):
    from backend.model import interpolate
    return interpolate(model['data'],t)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8000)
    args=parser.parse_args()
    server=http.server.ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'SnailLab is available at http://localhost:{args.port} (Python API enabled)',flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__=='__main__':
    main()

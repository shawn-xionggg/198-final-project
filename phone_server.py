"""Local HTTPS iPhone camera receiver. Run with --help."""
import argparse
import ipaddress
import json
from pathlib import Path
import secrets
import ssl
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from squat_counter import knee_angle
from exercise_logic import ExerciseTracker

BASE = Path(__file__).resolve().parent
MAX_FRAME = 300_000


class Engine:
    def __init__(self, args):
        import cv2
        import numpy as np
        from ultralytics import YOLO
        self.cv2, self.np = cv2, np
        self.model = YOLO(args.model)
        self.tracker = ExerciseTracker(args.config)
        self.side = args.side
        self.last_frame = time.monotonic()
        self.lock = threading.Lock()
        self.link = None
        self.mode_generation = 0
        if args.port:
            from exercise_link import ExerciseLink
            self.link = ExerciseLink(args.port)
        self.stop_event = threading.Event()
        self.controls_thread = threading.Thread(target=self.controls, daemon=True)
        self.controls_thread.start()

    def poll_mode(self):
        if self.link:
            mode = self.link.poll_mode()
            if mode:
                if self.link.mode_changed:
                    self.mode_generation += 1
                    self.tracker.cancel()
                    self.tracker.result, self.tracker.duration = 'NONE', None
                self.tracker.set_mode(mode)

    def snapshot(self):
        data = self.tracker.snapshot()
        data['warning'] = getattr(self.link, 'error', None)
        data['targets'] = self.tracker.config[self.tracker.mode]
        return data

    def send(self):
        if self.link:
            self.link.update(self.tracker.snapshot())

    def reset(self):
        self.tracker.reset()
        self.send()
        return self.snapshot()

    def controls(self):
        while not self.stop_event.wait(0.05):
            if not self.lock.acquire(blocking=False):
                continue
            try:
                self.poll_mode()
                if time.monotonic() - self.last_frame > 1.5:
                    self.tracker.update(None, time.monotonic())
                self.send()
            finally:
                self.lock.release()

    def close(self):
        self.stop_event.set()
        self.controls_thread.join(timeout=2)
        if self.link:
            self.link.close()

    def frame(self, raw):
        frame = self.cv2.imdecode(self.np.frombuffer(raw,dtype=self.np.uint8),self.cv2.IMREAD_COLOR)
        if frame is None or max(frame.shape[:2])>1280:
            raise ValueError('Invalid or oversized image')
        self.poll_mode()
        mode = self.tracker.mode
        generation = self.mode_generation
        result = self.model.predict(frame,verbose=False,conf=0.5)[0]
        now = time.monotonic()
        self.last_frame = now
        self.poll_mode()
        if self.mode_generation != generation:
            self.send()
            return self.snapshot()  # Discard a frame captured for the old exercise.
        indices = ((11,13,15) if self.side=='left' else (12,14,16)) if mode=='SQUAT' else ((5,7,9) if self.side=='left' else (6,8,10))
        angle=None
        if result.keypoints is not None and len(result.keypoints)==1:
            points=result.keypoints.data[0].cpu().tolist()
            joints=[points[i] for i in indices]
            if all(len(p)>=3 and p[2]>=0.5 for p in joints):
                angle=knee_angle(*joints)
        self.tracker.update(angle,now)
        self.send()
        return self.snapshot()


def handler(engine, token, origin):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass  # Never log session codes or camera data.

        def setup(self):
            super().setup()
            self.connection.settimeout(15)

        def reply(self, status, data, mime='application/json'):
            if not isinstance(data,bytes): data=json.dumps(data).encode()
            self.send_response(status)
            self.send_header('Content-Type',mime)
            self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('Permissions-Policy','camera=(self), microphone=()')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path=='/': self.reply(200,(BASE/'phone_camera.html').read_bytes(),'text/html; charset=utf-8')
            else: self.reply(404,{'error':'Not found'})

        def do_POST(self):
            if not secrets.compare_digest(self.headers.get('X-Session-Code',''),token):
                self.reply(401,{'error':'Session code required'}); return
            if self.headers.get('Origin',origin)!=origin:
                self.reply(403,{'error':'Wrong origin'}); return
            if self.path not in ('/frame','/reset','/status'):
                self.reply(404,{'error':'Not found'}); return
            try: size=int(self.headers.get('Content-Length','-1'))
            except ValueError: size=-1
            if size<0 or size>MAX_FRAME:
                self.reply(413,{'error':'Invalid size'}); return
            raw=self.rfile.read(size)
            if len(raw)!=size:
                self.reply(400,{'error':'Incomplete request'}); return
            if not engine.lock.acquire(timeout=0.1):
                self.reply(409,{'error':'Busy'}); return
            try:
                if self.path=='/reset':
                    data=engine.reset()
                elif self.path=='/status':
                    data=engine.snapshot()
                else:
                    if self.headers.get('Content-Type')!='image/jpeg' or not raw.startswith(b'\xff\xd8'):
                        raise ValueError('Expected JPEG')
                    data=engine.frame(raw)
                self.reply(200,data)
            except ValueError as error:
                self.reply(400,{'error':str(error)})
            except Exception as error:
                print(f'Processing error: {error}',flush=True)
                self.reply(500,{'error':'Processing failed; see laptop terminal'})
            finally:
                engine.lock.release()
    return Handler


def pair_handler(cert, code):
    class Pair(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_GET(self):
            if self.path!=f'/{code}/phone-root.cer':
                self.send_error(404);return
            data=cert.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type','application/x-x509-ca-cert')
            self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','no-store')
            self.end_headers()
            self.wfile.write(data)
    return Pair


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host',required=True,help='Laptop hotspot IPv4 address from ipconfig')
    p.add_argument('--port',help='Arduino COM port (optional)')
    p.add_argument('--side',choices=['left','right'],default='left')
    p.add_argument('--down',type=float,help='Optional squat target override')
    p.add_argument('--up',type=float,help='Optional squat starting-angle override')
    p.add_argument('--config',default=str(BASE/'exercise_config.json'),help='Range and whole-rep timing settings')
    p.add_argument('--model',default=str(BASE/'yolo26n-pose.pt'))
    p.add_argument('--pair',action='store_true',help='Serve public certificate on HTTP 8080 for 10 minutes')
    args=p.parse_args()
    try: address=ipaddress.IPv4Address(args.host)
    except ValueError: p.error('Use your laptop IPv4 address')
    if not (address.is_private and not address.is_unspecified and not address.is_multicast):
        p.error('Use a private local IPv4 address, not a public or wildcard address')
    try:
        args.config=json.loads(Path(args.config).read_text(encoding='utf-8'))
        if args.down is not None: args.config['SQUAT']['target_angle']=args.down
        if args.up is not None: args.config['SQUAT']['start_angle']=args.up
        ExerciseTracker(args.config)
    except (OSError, ValueError, TypeError, KeyError) as error:
        p.error(f'Invalid exercise settings: {error}')
    from phone_tls import certificates
    folder=BASE/'.phone-tls'
    cert,fingerprint=certificates(folder,args.host)
    token=secrets.token_urlsafe(24)
    origin=f'https://{args.host}:8443'
    engine=Engine(args)
    server=None
    pair=None
    try:
        server=ThreadingHTTPServer((args.host,8443),handler(engine,token,origin))
        ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.minimum_version=ssl.TLSVersion.TLSv1_2
        ctx.load_cert_chain(folder/'server.pem',folder/'server-key.pem')
        server.socket=ctx.wrap_socket(server.socket,server_side=True)
        if args.pair:
            code=secrets.token_urlsafe(12)
            pair=ThreadingHTTPServer((args.host,8080),pair_handler(cert,code))
            threading.Thread(target=pair.serve_forever,daemon=True).start()
            timer=threading.Timer(600,lambda:(pair.shutdown(),pair.server_close()))
            timer.daemon=True
            timer.start()
            print(f'ONE-TIME CERTIFICATE: http://{args.host}:8080/{code}/phone-root.cer',flush=True)
            print(f'Certificate SHA256: {fingerprint}',flush=True)
        print(f'CAMERA PAGE: {origin}/#token={token}',flush=True)
        print(f'Or open {origin} and paste session code: {token}',flush=True)
        print('Local receiver ready. Ctrl+C stops it. No images are saved.',flush=True)
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print('\nStopped.')
    finally:
        if server: server.server_close()
        if pair: pair.shutdown();pair.server_close()
        engine.close()


if __name__=='__main__':main()

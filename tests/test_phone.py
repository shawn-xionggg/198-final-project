import http.client
import json
from pathlib import Path
import ssl
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from types import SimpleNamespace
from phone_server import handler, pair_handler, MAX_FRAME
from phone_tls import certificates
from exercise_logic import ExerciseTracker
from cryptography import x509
from cryptography.hazmat.primitives import serialization


class PhoneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        folder=Path(cls.temp.name)
        cls.cert,_=certificates(folder,'127.0.0.1')
        cls.engine=SimpleNamespace(lock=threading.Lock(),tracker=ExerciseTracker(),link=None,
                                  frame=lambda raw:{'reps':1,'status':'Standing','angle':170})
        cls.engine.snapshot=cls.engine.tracker.snapshot
        def reset():
            cls.engine.tracker.reset()
            return cls.engine.snapshot()
        cls.engine.reset=reset
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),handler(cls.engine,'secret','https://test'))
        ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(folder/'server.pem',folder/'server-key.pem')
        cls.server.socket=ctx.wrap_socket(cls.server.socket,server_side=True)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        pem=x509.load_der_x509_certificate(cls.cert.read_bytes()).public_bytes(serialization.Encoding.PEM).decode()
        cls.client_context=ssl.create_default_context(cadata=pem)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join();cls.temp.cleanup()

    def call(self,path,body=b'',headers=None,method='POST'):
        c=http.client.HTTPSConnection('127.0.0.1',self.server.server_port,context=self.client_context,timeout=3)
        h={'X-Session-Code':'secret','Origin':'https://test','Content-Type':'image/jpeg'}
        h.update(headers or {})
        try:
            c.request(method,path,body,headers=h)
            r=c.getresponse()
            return r.status,r.read()
        finally:c.close()

    def test_trusted_https_page(self):
        status,body=self.call('/',method='GET')
        self.assertEqual(status,200)
        self.assertIn(b'Start camera',body)

    def test_token_required(self):
        self.assertEqual(self.call('/frame',b'\xff\xd8test',{'X-Session-Code':'wrong'})[0],401)

    def test_cross_origin_rejected(self):
        self.assertEqual(self.call('/frame',b'\xff\xd8test',{'Origin':'https://other'})[0],403)

    def test_frame_roundtrip(self):
        status,body=self.call('/frame',b'\xff\xd8test')
        self.assertEqual(status,200)
        self.assertEqual(json.loads(body)['reps'],1)

    def test_reset(self):
        self.engine.tracker.counts['SQUAT']['attempts']=5
        self.assertEqual(self.call('/reset')[0],200)
        self.assertEqual(self.engine.tracker.counts['SQUAT']['attempts'],0)

    def test_status(self):
        status,body=self.call('/status')
        self.assertEqual(status,200)
        self.assertIn('mode',json.loads(body))

    def test_bad_image(self):
        self.assertEqual(self.call('/frame',b'not an image')[0],400)

    def test_size_limit(self):
        self.assertEqual(self.call('/frame',headers={'Content-Length':str(MAX_FRAME+1)})[0],413)

    def test_no_private_file_serving(self):
        self.assertEqual(self.call('/.phone-tls/root-key.pem',method='GET')[0],404)

    def test_pairing_only_serves_public_cert(self):
        s=ThreadingHTTPServer(('127.0.0.1',0),pair_handler(self.cert,'pair'))
        t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
        try:
            for path,expected in [('/pair/phone-root.cer',200),('/root-key.pem',404),('/',404)]:
                c=http.client.HTTPConnection('127.0.0.1',s.server_port,timeout=3)
                c.request('GET',path);r=c.getresponse();self.assertEqual(r.status,expected);r.read();c.close()
        finally:s.shutdown();s.server_close();t.join()


if __name__=='__main__':unittest.main()

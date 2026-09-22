import json
import socket
import time
import unittest
from fixtures import Server


class HTTPTests(unittest.TestCase):
    def test_http_post_once_and_get_retry_at_most_three(self):
        with Server() as server:
            server.routes['GET','/v2/balance']=(503,{'secret':'do not expose'}, {})
            server.routes['POST','/v2/create-image-pixen']=(503,{'secret':'do not expose'}, {})
            transport=server.transport(timeout=1, retry_delay=0)
            for method,path,count in [('GET','/v2/balance',3),('POST','/v2/create-image-pixen',1)]:
                with self.assertRaisesRegex(ValueError,'http_503') as error:
                    transport.json('pixellab',method,path,body={} if method=='POST' else None,credential='fixture-secret')
                self.assertNotIn('do not expose',str(error.exception))
                self.assertEqual(sum(c[0]==method for c in server.calls),count)
    def test_http_auth_errors_malformed_json_and_error_envelopes_safe(self):
        with Server() as server:
            for status in [401,402,422,429,500]:
                server.routes['POST','/v2/create-image-pixen']=(status,b'signed secret query',{})
                with self.assertRaises(ValueError) as error:
                    server.transport(retry_delay=0).json('pixellab','POST','/v2/create-image-pixen',body={},credential='fixture-secret')
                self.assertNotIn('signed secret query',str(error.exception))
            server.routes['GET','/v2/balance']=(200,b'{broken',{})
            with self.assertRaises(ValueError): server.transport().json('pixellab','GET','/v2/balance',credential='x')
    def test_http_download_is_credential_free_and_redirect_checked(self):
        with Server() as server:
            server.routes['GET','/asset?signature=secret']=(200,b'content',{})
            transport=server.transport()
            self.assertEqual(transport.download('https://fixture-cdn.example/asset?signature=secret'),b'content')
            self.assertNotIn('Authorization',server.calls[0][2])
            server.routes['GET','/redirect']=(302,b'',{'Location':'http://127.0.0.1/private'})
            with self.assertRaises(ValueError): transport.download('https://fixture-cdn.example/redirect')
            server.routes['GET','/v2/balance']=(302,b'',{'Location':'https://fixture-cdn.example/asset'})
            with self.assertRaises(ValueError): transport.json('pixellab','GET','/v2/balance',credential='secret')
            self.assertEqual(len(server.calls),3)
    def test_http_bounds_partial_body_and_deadline(self):
        with Server() as server:
            server.routes['GET','/large']=(200,b'123456789',{})
            with self.assertRaises(ValueError): server.transport().download('https://fixture-cdn.example/large',limit=8)
            server.routes['GET','/partial']=(200,b'short',{'Content-Length':'100'})
            with self.assertRaises(ValueError): server.transport(timeout=.1,retry_delay=0).download('https://fixture-cdn.example/partial')
            def slow(handler):
                time.sleep(.2)
                handler.send_response(200); handler.send_header('Content-Length','2'); handler.end_headers()
                try: handler.wfile.write(b'{}')
                except OSError: pass
            server.routes['GET','/v2/balance']=slow
            before=time.monotonic()
            with self.assertRaises(ValueError): server.transport(timeout=1,retry_delay=0).json('pixellab','GET','/v2/balance',credential='x',deadline=before+.05)
            self.assertLess(time.monotonic()-before,.3)
    def test_http_private_urls_rejected_without_network(self):
        from ccgs.assets.http import Transport
        for url in ['http://example.com/a','https://127.0.0.1/a','https://[::1]/a','https://169.254.169.254/metadata','https://user:secret@example.com/a','https://example.com:8080/a']:
            with self.assertRaises(ValueError): Transport().download(url)

    def test_http_upload_is_one_bounded_multipart_file(self):
        from fixtures import png
        with Server() as server:
            server.routes['POST','/v2/upload-fixture']=(200,{'uploaded':True},{})
            result=server.transport().multipart('pixellab','/v2/upload-fixture',filename='source.png',content=png(),content_type='image/png',credential='x')
            self.assertTrue(result['uploaded'])
            call=server.calls[0]
            self.assertIn(b'name="file"; filename="source.png"',call[3])
            self.assertIn(png(),call[3]); self.assertEqual(len(server.calls),1)
            with self.assertRaises(ValueError):server.transport().multipart('pixellab','/v2/upload-fixture',filename='../source.png',content=png(),content_type='image/png',credential='x')
            self.assertEqual(len(server.calls),1)
    def test_http_redirect_between_public_hosts_never_sends_api_authorization(self):
        with Server() as server:
            server.routes['GET','/first']=(302,b'',{'Location':'https://fixture-cdn.example/second?signature=secret'})
            server.routes['GET','/second?signature=secret']=(200,b'image bytes',{})
            self.assertEqual(server.transport().download('https://fixture-cdn.example/first'),b'image bytes')
            self.assertEqual(len(server.calls),2)
            for call in server.calls:self.assertNotIn('Authorization',call[2])
    def test_http_slow_drip_body_ends_at_overall_deadline(self):
        with Server() as server:
            def drip(handler):
                handler.send_response(200);handler.send_header('Content-Length','20');handler.end_headers()
                for _ in range(20):
                    try:handler.wfile.write(b'x');handler.wfile.flush()
                    except OSError:break
                    time.sleep(.02)
            server.routes['GET','/drip']=drip
            before=time.monotonic()
            with self.assertRaises(ValueError):server.transport(timeout=.08,retry_delay=0).download('https://fixture-cdn.example/drip')
            self.assertLess(time.monotonic()-before,.25)

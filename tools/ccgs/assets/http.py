"""Fixed-origin TLS transport with bounded bodies, deadlines and single-attempt mutations."""
import http.client
import ipaddress
import math
import queue
import re
import socket
import ssl
import threading
import time
from urllib.parse import urlsplit, urljoin
from .request import JSON_LIMIT, ARTIFACT_LIMIT, IMAGE_LIMIT, canonical, fail, strict_json

ORIGINS = {'pixellab':'https://api.pixellab.ai', 'meshy':'https://api.meshy.ai',
           'tripo':'https://openapi.tripo3d.ai', 'elevenlabs':'https://api.elevenlabs.io'}


class TransportError(ValueError):
    """Safe category/status only; deliberately excludes response bodies and URLs."""
    def __init__(self, category, status=None):
        self.category, self.status = category, status
        super().__init__(category)


def budget(deadline, timeout):
    value = timeout if deadline is None else min(timeout, deadline-time.monotonic())
    if value <= 0:
        raise TransportError('deadline_exhausted')
    return value


def public_addresses(host, port, deadline):
    """Bound DNS wait and pin a checked address for the actual TLS connection."""
    result = queue.Queue(maxsize=1)
    def lookup():
        try:
            result.put(socket.getaddrinfo(host,port,type=socket.SOCK_STREAM))
        except OSError:
            result.put(None)
    threading.Thread(target=lookup,daemon=True).start()
    try:
        records = result.get(timeout=budget(deadline,30))
    except queue.Empty:
        raise TransportError('deadline_exhausted') from None
    if not records:
        raise TransportError('dns_unavailable')
    addresses = [entry[4][0] for entry in records]
    if any(not ipaddress.ip_address(addr).is_global for addr in addresses):
        raise TransportError('private_network_target_rejected')
    return addresses


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host, address, timeout):
        super().__init__(host,443,timeout=timeout,context=ssl.create_default_context())
        self.address = address
    def connect(self):
        self.sock = socket.create_connection((self.address,443),self.timeout)
        self.sock = self._context.wrap_socket(self.sock,server_hostname=self.host)


class Transport:
    """origin_map is a library-only test boundary. It is never read from env/CLI/config."""
    def __init__(self, *, timeout=30, retry_delay=.5, origin_map=None):
        if isinstance(timeout,bool) or not isinstance(timeout,(int,float)) or not math.isfinite(timeout) or not 0 < timeout <= 30:
            fail('invalid_http_timeout')
        if isinstance(retry_delay,bool) or not isinstance(retry_delay,(int,float)) or not math.isfinite(retry_delay) or not 0 <= retry_delay <= 10:
            fail('invalid_retry_delay')
        self.timeout, self.retry_delay = timeout,retry_delay
        self.origin_map = dict(origin_map or {})
        for origin,target in self.origin_map.items():
            parsed=urlsplit(target)
            if parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1','::1') or parsed.username or parsed.path or parsed.query or parsed.fragment:
                fail('test_origin_must_be_loopback_http')

    def _validate_url(self,url):
        try:
            parsed=urlsplit(url)
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None,443) or parsed.fragment or any(ord(c)<33 for c in url):
                raise TransportError('unsafe_download_url')
            if parsed.hostname.lower() in ('localhost','localhost.localdomain'):
                raise TransportError('private_network_target_rejected')
            try:
                address=ipaddress.ip_address(parsed.hostname)
            except ValueError:
                address=None
            if address is not None and not address.is_global:
                raise TransportError('private_network_target_rejected')
            return parsed
        except (ValueError,TypeError):
            raise TransportError('unsafe_download_url') from None

    def _once(self,url,method,body,headers,limit,deadline):
        parsed=self._validate_url(url)
        origin='https://' + parsed.netloc
        end=min(deadline,time.monotonic()+self.timeout) if deadline is not None else time.monotonic()+self.timeout
        if origin in self.origin_map:
            target=urlsplit(self.origin_map[origin])
            connection=http.client.HTTPConnection(target.hostname,target.port,timeout=budget(end,self.timeout))
        else:
            address=public_addresses(parsed.hostname,443,end)[0]
            connection=PinnedHTTPSConnection(parsed.hostname,address,budget(end,self.timeout))
        expired=threading.Event()
        def expire():
            expired.set()
            if connection.sock:
                try: connection.sock.shutdown(socket.SHUT_RDWR)
                except OSError: pass
                connection.close()
        timer=threading.Timer(budget(end,self.timeout),expire)
        timer.daemon=True; timer.start()
        try:
            connection.request(method,(parsed.path or '/')+('?' + parsed.query if parsed.query else ''),body=body,headers=headers)
            response=connection.getresponse()
            length=response.getheader('Content-Length')
            if length is not None and (not length.isdigit() or int(length)>limit):
                raise TransportError('response_size_limit')
            if response.getheader('Content-Encoding') not in (None,'identity'):
                raise TransportError('unsupported_content_encoding')
            chunks=[]; total=0
            while True:
                if expired.is_set(): raise TransportError('deadline_exhausted')
                if connection.sock: connection.sock.settimeout(budget(end,self.timeout))
                chunk=response.read1(min(65536,limit+1-total))
                if not chunk: break
                total+=len(chunk)
                if total>limit: raise TransportError('response_size_limit')
                chunks.append(chunk)
            if expired.is_set(): raise TransportError('deadline_exhausted')
            if length is not None and total!=int(length):
                raise TransportError('partial_response')
            return response.status, response.getheader('Location'), b''.join(chunks)
        except (OSError,http.client.HTTPException):
            raise TransportError('deadline_exhausted' if expired.is_set() or time.monotonic()>=end else 'network_or_partial_response') from None
        finally:
            timer.cancel(); connection.close()

    def _request(self,url,method,body,headers,limit,deadline):
        attempts=3 if method=='GET' else 1
        for attempt in range(attempts):
            try:
                status,location,raw=self._once(url,method,body,headers,limit,deadline)
                if status==429 or status>=500:
                    raise TransportError('http_'+str(status),status)
                return status,location,raw
            except TransportError as exc:
                retry=exc.status==429 or (exc.status is not None and exc.status>=500) or exc.category in ('network_or_partial_response','partial_response')
                if attempt+1==attempts or not retry:
                    raise
                delay=min(self.retry_delay*2**attempt,budget(deadline,self.timeout))
                if delay: time.sleep(delay)

    def json(self,provider,method,path,*,body=None,credential=None,deadline=None):
        if provider not in ORIGINS or method not in ('GET','POST','DELETE') or not isinstance(path,str) or not path.startswith('/') or path.startswith('//') or '#' in path or any(ord(c)<33 for c in path):
            fail('unsupported_api_request')
        if not isinstance(credential,str) or not credential or '\r' in credential or '\n' in credential:
            fail('provider_credential_unavailable')
        payload=None if body is None else canonical(body)
        if payload is not None and len(payload)>JSON_LIMIT:
            fail('request_body_limit')
        status,_,raw=self._request(ORIGINS[provider]+path,method,payload,
                                  {'Authorization':'Bearer '+credential,'Content-Type':'application/json','Accept':'application/json'},JSON_LIMIT,deadline)
        if not 200<=status<300:
            raise TransportError('http_'+str(status),status)
        return strict_json(raw,JSON_LIMIT)

    def multipart(self,provider,path,*,filename,content,content_type,credential,deadline=None):
        """One explicit bounded binary upload. No hidden mutation or automatic retry."""
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',filename) or content_type not in ('image/png','image/jpeg') or not isinstance(content,bytes) or len(content)>IMAGE_LIMIT:
            fail('invalid_upload_part')
        if provider not in ORIGINS or not path.startswith('/') or path.startswith('//') or '?' in path or '#' in path or any(ord(c)<33 for c in path):
            fail('unsupported_api_request')
        if not isinstance(credential,str) or not credential or '\r' in credential or '\n' in credential:
            fail('provider_credential_unavailable')
        import secrets
        boundary='ccgs-'+secrets.token_hex(24)
        body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n').encode()+content+f'\r\n--{boundary}--\r\n'.encode()
        status,_,raw=self._request(ORIGINS[provider]+path,'POST',body,
            {'Authorization':'Bearer '+credential,'Content-Type':'multipart/form-data; boundary='+boundary},JSON_LIMIT,deadline)
        if not 200<=status<300: raise TransportError('http_'+str(status),status)
        return strict_json(raw,JSON_LIMIT)

    def elevenlabs_json(self,method,path,*,credential,deadline=None):
        """Fixed ElevenLabs read-only JSON boundary using only xi-api-key."""
        if method != 'GET' or not isinstance(path,str) or not path.startswith('/') or path.startswith('//') or '#' in path or any(ord(c)<33 for c in path):
            fail('unsupported_api_request')
        if not isinstance(credential,str) or not credential or '\r' in credential or '\n' in credential:
            fail('provider_credential_unavailable')
        status,_,raw=self._request(ORIGINS['elevenlabs']+path,'GET',None,
            {'xi-api-key':credential,'Accept':'application/json'},JSON_LIMIT,deadline)
        if not 200<=status<300: raise TransportError('http_'+str(status),status)
        return strict_json(raw,JSON_LIMIT)

    def elevenlabs_audio(self,path,*,body,credential,deadline=None):
        """Single-attempt bounded synchronous ElevenLabs binary POST."""
        if not isinstance(path,str) or not path.startswith('/v1/text-to-speech/') or path.startswith('//') or '#' in path or any(ord(c)<33 for c in path):
            fail('unsupported_api_request')
        if not isinstance(credential,str) or not credential or '\r' in credential or '\n' in credential:
            fail('provider_credential_unavailable')
        payload=canonical(body)
        if len(payload)>JSON_LIMIT: fail('request_body_limit')
        limit=64*1024*1024
        status,_,raw=self._request(ORIGINS['elevenlabs']+path,'POST',payload,
            {'xi-api-key':credential,'Content-Type':'application/json','Accept':'audio/wav'},limit,deadline)
        if not 200<=status<300: raise TransportError('http_'+str(status),status)
        return raw

    def download(self,url,*,limit=ARTIFACT_LIMIT,deadline=None):
        if type(limit) is not int or not 0<limit<=ARTIFACT_LIMIT: fail('invalid_download_limit')
        end=deadline if deadline is not None else time.monotonic()+self.timeout
        for redirect in range(4):
            status,location,raw=self._request(url,'GET',None,{'Accept':'application/octet-stream'},limit,end)
            if status in (301,302,303,307,308):
                if not location or redirect==3: raise TransportError('redirect_limit')
                url=urljoin(url,location)
                self._validate_url(url)
                continue
            if not 200<=status<300: raise TransportError('http_'+str(status),status)
            return raw
        raise TransportError('redirect_limit')

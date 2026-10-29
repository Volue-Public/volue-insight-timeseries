import http.server
import json
import socket
import threading
import time

import pytest
import requests
import requests_mock
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

import volue_insight_timeseries as vit


TOKEN = json.dumps({'token_type': 'Bearer', 'access_token': 'secrettoken', 'expires_in': 1000})


class _Handler(http.server.BaseHTTPRequestHandler):
    """/503... always fails, /429 fails with Retry-After: 1, /slow answers after the
    client timeout, anything else is 200"""

    def do_GET(self):
        self.server.record(self.path)
        if self.path == '/slow':
            time.sleep(0.5)
        status = 503 if self.path.startswith('/503') else 429 if self.path == '/429' else 200
        self.send_response(status)
        if status == 429:
            self.send_header('Retry-After', '1')
        self.send_header('Content-Length', '0')
        self.end_headers()

    do_POST = do_GET

    def log_message(self, *args):
        pass


class _Server(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self):
        super().__init__(('127.0.0.1', 0), _Handler)
        self.hits = {}
        self._lock = threading.Lock()

    def record(self, path):
        with self._lock:
            self.hits[path] = self.hits.get(path, 0) + 1


@pytest.fixture
def server(monkeypatch):
    monkeypatch.setattr(vit.session, 'RETRY_DELAY', 0.001)
    srv = _Server()
    threading.Thread(target=srv.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True).start()
    srv.url = 'http://127.0.0.1:{}'.format(srv.server_port)
    yield srv
    srv.shutdown()
    srv.server_close()


def _retry(total):
    return Retry(total=total, status_forcelist=[503], allowed_methods=None, raise_on_status=False)


#
# Retries
#
def test_default_retries_match_retry_count(server):
    s = vit.Session(urlbase=server.url)
    assert s.data_request('GET', None, '/503').status_code == 503
    assert server.hits['/503'] == vit.session.RETRY_COUNT + 1


def test_session_retries(server):
    s = vit.Session(urlbase=server.url, retries=2)
    s.data_request('GET', None, '/503')
    assert server.hits['/503'] == 3


def test_retries_zero_sends_once(server):
    s = vit.Session(urlbase=server.url, retries=0)
    s.data_request('GET', None, '/503')
    assert server.hits['/503'] == 1


def test_post_is_retried(server):
    s = vit.Session(urlbase=server.url, retries=2)
    s.data_request('POST', None, '/503', data={'a': 1})
    assert server.hits['/503'] == 3


def test_call_retries_take_priority_over_session(server):
    s = vit.Session(urlbase=server.url, retries=3)
    s.data_request('GET', None, '/503', retries=1)
    assert server.hits['/503'] == 2


def test_retry_object_is_used(server):
    s = vit.Session(urlbase=server.url, retries=_retry(1))
    s.data_request('GET', None, '/503')
    assert server.hits['/503'] == 2


def test_retried_read_timeout_raises_timeout(server):
    s = vit.Session(urlbase=server.url, timeout=0.1, retries=1)
    with pytest.raises(requests.exceptions.ReadTimeout):
        s.data_request('GET', None, '/slow')
    assert server.hits['/slow'] == 2



def test_retry_read_limit_is_used(server):
    s = vit.Session(urlbase=server.url, timeout=0.1, retries=Retry(total=10, read=1, backoff_factor=0))
    with pytest.raises(requests.exceptions.ReadTimeout):
        s.data_request('GET', None, '/slow')
    assert server.hits['/slow'] == 2


def test_retry_allowed_methods_apply_to_network_errors(server):
    # urllib3's default allowed_methods leave out POST
    s = vit.Session(urlbase=server.url, timeout=0.1, retries=Retry(total=2, backoff_factor=0))
    with pytest.raises(requests.exceptions.ReadTimeout):
        s.data_request('POST', None, '/slow')
    assert server.hits['/slow'] == 1


def test_retry_raise_on_status_raises_retry_error(server):
    s = vit.Session(urlbase=server.url, retries=Retry(total=1, status_forcelist=[503], backoff_factor=0))
    with pytest.raises(requests.exceptions.RetryError):
        s.data_request('GET', None, '/503')
    assert server.hits['/503'] == 2


def test_retry_after_is_honoured_by_retry_that_asks_for_it(server):
    s = vit.Session(urlbase=server.url, retries=Retry(total=1, backoff_factor=0, raise_on_status=False))
    start = time.monotonic()
    assert s.data_request('GET', None, '/429').status_code == 429
    assert server.hits['/429'] == 2
    assert time.monotonic() - start >= 1


def test_default_retries_ignore_retry_after(server):
    s = vit.Session(urlbase=server.url)
    assert s.data_request('GET', None, '/429').status_code == 429
    assert server.hits['/429'] == 1


class _CountingSession(requests.Session):
    """requests session that counts its requests"""

    calls = 0

    def request(self, *args, **kwargs):
        self.calls += 1
        return super().request(*args, **kwargs)


def test_retry_connect_limit_is_used():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        closed_port = sock.getsockname()[1]
    http_session = _CountingSession()
    s = vit.Session(urlbase='http://127.0.0.1:{}'.format(closed_port), requests_session=http_session,
                    retries=Retry(total=10, connect=1, backoff_factor=0))
    with pytest.raises(requests.exceptions.ConnectionError):
        s.data_request('GET', None, '/curves')
    assert http_session.calls == 2

class _FailingSession(requests.Session):
    """requests session whose every request raises error"""

    def __init__(self, error):
        super().__init__()
        self.error = error
        self.calls = 0

    def request(self, *args, **kwargs):
        self.calls += 1
        raise self.error


@pytest.mark.parametrize('error,attempts', [
    (requests.exceptions.ConnectionError(), vit.session.RETRY_COUNT + 1),
    (requests.exceptions.SSLError(), 1),
    (requests.exceptions.ProxyError(), 1),
])
def test_connection_errors_are_retried_except_ssl_and_proxy(monkeypatch, error, attempts):
    monkeypatch.setattr(vit.session, 'RETRY_DELAY', 0.001)
    http_session = _FailingSession(error)
    s = vit.Session(urlbase='http://127.0.0.1', requests_session=http_session)
    with pytest.raises(type(error)):
        s.data_request('GET', None, '/curves')
    assert http_session.calls == attempts


def test_concurrent_calls_keep_their_own_retries(server):
    s = vit.Session(urlbase=server.url)
    explicit = threading.Thread(target=s.data_request, args=('GET', None, '/503'), kwargs={'retries': 1})
    default = threading.Thread(target=s.data_request, args=('GET', None, '/503?default'))
    explicit.start(), default.start()
    explicit.join(), default.join()
    assert server.hits['/503'] == 2
    assert server.hits['/503?default'] == vit.session.RETRY_COUNT + 1


@pytest.mark.parametrize('retries,error', [(-1, ValueError), (None, TypeError), (True, TypeError), ('3', TypeError),
                                           (1.5, TypeError)])
def test_invalid_retries(retries, error):
    with pytest.raises(error):
        vit.Session(retries=retries)


#
# Caller's requests session
#
def test_retries_zero_leaves_retrying_to_requests_session(server):
    http_session = requests.Session()
    http_session.mount('http://', HTTPAdapter(max_retries=_retry(1)))
    s = vit.Session(urlbase=server.url, requests_session=http_session, retries=0)
    s.data_request('GET', None, '/503')
    assert server.hits['/503'] == 2


def test_requests_session_without_retry_gets_default(server):
    s = vit.Session(urlbase=server.url, requests_session=requests.Session())
    s.data_request('GET', None, '/503')
    assert server.hits['/503'] == vit.session.RETRY_COUNT + 1


def test_adapter_mounted_on_internal_session_keeps_default_retries(server):
    s = vit.Session(urlbase=server.url)
    s._session.mount('http://', HTTPAdapter(pool_maxsize=20))
    s.data_request('GET', None, '/503')
    assert server.hits['/503'] == vit.session.RETRY_COUNT + 1


def test_requests_outside_the_library_are_not_retried(server):
    http_session = requests.Session()
    vit.Session(urlbase=server.url, requests_session=http_session)
    assert http_session.get(server.url + '/503').status_code == 503
    assert server.hits['/503'] == 1


def test_requests_session_must_be_a_requests_session():
    with pytest.raises(TypeError):
        vit.Session(requests_session=object())


def test_requests_session_sends_auth_data_and_events():
    http_session = requests.Session()
    http_session.headers['X-Custom'] = 'kept'
    adapter = requests_mock.Adapter()
    http_session.mount('rtsp://', adapter)
    adapter.register_uri('POST', 'rtsp://auth/oauth2/token', text=TOKEN)
    adapter.register_uri('GET', 'rtsp://api/curves', text='[]')
    adapter.register_uri('GET', requests_mock.ANY, text='')

    s = vit.Session(urlbase='rtsp://api', auth_urlbase='rtsp://auth', client_id='id', client_secret='secret',
                    requests_session=http_session)
    s.data_request('GET', None, '/curves')
    listener = s.events([1])
    try:
        for _ in range(100):
            if any('/events' in r.url for r in adapter.request_history):
                break
            time.sleep(0.01)
    finally:
        listener.close()

    urls = [r.url for r in adapter.request_history]
    assert urls[0] == 'rtsp://auth/oauth2/token'
    assert 'rtsp://api/curves' in urls
    assert any('/api/v1/timeseries/events' in url for url in urls)
    expected = 'volue-insight-timeseries/{} '.format(vit.__version__)
    for request in adapter.request_history:
        assert request.headers['X-Custom'] == 'kept'
        assert request.headers['User-Agent'].startswith(expected)

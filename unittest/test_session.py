from unittest.mock import Mock, patch, MagicMock
import requests_mock
import pytest
import requests
import os
import json
import time

import volue_insight_timeseries as vit


authprefix = 'rtsp://auth.host/oauth2'

class MockResponse:
    def __init__(self, status_code, content="Mock content"):
        self.status_code = status_code
        self.content = content
        

def make_vit_session() -> vit.Session:
    return vit.session.Session(urlbase='https://data-forecasts.volue.com',
                                auth_urlbase='https://auth.vs.com',
                                client_id='client1',
                                client_secret='secret1')

# ignore auth
@patch('volue_insight_timeseries.session.auth', MagicMock())
@patch('volue_insight_timeseries.session.requests')
def test_data_request__get__ok(requests_mock):
    mock_response = MockResponse(200)
    # https://docs.python.org/3/library/unittest.mock-examples.html#mocking-chained-calls
    requests_mock.Session.return_value.request.return_value = mock_response

    session = make_vit_session()
    response = session.data_request('GET', None, '/curves')

    assert response == mock_response


@patch.object(vit.session.requests.Session, "request")
def test_data_request__token_expire__ok(mock_request):
    def mock_request_effect(**kwargs):
        if kwargs["method"] == "POST":
            return MockResponse(200, content=json.dumps({"access_token": "a", "token_type": "b", "expires_in": 10}).encode())
        elif kwargs["method"] == "GET":
            return MockResponse(200, "curves")

    mock_request.side_effect = mock_request_effect

    os.environ['REPORTED_DATA_SOURCE'] = 'testSource' # for testing the source

    # verify auth getting token and the request source at beginning
    session = make_vit_session()
    headers = session.auth.get_headers(None)
    assert  headers['Authorization'] == 'b a'
    assert  headers['X-Model-Name'] == 'testSource'

    # verify auth refreshing token
    session.auth.valid_until = 0 # simulating token expiring
    response = session.data_request('GET', None, '/curves')

    assert response.status_code == 200
    assert response.content == "curves"
    headers = session.auth.get_headers(None)
    assert  headers['Authorization'] == 'b a'
    assert  headers['X-Model-Name'] == 'testSource'

@pytest.mark.parametrize("urlbase,url,longurl_expected", 
    [
        (None, "/token", "https://data-forecasts.volue.com/token"), 
        ("http://urlbase", "/token", "http://urlbase/token")
    ])
@patch('volue_insight_timeseries.session.auth', MagicMock())
@patch('volue_insight_timeseries.session.requests')
def test_send_data_request__long_url__correct(requests_mock, urlbase, url, longurl_expected):
    requests_mock.Session.return_value.request.return_value = MockResponse(200)

    session = make_vit_session()    
    session.data_request('GET', urlbase=urlbase, url=url)

    call_args = requests_mock.Session.return_value.request.call_args
    assert call_args[1]["url"] == longurl_expected


@pytest.mark.parametrize("data,rawdata,databytes_expected", 
    [
        (None, "rawdata", "rawdata"), 
        (40, None, b"40"), 
        ("basestring", "rawdata", b"basestring")
    ])
@patch('volue_insight_timeseries.session.auth', MagicMock())
@patch('volue_insight_timeseries.session.requests')
def test_send_data_request__databytes__correct(requests_mock, data, rawdata, databytes_expected):
    requests_mock.Session.return_value.request.return_value = MockResponse(200)

    session =  make_vit_session()   
    session.data_request('GET', None, None, data=data, rawdata=rawdata)

    call_args = requests_mock.Session.return_value.request.call_args
    assert call_args[1]["data"] == databytes_expected


@pytest.mark.parametrize("failed_status_code", [408, 500, 599])
@patch('volue_insight_timeseries.session.auth', MagicMock())
@patch('volue_insight_timeseries.session.requests')
def test_send_data_request__retries__correct(requests_mock, failed_status_code):
    requests_mock.Session.return_value.request.return_value = MockResponse(failed_status_code)

    retries_count = 3
    vit.session.RETRY_DELAY = 0.00001
    session =  make_vit_session()   
    session.send_data_request("GET", "http://urlbase", "/url", "data", None, "headers", "authval", False, retries_count)

    call_args = requests_mock.Session.return_value.request.call_args
    assert call_args[1] == {"method": "GET", "url": "http://urlbase/url", "data": b"data", "headers": "headers", 
                            "auth": "authval", "stream": False, "timeout": 300}
    assert requests_mock.Session.return_value.request.call_count == retries_count + 1


@patch('volue_insight_timeseries.session.auth')
@patch('volue_insight_timeseries.session.requests')
def test_data_request__get_auth__first_failed_then_ok(requests_mock, auth_mock):
    mock_response = MockResponse(200)
    requests_mock.Session.return_value.request.return_value = mock_response
    oauth_mock = Mock()
    auth_mock.OAuth.return_value = oauth_mock
    validation_called = []

    def validate_auth():
        validation_called.append(1)
        if len(validation_called) == 1:
            raise requests.exceptions.ConnectionError
        return True

    oauth_mock.validate_auth = validate_auth
    oauth_mock.get_headers.return_value = {'Authorization': 'X Y'}

    vit.session.RETRY_DELAY = 0.00001
    session = make_vit_session()
    session.retry_update_auth = True

    response = session.data_request('GET', None, '/curves')

    assert response == mock_response

    assert len(validation_called) == 2
    assert requests_mock.Session.return_value.request.call_count == 1
    call_args = requests_mock.Session.return_value.request.call_args
    assert call_args[1]['method'] == "GET"
    assert call_args[1]['headers'] == {'Authorization': 'X Y'}


@patch('volue_insight_timeseries.session.auth')
@patch('volue_insight_timeseries.session.requests')
def test_data_request__fail_too_many_times(requests_mock, auth_mock):
    mock_response = MockResponse(200)
    requests_mock.Session.return_value.request.return_value = mock_response
    oauth_mock = Mock()
    auth_mock.OAuth.return_value = oauth_mock
    validation_called = []

    def validate_auth():
        validation_called.append(1)
        raise requests.exceptions.ConnectionError

    oauth_mock.validate_auth = validate_auth
    oauth_mock.get_headers.return_value = {'Authorization': 'X Y'}

    vit.session.RETRY_DELAY = 0.00001
    session = make_vit_session()
    session.retry_update_auth = True

    with pytest.raises(requests.exceptions.ConnectionError):
        session.data_request('GET', None, '/curves')

    assert len(validation_called) == 5
    assert requests_mock.Session.return_value.request.call_count == 0


#
# Test authentication setup
#
def test_build_sessions():
    s = vit.Session()
    assert s.urlbase == vit.session.API_URLBASE
    assert s.auth is None
    assert s.timeout == vit.session.TIMEOUT
    s = vit.Session(urlbase ='test_data', timeout=5)
    assert s.urlbase == 'test_data'
    assert s.timeout == 5


def test_configure_by_file():
    config_file = os.path.join(os.path.dirname(__file__), 'testconfig_oauth.ini')
    s = vit.Session(urlbase='rtsp://test.host')
    #
    mock = requests_mock.Adapter()
    # urllib does things based on protocol, so (ab)use one which is reasonably
    # http-like instead of inventing our own.
    s._session.mount('rtsp', mock)
    client_token = json.dumps({'token_type': 'Bearer', 'access_token': 'secrettoken',
                               'expires_in': 1000})
    mock.register_uri('POST', authprefix + '/token', text=client_token)
    #
    s.read_config_file(config_file)
    assert s.urlbase == 'rtsp://test.host'
    assert isinstance(s.auth, vit.auth.OAuth)
    assert s.auth.client_id == 'clientid'
    assert s.auth.client_secret == 'verysecret'
    assert s.auth.auth_urlbase == 'rtsp://auth.host'
    assert s.auth.token_type == 'Bearer'
    assert s.auth.token == 'secrettoken'
    lifetime = s.auth.valid_until - time.time()
    assert lifetime > 900
    assert lifetime < 1010
    assert s.timeout == 10.0


def test_minimal_config_file():
    config_file = os.path.join(os.path.dirname(__file__), 'testconfig_minimal.ini')
    s = vit.Session(config_file=config_file)
    #
    assert s.urlbase == 'https://data-forecasts.volue.com'
    assert s.auth is None


def test_configure_by_param():
    s = vit.Session(urlbase='rtsp://test.host')
    #
    mock = requests_mock.Adapter()
    # urllib does things based on protocol, so (ab)use one which is reasonably
    # http-like instead of inventing our own.
    s._session.mount('rtsp', mock)
    client_token = json.dumps({'token_type': 'Bearer', 'access_token': 'secrettoken',
                               'expires_in': 1000})
    mock.register_uri('POST', authprefix + '/token', text=client_token)
    #
    s.configure(client_id='clientid', client_secret='verysecret', auth_urlbase='rtsp://auth.host')
    assert s.urlbase == 'rtsp://test.host'
    assert isinstance(s.auth, vit.auth.OAuth)
    assert s.auth.client_id == 'clientid'
    assert s.auth.client_secret == 'verysecret'
    assert s.auth.auth_urlbase == 'rtsp://auth.host'
    assert s.auth.token_type == 'Bearer'
    assert s.auth.token == 'secrettoken'
    lifetime = s.auth.valid_until - time.time()
    assert lifetime > 900
    assert lifetime < 1010
    assert s.timeout == vit.session.TIMEOUT

def test_reconfigure_session():
    config_file = os.path.join(os.path.dirname(__file__), 'testconfig_oauth.ini')
    s = vit.Session(urlbase='test_data')
    #
    mock = requests_mock.Adapter()
    # urllib does things based on protocol, so (ab)use one which is reasonably
    # http-like instead of inventing our own.
    s._session.mount('rtsp', mock)
    client_token = json.dumps({'token_type': 'Bearer', 'access_token': 'secrettoken',
                               'expires_in': 1000})
    mock.register_uri('POST', authprefix + '/token', text=client_token)
    #
    s.read_config_file(config_file)
    assert s.urlbase == 'rtsp://test.host'
    with pytest.raises(vit.session.ConfigException) as exinfo:
        s.configure('clientid', 'clientsecret')
    assert 'already done' in str(exinfo.value)


#
# Test Volue Identity authentication
#
VI_TOKEN_URL = 'https://auth.identity.volue.com/connect/token'
API_CURVES_URL = vit.session.API_URLBASE + '/api/v1/timeseries/curves'
VI_TOKEN = json.dumps({'token_type': 'Bearer', 'access_token': 'vitoken', 'expires_in': 3600})


def test_volue_identity_by_file():
    config_file = os.path.join(os.path.dirname(__file__), 'testconfig_volueidentity.ini')
    with requests_mock.Mocker() as m:
        m.post(VI_TOKEN_URL, text=VI_TOKEN)
        s = vit.Session(config_file=config_file)
        token_request = m.request_history[0]
    assert isinstance(s.auth, vit.auth.VolueIdentity)
    assert s.urlbase == 'https://test.host'
    assert s.auth.auth_urlbase == 'https://auth.identity.volue.com'
    assert s.auth.token == 'vitoken'
    body = dict(pair.split('=') for pair in token_request.text.split('&'))
    assert body == {'grant_type': 'client_credentials', 'scope': 'in.dnf%3Aapi'}
    assert token_request.headers['Authorization'].startswith('Basic ')


def test_volue_identity_by_param():
    with requests_mock.Mocker() as m:
        m.post('https://auth.test.host/connect/token', text=VI_TOKEN)
        s = vit.Session(client_id='viclientid', client_secret='visecret',
                        auth_urlbase='https://auth.test.host', auth_type='VolueIdentity')
    assert isinstance(s.auth, vit.auth.VolueIdentity)
    assert s.auth.client_id == 'viclientid'
    # The API address is not changed by the auth type
    assert s.urlbase == vit.session.API_URLBASE


def test_oauth_sends_no_scope():
    with requests_mock.Mocker() as m:
        m.post('https://auth.volueinsight.com/oauth2/token', text=VI_TOKEN)
        s = vit.Session(client_id='client', client_secret='secret')
        assert m.request_history[0].text == 'grant_type=client_credentials'
    assert type(s.auth) is vit.auth.OAuth


def test_unknown_auth_type():
    config_file = os.path.join(os.path.dirname(__file__), 'testconfig_unknown_auth.ini')
    with pytest.raises(vit.session.ConfigException, match='VolueIdentiy'):
        vit.Session(config_file=config_file)
    with pytest.raises(vit.session.ConfigException, match='Unknown auth_type'):
        vit.Session(client_id='client', client_secret='secret', auth_type='Sales')


@pytest.mark.parametrize('auth_type,token_url,error,expected', [
    ('VolueIdentity', VI_TOKEN_URL, 'invalid_client', 'set auth_type = OAuth'),
    ('OAuth', 'https://auth.volueinsight.com/oauth2/token', 'invalid_client', 'set auth_type = VolueIdentity'),
    ('VolueIdentity', VI_TOKEN_URL, 'invalid_scope', 'not allowed to access'),
])
def test_token_request_errors(auth_type, token_url, error, expected):
    with requests_mock.Mocker() as m:
        m.post(token_url, status_code=400, json={'error': error})
        with pytest.raises(vit.auth.AuthFailedException) as e:
            vit.Session(client_id='client', client_secret='secret', auth_type=auth_type)
    assert 'Authentication failed ({})'.format(auth_type) in str(e.value)
    assert error in str(e.value)
    assert expected in str(e.value)
    if error == 'invalid_client':
        assert 'revoked or have expired' in str(e.value)


def test_token_endpoint_not_found():
    with requests_mock.Mocker() as m:
        m.post('https://auth.identity.volue.com/oauth2/token', status_code=404, text='Not found')
        with pytest.raises(vit.auth.AuthFailedException, match='auth_type and auth_urlbase'):
            vit.Session(client_id='client', client_secret='secret',
                        auth_urlbase='https://auth.identity.volue.com')


def test_volue_identity_token_rejected_by_api():
    with requests_mock.Mocker() as m:
        m.post(VI_TOKEN_URL, text=VI_TOKEN)
        m.get(API_CURVES_URL, status_code=401)
        s = vit.Session(client_id='client', client_secret='secret', auth_type='VolueIdentity')
        with pytest.raises(vit.auth.AuthFailedException, match='keep using your current credentials'):
            s.data_request('GET', None, '/api/v1/timeseries/curves')


def test_oauth_401_is_returned_unchanged():
    with requests_mock.Mocker() as m:
        m.post('https://auth.volueinsight.com/oauth2/token', text=VI_TOKEN)
        m.get(API_CURVES_URL, status_code=401)
        s = vit.Session(client_id='client', client_secret='secret')
        assert s.data_request('GET', None, '/api/v1/timeseries/curves').status_code == 401


def test_user_agent_has_library_version():
    with requests_mock.Mocker() as m:
        m.post(VI_TOKEN_URL, text=VI_TOKEN)
        m.get(API_CURVES_URL, text='[]')
        s = vit.Session(client_id='client', client_secret='secret', auth_type='VolueIdentity')
        s.data_request('GET', None, '/api/v1/timeseries/curves')
        user_agents = [r.headers['User-Agent'] for r in m.request_history]
    expected = 'volue-insight-timeseries/{} '.format(vit.__version__)
    assert all(ua.startswith(expected) for ua in user_agents)


def test_auth_type_enum():
    assert str(vit.auth.AuthType.VOLUE_IDENTITY) == 'VolueIdentity'
    assert vit.auth.AuthType('OAuth') is vit.auth.AuthType.OAUTH
    with requests_mock.Mocker() as m:
        m.post(VI_TOKEN_URL, text=VI_TOKEN)
        s = vit.Session(client_id='client', client_secret='secret',
                        auth_type=vit.auth.AuthType.VOLUE_IDENTITY)
    assert isinstance(s.auth, vit.auth.VolueIdentity)
    assert s.auth.auth_type is vit.auth.AuthType.VOLUE_IDENTITY

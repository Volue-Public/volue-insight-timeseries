#
# Authentication support
#

import json
import time
import threading
import os
from enum import Enum

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin


class AuthFailedException(Exception):
    pass


class AuthType(str, Enum):
    """
    Supported values for ``auth_type``.
    Behaves like ``enum.StrEnum``, which is not available in Python 3.10.
    """

    OAUTH = 'OAuth'
    VOLUE_IDENTITY = 'VolueIdentity'

    def __str__(self):
        return self.value


class OAuth:
    """
    Authentication based on OAuth client ID.
    This is the main authentication mechanism for customer access to the data center.
    """

    auth_type = AuthType.OAUTH
    token_path = '/oauth2/token'
    scope = None
    mismatch_hint = ('Check that the client ID and secret are your Volue Data & Forecasts credentials. '
                     'If they are Volue Identity credentials, set auth_type = VolueIdentity.')

    def __init__(self, session, client_id, client_secret, auth_urlbase):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_urlbase = auth_urlbase
        self.token = None
        self.token_type = None
        self.valid_until = None
        self.session = session
        self._authenticate()

    def validate_auth(self):
        """Check valid_until and fetch new token if needed"""
        # To avoid sending duplicated authentication requests in other threads
        with threading.Lock():
            if (not self.valid_until) or time.time() > self.valid_until:
                self._authenticate()

    def _authenticate(self):
        # Wipe out any old values before (re-)login
        self.token = None
        self.token_type = None
        self.valid_until = None
        now = time.time()
        url = urljoin(self.auth_urlbase, self.token_path)
        auth = (self.client_id, self.client_secret)
        data = {'grant_type': 'client_credentials'}
        if self.scope is not None:
            data['scope'] = self.scope
        response = self.session.send_data_request('POST', self.auth_urlbase, url, rawdata=data, authval=auth)
        if response.status_code != 200:
            raise AuthFailedException(self._failure_message(url, response))
        # Parse token
        rsp = json.loads(response.content.decode())
        self.token = rsp['access_token']
        self.token_type = rsp['token_type']
        self.valid_until = now + int(rsp['expires_in'] * 0.95)

    def _failure_message(self, url, response):
        """Explain a failed token request, so it is not mistaken for an API error"""
        message = 'Authentication failed ({}) when requesting a token from {}'.format(self.auth_type, url)
        error = None
        try:
            body = json.loads(response.content.decode())
            error = body.get('error')
            message += ': {}'.format(error)
            if body.get('error_description'):
                message += ' ({})'.format(body['error_description'])
        except (ValueError, AttributeError):
            message += ': HTTP {} {}'.format(response.status_code, response.content)
        if error == 'invalid_client':
            message += '. ' + self.mismatch_hint + ' The credentials may also have been revoked or have expired.'
        elif error == 'invalid_scope':
            message += '. The client is not allowed to access the Volue Data & Forecasts API. Contact support.'
        elif response.status_code == 404:
            message += '. Check that auth_type and auth_urlbase belong together.'
        return message

    def get_headers(self, data):
        """The web-token auth header is simple"""
        headers = {}
        if self.token is not None and self.token_type is not None:
            headers['Authorization'] = '{} {}'.format(self.token_type, self.token)
        
        wapi_request_source = os.getenv('REPORTED_DATA_SOURCE')
        if wapi_request_source:
            headers['X-Model-Name'] = wapi_request_source
            
        return headers


class VolueIdentity(OAuth):
    """
    Authentication with a Volue Identity client ID (client credentials).
    """

    auth_type = AuthType.VOLUE_IDENTITY
    token_path = '/connect/token'
    scope = 'in.dnf:api'
    mismatch_hint = ('Check that the client ID and secret are your Volue Identity credentials. '
                     'If they are your existing Volue Data & Forecasts credentials, set auth_type = OAuth.')

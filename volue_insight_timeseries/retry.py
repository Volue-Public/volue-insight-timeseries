"""Retrying requests to the Volue Data & Forecasts API.

A urllib3 ``Retry`` decides which failures are retried, how often and how long
to wait.
"""

import requests
from urllib3.exceptions import MaxRetryError
from urllib3.response import HTTPResponse
from urllib3.util import Retry


class _FixedDelayRetry(Retry):
    """Retry that waits the same delay, in seconds, before every attempt, with no backoff"""

    def __init__(self, delay=0, **kwargs):
        super().__init__(**kwargs)
        self.delay = delay

    def new(self, **kwargs):
        # Retry.new passes on only urllib3's own settings
        retry = super().new(**kwargs)
        retry.delay = self.delay
        return retry

    def get_backoff_time(self):
        return self.delay


def make_retry(retries, delay):
    """Turn a ``retries`` argument into a urllib3 Retry, or None when not given.

    An int gets delay seconds between attempts.
    """
    if retries is None or isinstance(retries, Retry):
        return retries
    if isinstance(retries, bool) or not isinstance(retries, int):
        raise TypeError('retries must be an int or a urllib3 Retry, not {}'.format(type(retries).__name__))
    if retries < 0:
        raise ValueError('retries must be 0 or more, not {}'.format(retries))
    # Retried statuses: 408 and every 5xx
    return _FixedDelayRetry(delay=delay, total=retries, status_forcelist={408, *range(500, 600)}, allowed_methods=None,
                            raise_on_status=False, respect_retry_after_header=False)


def _urllib3_error(error):
    """The urllib3 error inside a requests exception, so Retry can tell connect and read errors apart"""
    cause = error.args[0] if error.args else None
    if isinstance(cause, MaxRetryError):
        cause = cause.reason
    return cause if isinstance(cause, Exception) else error


def request_with_retries(http_session, retry_state, method, url, **kwargs):
    """Send a request through http_session, retrying as retry_state allows, and return the response.

    kwargs are passed to http_session.request for every attempt. When retries run
    out, the last response is returned, or RetryError is raised if retry_state has
    raise_on_status. A Timeout or ConnectionError that is not retried is raised.
    SSLError and ProxyError are raised at once: they come from configuration, which
    a retry does not fix.
    """
    while True:
        try:
            res = http_session.request(method=method, url=url, **kwargs)
        except (requests.exceptions.SSLError, requests.exceptions.ProxyError):
            raise
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            try:
                retry_state = retry_state.increment(method, url, error=_urllib3_error(e))
            except Exception:
                # Out of retries, or not retried (such as a read error for a method
                # outside allowed_methods): raise the requests exception, not urllib3's
                raise e from None
            retry_state.sleep()
            continue
        # Response headers are read only for a Retry that honours Retry-After
        headers = res.headers if retry_state.respect_retry_after_header else None
        if not retry_state.is_retry(method, res.status_code, headers is not None and 'Retry-After' in headers):
            return res
        response = HTTPResponse(status=res.status_code, headers=headers)
        try:
            retry_state = retry_state.increment(method, url, response=response)
        except MaxRetryError as e:
            if retry_state.raise_on_status:
                raise requests.exceptions.RetryError(e, request=res.request) from None
            return res
        retry_state.sleep(response)

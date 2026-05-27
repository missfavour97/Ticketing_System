import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings


VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'


def is_recaptcha_enabled():
    return settings.RECAPTCHA_ENABLED or settings.RECAPTCHA_DEMO_MODE


def recaptcha_mode():
    if settings.RECAPTCHA_ENABLED:
        return 'google'
    if settings.RECAPTCHA_DEMO_MODE:
        return 'demo'
    return 'off'


def verify_recaptcha(response_token, remote_ip=None, demo_response=None):
    mode = recaptcha_mode()

    if mode == 'off':
        return True, ''

    if mode == 'demo':
        if demo_response == 'checked':
            return True, ''
        return False, 'Please complete the demo reCAPTCHA checkbox.'

    if not response_token:
        return False, 'Please complete the reCAPTCHA challenge.'

    payload = {
        'secret': settings.RECAPTCHA_SECRET_KEY,
        'response': response_token,
    }

    if remote_ip:
        payload['remoteip'] = remote_ip

    data = urlencode(payload).encode()
    request = Request(VERIFY_URL, data=data, method='POST')

    try:
        with urlopen(request, timeout=5) as response:
            result = json.loads(response.read().decode())
    except Exception:
        return False, 'Could not verify reCAPTCHA. Please try again.'

    if result.get('success'):
        return True, ''

    return False, 'reCAPTCHA verification failed. Please try again.'

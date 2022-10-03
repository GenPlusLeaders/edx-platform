import logging
from hashlib import sha1
from json import JSONDecodeError
from django.conf import settings
import requests
import base64
import hmac
from datetime import datetime


logger = logging.getLogger(__name__)

class RmUnify:
    ORGANISATION = 'organisation/'
    TEACHING_GROUP = '{}{}/teachinggroup/'
    REGISTRATION_GROUP = '{}{}/registrationgroup/'

    def __init__(self):
        self.key = settings.RM_UNIFY_KEY
        self.secret = settings.RM_UNIFY_SECRET
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    def fetch(self, source, source_id=None):
        headers = {"Authorization": "Unify " + self.key + "_" + self.timestamp + ":" + self.hashed}
        url = self.generate_url(source, source_id)
        r = requests.get(url, headers=headers)
        try:
            return r.json()
        except BaseException as e:
            logger.exception(e)
            return []



    @property
    def hashed(self):
        hashed = hmac.new(bytes(self.secret, 'utf-8'), bytes(self.timestamp, 'utf-8'), sha1).digest()
        hashed = str(base64.urlsafe_b64encode(hashed), "UTF-8")
        hashed = hashed.replace('-', '+')
        return hashed.replace('_', '/')

    @staticmethod
    def generate_url(source, source_id):
        url = settings.RM_UNIFY_URL
        if source:
            url = url + source
        if source_id:
            url = url + source_id
        return url

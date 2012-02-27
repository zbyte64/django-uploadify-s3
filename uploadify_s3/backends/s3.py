from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from urllib import quote_plus
from datetime import datetime
from datetime import timedelta
import base64
import hmac
import hashlib
import os

from base import BaseUploadifyBackend, _set_default_if_none

PASS_THRU_OPTIONS = ('folder', 'fileExt',)
FILTERED_KEYS  = []#('filename',)
EXCLUDED_KEYS     = ('AWSAccessKeyId', 'policy', 'signature')

# AWS Options
ACCESS_KEY_ID       = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
SECRET_ACCESS_KEY   = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
BUCKET_NAME         = getattr(settings, 'AWS_BUCKET_NAME', None)
SECURE_URLS         = getattr(settings, 'AWS_S3_SECURE_URLS', False)
BUCKET_URL          = getattr(settings, 'AWS_BUCKET_URL', ('https://' if SECURE_URLS else 'http://') + BUCKET_NAME + '.s3.amazonaws.com')
DEFAULT_ACL         = getattr(settings, 'AWS_DEFAULT_ACL', 'public')
DEFAULT_KEY_PATTERN = getattr(settings, 'AWS_DEFAULT_KEY_PATTERN', '${filename}')
DEFAULT_FORM_TIME   = getattr(settings, 'AWS_DEFAULT_FORM_LIFETIME', 36000) # 10 HOURS


class S3UploadifyBackend(BaseUploadifyBackend):
    """Uploadify for Amazon S3"""
    
    def __init__(self, request, uploadify_options={}, post_data={}, conditions={}):
        self.conditions = conditions
        super(S3UploadifyBackend, self).__init__(request, uploadify_options, post_data)
    
    def get_uploader(self):
        return BUCKET_URL
    
    def build_post_data(self):
        if 'folder' in self.options:
            key = os.path.join(self.options['folder'], DEFAULT_KEY_PATTERN)
        else:
            key = DEFAULT_KEY_PATTERN
        _set_default_if_none(self.post_data, 'key', key)
        _set_default_if_none(self.post_data, 'acl', DEFAULT_ACL)
        
        try:
            _set_default_if_none(self.post_data, 'bucket', BUCKET_NAME)
        except ValueError:
            raise ImproperlyConfigured("Bucket name is a required property.")
 
        try:
            _set_default_if_none(self.post_data, 'AWSAccessKeyId', ACCESS_KEY_ID)
        except ValueError:
            raise ImproperlyConfigured("AWS Access Key ID is a required property.")

        self.conditions = build_conditions(self.options, self.post_data, self.conditions)

        if not SECRET_ACCESS_KEY:
            raise ImproperlyConfigured("AWS Secret Access Key is a required property.")
        
        expiration_time = datetime.utcnow() + timedelta(seconds=DEFAULT_FORM_TIME)
        self.policy_string = build_post_policy(expiration_time, self.conditions)
        self.policy = base64.b64encode(self.policy_string)
         
        self.signature = base64.encodestring(hmac.new(SECRET_ACCESS_KEY, self.policy, hashlib.sha1).digest()).strip()
        
        self.post_data['policy'] = self.policy
        self.post_data['signature'] = self.signature


def build_conditions(options, post_data, conditions):
    # PASS_THRU_OPTIONS are Uploadify options that if set in the settings are 
    # passed into the POST. As a result, a default policy condition is created here.
    for opt in PASS_THRU_OPTIONS:
        if opt in options and opt not in conditions:
            conditions[opt] = None

    # FILTERED_KEYS are those created by Uploadify and passed into the POST on submit.
    # As a result, a default policy condition is created here.
    for opt in FILTERED_KEYS:
        if opt not in conditions:
            conditions[opt] = None

    conds = post_data.copy()
    conds.update(conditions)

    # EXCLUDED_KEYS are those that are set by UploadifyS3 but need to be stripped out
    # for the purposes of creating conditions.
    for key in EXCLUDED_KEYS:
        if key in conds:
            del conds[key]

    return conds

def build_post_policy(expiration_time, conditions):
    """ Function to build S3 POST policy. Adapted from Programming Amazon Web Services, Murty, pg 104-105. """
    conds = []
    for name, test in conditions.iteritems():
        if test is None:
            # A None condition value means allow anything.
            conds.append('["starts-with", "$%s", ""]' % name)
        elif isinstance(test,str) or isinstance(test, unicode):
            conds.append('{"%s": "%s" }' % (name, test))
        elif isinstance(test,list):
            conds.append('{"%s": "%s" }' % (name, ','.join(test)))
        elif isinstance(test, dict):
            operation = test['op']
            value = test['value']
            conds.append('["%s", "$%s", "%s"]' % (operation, name, value))
        elif isinstance(test,slice):
            conds.append('["%s", "%s", "%s"]' %(name, test.start, test.stop))
        else:
            raise TypeError("Unexpected value type for condition '%s': %s" % (name, type(test)))

    return '{"expiration": "%s", "conditions": [%s]}' \
            % (expiration_time.strftime("%Y-%m-%dT%H:%M:%SZ"), ', '.join(conds))
            
def _uri_encode(str):
    try:
        # The Uploadify flash component apparently decodes the scriptData once, so we need to encode twice here.
        return quote_plus(quote_plus(str, safe='~'), safe='~')
    except:
        raise ValueError


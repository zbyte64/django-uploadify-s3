from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from urllib import quote_plus
from datetime import datetime
from datetime import timedelta
import base64
import hmac
import hashlib
import json
import os

UPLOADIFY_OPTIONS = ('auto', 'buttonImg', 'buttonText', 'cancelImg', 'checkScript', 'displayData', 'expressInstall', 'fileDataName', 'fileDesc', 'fileExt', 'folder', 'height', 'hideButton', 'method', 'multi', 'queueID', 'queueSizeLimit', 'removeCompleted', 'rollover', 'script','scriptAccess', 'scriptData', 'simUploadLimit', 'sizeLimit', 'uploader', 'width', 'wmode')

UPLOADIFY_METHODS = ('onAllComplete', 'onCancel', 'onCheck', 'onClearQueue', 'onComplete', 'onError', 'onInit', 'onOpen', 'onProgress', 'onQueueFull', 'onSelect', 'onSelectOnce', 'onSWFReady')

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

BUTTON_TEXT = 'Select File'

# Defaults for required Uploadify options
DEFAULT_CANCELIMG = settings.STATIC_URL + "uploadify/uploadify-cancel.png"
DEFAULT_UPLOADER  = settings.STATIC_URL + "uploadify/uploadify.swf"

class UploadifyS3(object):
    """Uploadify for Amazon S3"""
    
    def __init__(self, uploadify_options={}, post_data={}, conditions={}):
        self.options = getattr(settings, 'UPLOADIFY_DEFAULT_OPTIONS', {})
        self.options.update(uploadify_options)
        
        if any(True for key in self.options if key not in UPLOADIFY_OPTIONS + UPLOADIFY_METHODS):
            raise ImproperlyConfigured("Attempted to initialize with unrecognized option '%s'." % key)

        _set_default_if_none(self.options, 'cancelImage', DEFAULT_CANCELIMG)
        _set_default_if_none(self.options, 'swf', DEFAULT_UPLOADER)
        _set_default_if_none(self.options, 'uploader', BUCKET_URL)
        _set_default_if_none(self.options, 'buttonText', BUTTON_TEXT)
        _set_default_if_none(self.options, 'checkExisting', False)

        self.post_data = post_data

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

        self.conditions = build_conditions(self.options, self.post_data, conditions)

        if not SECRET_ACCESS_KEY:
            raise ImproperlyConfigured("AWS Secret Access Key is a required property.")
        
        expiration_time = datetime.utcnow() + timedelta(seconds=DEFAULT_FORM_TIME)
        self.policy_string = build_post_policy(expiration_time, self.conditions)
        self.policy = base64.b64encode(self.policy_string)
         
        self.signature = base64.encodestring(hmac.new(SECRET_ACCESS_KEY, self.policy, hashlib.sha1).digest()).strip()
        
        self.post_data['policy'] = self.policy
        self.post_data['signature'] = self.signature
        self.options['scriptData'] = self.post_data
        # self.options['policyDebug'] = self.policy_string
        
    def get_options_json(self):
        # return json.dumps(self.options)
        
        subs = []
        for key in self.options:
            if key in UPLOADIFY_METHODS:
                subs.append(('"%%%s%%"' % key, self.options[key]))
                self.options[key] = "%%%s%%" % key
                
        out = json.dumps(self.options)
        
        for search, replace in subs:
            out = out.replace(search, replace)
            
        return out

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

def _set_default_if_none(dict, key, default=None):
    if key not in dict:
        if default is not None:
            dict[key] = default
        else:
            raise ValueError


from django.conf import settings

UPLOADIFY_BACKEND = getattr(settings, 'UPLOADIFY_BACKEND', 'uploadify_s3.backends.djangoview.DjangoViewBackend')
#UPLOADIFY_BACKEND = getattr(settings, 'UPLOADIFY_BACKEND', 'uploadify_s3.backends.s3.S3UploadifyBackend')


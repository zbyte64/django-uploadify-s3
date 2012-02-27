from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('uploadify_s3.views',
    url(r'^uploadify-options/$', 'uploadify_options_view', name='uploadify-options'),
    url(r'^upload/$', 'upload_file', name='uploadify-upload-file'),
    url(r'^exists/$', 'check_exists', name='uploadify-check-exists'),
)


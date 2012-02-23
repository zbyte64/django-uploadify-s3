from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('uploadify_s3.views',
    url(r'^uploadify-options/$', 'uploadify_options_view', name='uploadify-options'),
)


from django.http import HttpResponse

from uploadify_s3 import UploadifyS3

#TODO staff only? csrf?
def uploadify_options_view(request):
    return HttpResponse(UploadifyS3().get_options_json())

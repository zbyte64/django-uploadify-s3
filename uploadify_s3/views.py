from django.http import HttpResponse

from uploadify_s3 import UploadifyS3

#TODO staff only? csrf?
def uploadify_options_view(request):
    #TODO accept upload_to argument, this view would then be called per filefield
    #TODO make an uploadify backend
    uploadify_options = {}
    if 'upload_to' in request.GET:
        uploadify_options['folder'] = request.GET['upload_to']
    return HttpResponse(UploadifyS3(uploadify_options=uploadify_options).get_options_json())

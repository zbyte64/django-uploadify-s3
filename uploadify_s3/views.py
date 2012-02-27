from django.http import HttpResponse, HttpResponseBadRequest
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt

from uploadify_s3.backends import get_uploadify_backend

from urlparse import parse_qsl
import os

#TODO staff only? csrf?
def uploadify_options_view(request):
    uploadify_options = {}
    if 'upload_to' in request.GET:
        uploadify_options['folder'] = request.GET['upload_to']
    backend = get_uploadify_backend()
    json = backend(request=request, 
                   uploadify_options=uploadify_options).get_options_json()
    return HttpResponse(json)

@csrf_exempt
def upload_file(request):
    #this is handled by a different session then the user's browser
    if not request.POST:
        return HttpResponseBadRequest()
    from uploadify_s3.backends.djangoview import unsign
    data = dict(parse_qsl(unsign(request.POST['payload'])))
    assert data['request_time'] #TODO respect some expiration
    path = os.path.join(data['upload_to'], request.FILES['Filedata'].name)
    file_path = default_storage.save(path, request.FILES['Filedata']) #TODO how to tell the storage engine not to rename?
    return HttpResponse(file_path)

@csrf_exempt
def check_exists(request):
    if not request.POST:
        return HttpResponseBadRequest()
    #if default_storage.exists(request.POST['filename']):
    #    return HttpResponse('1')
    return HttpResponse('0')


from django.db import models

from widgets import UploadifyClearableFileInput

def patch_admin():
    from django.contrib.admin.options import FORMFIELD_FOR_DBFIELD_DEFAULTS
    FORMFIELD_FOR_DBFIELD_DEFAULTS[models.ImageField] = {'widget': UploadifyClearableFileInput}
    FORMFIELD_FOR_DBFIELD_DEFAULTS[models.FileField] = {'widget': UploadifyClearableFileInput}

patch_admin()
#TODO make an admin mixin instead. This is needed as the widget needs to know about the storage engine and the upload_to



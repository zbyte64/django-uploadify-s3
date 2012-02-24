from django.db import models
from django.contrib.admin import ModelAdmin

class UploadifyAdminMixin(object):
    def formfield_for_dbfield(self, db_field, **kwargs):
        if isinstance(db_field, models.FileField):
            return self.formfield_for_field_field(db_field, kwargs.pop('request', None), **kwargs)
        return ModelAdmin.formfield_for_dbfield(self, db_field, **kwargs)
    
    def formfield_for_file_field(self, db_field, request=None, **kwargs):
        """
        Get a form Field that is prepared for uploadify
        """
        #TODO kwargs['form_class'] = UploadifyFormField
        return db_field.formfield(**kwargs)

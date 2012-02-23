from django.forms.widgets import FileInput, ClearableFileInput
from django.core.files.storage import default_storage

class UploadifyFileInput(FileInput):
    class Media: #this does not work for the admin as django ignores it [WTF]
        css = ('uploadify/uploadify.css',)
        js = ('uploadify/jquery.uploadify.js', 'uploadify/widget.js')
    
    def value_from_datadict(self, data, files, name):
        "File widgets take data from FILES, not POST"
        if name in data:
            file_path = data[name]
            #TODO we need to know the storage engine of the file field
            return default_storage.open(file_path)
        return super(UploadifyFileInput, self).value_from_datadict(data, files, name)
    
    def render(self, name, value, attrs=None):
        attrs = attrs or {}
        attrs['class'] = 'uploadify'
        return super(UploadifyFileInput, self).render(name, value, attrs)

class UploadifyClearableFileInput(ClearableFileInput):
    class Media: #this does not work for the admin as django ignores it [WTF]
        css = ('uploadify/uploadify.css',)
        js = ('uploadify/jquery.uploadify.js', 'uploadify/widget.js')
    
    def value_from_datadict(self, data, files, name):
        "File widgets take data from FILES, not POST"
        if name in data:
            file_path = data[name]
            #TODO we need to know the storage engine of the file field
            return default_storage.open(file_path)
        return super(UploadifyClearableFileInput, self).value_from_datadict(data, files, name)
    
    def render(self, name, value, attrs=None):
        attrs = attrs or {}
        attrs['class'] = 'uploadify'
        return super(UploadifyClearableFileInput, self).render(name, value, attrs)


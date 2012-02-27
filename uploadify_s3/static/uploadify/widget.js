function make_file_fields_dynamic($, options_url) {
    $('.uploadifyinput').each(function() {
        var $this = $(this);
        var form = $this.parents('form');
        var upload_to = $this.attr('data-upload-to');
        if (upload_to.substr(-1) != '/') {
            upload_to += '/';
        }
        //TODO if upload_to has already been seen, don't hit the wire
        $.getJSON(options_url, {'upload_to': upload_to}, function(data) {
            var options = data;
            
            function init_form() {
                if (form.data('uploadify_init')) {
                    return
                }
                form.data('pending_uploads', {});
                form.data('submit', false);
                form.submit(function() {
                    if ($.isEmptyObject(form.data('pending_uploads'))) {
                        form.find('.uploadify').replaceWith(function() {
                            var path = $(this).data('path')
                            if (path) {
                                var fname = $(this).attr('id').substr(3) //uploadify is nice enough to nuke this variable /s
                                return '<input type="hidden" name="'+fname+'" id="'+$(this).attr('id')+'" value="'+path+'"/>';
                            }
                        });
                        return true;
                    }
                    form.data('submit', true);
                    return false;
                });
                form.data('uploadify_init', true);
            }
            
            function on_upload_success(file, data, response) {
                delete form.data('pending_uploads')[this.id];
                if (data) {
                    $('#'+this.id).data('path', data); //store the actuall path
                } else {
                    $('#'+this.id).data('path', upload_to + file.name);
                }
                if ($.isEmptyObject(form.data('pending_uploads')) && form.data('submit')) {
                    form.submit();
                }
            }
            
            function on_select() {
                if (!form.data('uploadify_init')) { //hack around
                    init_form()
                }
                form.data('pending_uploads')[this.id] = true;
            }
            
            function on_upload_error(file,errorCode,errorMsg,errorString, queue) {
                delete form.data('pending_uploads')[this.id];
            }
            
            function on_upload_cancel() {
                delete form.data('pending_uploads')[this.id];
            }
            
            options['onUploadSuccess'] = on_upload_success;
            options['onSelect'] = on_select;
            options['onUploadError'] = on_upload_error;
            options['onUploadCancel'] = on_upload_cancel;
            options['onSWFReady'] = init_form; //this may not work
            /* Uploadify Setup */
            options['auto'] = true;
            options['multi'] = false;
            options['removeCompleted'] = false;
            options['uploadLimit'] = 1;
            $this.uploadify(options);
        });
    });
}



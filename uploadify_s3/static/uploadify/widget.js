function make_file_fields_dynamic($, options_url) {
    $.getJSON(options_url, function(data) {
        $('form:has(.uploadifyinput)').each(function() {
            var form = $(this);
            var options = data;
            
            function init_form() {
                console.log('init plz')
                if (form.data('uploadify_init')) {
                    console.log('aready init')
                    return
                }
                form.data('pending_uploads', {})
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
                console.log('init_form')
            }
            
            function on_all_complete(status) {
                //$('#'+this.id).data('path', name)
                
                console.log(['on_all_complete', this, status, form.data('pending_uploads')])
            }
            
            function on_complete(file, queue) {
                delete form.data('pending_uploads')[this.id];
                $('#'+this.id).data('path', file.name)
                if ($.isEmptyObject(form.data('pending_uploads')) && form.data('submit')) {
                    form.submit();
                }
                console.log([this, file, queue, form.data('pending_uploads')])
                
                //event.name
                
            }
            
            function on_select() {
                if (!form.data('uploadify_init')) { //hack around
                    init_form()
                }
                form.data('pending_uploads')[this.id] = true;
                console.log('on_select', form.data('pending_uploads'))
            }
            
            function on_upload_error(file,errorCode,errorMsg,errorString, queue) {
                delete form.data('pending_uploads')[this.id];
                console.log(['error', errorCode, errorMsg, errorString])
            }
            
            function on_upload_cancel() {
                delete form.data('pending_uploads')[this.id];
            }
            
            options['onQueueComplete'] = on_all_complete;
            options['onUploadComplete'] = on_complete;
            options['onSelect'] = on_select;
            options['onUploadError'] = on_upload_error;
            options['onUploadCancel'] = on_upload_cancel;
            options['onSWFReady'] = init_form; //this may not work
            /* Uploadify Setup */
            options['auto'] = true;
            options['multi'] = false;
            options['removeCompleted'] = false;
            options['uploadLimit'] = 1;
            var fields = form.find('.uploadifyinput');
            fields.uploadify(options);
        });
    });
}



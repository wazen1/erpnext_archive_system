// Archive Document JavaScript
frappe.ready(function() {
    // Archive Document functionality
    frappe.archive_document = {
        init: function() {
            this.setup_form_events();
        },
        
        setup_form_events: function() {
            // Setup form-specific event handlers
            $(document).on('change', '[data-fieldname="category"]', function() {
                frappe.archive_document.update_subcategories();
            });
            
            $(document).on('click', '.btn-upload-document', function() {
                frappe.archive_document.upload_document();
            });
        },
        
        update_subcategories: function() {
            var category = frappe.get_doc('Archive Document').category;
            if (category) {
                frappe.call({
                    method: 'erpnext_archive_system.api.archive_api.get_subcategories',
                    args: { category: category },
                    callback: function(r) {
                        if (r.message) {
                            frappe.archive_document.populate_subcategories(r.message);
                        }
                    }
                });
            }
        },
        
        populate_subcategories: function(subcategories) {
            var subcategory_field = frappe.meta.get_docfield('Archive Document', 'subcategory');
            if (subcategory_field) {
                subcategory_field.options = subcategories.join('\n');
                frappe.model.clear_doc('Archive Document');
            }
        },
        
        upload_document: function() {
            // Handle document upload
            frappe.upload.make({
                doctype: 'Archive Document',
                docname: frappe.get_doc('Archive Document').name,
                fieldname: 'file',
                callback: function(attachment) {
                    frappe.show_alert({
                        message: __('Document uploaded successfully'),
                        indicator: 'green'
                    });
                }
            });
        }
    };
    
    // Initialize archive document functionality
    frappe.archive_document.init();
});
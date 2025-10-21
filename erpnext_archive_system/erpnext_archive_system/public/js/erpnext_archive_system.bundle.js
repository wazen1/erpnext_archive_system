// ERPNext Archive System Bundle
// This file combines all the archive system functionality

// Main archive system functionality
frappe.ready(function() {
    console.log("ERPNext Archive System assets loaded");
    
    // Archive System initialization
    frappe.archive_system = {
        init: function() {
            console.log("Archive System initialized");
        }
    };
    
    // Initialize when page loads
    frappe.archive_system.init();
});

// Archive Dashboard functionality
frappe.ready(function() {
    // Archive Dashboard functionality
    frappe.archive_dashboard = {
        init: function() {
            this.setup_event_handlers();
            this.load_dashboard_data();
        },
        
        setup_event_handlers: function() {
            // Add event handlers for dashboard interactions
            $(document).on('click', '.archive-document-card', function() {
                frappe.archive_dashboard.open_document($(this).data('document-id'));
            });
        },
        
        load_dashboard_data: function() {
            // Load dashboard data via AJAX
            frappe.call({
                method: 'erpnext_archive_system.api.archive_api.get_dashboard_data',
                callback: function(r) {
                    if (r.message) {
                        frappe.archive_dashboard.render_dashboard(r.message);
                    }
                }
            });
        },
        
        render_dashboard: function(data) {
            // Render dashboard with data
            console.log('Rendering dashboard with data:', data);
        },
        
        open_document: function(document_id) {
            // Open document in new form
            frappe.set_route('Form', 'Archive Document', document_id);
        }
    };
    
    // Initialize dashboard
    frappe.archive_dashboard.init();
});

// Archive Document functionality
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
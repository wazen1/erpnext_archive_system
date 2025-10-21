// Archive Dashboard JavaScript
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
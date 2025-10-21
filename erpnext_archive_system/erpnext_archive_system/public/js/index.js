// Main entry point for ERPNext Archive System
import './erpnext_archive_system.js';
import './archive_dashboard.js';
import './archive_document.js';

// Export main functionality
window.ArchiveSystem = {
    version: '1.0.0',
    init: function() {
        console.log('Archive System v' + this.version + ' initialized');
    }
};

// Auto-initialize
frappe.ready(function() {
    window.ArchiveSystem.init();
});
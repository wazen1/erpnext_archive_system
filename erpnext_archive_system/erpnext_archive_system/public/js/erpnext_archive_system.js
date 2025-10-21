// ERPNext Archive System JavaScript
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

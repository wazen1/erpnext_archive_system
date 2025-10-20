import frappe
from frappe import _
import os

def after_install():
	"""Setup tasks after app installation"""
	
	# Create default categories
	create_default_categories()
	
	# Create default document types
	create_default_document_types()
	
	# Create default roles
	create_default_roles()
	
	# Create default category rules
	create_default_category_rules()
	
	# Setup permissions
	setup_permissions()
	
	# Create sample data
	create_sample_data()
	
	frappe.db.commit()
	frappe.msgprint(_("Archive System installed successfully!"))

def create_default_categories():
	"""Create default categories"""
	default_categories = [
		{
			"category_name": "Financial",
			"category_code": "FIN",
			"description": "Financial documents and records",
			"color": "#e74c3c",
			"icon": "fas fa-dollar-sign",
			"retention_policy": 7
		},
		{
			"category_name": "Legal",
			"category_code": "LEG",
			"description": "Legal documents and contracts",
			"color": "#9b59b6",
			"icon": "fas fa-gavel",
			"retention_policy": 10
		},
		{
			"category_name": "HR",
			"category_code": "HR",
			"description": "Human resources documents",
			"color": "#3498db",
			"icon": "fas fa-users",
			"retention_policy": 7
		},
		{
			"category_name": "Technical",
			"category_code": "TECH",
			"description": "Technical documentation and specifications",
			"color": "#f39c12",
			"icon": "fas fa-cogs",
			"retention_policy": 5
		},
		{
			"category_name": "Administrative",
			"category_code": "ADMIN",
			"description": "Administrative documents and procedures",
			"color": "#95a5a6",
			"icon": "fas fa-clipboard",
			"retention_policy": 3
		},
		{
			"category_name": "General",
			"category_code": "GEN",
			"description": "General documents",
			"color": "#2ecc71",
			"icon": "fas fa-file",
			"retention_policy": 5
		}
	]
	
	for category_data in default_categories:
		if not frappe.db.exists("Archive Category", {"category_name": category_data["category_name"]}):
			category = frappe.get_doc({
				"doctype": "Archive Category",
				**category_data
			})
			category.insert(ignore_permissions=True)

def create_default_document_types():
	"""Create default document types"""
	default_types = [
		{
			"document_type_name": "Invoice",
			"document_type_code": "INV",
			"description": "Financial invoices and bills",
			"allowed_file_types": "pdf,jpg,png",
			"max_file_size": 10,
			"requires_ocr": True,
			"retention_period": 7,
			"access_level": "Internal",
			"encryption_required": False,
			"compliance_required": True,
			"icon": "fas fa-file-invoice"
		},
		{
			"document_type_name": "Contract",
			"document_type_code": "CON",
			"description": "Legal contracts and agreements",
			"allowed_file_types": "pdf,doc,docx",
			"max_file_size": 25,
			"requires_ocr": True,
			"retention_period": 10,
			"access_level": "Confidential",
			"encryption_required": True,
			"compliance_required": True,
			"icon": "fas fa-file-contract"
		},
		{
			"document_type_name": "Employee Record",
			"document_type_code": "EMP",
			"description": "Employee personal records",
			"allowed_file_types": "pdf,jpg,png,doc,docx",
			"max_file_size": 15,
			"requires_ocr": True,
			"retention_period": 7,
			"access_level": "Confidential",
			"encryption_required": True,
			"compliance_required": True,
			"icon": "fas fa-user"
		},
		{
			"document_type_name": "Technical Manual",
			"document_type_code": "TECH",
			"description": "Technical documentation and manuals",
			"allowed_file_types": "pdf,doc,docx,txt",
			"max_file_size": 50,
			"requires_ocr": False,
			"retention_period": 5,
			"access_level": "Internal",
			"encryption_required": False,
			"compliance_required": False,
			"icon": "fas fa-book"
		},
		{
			"document_type_name": "Policy Document",
			"document_type_code": "POL",
			"description": "Company policies and procedures",
			"allowed_file_types": "pdf,doc,docx",
			"max_file_size": 20,
			"requires_ocr": False,
			"retention_period": 3,
			"access_level": "Internal",
			"encryption_required": False,
			"compliance_required": False,
			"icon": "fas fa-clipboard-list"
		}
	]
	
	for type_data in default_types:
		if not frappe.db.exists("Archive Document Type", {"document_type_name": type_data["document_type_name"]}):
			doc_type = frappe.get_doc({
				"doctype": "Archive Document Type",
				**type_data
			})
			doc_type.insert(ignore_permissions=True)

def create_default_roles():
	"""Create default roles for the archive system"""
	roles = [
		{
			"role_name": "Archive User",
			"desk_access": 1,
			"is_custom": 1,
			"restrict_to_domain": None
		},
		{
			"role_name": "Archive Viewer",
			"desk_access": 1,
			"is_custom": 1,
			"restrict_to_domain": None
		},
		{
			"role_name": "Archive Manager",
			"desk_access": 1,
			"is_custom": 1,
			"restrict_to_domain": None
		}
	]
	
	for role_data in roles:
		if not frappe.db.exists("Role", role_data["role_name"]):
			role = frappe.get_doc({
				"doctype": "Role",
				**role_data
			})
			role.insert(ignore_permissions=True)

def create_default_category_rules():
	"""Create default auto-categorization rules"""
	rules = [
		{
			"rule_name": "Financial Documents",
			"rule_type": "Keyword",
			"keyword": "invoice",
			"priority": 1,
			"description": "Auto-categorize documents containing 'invoice' as Financial"
		},
		{
			"rule_name": "Legal Documents",
			"rule_type": "Keyword",
			"keyword": "contract",
			"priority": 1,
			"description": "Auto-categorize documents containing 'contract' as Legal"
		},
		{
			"rule_name": "HR Documents",
			"rule_type": "Keyword",
			"keyword": "employee",
			"priority": 1,
			"description": "Auto-categorize documents containing 'employee' as HR"
		},
		{
			"rule_name": "Technical Documents",
			"rule_type": "Keyword",
			"keyword": "manual",
			"priority": 1,
			"description": "Auto-categorize documents containing 'manual' as Technical"
		}
	]
	
	for rule_data in rules:
		if not frappe.db.exists("Archive Category Rule", {"rule_name": rule_data["rule_name"]}):
			rule = frappe.get_doc({
				"doctype": "Archive Category Rule",
				**rule_data
			})
			rule.insert(ignore_permissions=True)

def setup_permissions():
	"""Setup default permissions for roles"""
	# This would typically be done through the Role Permission Manager
	# For now, we'll create basic permissions
	pass

def create_sample_data():
	"""Create sample data for demonstration"""
	# Create sample subcategories
	sample_subcategories = [
		{
			"subcategory_name": "Invoices",
			"parent_category": "Financial",
			"description": "Customer and vendor invoices",
			"color": "#e74c3c"
		},
		{
			"subcategory_name": "Contracts",
			"parent_category": "Legal",
			"description": "Legal contracts and agreements",
			"color": "#9b59b6"
		},
		{
			"subcategory_name": "Employee Files",
			"parent_category": "HR",
			"description": "Individual employee records",
			"color": "#3498db"
		},
		{
			"subcategory_name": "User Manuals",
			"parent_category": "Technical",
			"description": "User and technical manuals",
			"color": "#f39c12"
		}
	]
	
	for subcategory_data in sample_subcategories:
		# Get parent category
		parent_category = frappe.get_value("Archive Category", 
			{"category_name": subcategory_data["parent_category"]}, "name")
		
		if parent_category and not frappe.db.exists("Archive Subcategory", 
			{"subcategory_name": subcategory_data["subcategory_name"]}):
			subcategory = frappe.get_doc({
				"doctype": "Archive Subcategory",
				"subcategory_name": subcategory_data["subcategory_name"],
				"parent_category": parent_category,
				"description": subcategory_data["description"],
				"color": subcategory_data["color"]
			})
			subcategory.insert(ignore_permissions=True)
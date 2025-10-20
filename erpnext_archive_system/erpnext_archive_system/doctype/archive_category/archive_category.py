import frappe
from frappe.model.document import Document
from frappe import _
import json

class ArchiveCategory(Document):
	def validate(self):
		"""Validate category before saving"""
		self.validate_category_code()
		self.validate_parent_category()
		self.set_default_values()
	
	def before_save(self):
		"""Process before saving"""
		self.update_modified_info()
	
	def after_insert(self):
		"""Process after category creation"""
		self.create_audit_log("Category Created")
	
	def on_trash(self):
		"""Process before category deletion"""
		self.validate_category_deletion()
		self.create_audit_log("Category Deleted")
	
	def validate_category_code(self):
		"""Ensure category code is unique"""
		if self.category_code:
			if frappe.db.exists("Archive Category", {"category_code": self.category_code, "name": ["!=", self.name]}):
				frappe.throw(_("Category Code {0} already exists").format(self.category_code))
	
	def validate_parent_category(self):
		"""Validate parent category selection"""
		if self.parent_category:
			if self.parent_category == self.name:
				frappe.throw(_("Category cannot be its own parent"))
			
			# Check for circular reference
			parent = frappe.get_doc("Archive Category", self.parent_category)
			if self.is_child_of(parent.name):
				frappe.throw(_("Circular reference detected in category hierarchy"))
	
	def is_child_of(self, parent_name):
		"""Check if current category is child of given parent"""
		if not self.parent_category:
			return False
		
		if self.parent_category == parent_name:
			return True
		
		parent = frappe.get_doc("Archive Category", self.parent_category)
		return parent.is_child_of(parent_name)
	
	def set_default_values(self):
		"""Set default values"""
		if not self.category_code:
			self.category_code = self.category_name.lower().replace(" ", "_")
		
		if not self.color:
			self.color = "#3498db"  # Default blue color
	
	def update_modified_info(self):
		"""Update modification information"""
		if not self.created_by:
			self.created_by = frappe.session.user
			self.created_on = frappe.utils.now()
		
		self.last_modified_by = frappe.session.user
		self.last_modified_on = frappe.utils.now()
	
	def validate_category_deletion(self):
		"""Validate if category can be deleted"""
		# Check if category has child categories
		child_categories = frappe.get_all("Archive Category", filters={"parent_category": self.name})
		if child_categories:
			frappe.throw(_("Cannot delete category with child categories. Please delete child categories first."))
		
		# Check if category has documents
		documents = frappe.get_all("Archive Document", filters={"category": self.name})
		if documents:
			frappe.throw(_("Cannot delete category with documents. Please move or delete documents first."))
	
	def create_audit_log(self, action):
		"""Create audit log entry"""
		audit_entry = {
			"doctype": "Archive Audit Trail",
			"action": f"Category {action}",
			"category_id": self.name,
			"user": frappe.session.user,
			"timestamp": frappe.utils.now(),
			"ip_address": frappe.local.request.environ.get('REMOTE_ADDR') if frappe.local.request else "System",
			"details": f"Category '{self.category_name}' {action.lower()}"
		}
		
		audit_doc = frappe.get_doc(audit_entry)
		audit_doc.insert(ignore_permissions=True)
	
	def get_child_categories(self):
		"""Get all child categories"""
		children = frappe.get_all("Archive Category", 
			filters={"parent_category": self.name, "is_active": 1},
			fields=["name", "category_name", "description", "color", "icon"]
		)
		return children
	
	def get_document_count(self):
		"""Get count of documents in this category"""
		count = frappe.db.count("Archive Document", {"category": self.name})
		return count
	
	def get_category_hierarchy(self):
		"""Get full category hierarchy"""
		hierarchy = []
		current = self
		
		while current:
			hierarchy.insert(0, {
				"name": current.name,
				"category_name": current.category_name,
				"category_code": current.category_code
			})
			if current.parent_category:
				current = frappe.get_doc("Archive Category", current.parent_category)
			else:
				current = None
		
		return hierarchy
	
	def apply_auto_categorization(self, document_content, document_title=""):
		"""Apply auto categorization rules"""
		if not self.auto_categorization_rules:
			return False
		
		content_to_check = f"{document_title} {document_content}".lower()
		
		for rule in self.auto_categorization_rules:
			if rule.rule_type == "Keyword":
				if rule.keyword.lower() in content_to_check:
					return True
			elif rule.rule_type == "Pattern":
				import re
				if re.search(rule.pattern, content_to_check):
					return True
			elif rule.rule_type == "Document Type":
				# This would need to be implemented based on document type detection
				pass
		
		return False

@frappe.whitelist()
def get_category_tree():
	"""Get category tree structure"""
	def build_tree(parent=None):
		categories = frappe.get_all("Archive Category",
			filters={"parent_category": parent, "is_active": 1},
			fields=["name", "category_name", "description", "color", "icon", "parent_category"],
			order_by="category_name"
		)
		
		for category in categories:
			category["children"] = build_tree(category.name)
			category["document_count"] = frappe.db.count("Archive Document", {"category": category.name})
		
		return categories
	
	return build_tree()

@frappe.whitelist()
def get_category_documents(category_name, limit=20, offset=0):
	"""Get documents in a category"""
	documents = frappe.get_all("Archive Document",
		filters={"category": category_name},
		fields=["name", "document_id", "document_title", "status", "created_on", "access_level"],
		limit=limit,
		start=offset,
		order_by="created_on desc"
	)
	
	return documents

@frappe.whitelist()
def auto_categorize_document(document_name):
	"""Auto categorize a document based on rules"""
	doc = frappe.get_doc("Archive Document", document_name)
	
	# Get all active categories
	categories = frappe.get_all("Archive Category", 
		filters={"is_active": 1},
		fields=["name", "category_name"]
	)
	
	content = f"{doc.document_title} {doc.description or ''} {doc.ocr_text or ''}"
	
	for category in categories:
		category_doc = frappe.get_doc("Archive Category", category.name)
		if category_doc.apply_auto_categorization(content, doc.document_title):
			doc.category = category.name
			doc.save()
			return {"status": "success", "category": category.category_name}
	
	return {"status": "no_match", "message": "No matching category found"}

@frappe.whitelist()
def get_category_statistics():
	"""Get category statistics"""
	stats = frappe.db.sql("""
		SELECT 
			c.name,
			c.category_name,
			c.color,
			COUNT(d.name) as document_count,
			COUNT(CASE WHEN d.status = 'Active' THEN 1 END) as active_documents,
			COUNT(CASE WHEN d.access_level = 'Confidential' THEN 1 END) as confidential_documents
		FROM `tabArchive Category` c
		LEFT JOIN `tabArchive Document` d ON c.name = d.category
		WHERE c.is_active = 1
		GROUP BY c.name, c.category_name, c.color
		ORDER BY document_count DESC
	""", as_dict=True)
	
	return stats
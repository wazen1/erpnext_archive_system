import frappe
from frappe.model.document import Document
from frappe import _

class ArchiveSubcategory(Document):
	def validate(self):
		"""Validate subcategory before saving"""
		self.validate_subcategory_code()
		self.validate_parent_category()
		self.set_default_values()
		self.set_audit_info()
	
	def before_save(self):
		"""Process before saving"""
		self.update_modified_info()
	
	def after_insert(self):
		"""Process after subcategory creation"""
		self.create_subcategory_audit_log("Subcategory Created")
	
	def on_trash(self):
		"""Process before subcategory deletion"""
		self.validate_subcategory_deletion()
		self.create_subcategory_audit_log("Subcategory Deleted")
	
	def validate_subcategory_code(self):
		"""Ensure subcategory code is unique"""
		if self.subcategory_code:
			if frappe.db.exists("Archive Subcategory", {"subcategory_code": self.subcategory_code, "name": ["!=", self.name]}):
				frappe.throw(_("Subcategory Code {0} already exists").format(self.subcategory_code))
	
	def validate_parent_category(self):
		"""Validate parent category exists and is active"""
		if self.parent_category:
			parent = frappe.get_doc("Archive Category", self.parent_category)
			if not parent.is_active:
				frappe.throw(_("Parent category is not active"))
	
	def set_default_values(self):
		"""Set default values"""
		if not self.subcategory_code:
			self.subcategory_code = self.subcategory_name.lower().replace(" ", "_")
		
		if not self.color:
			self.color = "#95a5a6"  # Default gray color
	
	def set_audit_info(self):
		"""Set audit information"""
		if not self.created_by:
			self.created_by = frappe.session.user
			self.created_on = frappe.utils.now()
	
	def update_modified_info(self):
		"""Update modification information"""
		self.last_modified_by = frappe.session.user
		self.last_modified_on = frappe.utils.now()
	
	def validate_subcategory_deletion(self):
		"""Validate if subcategory can be deleted"""
		# Check if subcategory has documents
		documents = frappe.get_all("Archive Document", filters={"subcategory": self.name})
		if documents:
			frappe.throw(_("Cannot delete subcategory with documents. Please move or delete documents first."))
	
	def create_subcategory_audit_log(self, action):
		"""Create subcategory audit log entry"""
		audit_entry = {
			"doctype": "Archive Audit Trail",
			"action": f"Subcategory {action}",
			"category_id": self.parent_category,
			"user": frappe.session.user,
			"timestamp": frappe.utils.now(),
			"ip_address": frappe.local.request.environ.get('REMOTE_ADDR') if frappe.local.request else "System",
			"details": f"Subcategory '{self.subcategory_name}' {action.lower()}"
		}
		
		audit_doc = frappe.get_doc(audit_entry)
		audit_doc.insert(ignore_permissions=True)
	
	def get_document_count(self):
		"""Get count of documents in this subcategory"""
		count = frappe.db.count("Archive Document", {"subcategory": self.name})
		return count
	
	def get_subcategory_hierarchy(self):
		"""Get full subcategory hierarchy including parent category"""
		hierarchy = []
		
		# Add parent category info
		if self.parent_category:
			parent = frappe.get_doc("Archive Category", self.parent_category)
			hierarchy.append({
				"name": parent.name,
				"category_name": parent.category_name,
				"category_code": parent.category_code,
				"level": "category"
			})
		
		# Add current subcategory
		hierarchy.append({
			"name": self.name,
			"subcategory_name": self.subcategory_name,
			"subcategory_code": self.subcategory_code,
			"level": "subcategory"
		})
		
		return hierarchy

@frappe.whitelist()
def create_subcategory(subcategory_name, parent_category, **kwargs):
	"""Create a new subcategory"""
	try:
		subcategory_doc = frappe.get_doc({
			"doctype": "Archive Subcategory",
			"subcategory_name": subcategory_name,
			"parent_category": parent_category,
			"description": kwargs.get("description", ""),
			"subcategory_code": kwargs.get("subcategory_code", ""),
			"color": kwargs.get("color", ""),
			"icon": kwargs.get("icon", ""),
			"is_active": kwargs.get("is_active", True),
			"retention_policy": kwargs.get("retention_policy", 0),
			"access_restrictions": kwargs.get("access_restrictions", "")
		})
		
		subcategory_doc.insert(ignore_permissions=True)
		
		return {"status": "success", "subcategory_name": subcategory_doc.name}
		
	except Exception as e:
		frappe.log_error(f"Error creating subcategory: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_subcategories_by_category(category_name):
	"""Get all subcategories for a specific category"""
	try:
		subcategories = frappe.get_all("Archive Subcategory",
			filters={"parent_category": category_name, "is_active": 1},
			fields=["name", "subcategory_name", "subcategory_code", "description", "color", "icon"],
			order_by="subcategory_name"
		)
		
		# Add document count for each subcategory
		for subcategory in subcategories:
			subcategory["document_count"] = frappe.db.count("Archive Document", {"subcategory": subcategory.name})
		
		return subcategories
		
	except Exception as e:
		frappe.log_error(f"Error getting subcategories: {str(e)}")
		return []

@frappe.whitelist()
def get_subcategory_statistics():
	"""Get subcategory statistics"""
	try:
		stats = frappe.db.sql("""
			SELECT 
				s.name,
				s.subcategory_name,
				s.parent_category,
				c.category_name,
				COUNT(d.name) as document_count,
				COUNT(CASE WHEN d.status = 'Active' THEN 1 END) as active_documents
			FROM `tabArchive Subcategory` s
			LEFT JOIN `tabArchive Category` c ON s.parent_category = c.name
			LEFT JOIN `tabArchive Document` d ON s.name = d.subcategory
			WHERE s.is_active = 1
			GROUP BY s.name, s.subcategory_name, s.parent_category, c.category_name
			ORDER BY document_count DESC
		""", as_dict=True)
		
		return stats
		
	except Exception as e:
		frappe.log_error(f"Error getting subcategory statistics: {str(e)}")
		return []

@frappe.whitelist()
def get_subcategory_hierarchy():
	"""Get complete subcategory hierarchy"""
	try:
		hierarchy = frappe.db.sql("""
			SELECT 
				c.name as category_name,
				c.category_name as category_display_name,
				c.color as category_color,
				s.name as subcategory_name,
				s.subcategory_name as subcategory_display_name,
				s.color as subcategory_color,
				COUNT(d.name) as document_count
			FROM `tabArchive Category` c
			LEFT JOIN `tabArchive Subcategory` s ON c.name = s.parent_category
			LEFT JOIN `tabArchive Document` d ON s.name = d.subcategory
			WHERE c.is_active = 1 AND (s.is_active = 1 OR s.is_active IS NULL)
			GROUP BY c.name, c.category_name, c.color, s.name, s.subcategory_name, s.color
			ORDER BY c.category_name, s.subcategory_name
		""", as_dict=True)
		
		# Organize into hierarchical structure
		categories = {}
		for item in hierarchy:
			category_name = item.category_name
			if category_name not in categories:
				categories[category_name] = {
					"category_name": item.category_display_name,
					"color": item.category_color,
					"subcategories": [],
					"total_documents": 0
				}
			
			if item.subcategory_name:
				categories[category_name]["subcategories"].append({
					"subcategory_name": item.subcategory_display_name,
					"color": item.subcategory_color,
					"document_count": item.document_count
				})
				categories[category_name]["total_documents"] += item.document_count
		
		return list(categories.values())
		
	except Exception as e:
		frappe.log_error(f"Error getting subcategory hierarchy: {str(e)}")
		return []
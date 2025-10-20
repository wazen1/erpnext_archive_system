import frappe
from frappe.model.document import Document
from frappe import _

class ArchiveRelatedDocument(Document):
	def validate(self):
		"""Validate related document entry"""
		self.validate_related_document()
		self.set_audit_info()
	
	def before_save(self):
		"""Process before saving"""
		self.update_modified_info()
	
	def after_insert(self):
		"""Process after related document creation"""
		self.create_relationship_audit_log("Relationship Created")
	
	def on_trash(self):
		"""Process before related document deletion"""
		self.create_relationship_audit_log("Relationship Deleted")
	
	def validate_related_document(self):
		"""Validate that related document exists and is different from parent"""
		if self.related_document_id:
			# Check if related document exists
			if not frappe.db.exists("Archive Document", self.related_document_id):
				frappe.throw(_("Related document {0} does not exist").format(self.related_document_id))
			
			# Check if it's not the same as parent document
			if self.parent and self.related_document_id == self.parent:
				frappe.throw(_("Document cannot be related to itself"))
			
			# Check for duplicate relationship
			existing = frappe.get_all("Archive Related Document",
				filters={
					"parent": self.parent,
					"related_document_id": self.related_document_id,
					"relationship_type": self.relationship_type,
					"name": ["!=", self.name]
				}
			)
			
			if existing:
				frappe.throw(_("This relationship already exists"))
	
	def set_audit_info(self):
		"""Set audit information"""
		if not self.created_by:
			self.created_by = frappe.session.user
			self.created_on = frappe.utils.now()
	
	def update_modified_info(self):
		"""Update modification information"""
		self.last_modified_by = frappe.session.user
		self.last_modified_on = frappe.utils.now()
	
	def create_relationship_audit_log(self, action):
		"""Create relationship audit log entry"""
		audit_entry = {
			"doctype": "Archive Audit Trail",
			"action": f"Relationship {action}",
			"document_id": self.parent,
			"user": frappe.session.user,
			"timestamp": frappe.utils.now(),
			"ip_address": frappe.local.request.environ.get('REMOTE_ADDR') if frappe.local.request else "System",
			"details": f"Relationship {action}: {self.relationship_type} -> {self.related_document_id}"
		}
		
		audit_doc = frappe.get_doc(audit_entry)
		audit_doc.insert(ignore_permissions=True)
	
	def get_related_document_info(self):
		"""Get information about the related document"""
		try:
			related_doc = frappe.get_doc("Archive Document", self.related_document_id)
			return {
				"document_id": related_doc.document_id,
				"document_title": related_doc.document_title,
				"category": related_doc.category,
				"status": related_doc.status,
				"access_level": related_doc.access_level,
				"created_on": related_doc.created_on
			}
		except Exception as e:
			frappe.log_error(f"Error getting related document info: {str(e)}")
			return {}

@frappe.whitelist()
def add_relationship(parent_document, related_document_id, relationship_type, notes=""):
	"""Add a relationship between documents"""
	try:
		# Validate parent document exists
		if not frappe.db.exists("Archive Document", parent_document):
			return {"status": "error", "message": "Parent document not found"}
		
		# Validate related document exists
		if not frappe.db.exists("Archive Document", related_document_id):
			return {"status": "error", "message": "Related document not found"}
		
		# Check for existing relationship
		existing = frappe.get_all("Archive Related Document",
			filters={
				"parent": parent_document,
				"related_document_id": related_document_id,
				"relationship_type": relationship_type
			}
		)
		
		if existing:
			return {"status": "error", "message": "Relationship already exists"}
		
		# Create relationship
		relationship_doc = frappe.get_doc({
			"doctype": "Archive Related Document",
			"parent": parent_document,
			"parentfield": "related_documents",
			"parenttype": "Archive Document",
			"related_document_id": related_document_id,
			"relationship_type": relationship_type,
			"notes": notes
		})
		
		relationship_doc.insert(ignore_permissions=True)
		
		# Create reverse relationship if applicable
		reverse_relationships = {
			"Supersedes": "Superseded By",
			"Superseded By": "Supersedes",
			"References": "Referenced By",
			"Referenced By": "References",
			"Part Of": "Contains",
			"Contains": "Part Of",
			"Version Of": "Original Of",
			"Original Of": "Version Of"
		}
		
		if relationship_type in reverse_relationships:
			reverse_relationship_doc = frappe.get_doc({
				"doctype": "Archive Related Document",
				"parent": related_document_id,
				"parentfield": "related_documents",
				"parenttype": "Archive Document",
				"related_document_id": parent_document,
				"relationship_type": reverse_relationships[relationship_type],
				"notes": f"Reverse of: {notes}" if notes else "Reverse relationship"
			})
			
			reverse_relationship_doc.insert(ignore_permissions=True)
		
		return {"status": "success", "message": "Relationship added successfully"}
		
	except Exception as e:
		frappe.log_error(f"Error adding relationship: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_document_relationships(document_id, relationship_type=None):
	"""Get all relationships for a document"""
	try:
		filters = {"parent": document_id}
		if relationship_type:
			filters["relationship_type"] = relationship_type
		
		relationships = frappe.get_all("Archive Related Document",
			filters=filters,
			fields=["name", "related_document_id", "relationship_type", "notes", "created_on"],
			order_by="created_on desc"
		)
		
		# Get related document details
		for rel in relationships:
			rel["related_document_info"] = get_related_document_info(rel["related_document_id"])
		
		return relationships
		
	except Exception as e:
		frappe.log_error(f"Error getting document relationships: {str(e)}")
		return []

@frappe.whitelist()
def get_related_document_info(document_id):
	"""Get basic information about a related document"""
	try:
		doc = frappe.get_doc("Archive Document", document_id)
		return {
			"document_id": doc.document_id,
			"document_title": doc.document_title,
			"category": doc.category,
			"status": doc.status,
			"access_level": doc.access_level,
			"created_on": doc.created_on
		}
	except Exception as e:
		frappe.log_error(f"Error getting related document info: {str(e)}")
		return {}

@frappe.whitelist()
def remove_relationship(relationship_name):
	"""Remove a relationship"""
	try:
		relationship_doc = frappe.get_doc("Archive Related Document", relationship_name)
		parent_document = relationship_doc.parent
		related_document = relationship_doc.related_document_id
		relationship_type = relationship_doc.relationship_type
		
		# Delete the relationship
		relationship_doc.delete()
		
		# Remove reverse relationship if it exists
		reverse_relationships = {
			"Supersedes": "Superseded By",
			"Superseded By": "Supersedes",
			"References": "Referenced By",
			"Referenced By": "References",
			"Part Of": "Contains",
			"Contains": "Part Of",
			"Version Of": "Original Of",
			"Original Of": "Version Of"
		}
		
		if relationship_type in reverse_relationships:
			reverse_relationship = frappe.get_all("Archive Related Document",
				filters={
					"parent": related_document,
					"related_document_id": parent_document,
					"relationship_type": reverse_relationships[relationship_type]
				}
			)
			
			if reverse_relationship:
				frappe.delete_doc("Archive Related Document", reverse_relationship[0].name)
		
		return {"status": "success", "message": "Relationship removed successfully"}
		
	except Exception as e:
		frappe.log_error(f"Error removing relationship: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_relationship_statistics():
	"""Get relationship statistics"""
	try:
		stats = frappe.db.sql("""
			SELECT 
				relationship_type,
				COUNT(*) as count
			FROM `tabArchive Related Document`
			GROUP BY relationship_type
			ORDER BY count DESC
		""", as_dict=True)
		
		return stats
		
	except Exception as e:
		frappe.log_error(f"Error getting relationship statistics: {str(e)}")
		return []
import frappe
from frappe.model.document import Document
from frappe import _
import hashlib
import os
from frappe.utils import cstr

class ArchiveDocumentVersion(Document):
	def validate(self):
		"""Validate version before saving"""
		self.validate_version_number()
		self.set_file_hash()
		self.set_audit_info()
	
	def before_save(self):
		"""Process before saving"""
		if self.is_current_version:
			self.update_other_versions()
	
	def after_insert(self):
		"""Process after version creation"""
		self.create_version_audit_log("Version Created")
	
	def on_trash(self):
		"""Process before version deletion"""
		self.create_version_audit_log("Version Deleted")
	
	def validate_version_number(self):
		"""Ensure version number is unique for the parent document"""
		if self.parent:
			existing_versions = frappe.get_all("Archive Document Version",
				filters={
					"parent": self.parent,
					"parentfield": "version_info",
					"version_number": self.version_number,
					"name": ["!=", self.name]
				}
			)
			
			if existing_versions:
				frappe.throw(_("Version number {0} already exists for this document").format(self.version_number))
	
	def set_file_hash(self):
		"""Set file hash for integrity verification"""
		if self.file_url:
			try:
				file_doc = frappe.get_doc("File", {"file_url": self.file_url})
				file_path = file_doc.get_full_path()
				
				if os.path.exists(file_path):
					with open(file_path, 'rb') as f:
						file_content = f.read()
						self.file_hash = hashlib.sha256(file_content).hexdigest()
			except Exception as e:
				frappe.log_error(f"Error calculating file hash: {str(e)}")
	
	def set_audit_info(self):
		"""Set audit information"""
		if not self.created_by:
			self.created_by = frappe.session.user
			self.created_on = frappe.utils.now()
		
		self.last_modified_by = frappe.session.user
		self.last_modified_on = frappe.utils.now()
	
	def update_other_versions(self):
		"""Update other versions to not be current"""
		if self.parent:
			frappe.db.sql("""
				UPDATE `tabArchive Document Version`
				SET is_current_version = 0
				WHERE parent = %s AND name != %s
			""", (self.parent, self.name))
	
	def create_version_audit_log(self, action):
		"""Create version audit log entry"""
		audit_entry = {
			"doctype": "Archive Audit Trail",
			"action": f"Version {action}",
			"document_id": self.parent,
			"version_number": self.version_number,
			"user": frappe.session.user,
			"timestamp": frappe.utils.now(),
			"ip_address": frappe.local.request.environ.get('REMOTE_ADDR') if frappe.local.request else "System",
			"details": f"Version {self.version_number} {action.lower()}"
		}
		
		audit_doc = frappe.get_doc(audit_entry)
		audit_doc.insert(ignore_permissions=True)
	
	def get_file_integrity_status(self):
		"""Check file integrity using hash"""
		if not self.file_url or not self.file_hash:
			return "No file or hash available"
		
		try:
			file_doc = frappe.get_doc("File", {"file_url": self.file_url})
			file_path = file_doc.get_full_path()
			
			if os.path.exists(file_path):
				with open(file_path, 'rb') as f:
					file_content = f.read()
					current_hash = hashlib.sha256(file_content).hexdigest()
				
				if current_hash == self.file_hash:
					return "Integrity verified"
				else:
					return "Integrity check failed"
			else:
				return "File not found"
		except Exception as e:
			frappe.log_error(f"File integrity check error: {str(e)}")
			return "Error checking integrity"
	
	def get_version_comparison(self, other_version_name):
		"""Compare this version with another version"""
		try:
			other_version = frappe.get_doc("Archive Document Version", other_version_name)
			
			comparison = {
				"current_version": {
					"version_number": self.version_number,
					"version_date": self.version_date,
					"file_size": self.file_size,
					"created_by": self.created_by
				},
				"other_version": {
					"version_number": other_version.version_number,
					"version_date": other_version.version_date,
					"file_size": other_version.file_size,
					"created_by": other_version.created_by
				},
				"differences": []
			}
			
			# Compare basic fields
			if self.file_size != other_version.file_size:
				comparison["differences"].append("File size changed")
			
			if self.version_notes != other_version.version_notes:
				comparison["differences"].append("Version notes changed")
			
			if self.encryption_status != other_version.encryption_status:
				comparison["differences"].append("Encryption status changed")
			
			return comparison
			
		except Exception as e:
			frappe.log_error(f"Version comparison error: {str(e)}")
			return {"error": "Comparison failed"}

@frappe.whitelist()
def create_new_version(parent_document, file_url, version_notes="", change_summary=""):
	"""Create a new version of a document"""
	try:
		# Get the next version number
		last_version = frappe.get_all("Archive Document Version",
			filters={"parent": parent_document},
			fields=["version_number"],
			order_by="version_number desc",
			limit=1
		)
		
		next_version_number = 1
		if last_version:
			next_version_number = last_version[0].version_number + 1
		
		# Get file size
		file_size = 0
		if file_url:
			file_doc = frappe.get_doc("File", {"file_url": file_url})
			file_size = file_doc.file_size
		
		# Create new version
		version_doc = frappe.get_doc({
			"doctype": "Archive Document Version",
			"parent": parent_document,
			"parentfield": "version_info",
			"parenttype": "Archive Document",
			"version_number": next_version_number,
			"version_date": frappe.utils.now(),
			"version_notes": version_notes,
			"file_url": file_url,
			"file_size": file_size,
			"change_summary": change_summary,
			"is_current_version": 1,
			"version_status": "Published"
		})
		
		version_doc.insert(ignore_permissions=True)
		
		# Update the parent document
		parent_doc = frappe.get_doc("Archive Document", parent_document)
		parent_doc.file_attachment = file_url
		parent_doc.save()
		
		return {"status": "success", "version_number": next_version_number}
		
	except Exception as e:
		frappe.log_error(f"Error creating new version: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist()
def restore_version(version_name):
	"""Restore a specific version"""
	try:
		version_doc = frappe.get_doc("Archive Document Version", version_name)
		parent_doc = frappe.get_doc("Archive Document", version_doc.parent)
		
		# Create a new version with the restored content
		result = create_new_version(
			version_doc.parent,
			version_doc.file_url,
			f"Restored from version {version_doc.version_number}",
			f"Restored from version {version_doc.version_number} on {frappe.utils.now()}"
		)
		
		return result
		
	except Exception as e:
		frappe.log_error(f"Error restoring version: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_version_history(document_name):
	"""Get version history for a document"""
	versions = frappe.get_all("Archive Document Version",
		filters={"parent": document_name},
		fields=["name", "version_number", "version_date", "version_notes", 
				"file_size", "created_by", "is_current_version", "version_status"],
		order_by="version_number desc"
	)
	
	return versions

@frappe.whitelist()
def compare_versions(version1_name, version2_name):
	"""Compare two versions"""
	try:
		version1 = frappe.get_doc("Archive Document Version", version1_name)
		return version1.get_version_comparison(version2_name)
	except Exception as e:
		frappe.log_error(f"Error comparing versions: {str(e)}")
		return {"error": "Comparison failed"}

@frappe.whitelist()
def check_file_integrity(version_name):
	"""Check file integrity for a version"""
	try:
		version_doc = frappe.get_doc("Archive Document Version", version_name)
		integrity_status = version_doc.get_file_integrity_status()
		return {"status": "success", "integrity_status": integrity_status}
	except Exception as e:
		frappe.log_error(f"Error checking file integrity: {str(e)}")
		return {"status": "error", "message": str(e)}
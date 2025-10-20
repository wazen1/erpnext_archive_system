import frappe
from frappe.model.document import Document
from frappe import _

class ArchiveDocumentType(Document):
	def validate(self):
		"""Validate document type before saving"""
		self.validate_document_type_code()
		self.validate_file_requirements()
		self.set_audit_info()
	
	def before_save(self):
		"""Process before saving"""
		self.update_modified_info()
	
	def after_insert(self):
		"""Process after document type creation"""
		self.create_document_type_audit_log("Document Type Created")
	
	def on_trash(self):
		"""Process before document type deletion"""
		self.validate_document_type_deletion()
		self.create_document_type_audit_log("Document Type Deleted")
	
	def validate_document_type_code(self):
		"""Ensure document type code is unique"""
		if frappe.db.exists("Archive Document Type", {"document_type_code": self.document_type_code, "name": ["!=", self.name]}):
			frappe.throw(_("Document Type Code {0} already exists").format(self.document_type_code))
	
	def validate_file_requirements(self):
		"""Validate file requirements"""
		if self.allowed_file_types:
			# Validate file type format
			file_types = [ft.strip().lower() for ft in self.allowed_file_types.split(',')]
			for file_type in file_types:
				if not file_type.replace('.', '').isalnum():
					frappe.throw(_("Invalid file type format: {0}").format(file_type))
		
		if self.max_file_size and self.max_file_size <= 0:
			frappe.throw(_("Max file size must be greater than 0"))
	
	def set_audit_info(self):
		"""Set audit information"""
		if not self.created_by:
			self.created_by = frappe.session.user
			self.created_on = frappe.utils.now()
	
	def update_modified_info(self):
		"""Update modification information"""
		self.last_modified_by = frappe.session.user
		self.last_modified_on = frappe.utils.now()
	
	def validate_document_type_deletion(self):
		"""Validate if document type can be deleted"""
		# Check if document type has documents
		documents = frappe.get_all("Archive Document", filters={"document_type": self.name})
		if documents:
			frappe.throw(_("Cannot delete document type with documents. Please move or delete documents first."))
	
	def create_document_type_audit_log(self, action):
		"""Create document type audit log entry"""
		audit_entry = {
			"doctype": "Archive Audit Trail",
			"action": f"Document Type {action}",
			"user": frappe.session.user,
			"timestamp": frappe.utils.now(),
			"ip_address": frappe.local.request.environ.get('REMOTE_ADDR') if frappe.local.request else "System",
			"details": f"Document Type '{self.document_type_name}' {action.lower()}"
		}
		
		audit_doc = frappe.get_doc(audit_entry)
		audit_doc.insert(ignore_permissions=True)
	
	def get_allowed_file_types_list(self):
		"""Get list of allowed file types"""
		if not self.allowed_file_types:
			return []
		
		return [ft.strip().lower() for ft in self.allowed_file_types.split(',')]
	
	def validate_file_type(self, file_extension):
		"""Validate if file extension is allowed"""
		if not self.allowed_file_types:
			return True
		
		allowed_types = self.get_allowed_file_types_list()
		file_ext = file_extension.lower().replace('.', '')
		
		return file_ext in allowed_types
	
	def validate_file_size(self, file_size_bytes):
		"""Validate if file size is within limits"""
		if not self.max_file_size:
			return True
		
		max_size_bytes = self.max_file_size * 1024 * 1024  # Convert MB to bytes
		return file_size_bytes <= max_size_bytes
	
	def get_document_count(self):
		"""Get count of documents of this type"""
		count = frappe.db.count("Archive Document", {"document_type": self.name})
		return count
	
	def get_document_type_summary(self):
		"""Get document type summary for reporting"""
		summary = {
			"document_type_name": self.document_type_name,
			"document_type_code": self.document_type_code,
			"description": self.description,
			"allowed_file_types": self.allowed_file_types,
			"max_file_size": self.max_file_size,
			"requires_ocr": self.requires_ocr,
			"auto_categorize": self.auto_categorize,
			"retention_period": self.retention_period,
			"access_level": self.access_level,
			"encryption_required": self.encryption_required,
			"compliance_required": self.compliance_required,
			"is_active": self.is_active,
			"document_count": self.get_document_count()
		}
		
		return summary

@frappe.whitelist()
def create_document_type(document_type_name, document_type_code, **kwargs):
	"""Create a new document type"""
	try:
		doc_type = frappe.get_doc({
			"doctype": "Archive Document Type",
			"document_type_name": document_type_name,
			"document_type_code": document_type_code,
			"description": kwargs.get("description", ""),
			"allowed_file_types": kwargs.get("allowed_file_types", ""),
			"max_file_size": kwargs.get("max_file_size", 0),
			"requires_ocr": kwargs.get("requires_ocr", False),
			"auto_categorize": kwargs.get("auto_categorize", True),
			"retention_period": kwargs.get("retention_period", 7),
			"access_level": kwargs.get("access_level", "Internal"),
			"encryption_required": kwargs.get("encryption_required", False),
			"compliance_required": kwargs.get("compliance_required", False),
			"is_active": kwargs.get("is_active", True),
			"icon": kwargs.get("icon", "")
		})
		
		doc_type.insert(ignore_permissions=True)
		
		return {"status": "success", "document_type_name": doc_type.name}
		
	except Exception as e:
		frappe.log_error(f"Error creating document type: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_document_type_statistics():
	"""Get document type statistics"""
	try:
		stats = frappe.db.sql("""
			SELECT 
				dt.name,
				dt.document_type_name,
				dt.document_type_code,
				dt.is_active,
				COUNT(d.name) as document_count,
				SUM(CASE WHEN d.status = 'Active' THEN 1 ELSE 0 END) as active_documents,
				SUM(CASE WHEN d.access_level = 'Confidential' THEN 1 ELSE 0 END) as confidential_documents
			FROM `tabArchive Document Type` dt
			LEFT JOIN `tabArchive Document` d ON dt.name = d.document_type
			GROUP BY dt.name, dt.document_type_name, dt.document_type_code, dt.is_active
			ORDER BY document_count DESC
		""", as_dict=True)
		
		return stats
		
	except Exception as e:
		frappe.log_error(f"Error getting document type statistics: {str(e)}")
		return []

@frappe.whitelist()
def validate_document_file(document_type_name, file_extension, file_size):
	"""Validate a file against document type requirements"""
	try:
		doc_type = frappe.get_doc("Archive Document Type", document_type_name)
		
		validation_result = {
			"is_valid": True,
			"errors": [],
			"warnings": []
		}
		
		# Validate file type
		if not doc_type.validate_file_type(file_extension):
			validation_result["is_valid"] = False
			validation_result["errors"].append(f"File type '{file_extension}' is not allowed for this document type")
		
		# Validate file size
		if not doc_type.validate_file_size(file_size):
			validation_result["is_valid"] = False
			validation_result["errors"].append(f"File size exceeds maximum allowed size of {doc_type.max_file_size} MB")
		
		# Check if OCR is required
		if doc_type.requires_ocr:
			validation_result["warnings"].append("OCR processing will be required for this document type")
		
		# Check if encryption is required
		if doc_type.encryption_required:
			validation_result["warnings"].append("Encryption will be required for this document type")
		
		return validation_result
		
	except Exception as e:
		frappe.log_error(f"Error validating document file: {str(e)}")
		return {"is_valid": False, "errors": [str(e)], "warnings": []}

@frappe.whitelist()
def get_document_type_requirements(document_type_name):
	"""Get requirements for a document type"""
	try:
		doc_type = frappe.get_doc("Archive Document Type", document_type_name)
		
		requirements = {
			"allowed_file_types": doc_type.get_allowed_file_types_list(),
			"max_file_size_mb": doc_type.max_file_size,
			"requires_ocr": doc_type.requires_ocr,
			"auto_categorize": doc_type.auto_categorize,
			"retention_period_years": doc_type.retention_period,
			"default_access_level": doc_type.access_level,
			"encryption_required": doc_type.encryption_required,
			"compliance_required": doc_type.compliance_required
		}
		
		return requirements
		
	except Exception as e:
		frappe.log_error(f"Error getting document type requirements: {str(e)}")
		return {}

@frappe.whitelist()
def get_active_document_types():
	"""Get all active document types"""
	try:
		doc_types = frappe.get_all("Archive Document Type",
			filters={"is_active": 1},
			fields=["name", "document_type_name", "document_type_code", "description", "icon"],
			order_by="document_type_name"
		)
		
		return doc_types
		
	except Exception as e:
		frappe.log_error(f"Error getting active document types: {str(e)}")
		return []
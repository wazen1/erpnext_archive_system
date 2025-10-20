import frappe
from frappe.model.document import Document
from frappe import _
import json
import os
from .utils import process_ocr, encrypt_file, decrypt_file, generate_audit_log

class ArchiveDocument(Document):
	def validate(self):
		"""Validate document before saving"""
		self.validate_document_id()
		self.validate_file_attachment()
		self.set_metadata()
		
	def before_save(self):
		"""Process document before saving"""
		if self.file_attachment and not self.ocr_text:
			self.process_ocr()
		
		if self.encryption_status != "Encrypted" and self.access_level in ["Confidential", "Restricted"]:
			self.encrypt_document()
		
		self.update_audit_trail("Document Updated")
	
	def after_insert(self):
		"""Process after document creation"""
		self.update_audit_trail("Document Created")
		self.create_initial_version()
	
	def on_trash(self):
		"""Process before document deletion"""
		self.update_audit_trail("Document Deleted")
	
	def validate_document_id(self):
		"""Ensure document ID is unique"""
		if frappe.db.exists("Archive Document", {"document_id": self.document_id, "name": ["!=", self.name]}):
			frappe.throw(_("Document ID {0} already exists").format(self.document_id))
	
	def validate_file_attachment(self):
		"""Validate file attachment if provided"""
		if self.file_attachment:
			file_path = frappe.get_doc("File", {"file_url": self.file_attachment}).get_full_path()
			if not os.path.exists(file_path):
				frappe.throw(_("File attachment not found"))
	
	def set_metadata(self):
		"""Set document metadata"""
		if not self.metadata:
			self.metadata = json.dumps({
				"file_size": self.get_file_size(),
				"file_type": self.get_file_type(),
				"created_date": str(self.creation),
				"last_accessed": str(frappe.utils.now())
			})
	
	def process_ocr(self):
		"""Process OCR on attached file"""
		try:
			if self.file_attachment:
				file_path = frappe.get_doc("File", {"file_url": self.file_attachment}).get_full_path()
				ocr_text = process_ocr(file_path)
				self.ocr_text = ocr_text
				frappe.msgprint(_("OCR processing completed"))
		except Exception as e:
			frappe.log_error(f"OCR processing failed: {str(e)}")
			frappe.msgprint(_("OCR processing failed. Please try again."))
	
	def encrypt_document(self):
		"""Encrypt document file"""
		try:
			if self.file_attachment:
				file_doc = frappe.get_doc("File", {"file_url": self.file_attachment})
				file_path = file_doc.get_full_path()
				
				# Encrypt the file
				encrypted_path = encrypt_file(file_path)
				
				# Update file attachment
				self.file_attachment = encrypted_path
				self.encryption_status = "Encrypted"
				frappe.msgprint(_("Document encrypted successfully"))
		except Exception as e:
			frappe.log_error(f"Encryption failed: {str(e)}")
			self.encryption_status = "Encryption Failed"
			frappe.msgprint(_("Encryption failed. Please try again."))
	
	def decrypt_document(self):
		"""Decrypt document file"""
		try:
			if self.file_attachment and self.encryption_status == "Encrypted":
				file_doc = frappe.get_doc("File", {"file_url": self.file_attachment})
				file_path = file_doc.get_full_path()
				
				# Decrypt the file
				decrypted_path = decrypt_file(file_path)
				
				# Update file attachment
				self.file_attachment = decrypted_path
				self.encryption_status = "Not Encrypted"
				frappe.msgprint(_("Document decrypted successfully"))
		except Exception as e:
			frappe.log_error(f"Decryption failed: {str(e)}")
			frappe.msgprint(_("Decryption failed. Please try again."))
	
	def get_file_size(self):
		"""Get file size in bytes"""
		if self.file_attachment:
			file_doc = frappe.get_doc("File", {"file_url": self.file_attachment})
			return file_doc.file_size
		return 0
	
	def get_file_type(self):
		"""Get file type"""
		if self.file_attachment:
			file_doc = frappe.get_doc("File", {"file_url": self.file_attachment})
			return file_doc.file_name.split('.')[-1].upper()
		return ""
	
	def create_initial_version(self):
		"""Create initial version entry"""
		version_doc = frappe.get_doc({
			"doctype": "Archive Document Version",
			"parent": self.name,
			"parentfield": "version_info",
			"parenttype": "Archive Document",
			"version_number": 1,
			"version_date": frappe.utils.now(),
			"version_notes": "Initial version",
			"file_url": self.file_attachment,
			"created_by": frappe.session.user
		})
		version_doc.insert(ignore_permissions=True)
	
	def update_audit_trail(self, action):
		"""Update audit trail"""
		audit_entry = {
			"doctype": "Archive Audit Trail",
			"parent": self.name,
			"parentfield": "audit_trail",
			"parenttype": "Archive Document",
			"action": action,
			"timestamp": frappe.utils.now(),
			"user": frappe.session.user,
			"ip_address": frappe.local.request.environ.get('REMOTE_ADDR') if frappe.local.request else "System",
			"details": f"Document {action.lower()}"
		}
		
		audit_doc = frappe.get_doc(audit_entry)
		audit_doc.insert(ignore_permissions=True)
	
	def search_documents(self, search_term, filters=None):
		"""Search documents with filters"""
		query = """
			SELECT name, document_id, document_title, category, status, created_on
			FROM `tabArchive Document`
			WHERE 1=1
		"""
		
		params = []
		
		if search_term:
			query += """
				AND (document_title LIKE %s 
				OR document_id LIKE %s 
				OR ocr_text LIKE %s 
				OR tags LIKE %s)
			"""
			search_param = f"%{search_term}%"
			params.extend([search_param, search_param, search_param, search_param])
		
		if filters:
			for field, value in filters.items():
				if value:
					query += f" AND {field} = %s"
					params.append(value)
		
		query += " ORDER BY created_on DESC"
		
		return frappe.db.sql(query, params, as_dict=True)
	
	def get_related_documents(self):
		"""Get related documents"""
		related_docs = []
		for doc in self.related_documents:
			related_docs.append({
				"document_id": doc.related_document_id,
				"relationship_type": doc.relationship_type,
				"notes": doc.notes
			})
		return related_docs
	
	def add_related_document(self, related_doc_id, relationship_type, notes=""):
		"""Add related document"""
		related_doc = {
			"doctype": "Archive Related Document",
			"parent": self.name,
			"parentfield": "related_documents",
			"parenttype": "Archive Document",
			"related_document_id": related_doc_id,
			"relationship_type": relationship_type,
			"notes": notes
		}
		
		related_doc_obj = frappe.get_doc(related_doc)
		related_doc_obj.insert(ignore_permissions=True)
		
		self.reload()
		self.update_audit_trail(f"Added related document: {related_doc_id}")

@frappe.whitelist()
def process_document_ocr(docname):
	"""Process OCR for a document"""
	doc = frappe.get_doc("Archive Document", docname)
	doc.process_ocr()
	doc.save()
	return {"status": "success", "message": "OCR processing completed"}

@frappe.whitelist()
def encrypt_document(docname):
	"""Encrypt a document"""
	doc = frappe.get_doc("Archive Document", docname)
	doc.encrypt_document()
	doc.save()
	return {"status": "success", "message": "Document encrypted successfully"}

@frappe.whitelist()
def decrypt_document(docname):
	"""Decrypt a document"""
	doc = frappe.get_doc("Archive Document", docname)
	doc.decrypt_document()
	doc.save()
	return {"status": "success", "message": "Document decrypted successfully"}

@frappe.whitelist()
def search_archive_documents(search_term="", filters=None):
	"""Search archive documents"""
	doc = frappe.get_doc("Archive Document")
	if filters:
		filters = json.loads(filters)
	return doc.search_documents(search_term, filters)

@frappe.whitelist()
def add_related_document(docname, related_doc_id, relationship_type, notes=""):
	"""Add related document"""
	doc = frappe.get_doc("Archive Document", docname)
	doc.add_related_document(related_doc_id, relationship_type, notes)
	doc.save()
	return {"status": "success", "message": "Related document added successfully"}
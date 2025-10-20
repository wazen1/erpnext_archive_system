import frappe
from frappe import _
import json
from frappe.utils import cstr, now
from frappe.model.document import Document
import base64
import hashlib
from datetime import datetime, timedelta

@frappe.whitelist(allow_guest=False)
def upload_document(file_data, document_title, document_type, category, **kwargs):
	"""Upload and process a new document"""
	try:
		# Validate required fields
		if not file_data or not document_title or not document_type or not category:
			return {"status": "error", "message": "Missing required fields"}
		
		# Decode file data
		file_content = base64.b64decode(file_data)
		file_hash = hashlib.sha256(file_content).hexdigest()
		
		# Create file document
		file_doc = frappe.get_doc({
			"doctype": "File",
			"file_name": kwargs.get("file_name", "document"),
			"file_size": len(file_content),
			"content": file_data,
			"is_private": 1
		})
		file_doc.insert(ignore_permissions=True)
		
		# Generate document ID
		from erpnext_archive_system.erpnext_archive_system.doctype.archive_document.utils import generate_document_id
		document_id = generate_document_id()
		
		# Create archive document
		archive_doc = frappe.get_doc({
			"doctype": "Archive Document",
			"document_id": document_id,
			"document_title": document_title,
			"document_type": document_type,
			"category": category,
			"subcategory": kwargs.get("subcategory"),
			"description": kwargs.get("description", ""),
			"file_attachment": file_doc.file_url,
			"access_level": kwargs.get("access_level", "Internal"),
			"status": "Active",
			"priority": kwargs.get("priority", "Medium"),
			"tags": kwargs.get("tags", ""),
			"retention_period": kwargs.get("retention_period", 7)
		})
		
		archive_doc.insert(ignore_permissions=True)
		
		# Process OCR if required
		if kwargs.get("process_ocr", False):
			archive_doc.process_ocr()
			archive_doc.save()
		
		# Auto categorize if enabled
		if kwargs.get("auto_categorize", True):
			from erpnext_archive_system.erpnext_archive_system.doctype.archive_category.archive_category import auto_categorize_document
			auto_categorize_document(archive_doc.name)
		
		return {
			"status": "success",
			"document_id": archive_doc.document_id,
			"archive_id": archive_doc.name,
			"file_url": file_doc.file_url,
			"message": "Document uploaded successfully"
		}
		
	except Exception as e:
		frappe.log_error(f"Error uploading document: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=False)
def search_documents(search_term="", filters=None, limit=20, offset=0):
	"""Search documents with filters"""
	try:
		# Parse filters if provided as JSON string
		if isinstance(filters, str):
			filters = json.loads(filters)
		
		# Build query
		query = """
			SELECT 
				ad.name,
				ad.document_id,
				ad.document_title,
				ad.category,
				ad.subcategory,
				ad.status,
				ad.access_level,
				ad.created_on,
				ad.last_modified_on,
				adt.document_type_name,
				ac.category_name
			FROM `tabArchive Document` ad
			LEFT JOIN `tabArchive Document Type` adt ON ad.document_type = adt.name
			LEFT JOIN `tabArchive Category` ac ON ad.category = ac.name
			WHERE 1=1
		"""
		
		params = []
		
		# Add search term
		if search_term:
			query += """
				AND (ad.document_title LIKE %s 
				OR ad.document_id LIKE %s 
				OR ad.ocr_text LIKE %s 
				OR ad.tags LIKE %s
				OR ad.description LIKE %s)
			"""
			search_param = f"%{search_term}%"
			params.extend([search_param, search_param, search_param, search_param, search_param])
		
		# Add filters
		if filters:
			for field, value in filters.items():
				if value:
					query += f" AND ad.{field} = %s"
					params.append(value)
		
		# Add ordering and pagination
		query += " ORDER BY ad.created_on DESC LIMIT %s OFFSET %s"
		params.extend([limit, offset])
		
		documents = frappe.db.sql(query, params, as_dict=True)
		
		# Get total count for pagination
		count_query = query.replace("SELECT ad.name, ad.document_id, ad.document_title, ad.category, ad.subcategory, ad.status, ad.access_level, ad.created_on, ad.last_modified_on, adt.document_type_name, ac.category_name", "SELECT COUNT(*) as total")
		count_query = count_query.replace("ORDER BY ad.created_on DESC LIMIT %s OFFSET %s", "")
		count_params = params[:-2]  # Remove limit and offset
		
		total_count = frappe.db.sql(count_query, count_params, as_dict=True)[0].total
		
		return {
			"status": "success",
			"documents": documents,
			"total_count": total_count,
			"limit": limit,
			"offset": offset
		}
		
	except Exception as e:
		frappe.log_error(f"Error searching documents: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=False)
def get_document_details(document_id):
	"""Get detailed information about a document"""
	try:
		# Get document
		document = frappe.get_doc("Archive Document", document_id)
		
		# Get related documents
		related_docs = []
		for rel in document.related_documents:
			related_docs.append({
				"related_document_id": rel.related_document_id,
				"relationship_type": rel.relationship_type,
				"notes": rel.notes
			})
		
		# Get version history
		versions = []
		for ver in document.version_info:
			versions.append({
				"version_number": ver.version_number,
				"version_date": ver.version_date,
				"version_notes": ver.version_notes,
				"file_size": ver.file_size,
				"created_by": ver.created_by,
				"is_current_version": ver.is_current_version
			})
		
		# Get audit trail
		audit_trail = frappe.get_all("Archive Audit Trail",
			filters={"document_id": document_id},
			fields=["action", "timestamp", "user", "details", "severity"],
			order_by="timestamp desc",
			limit=10
		)
		
		return {
			"status": "success",
			"document": {
				"name": document.name,
				"document_id": document.document_id,
				"document_title": document.document_title,
				"document_type": document.document_type,
				"category": document.category,
				"subcategory": document.subcategory,
				"description": document.description,
				"status": document.status,
				"priority": document.priority,
				"access_level": document.access_level,
				"file_attachment": document.file_attachment,
				"ocr_text": document.ocr_text,
				"tags": document.tags,
				"retention_period": document.retention_period,
				"encryption_status": document.encryption_status,
				"compliance_status": document.compliance_status,
				"created_by": document.created_by,
				"created_on": document.created_on,
				"last_modified_by": document.last_modified_by,
				"last_modified_on": document.last_modified_on
			},
			"related_documents": related_docs,
			"versions": versions,
			"audit_trail": audit_trail
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting document details: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=False)
def download_document(document_id, version_number=None):
	"""Download a document file"""
	try:
		document = frappe.get_doc("Archive Document", document_id)
		
		# Check access permissions
		if not frappe.has_permission("Archive Document", "read", document.name):
			return {"status": "error", "message": "Access denied"}
		
		# Get file URL
		file_url = document.file_attachment
		
		# If specific version requested
		if version_number:
			version = frappe.get_all("Archive Document Version",
				filters={"parent": document_id, "version_number": version_number},
				fields=["file_url"],
				limit=1
			)
			if version:
				file_url = version[0].file_url
		
		if not file_url:
			return {"status": "error", "message": "File not found"}
		
		# Get file document
		file_doc = frappe.get_doc("File", {"file_url": file_url})
		
		# Create audit log
		from erpnext_archive_system.erpnext_archive_system.doctype.archive_audit_trail.archive_audit_trail import create_audit_entry
		create_audit_entry("Document Downloaded", document_id, version_number=version_number)
		
		return {
			"status": "success",
			"file_url": file_doc.file_url,
			"file_name": file_doc.file_name,
			"file_size": file_doc.file_size,
			"content_type": file_doc.content_type
		}
		
	except Exception as e:
		frappe.log_error(f"Error downloading document: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=False)
def create_document_version(document_id, file_data, version_notes="", change_summary=""):
	"""Create a new version of a document"""
	try:
		# Validate document exists
		if not frappe.db.exists("Archive Document", document_id):
			return {"status": "error", "message": "Document not found"}
		
		# Decode file data
		file_content = base64.b64decode(file_data)
		
		# Create file document
		file_doc = frappe.get_doc({
			"doctype": "File",
			"file_name": f"version_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
			"file_size": len(file_content),
			"content": file_data,
			"is_private": 1
		})
		file_doc.insert(ignore_permissions=True)
		
		# Create version
		from erpnext_archive_system.erpnext_archive_system.doctype.archive_document_version.archive_document_version import create_new_version
		result = create_new_version(document_id, file_doc.file_url, version_notes, change_summary)
		
		return result
		
	except Exception as e:
		frappe.log_error(f"Error creating document version: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=False)
def get_categories():
	"""Get all active categories"""
	try:
		categories = frappe.get_all("Archive Category",
			filters={"is_active": 1},
			fields=["name", "category_name", "description", "color", "icon"],
			order_by="category_name"
		)
		
		return {"status": "success", "categories": categories}
		
	except Exception as e:
		frappe.log_error(f"Error getting categories: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=False)
def get_document_types():
	"""Get all active document types"""
	try:
		document_types = frappe.get_all("Archive Document Type",
			filters={"is_active": 1},
			fields=["name", "document_type_name", "document_type_code", "description", "icon"],
			order_by="document_type_name"
		)
		
		return {"status": "success", "document_types": document_types}
		
	except Exception as e:
		frappe.log_error(f"Error getting document types: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=False)
def get_archive_statistics():
	"""Get archive system statistics"""
	try:
		stats = frappe.db.sql("""
			SELECT 
				COUNT(*) as total_documents,
				SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active_documents,
				SUM(CASE WHEN access_level = 'Confidential' THEN 1 ELSE 0 END) as confidential_documents,
				SUM(CASE WHEN encryption_status = 'Encrypted' THEN 1 ELSE 0 END) as encrypted_documents
			FROM `tabArchive Document`
		""", as_dict=True)[0]
		
		category_stats = frappe.db.sql("""
			SELECT 
				c.category_name,
				COUNT(d.name) as document_count
			FROM `tabArchive Category` c
			LEFT JOIN `tabArchive Document` d ON c.name = d.category
			WHERE c.is_active = 1
			GROUP BY c.name, c.category_name
			ORDER BY document_count DESC
			LIMIT 10
		""", as_dict=True)
		
		return {
			"status": "success",
			"statistics": stats,
			"category_stats": category_stats
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting archive statistics: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=False)
def bulk_upload_documents(documents_data):
	"""Bulk upload multiple documents"""
	try:
		if isinstance(documents_data, str):
			documents_data = json.loads(documents_data)
		
		results = {
			"total": len(documents_data),
			"success": 0,
			"failed": 0,
			"errors": []
		}
		
		for doc_data in documents_data:
			try:
				result = upload_document(**doc_data)
				if result["status"] == "success":
					results["success"] += 1
				else:
					results["failed"] += 1
					results["errors"].append({
						"document": doc_data.get("document_title", "Unknown"),
						"error": result["message"]
					})
			except Exception as e:
				results["failed"] += 1
				results["errors"].append({
					"document": doc_data.get("document_title", "Unknown"),
					"error": str(e)
				})
		
		return {"status": "success", "results": results}
		
	except Exception as e:
		frappe.log_error(f"Error in bulk upload: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=False)
def export_documents(document_ids, format="json"):
	"""Export documents in specified format"""
	try:
		if isinstance(document_ids, str):
			document_ids = json.loads(document_ids)
		
		documents = []
		for doc_id in document_ids:
			doc = frappe.get_doc("Archive Document", doc_id)
			documents.append({
				"document_id": doc.document_id,
				"document_title": doc.document_title,
				"category": doc.category,
				"status": doc.status,
				"created_on": doc.created_on,
				"description": doc.description,
				"tags": doc.tags
			})
		
		if format == "json":
			return {"status": "success", "data": documents}
		elif format == "csv":
			# Convert to CSV format
			import csv
			import io
			
			output = io.StringIO()
			writer = csv.DictWriter(output, fieldnames=documents[0].keys() if documents else [])
			writer.writeheader()
			writer.writerows(documents)
			
			return {"status": "success", "data": output.getvalue()}
		else:
			return {"status": "error", "message": "Unsupported format"}
		
	except Exception as e:
		frappe.log_error(f"Error exporting documents: {str(e)}")
		return {"status": "error", "message": str(e)}
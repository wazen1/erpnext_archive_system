import frappe
from frappe.model.document import Document
from frappe import _
import json
from datetime import datetime, timedelta

class ArchiveAuditTrail(Document):
	def validate(self):
		"""Validate audit trail entry"""
		self.set_default_values()
		self.validate_required_fields()
	
	def before_save(self):
		"""Process before saving"""
		self.set_retention_date()
		self.set_compliance_flag()
	
	def set_default_values(self):
		"""Set default values"""
		if not self.timestamp:
			self.timestamp = frappe.utils.now()
		
		if not self.user:
			self.user = frappe.session.user
		
		if not self.ip_address and frappe.local.request:
			self.ip_address = frappe.local.request.environ.get('REMOTE_ADDR', 'Unknown')
		
		if not self.user_agent and frappe.local.request:
			self.user_agent = frappe.local.request.environ.get('HTTP_USER_AGENT', 'Unknown')
		
		if not self.session_id:
			self.session_id = frappe.session.sid if frappe.session.sid else 'Unknown'
	
	def validate_required_fields(self):
		"""Validate required fields"""
		if not self.action:
			frappe.throw(_("Action is required"))
		
		if not self.user:
			frappe.throw(_("User is required"))
	
	def set_retention_date(self):
		"""Set retention date based on action type"""
		retention_days = {
			"Document Created": 2555,  # 7 years
			"Document Updated": 2555,
			"Document Deleted": 2555,
			"Document Accessed": 365,   # 1 year
			"Document Downloaded": 2555,
			"Document Shared": 2555,
			"Version Created": 2555,
			"Version Restored": 2555,
			"Category Created": 2555,
			"Category Updated": 2555,
			"Category Deleted": 2555,
			"Access Granted": 2555,
			"Access Revoked": 2555,
			"Encryption Applied": 2555,
			"Decryption Applied": 2555,
			"OCR Processed": 2555,
			"Auto Categorized": 2555,
			"Compliance Check": 2555,
			"Audit Report Generated": 2555,
			"System Error": 2555,
			"Security Violation": 2555
		}
		
		days = retention_days.get(self.action, 2555)  # Default 7 years
		self.retention_until = (datetime.now() + timedelta(days=days)).date()
	
	def set_compliance_flag(self):
		"""Set compliance flag based on action type"""
		compliance_actions = [
			"Document Created",
			"Document Updated", 
			"Document Deleted",
			"Document Downloaded",
			"Document Shared",
			"Access Granted",
			"Access Revoked",
			"Encryption Applied",
			"Decryption Applied",
			"Compliance Check",
			"Security Violation"
		]
		
		self.compliance_flag = self.action in compliance_actions
	
	def get_audit_summary(self):
		"""Get audit summary for reporting"""
		summary = {
			"action": self.action,
			"timestamp": self.timestamp,
			"user": self.user,
			"severity": self.severity,
			"status": self.status,
			"compliance_flag": self.compliance_flag,
			"details": self.details
		}
		
		if self.document_id:
			summary["document_id"] = self.document_id
		
		if self.category_id:
			summary["category_id"] = self.category_id
		
		if self.version_number:
			summary["version_number"] = self.version_number
		
		return summary

@frappe.whitelist()
def create_audit_entry(action, document_id=None, category_id=None, version_number=None, 
					  details="", severity="Low", status="Success"):
	"""Create audit trail entry"""
	try:
		audit_entry = {
			"doctype": "Archive Audit Trail",
			"action": action,
			"document_id": document_id,
			"category_id": category_id,
			"version_number": version_number,
			"details": details,
			"severity": severity,
			"status": status,
			"user": frappe.session.user,
			"timestamp": frappe.utils.now(),
			"ip_address": frappe.local.request.environ.get('REMOTE_ADDR') if frappe.local.request else "System",
			"user_agent": frappe.local.request.environ.get('HTTP_USER_AGENT') if frappe.local.request else "System",
			"session_id": frappe.session.sid if frappe.session.sid else "System"
		}
		
		audit_doc = frappe.get_doc(audit_entry)
		audit_doc.insert(ignore_permissions=True)
		
		return {"status": "success", "audit_id": audit_doc.name}
		
	except Exception as e:
		frappe.log_error(f"Error creating audit entry: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_audit_trail(document_id=None, category_id=None, user=None, 
				   start_date=None, end_date=None, action=None, limit=100):
	"""Get audit trail entries with filters"""
	try:
		filters = {}
		
		if document_id:
			filters["document_id"] = document_id
		
		if category_id:
			filters["category_id"] = category_id
		
		if user:
			filters["user"] = user
		
		if action:
			filters["action"] = action
		
		if start_date:
			filters["timestamp"] = [">=", start_date]
		
		if end_date:
			if "timestamp" in filters:
				filters["timestamp"] = [filters["timestamp"][0], filters["timestamp"][1], "<=", end_date]
			else:
				filters["timestamp"] = ["<=", end_date]
		
		audit_entries = frappe.get_all("Archive Audit Trail",
			filters=filters,
			fields=["name", "action", "timestamp", "user", "document_id", 
				   "category_id", "version_number", "severity", "status", 
				   "details", "compliance_flag"],
			order_by="timestamp desc",
			limit=limit
		)
		
		return audit_entries
		
	except Exception as e:
		frappe.log_error(f"Error getting audit trail: {str(e)}")
		return []

@frappe.whitelist()
def get_audit_statistics(start_date=None, end_date=None):
	"""Get audit statistics"""
	try:
		date_filter = {}
		if start_date:
			date_filter["timestamp"] = [">=", start_date]
		if end_date:
			if "timestamp" in date_filter:
				date_filter["timestamp"] = [date_filter["timestamp"][0], date_filter["timestamp"][1], "<=", end_date]
			else:
				date_filter["timestamp"] = ["<=", end_date]
		
		# Get action counts
		action_counts = frappe.db.sql("""
			SELECT action, COUNT(*) as count
			FROM `tabArchive Audit Trail`
			WHERE 1=1
			{filters}
			GROUP BY action
			ORDER BY count DESC
		""".format(filters=" AND ".join([f"{k} {v[0]} '{v[1]}'" for k, v in date_filter.items()])), as_dict=True)
		
		# Get user activity
		user_activity = frappe.db.sql("""
			SELECT user, COUNT(*) as count
			FROM `tabArchive Audit Trail`
			WHERE 1=1
			{filters}
			GROUP BY user
			ORDER BY count DESC
			LIMIT 10
		""".format(filters=" AND ".join([f"{k} {v[0]} '{v[1]}'" for k, v in date_filter.items()])), as_dict=True)
		
		# Get compliance statistics
		compliance_stats = frappe.db.sql("""
			SELECT 
				SUM(CASE WHEN compliance_flag = 1 THEN 1 ELSE 0 END) as compliance_actions,
				COUNT(*) as total_actions,
				SUM(CASE WHEN severity = 'Critical' THEN 1 ELSE 0 END) as critical_actions,
				SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed_actions
			FROM `tabArchive Audit Trail`
			WHERE 1=1
			{filters}
		""".format(filters=" AND ".join([f"{k} {v[0]} '{v[1]}'" for k, v in date_filter.items()])), as_dict=True)
		
		return {
			"action_counts": action_counts,
			"user_activity": user_activity,
			"compliance_stats": compliance_stats[0] if compliance_stats else {}
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting audit statistics: {str(e)}")
		return {}

@frappe.whitelist()
def generate_compliance_report(start_date=None, end_date=None):
	"""Generate compliance report"""
	try:
		date_filter = {}
		if start_date:
			date_filter["timestamp"] = [">=", start_date]
		if end_date:
			if "timestamp" in date_filter:
				date_filter["timestamp"] = [date_filter["timestamp"][0], date_filter["timestamp"][1], "<=", end_date]
			else:
				date_filter["timestamp"] = ["<=", end_date]
		
		# Get compliance-related actions
		compliance_actions = frappe.get_all("Archive Audit Trail",
			filters={**date_filter, "compliance_flag": 1},
			fields=["action", "timestamp", "user", "document_id", "details", "severity"],
			order_by="timestamp desc"
		)
		
		# Generate report summary
		report = {
			"report_generated": frappe.utils.now(),
			"period": {
				"start_date": start_date,
				"end_date": end_date
			},
			"total_compliance_actions": len(compliance_actions),
			"actions_by_type": {},
			"actions_by_user": {},
			"critical_actions": [],
			"detailed_actions": compliance_actions
		}
		
		# Group by action type
		for action in compliance_actions:
			action_type = action.action
			if action_type not in report["actions_by_type"]:
				report["actions_by_type"][action_type] = 0
			report["actions_by_type"][action_type] += 1
			
			# Group by user
			user = action.user
			if user not in report["actions_by_user"]:
				report["actions_by_user"][user] = 0
			report["actions_by_user"][user] += 1
			
			# Collect critical actions
			if action.severity == "Critical":
				report["critical_actions"].append(action)
		
		return report
		
	except Exception as e:
		frappe.log_error(f"Error generating compliance report: {str(e)}")
		return {"error": "Report generation failed"}

@frappe.whitelist()
def cleanup_old_audit_entries():
	"""Clean up old audit entries based on retention policy"""
	try:
		# Delete entries past retention date
		deleted_count = frappe.db.sql("""
			DELETE FROM `tabArchive Audit Trail`
			WHERE retention_until < CURDATE()
		""")
		
		frappe.db.commit()
		
		return {"status": "success", "deleted_count": deleted_count}
		
	except Exception as e:
		frappe.log_error(f"Error cleaning up audit entries: {str(e)}")
		return {"status": "error", "message": str(e)}
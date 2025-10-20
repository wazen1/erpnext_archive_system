import frappe
from frappe.model.document import Document
from frappe import _
import re

class ArchiveCategoryRule(Document):
	def validate(self):
		"""Validate rule before saving"""
		self.validate_rule_configuration()
		self.set_audit_info()
	
	def before_save(self):
		"""Process before saving"""
		self.update_modified_info()
	
	def after_insert(self):
		"""Process after rule creation"""
		self.create_rule_audit_log("Rule Created")
	
	def on_trash(self):
		"""Process before rule deletion"""
		self.create_rule_audit_log("Rule Deleted")
	
	def validate_rule_configuration(self):
		"""Validate rule configuration based on type"""
		if self.rule_type == "Keyword" and not self.keyword:
			frappe.throw(_("Keyword is required for Keyword rule type"))
		
		if self.rule_type == "Pattern" and not self.pattern:
			frappe.throw(_("Pattern is required for Pattern rule type"))
		
		if self.rule_type == "Document Type" and not self.document_type:
			frappe.throw(_("Document Type is required for Document Type rule"))
		
		# Validate regex pattern
		if self.rule_type == "Pattern" and self.pattern:
			try:
				re.compile(self.pattern)
			except re.error as e:
				frappe.throw(_("Invalid regex pattern: {0}").format(str(e)))
	
	def set_audit_info(self):
		"""Set audit information"""
		if not self.created_by:
			self.created_by = frappe.session.user
			self.created_on = frappe.utils.now()
	
	def update_modified_info(self):
		"""Update modification information"""
		self.last_modified_by = frappe.session.user
		self.last_modified_on = frappe.utils.now()
	
	def create_rule_audit_log(self, action):
		"""Create rule audit log entry"""
		audit_entry = {
			"doctype": "Archive Audit Trail",
			"action": f"Rule {action}",
			"user": frappe.session.user,
			"timestamp": frappe.utils.now(),
			"ip_address": frappe.local.request.environ.get('REMOTE_ADDR') if frappe.local.request else "System",
			"details": f"Rule '{self.rule_name}' {action.lower()}"
		}
		
		audit_doc = frappe.get_doc(audit_entry)
		audit_doc.insert(ignore_permissions=True)
	
	def apply_rule(self, document_content, document_title="", document_type=""):
		"""Apply this rule to determine if document matches"""
		if not self.is_active:
			return False
		
		content_to_check = f"{document_title} {document_content}".lower()
		
		if self.rule_type == "Keyword":
			return self.keyword.lower() in content_to_check
		
		elif self.rule_type == "Pattern":
			try:
				return bool(re.search(self.pattern, content_to_check, re.IGNORECASE))
			except re.error:
				return False
		
		elif self.rule_type == "Document Type":
			return document_type == self.document_type
		
		elif self.rule_type == "File Extension":
			# This would need to be implemented based on file extension detection
			return False
		
		elif self.rule_type == "Content Analysis":
			# This would need ML-based content analysis
			return False
		
		return False
	
	def get_rule_summary(self):
		"""Get rule summary for reporting"""
		summary = {
			"rule_name": self.rule_name,
			"rule_type": self.rule_type,
			"priority": self.priority,
			"is_active": self.is_active,
			"description": self.description
		}
		
		if self.rule_type == "Keyword":
			summary["keyword"] = self.keyword
		elif self.rule_type == "Pattern":
			summary["pattern"] = self.pattern
		elif self.rule_type == "Document Type":
			summary["document_type"] = self.document_type
		
		return summary

@frappe.whitelist()
def create_rule(rule_name, rule_type, **kwargs):
	"""Create a new categorization rule"""
	try:
		rule_doc = frappe.get_doc({
			"doctype": "Archive Category Rule",
			"rule_name": rule_name,
			"rule_type": rule_type,
			"keyword": kwargs.get("keyword"),
			"pattern": kwargs.get("pattern"),
			"document_type": kwargs.get("document_type"),
			"priority": kwargs.get("priority", 1),
			"is_active": kwargs.get("is_active", True),
			"description": kwargs.get("description", "")
		})
		
		rule_doc.insert(ignore_permissions=True)
		
		return {"status": "success", "rule_name": rule_doc.name}
		
	except Exception as e:
		frappe.log_error(f"Error creating rule: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist()
def apply_rules_to_document(document_name):
	"""Apply all active rules to a document"""
	try:
		doc = frappe.get_doc("Archive Document", document_name)
		
		# Get all active rules ordered by priority
		rules = frappe.get_all("Archive Category Rule",
			filters={"is_active": 1},
			fields=["name", "rule_name", "rule_type", "keyword", "pattern", "document_type", "priority"],
			order_by="priority asc"
		)
		
		content = f"{doc.document_title} {doc.description or ''} {doc.ocr_text or ''}"
		
		for rule in rules:
			rule_doc = frappe.get_doc("Archive Category Rule", rule.name)
			if rule_doc.apply_rule(content, doc.document_title, doc.document_type):
				# Rule matched, update document category
				old_category = doc.category
				doc.category = rule_doc.parent_category if hasattr(rule_doc, 'parent_category') else doc.category
				
				if old_category != doc.category:
					doc.save()
					return {
						"status": "success", 
						"message": f"Document categorized using rule: {rule.rule_name}",
						"new_category": doc.category
					}
		
		return {"status": "no_match", "message": "No rules matched the document"}
		
	except Exception as e:
		frappe.log_error(f"Error applying rules to document: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist()
def test_rule(rule_name, test_content, test_title=""):
	"""Test a rule against sample content"""
	try:
		rule_doc = frappe.get_doc("Archive Category Rule", rule_name)
		result = rule_doc.apply_rule(test_content, test_title)
		
		return {
			"status": "success",
			"rule_name": rule_doc.rule_name,
			"rule_type": rule_doc.rule_type,
			"matches": result,
			"test_content": test_content[:100] + "..." if len(test_content) > 100 else test_content
		}
		
	except Exception as e:
		frappe.log_error(f"Error testing rule: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_rule_statistics():
	"""Get rule usage statistics"""
	try:
		stats = frappe.db.sql("""
			SELECT 
				rule_type,
				COUNT(*) as total_rules,
				SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_rules
			FROM `tabArchive Category Rule`
			GROUP BY rule_type
			ORDER BY total_rules DESC
		""", as_dict=True)
		
		return stats
		
	except Exception as e:
		frappe.log_error(f"Error getting rule statistics: {str(e)}")
		return []

@frappe.whitelist()
def bulk_apply_rules():
	"""Apply all active rules to all documents"""
	try:
		# Get all documents without category or with 'General' category
		documents = frappe.get_all("Archive Document",
			filters={"category": ["in", ["", "General"]]},
			fields=["name", "document_title", "description", "ocr_text", "document_type"]
		)
		
		results = {
			"total_documents": len(documents),
			"categorized": 0,
			"no_match": 0,
			"errors": 0
		}
		
		for doc in documents:
			try:
				result = apply_rules_to_document(doc.name)
				if result["status"] == "success":
					results["categorized"] += 1
				elif result["status"] == "no_match":
					results["no_match"] += 1
			except Exception:
				results["errors"] += 1
		
		return results
		
	except Exception as e:
		frappe.log_error(f"Error in bulk apply rules: {str(e)}")
		return {"status": "error", "message": str(e)}
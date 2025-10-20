import frappe
from frappe import _

class ArchiveConfig:
	"""Configuration class for the Archive System"""
	
	@staticmethod
	def get_ocr_settings():
		"""Get OCR configuration settings"""
		return {
			"tesseract_path": frappe.get_conf().get("archive_tesseract_path", "/usr/bin/tesseract"),
			"languages": frappe.get_conf().get("archive_ocr_languages", ["eng"]),
			"psm_mode": frappe.get_conf().get("archive_ocr_psm_mode", 6),
			"enable_preprocessing": frappe.get_conf().get("archive_ocr_preprocessing", True),
			"max_file_size_mb": frappe.get_conf().get("archive_ocr_max_file_size", 50)
		}
	
	@staticmethod
	def get_encryption_settings():
		"""Get encryption configuration settings"""
		return {
			"algorithm": frappe.get_conf().get("archive_encryption_algorithm", "AES-256-GCM"),
			"key_rotation_days": frappe.get_conf().get("archive_key_rotation_days", 365),
			"enable_at_rest": frappe.get_conf().get("archive_encrypt_at_rest", True),
			"enable_in_transit": frappe.get_conf().get("archive_encrypt_in_transit", True)
		}
	
	@staticmethod
	def get_storage_settings():
		"""Get storage configuration settings"""
		return {
			"storage_backend": frappe.get_conf().get("archive_storage_backend", "local"),
			"aws_s3_bucket": frappe.get_conf().get("archive_aws_s3_bucket"),
			"aws_region": frappe.get_conf().get("archive_aws_region"),
			"max_file_size_mb": frappe.get_conf().get("archive_max_file_size", 100),
			"compression_enabled": frappe.get_conf().get("archive_compression_enabled", True),
			"backup_enabled": frappe.get_conf().get("archive_backup_enabled", True)
		}
	
	@staticmethod
	def get_search_settings():
		"""Get search configuration settings"""
		return {
			"search_backend": frappe.get_conf().get("archive_search_backend", "database"),
			"elasticsearch_url": frappe.get_conf().get("archive_elasticsearch_url"),
			"elasticsearch_index": frappe.get_conf().get("archive_elasticsearch_index", "archive_documents"),
			"enable_full_text_search": frappe.get_conf().get("archive_full_text_search", True),
			"search_suggestions": frappe.get_conf().get("archive_search_suggestions", True)
		}
	
	@staticmethod
	def get_retention_settings():
		"""Get retention policy settings"""
		return {
			"default_retention_years": frappe.get_conf().get("archive_default_retention_years", 7),
			"auto_cleanup_enabled": frappe.get_conf().get("archive_auto_cleanup", True),
			"cleanup_schedule": frappe.get_conf().get("archive_cleanup_schedule", "0 2 * * 0"),  # Weekly on Sunday at 2 AM
			"notification_days_before": frappe.get_conf().get("archive_notification_days", 30)
		}
	
	@staticmethod
	def get_compliance_settings():
		"""Get compliance and audit settings"""
		return {
			"audit_retention_days": frappe.get_conf().get("archive_audit_retention_days", 2555),  # 7 years
			"enable_audit_logging": frappe.get_conf().get("archive_audit_logging", True),
			"compliance_standards": frappe.get_conf().get("archive_compliance_standards", ["SOX", "GDPR"]),
			"data_classification": frappe.get_conf().get("archive_data_classification", True),
			"access_logging": frappe.get_conf().get("archive_access_logging", True)
		}
	
	@staticmethod
	def get_performance_settings():
		"""Get performance optimization settings"""
		return {
			"enable_caching": frappe.get_conf().get("archive_enable_caching", True),
			"cache_ttl_seconds": frappe.get_conf().get("archive_cache_ttl", 3600),
			"max_concurrent_uploads": frappe.get_conf().get("archive_max_concurrent_uploads", 5),
			"thumbnail_generation": frappe.get_conf().get("archive_thumbnail_generation", True),
			"async_processing": frappe.get_conf().get("archive_async_processing", True)
		}
	
	@staticmethod
	def get_integration_settings():
		"""Get integration settings"""
		return {
			"enable_api": frappe.get_conf().get("archive_enable_api", True),
			"api_rate_limit": frappe.get_conf().get("archive_api_rate_limit", 1000),
			"webhook_url": frappe.get_conf().get("archive_webhook_url"),
			"external_systems": frappe.get_conf().get("archive_external_systems", []),
			"sync_enabled": frappe.get_conf().get("archive_sync_enabled", False)
		}
	
	@staticmethod
	def get_ui_settings():
		"""Get UI and user experience settings"""
		return {
			"theme": frappe.get_conf().get("archive_theme", "default"),
			"items_per_page": frappe.get_conf().get("archive_items_per_page", 20),
			"enable_drag_drop": frappe.get_conf().get("archive_drag_drop", True),
			"enable_bulk_operations": frappe.get_conf().get("archive_bulk_operations", True),
			"show_advanced_search": frappe.get_conf().get("archive_advanced_search", True)
		}
	
	@staticmethod
	def validate_configuration():
		"""Validate the current configuration"""
		errors = []
		warnings = []
		
		# Check OCR settings
		ocr_settings = ArchiveConfig.get_ocr_settings()
		if not ocr_settings["tesseract_path"]:
			warnings.append("Tesseract path not configured. OCR functionality may not work.")
		
		# Check encryption settings
		encryption_settings = ArchiveConfig.get_encryption_settings()
		if encryption_settings["enable_at_rest"] and not frappe.get_conf().get("archive_encryption_key"):
			errors.append("Encryption enabled but no encryption key configured.")
		
		# Check storage settings
		storage_settings = ArchiveConfig.get_storage_settings()
		if storage_settings["storage_backend"] == "s3" and not storage_settings["aws_s3_bucket"]:
			errors.append("S3 storage backend selected but S3 bucket not configured.")
		
		# Check search settings
		search_settings = ArchiveConfig.get_search_settings()
		if search_settings["search_backend"] == "elasticsearch" and not search_settings["elasticsearch_url"]:
			warnings.append("Elasticsearch backend selected but URL not configured. Falling back to database search.")
		
		return {
			"valid": len(errors) == 0,
			"errors": errors,
			"warnings": warnings
		}
	
	@staticmethod
	def get_default_settings():
		"""Get default configuration settings"""
		return {
			"ocr": ArchiveConfig.get_ocr_settings(),
			"encryption": ArchiveConfig.get_encryption_settings(),
			"storage": ArchiveConfig.get_storage_settings(),
			"search": ArchiveConfig.get_search_settings(),
			"retention": ArchiveConfig.get_retention_settings(),
			"compliance": ArchiveConfig.get_compliance_settings(),
			"performance": ArchiveConfig.get_performance_settings(),
			"integration": ArchiveConfig.get_integration_settings(),
			"ui": ArchiveConfig.get_ui_settings()
		}

@frappe.whitelist()
def get_archive_config():
	"""Get archive system configuration"""
	try:
		config = ArchiveConfig.get_default_settings()
		validation = ArchiveConfig.validate_configuration()
		
		return {
			"status": "success",
			"config": config,
			"validation": validation
		}
	except Exception as e:
		frappe.log_error(f"Error getting archive config: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist()
def update_archive_config(config_data):
	"""Update archive system configuration"""
	try:
		import json
		
		if isinstance(config_data, str):
			config_data = json.loads(config_data)
		
		# Update configuration values
		for section, settings in config_data.items():
			for key, value in settings.items():
				config_key = f"archive_{section}_{key}"
				frappe.conf[config_key] = value
		
		frappe.db.commit()
		
		return {"status": "success", "message": "Configuration updated successfully"}
		
	except Exception as e:
		frappe.log_error(f"Error updating archive config: {str(e)}")
		return {"status": "error", "message": str(e)}
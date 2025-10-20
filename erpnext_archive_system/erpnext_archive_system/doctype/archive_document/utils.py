import frappe
import pytesseract
from PIL import Image
import cv2
import numpy as np
import os
import json
from cryptography.fernet import Fernet
import base64
from frappe.utils import cstr

def process_ocr(file_path):
	"""Process OCR on image/document file"""
	try:
		# Check if file is an image
		image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
		file_ext = os.path.splitext(file_path)[1].lower()
		
		if file_ext in image_extensions:
			# Process image with OCR
			image = cv2.imread(file_path)
			
			# Preprocess image for better OCR
			gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
			denoised = cv2.medianBlur(gray, 3)
			
			# Apply threshold
			thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
			
			# OCR processing
			text = pytesseract.image_to_string(thresh, config='--psm 6')
			
			return text.strip()
		
		else:
			# For PDF files, you might want to use pdf2image or PyPDF2
			# This is a placeholder for PDF OCR processing
			return "PDF OCR processing not implemented yet"
			
	except Exception as e:
		frappe.log_error(f"OCR processing error: {str(e)}")
		return ""

def encrypt_file(file_path):
	"""Encrypt file using Fernet encryption"""
	try:
		# Generate or retrieve encryption key
		key = get_encryption_key()
		fernet = Fernet(key)
		
		# Read file content
		with open(file_path, 'rb') as file:
			file_data = file.read()
		
		# Encrypt file data
		encrypted_data = fernet.encrypt(file_data)
		
		# Create encrypted file path
		encrypted_path = file_path + '.encrypted'
		
		# Write encrypted data
		with open(encrypted_path, 'wb') as file:
			file.write(encrypted_data)
		
		return encrypted_path
		
	except Exception as e:
		frappe.log_error(f"File encryption error: {str(e)}")
		raise e

def decrypt_file(encrypted_file_path):
	"""Decrypt file using Fernet encryption"""
	try:
		# Generate or retrieve encryption key
		key = get_encryption_key()
		fernet = Fernet(key)
		
		# Read encrypted file content
		with open(encrypted_file_path, 'rb') as file:
			encrypted_data = file.read()
		
		# Decrypt file data
		decrypted_data = fernet.decrypt(encrypted_data)
		
		# Create decrypted file path
		decrypted_path = encrypted_file_path.replace('.encrypted', '_decrypted')
		
		# Write decrypted data
		with open(decrypted_path, 'wb') as file:
			file.write(decrypted_data)
		
		return decrypted_path
		
	except Exception as e:
		frappe.log_error(f"File decryption error: {str(e)}")
		raise e

def get_encryption_key():
	"""Get or generate encryption key"""
	# In production, store this key securely
	key = frappe.get_conf().get('archive_encryption_key')
	
	if not key:
		# Generate new key
		key = Fernet.generate_key()
		# Store key in site config (in production, use a secure key management system)
		frappe.conf.archive_encryption_key = key.decode()
		frappe.db.commit()
	
	return key.encode() if isinstance(key, str) else key

def generate_audit_log(action, document_id, user=None, details=None):
	"""Generate audit log entry"""
	audit_entry = {
		"doctype": "Archive Audit Trail",
		"action": action,
		"document_id": document_id,
		"user": user or frappe.session.user,
		"timestamp": frappe.utils.now(),
		"ip_address": frappe.local.request.environ.get('REMOTE_ADDR') if frappe.local.request else "System",
		"details": details or f"Action: {action}"
	}
	
	audit_doc = frappe.get_doc(audit_entry)
	audit_doc.insert(ignore_permissions=True)
	
	return audit_doc.name

def categorize_document(document_content, document_type):
	"""Automatically categorize document based on content"""
	try:
		# This is a simplified categorization logic
		# In production, you might want to use ML models for better categorization
		
		category_keywords = {
			"Financial": ["invoice", "payment", "receipt", "financial", "budget", "expense"],
			"Legal": ["contract", "agreement", "legal", "terms", "conditions", "law"],
			"HR": ["employee", "hr", "personnel", "salary", "benefits", "policy"],
			"Technical": ["technical", "specification", "manual", "guide", "documentation"],
			"Administrative": ["admin", "administrative", "procedure", "policy", "guideline"]
		}
		
		content_lower = document_content.lower()
		
		for category, keywords in category_keywords.items():
			if any(keyword in content_lower for keyword in keywords):
				return category
		
		return "General"
		
	except Exception as e:
		frappe.log_error(f"Document categorization error: {str(e)}")
		return "General"

def extract_metadata(file_path):
	"""Extract metadata from file"""
	try:
		metadata = {
			"file_size": os.path.getsize(file_path),
			"file_extension": os.path.splitext(file_path)[1],
			"file_name": os.path.basename(file_path),
			"creation_time": os.path.getctime(file_path),
			"modification_time": os.path.getmtime(file_path)
		}
		
		# Add image-specific metadata
		if metadata["file_extension"].lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
			try:
				image = Image.open(file_path)
				metadata.update({
					"image_width": image.width,
					"image_height": image.height,
					"image_mode": image.mode
				})
			except Exception:
				pass
		
		return metadata
		
	except Exception as e:
		frappe.log_error(f"Metadata extraction error: {str(e)}")
		return {}

def validate_file_type(file_path, allowed_types=None):
	"""Validate file type"""
	if not allowed_types:
		allowed_types = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.txt', '.xlsx', '.xls']
	
	file_ext = os.path.splitext(file_path)[1].lower()
	return file_ext in allowed_types

def compress_image(file_path, quality=85):
	"""Compress image file"""
	try:
		image = Image.open(file_path)
		
		# Convert to RGB if necessary
		if image.mode in ('RGBA', 'LA', 'P'):
			image = image.convert('RGB')
		
		# Compress image
		compressed_path = file_path.replace('.', '_compressed.')
		image.save(compressed_path, 'JPEG', quality=quality, optimize=True)
		
		return compressed_path
		
	except Exception as e:
		frappe.log_error(f"Image compression error: {str(e)}")
		return file_path

def generate_document_id(prefix="ARCH"):
	"""Generate unique document ID"""
	import datetime
	timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
	random_suffix = frappe.generate_hash(length=4)
	return f"{prefix}{timestamp}{random_suffix}"
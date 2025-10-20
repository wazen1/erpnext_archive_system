import frappe
from frappe import _

def before_install():
	"""Pre-installation checks and setup"""
	
	# Check ERPNext version
	check_erpnext_version()
	
	# Check Python dependencies
	check_python_dependencies()
	
	# Check system requirements
	check_system_requirements()
	
	frappe.msgprint(_("Pre-installation checks completed successfully!"))

def check_erpnext_version():
	"""Check if ERPNext version is compatible"""
	try:
		erpnext_version = frappe.get_installed_version("erpnext")
		if not erpnext_version:
			frappe.throw(_("ERPNext is not installed. This app requires ERPNext to function."))
		
		# Check if version is 15.x
		if not erpnext_version.startswith("15"):
			frappe.throw(_("This app requires ERPNext version 15.x. Current version: {0}").format(erpnext_version))
		
		frappe.msgprint(_("ERPNext version check passed: {0}").format(erpnext_version))
		
	except Exception as e:
		frappe.throw(_("Error checking ERPNext version: {0}").format(str(e)))

def check_python_dependencies():
	"""Check if required Python packages are available"""
	required_packages = [
		"Pillow",
		"pytesseract", 
		"opencv-python",
		"cryptography",
		"elasticsearch",
		"redis",
		"celery"
	]
	
	missing_packages = []
	
	for package in required_packages:
		try:
			__import__(package.replace("-", "_"))
		except ImportError:
			missing_packages.append(package)
	
	if missing_packages:
		frappe.throw(_("Missing required Python packages: {0}. Please install them using: pip install {1}").format(
			", ".join(missing_packages), " ".join(missing_packages)
		))
	
	frappe.msgprint(_("Python dependencies check passed"))

def check_system_requirements():
	"""Check system requirements"""
	import os
	import platform
	
	# Check available disk space
	try:
		disk_usage = os.statvfs('/')
		free_space_gb = (disk_usage.f_frsize * disk_usage.f_bavail) / (1024**3)
		
		if free_space_gb < 1:  # Require at least 1GB free space
			frappe.msgprint(_("Warning: Low disk space detected. Archive system may require significant storage."))
	except:
		pass
	
	# Check Python version
	python_version = platform.python_version()
	if not python_version.startswith("3.8") and not python_version.startswith("3.9") and not python_version.startswith("3.10"):
		frappe.msgprint(_("Warning: Python version {0} may not be fully compatible. Recommended: Python 3.8-3.10").format(python_version))
	
	frappe.msgprint(_("System requirements check completed"))
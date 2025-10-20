# ERPNext Archive System

A comprehensive archiving system application for ERPNext version 15.82, built on the Frappe framework. This system provides secure and efficient storage, retrieval, and management of archived data with advanced features including OCR, versioning, automated categorization, and robust search functionality.

## Features

### Core Functionality
- **Document Management**: Secure storage and retrieval of archived documents
- **OCR Integration**: Automatic text extraction from images and scanned documents using Tesseract
- **Version Control**: Complete versioning system with change tracking and rollback capabilities
- **Related Files System**: Manage document relationships and dependencies
- **Automated Categorization**: AI-powered document classification based on content analysis
- **Advanced Search**: Full-text search with filters and faceted search capabilities

### Security & Compliance
- **Data Encryption**: End-to-end encryption for data at rest and in transit
- **Access Controls**: Role-based permissions and detailed access management
- **Audit Trails**: Comprehensive logging of all system activities
- **Compliance Support**: Built-in support for SOX, GDPR, and other regulatory requirements
- **Data Retention**: Automated retention policies and cleanup procedures

### User Experience
- **Intuitive Interface**: Modern, responsive web interface
- **Bulk Operations**: Upload, download, and manage multiple documents
- **Dashboard**: Real-time statistics and system overview
- **Mobile Support**: Responsive design for mobile devices
- **API Integration**: RESTful API for external system integration

### Performance & Scalability
- **High Performance**: Optimized for large data volumes
- **Caching**: Intelligent caching for improved response times
- **Async Processing**: Background processing for OCR and categorization
- **Scalable Architecture**: Designed to handle enterprise-level data volumes

## Installation

### Prerequisites
- ERPNext version 15.82 or higher
- Python 3.8-3.10
- Required Python packages (see requirements.txt)

### System Requirements
- Minimum 4GB RAM
- 10GB free disk space (more for large archives)
- Tesseract OCR engine installed

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd erpnext_archive_system
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Tesseract OCR**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr
   
   # CentOS/RHEL
   sudo yum install tesseract
   
   # macOS
   brew install tesseract
   ```

4. **Install the app in ERPNext**
   ```bash
   bench --site <your-site> install-app erpnext_archive_system
   ```

5. **Run migrations**
   ```bash
   bench --site <your-site> migrate
   ```

6. **Restart ERPNext**
   ```bash
   bench restart
   ```

## Configuration

### Basic Configuration

1. **Access the Archive System**
   - Navigate to the Archive Dashboard in ERPNext
   - Go to Settings > Archive Configuration

2. **Configure OCR Settings**
   - Set Tesseract path
   - Configure OCR languages
   - Enable/disable preprocessing

3. **Set up Encryption**
   - Generate encryption keys
   - Configure encryption algorithms
   - Set up key rotation policies

4. **Configure Storage**
   - Choose storage backend (local, S3, etc.)
   - Set file size limits
   - Configure compression settings

### Advanced Configuration

#### Elasticsearch Setup (Optional)
For enhanced search capabilities:

1. Install Elasticsearch
2. Configure connection settings
3. Enable full-text search

#### Redis Setup (Optional)
For improved performance:

1. Install Redis
2. Configure caching settings
3. Enable session storage

## Usage

### Uploading Documents

1. **Single Document Upload**
   - Click "Upload Document" button
   - Fill in document details
   - Select file and upload
   - OCR processing will start automatically

2. **Bulk Upload**
   - Use the bulk upload feature
   - Upload multiple files at once
   - Configure batch processing settings

### Managing Documents

1. **Search and Filter**
   - Use the search bar for quick searches
   - Apply filters by category, type, date, etc.
   - Use advanced search for complex queries

2. **Document Operations**
   - View document details
   - Download files
   - Create new versions
   - Manage relationships

3. **Version Control**
   - View version history
   - Compare versions
   - Restore previous versions
   - Track changes

### Category Management

1. **Create Categories**
   - Define document categories
   - Set up subcategories
   - Configure auto-categorization rules

2. **Manage Rules**
   - Create keyword-based rules
   - Set up pattern matching
   - Configure document type rules

### User Management

1. **Role Assignment**
   - Archive User: Can upload and manage documents
   - Archive Viewer: Read-only access
   - Archive Manager: Full administrative access

2. **Permission Management**
   - Set document-level permissions
   - Configure category access
   - Manage user groups

## API Documentation

### Authentication
All API endpoints require authentication. Include the API key in the request header:
```
Authorization: token <your-api-key>
```

### Endpoints

#### Upload Document
```http
POST /api/method/erpnext_archive_system.api.archive_api.upload_document
Content-Type: application/json

{
  "file_data": "base64-encoded-file",
  "document_title": "Document Title",
  "document_type": "Document Type ID",
  "category": "Category ID",
  "description": "Document Description",
  "access_level": "Internal|Confidential|Restricted",
  "process_ocr": true
}
```

#### Search Documents
```http
GET /api/method/erpnext_archive_system.api.archive_api.search_documents?search_term=keyword&filters={"category":"category_id"}
```

#### Get Document Details
```http
GET /api/method/erpnext_archive_system.api.archive_api.get_document_details?document_id=doc_id
```

#### Download Document
```http
GET /api/method/erpnext_archive_system.api.archive_api.download_document?document_id=doc_id&version_number=1
```

## Security Considerations

### Data Protection
- All sensitive data is encrypted at rest
- File transfers use secure protocols
- Access is logged and audited

### Access Control
- Role-based permissions
- Document-level access control
- IP-based restrictions (optional)

### Compliance
- GDPR compliance features
- SOX audit trail support
- Data retention policies
- Right to be forgotten implementation

## Troubleshooting

### Common Issues

1. **OCR Not Working**
   - Check Tesseract installation
   - Verify file format support
   - Check OCR configuration

2. **Upload Failures**
   - Check file size limits
   - Verify file type support
   - Check storage permissions

3. **Search Issues**
   - Rebuild search index
   - Check Elasticsearch connection
   - Verify search configuration

### Logs and Debugging

1. **Enable Debug Mode**
   ```python
   frappe.conf.developer_mode = 1
   ```

2. **Check Logs**
   - Application logs: `logs/frappe.log`
   - Error logs: `logs/error.log`
   - Archive logs: `logs/archive.log`

3. **Database Queries**
   - Enable query logging
   - Monitor slow queries
   - Check index usage

## Performance Optimization

### Database Optimization
- Regular index maintenance
- Query optimization
- Connection pooling

### Caching
- Enable Redis caching
- Configure cache TTL
- Monitor cache hit rates

### File Storage
- Use SSD storage for better I/O
- Implement file compression
- Consider CDN for large files

## Backup and Recovery

### Backup Strategy
1. **Database Backup**
   - Regular database dumps
   - Point-in-time recovery
   - Cross-region replication

2. **File Backup**
   - File system backups
   - Cloud storage replication
   - Versioned backups

3. **Configuration Backup**
   - Export configuration
   - Document system settings
   - Backup encryption keys

### Recovery Procedures
1. **Full System Recovery**
2. **Partial Data Recovery**
3. **Configuration Recovery**

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation wiki

## Changelog

### Version 1.0.0
- Initial release
- Core archiving functionality
- OCR integration
- Version control system
- Basic search capabilities
- User management
- API endpoints

## Roadmap

### Version 1.1.0
- Advanced analytics dashboard
- Machine learning categorization
- Mobile app
- Advanced reporting

### Version 1.2.0
- Workflow automation
- Integration with more systems
- Advanced security features
- Performance improvements

---

For more detailed documentation, please visit our [Wiki](https://github.com/your-repo/wiki).
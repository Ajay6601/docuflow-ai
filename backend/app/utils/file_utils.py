import uuid
from datetime import datetime
from pathlib import Path
import magic
from app.config import settings


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename while preserving the extension.
    Format: {uuid}_{original_name}
    """
    file_extension = Path(original_filename).suffix
    unique_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    # Remove extension from original filename
    name_without_ext = Path(original_filename).stem
    
    # Create unique filename
    unique_filename = f"{timestamp}_{unique_id}_{name_without_ext}{file_extension}"
    return unique_filename


def generate_storage_path(filename: str) -> str:
    """
    Generate storage path with year/month structure.
    Format: uploads/YYYY/MM/filename
    """
    now = datetime.utcnow()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    
    return f"uploads/{year}/{month}/{filename}"


def detect_file_type(file_content: bytes, filename: str) -> str:
    """
    Detect the actual MIME type of the file content.
    Falls back to extension-based detection if magic fails.
    """
    try:
        # Try to detect using python-magic
        mime = magic.Magic(mime=True)
        detected_type = mime.from_buffer(file_content)
        return detected_type
    except Exception:
        # Fallback to extension-based detection
        extension_map = {
            '.pdf': 'application/pdf',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.eml': 'message/rfc822'
        }
        
        ext = Path(filename).suffix.lower()
        return extension_map.get(ext, 'application/octet-stream')


def validate_file_size(file_size: int) -> bool:
    """Check if file size is within allowed limit."""
    return file_size <= settings.MAX_FILE_SIZE


def validate_file_type(mime_type: str) -> bool:
    """Check if file type is allowed."""
    return mime_type in settings.ALLOWED_FILE_TYPES


def format_file_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"
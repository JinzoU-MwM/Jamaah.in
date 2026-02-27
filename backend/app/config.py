"""
Configuration settings for the Hajj/Umrah Document Processing System
"""
import os
from pathlib import Path

# Base directories
# config is in backend/app/config.py -> parent is backend/app -> parent.parent is backend
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
TEMPLATE_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
TEMPLATE_DIR.mkdir(exist_ok=True, parents=True)
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# File settings
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Excel settings
EXCEL_SHEET_NAME = "Data Jamaah"
DEFAULT_TEMPLATE_NAME = "jamaah.xlsm"

# Default values
DEFAULT_NATIONALITY = "WNI"
DEFAULT_IDENTITY_TYPE_KTP = "KTP"
DEFAULT_IDENTITY_TYPE_PASSPORT = "PASPOR"

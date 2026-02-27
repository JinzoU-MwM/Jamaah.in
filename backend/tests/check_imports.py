import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))
print(f"Added {backend_dir} to sys.path")

try:
    from app.services.cleaner import validate_and_clean_name
    print("Import cleaner: SUCCESS")
    from app.services.parser import extract_nik
    print("Import parser: SUCCESS")
    from app.schemas import ExtractedDataItem
    print("Import schemas: SUCCESS")
except ImportError as e:
    print(f"Import FAILED: {e}")
except Exception as e:
    print(f"FAILED: {e}")

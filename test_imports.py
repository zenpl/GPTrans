#!/usr/bin/env python3
"""
Test script to verify all imports are working correctly
"""
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test all key module imports."""
    try:
        print("Testing core imports...")
        
        # Test shared modules
        from app.shared.schemas import Book, Block, Page, GlossaryTerm
        from app.shared.constants import CHINESE_FONTS, DATA_DIR
        from app.shared.utils.chinese_typography import ChineseTypography
        from app.shared.utils.fit_loop import FitLoop
        print("✅ Shared modules imported successfully")
        
        # Test backend modules
        from app.backend.database import get_db, engine
        from app.backend.models import Book as BookModel, Block as BlockModel
        from app.backend.services.translation import MockTranslationProvider
        from app.backend.services.typesetting import TypesettingEngine
        from app.backend.services.export import ExportService
        from app.backend.ocr_providers.mock import MockOCRProvider
        print("✅ Backend modules imported successfully")
        
        # Test workers
        from app.workers.main import sync_process_ocr_job
        print("✅ Workers imported successfully")
        
        print("\n🎉 All imports working correctly!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
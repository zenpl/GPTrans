from pathlib import Path

# File paths
DATA_DIR = Path("data")
BOOKS_DIR = DATA_DIR / "books"
EXPORTS_DIR = DATA_DIR / "exports"
FONTS_DIR = Path("app/shared/fonts")
SAMPLES_DIR = Path("app/samples")

# Supported formats
SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}
SUPPORTED_PDF_FORMATS = {".pdf"}
SUPPORTED_EXPORT_FORMATS = {"pdf", "epub"}

# OCR settings
DEFAULT_DPI = 300
MIN_CONFIDENCE = 0.7

# Translation settings
DEFAULT_LENGTH_POLICY = "normal"
CONCISE_LENGTH_RATIO = 0.9

# Chinese typography settings
CHINESE_FONTS = {
    "serif": "Noto Serif CJK SC",
    "sans": "Noto Sans CJK SC"
}

# Chinese punctuation rules
NO_LINE_START_CHARS = "!%),.:;?]}¢°·ˇˉ―‖'\"…‰′″›℃∶、。〃〉》」』】〕〗〞︰︱︳﹐﹑﹒﹕﹖﹗﹚﹜﹞！），．：；？｜｝︶"
NO_LINE_END_CHARS = "([{·'\"〈《「『【〔〖〝﹙﹛﹝（｛｟｠￠￡￥"

# Fit loop settings
FIT_LOOP_MAX_ITERATIONS = 10
DEFAULT_FRAME_MARGIN = 10  # pixels

# Page settings
A4_WIDTH_MM = 210
A4_HEIGHT_MM = 297
A4_DPI = 300

# CSS units conversion
MM_TO_PX = 3.779528  # at 96 DPI
PT_TO_PX = 1.333333  # at 96 DPI

# Redis settings
REDIS_URL = "redis://localhost:6379/0"
JOB_TIMEOUT = 3600  # 1 hour

# Database
DATABASE_URL = "postgresql://gptrans:password@localhost:5432/gptrans"

# API settings
API_PREFIX = "/api"
API_VERSION = "v1"

# File upload limits  
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_PAGES_PER_BOOK = 500
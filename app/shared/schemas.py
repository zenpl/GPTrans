from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class LanguageCode(str, Enum):
    GERMAN = "de"
    SWEDISH = "sv"
    CHINESE = "zh-CN"


class BlockType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph" 
    CAPTION = "caption"
    FOOTNOTE = "footnote"
    FIGURE = "figure"
    PAGE_NUMBER = "page-number"


class JobType(str, Enum):
    OCR = "ocr"
    TRANSLATE = "translate"
    TYPESET = "typeset"
    EXPORT = "export"


class JobStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class BBox(BaseModel):
    x: float
    y: float
    w: float 
    h: float


class OCRLine(BaseModel):
    bbox: BBox
    text: str
    confidence: Optional[float] = None


class OCRBlock(BaseModel):
    id: str
    type: BlockType
    bbox: BBox
    order: int
    lines: List[OCRLine]
    confidence: Optional[float] = None


class OCRPage(BaseModel):
    index: int
    width: int
    height: int
    dpi: Optional[int] = 300


class OCRResult(BaseModel):
    page: OCRPage
    blocks: List[OCRBlock]
    reading_order: List[str]


class BookCreate(BaseModel):
    title: str
    source_lang: LanguageCode
    target_lang: LanguageCode = LanguageCode.CHINESE
    glossary_id: Optional[int] = None


class Book(BaseModel):
    id: int
    title: str
    source_lang: LanguageCode
    target_lang: LanguageCode
    created_at: datetime
    glossary_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class PageCreate(BaseModel):
    book_id: int
    index: int
    image_url: str
    width: int
    height: int
    dpi: int = 300


class Page(BaseModel):
    id: int
    book_id: int
    index: int
    image_url: str
    width: int
    height: int
    dpi: int
    
    class Config:
        from_attributes = True


class BlockCreate(BaseModel):
    page_id: int
    type: BlockType
    bbox: BBox
    order: int
    text_source: str
    spans: Optional[List[Dict[str, Any]]] = []
    refs: Optional[List[str]] = []


class BlockUpdate(BaseModel):
    text_translated: Optional[str] = None
    status: Optional[str] = None


class Block(BaseModel):
    id: int
    page_id: int
    type: BlockType
    bbox: BBox
    order: int
    text_source: str
    text_translated: Optional[str] = None
    spans: List[Dict[str, Any]] = []
    refs: List[str] = []
    status: str = "pending"
    
    class Config:
        from_attributes = True


class GlossaryTermCreate(BaseModel):
    src: str
    tgt: str
    case_sensitive: bool = False
    notes: Optional[str] = None


class GlossaryTerm(BaseModel):
    id: int
    glossary_id: int
    src: str
    tgt: str
    case_sensitive: bool
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class GlossaryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class Glossary(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    terms: List[GlossaryTerm] = []
    
    class Config:
        from_attributes = True


class TranslationRequest(BaseModel):
    glossary_id: Optional[int] = None
    style: str = "normal"
    length_hint: str = "normal"  # normal | concise


class TypesetRequest(BaseModel):
    page_ids: Optional[List[int]] = None


class ExportRequest(BaseModel):
    formats: List[str] = Field(default=["pdf"], description="Export formats: pdf, epub")
    

class Export(BaseModel):
    id: int
    book_id: int
    formats: List[str]
    url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class Job(BaseModel):
    id: int
    book_id: int
    type: JobType
    status: JobStatus
    logs: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FitLoopConfig(BaseModel):
    initial_line_height: float = 1.5
    initial_letter_spacing: float = 0.0
    min_letter_spacing: float = -0.02
    min_line_height: float = 1.45
    max_line_height: float = 1.6
    max_letter_spacing: float = 0.01
    overflow_tolerance: float = 0.02  # 2% overflow tolerance
    concise_threshold: float = 0.9  # trigger concise translation at 90%


class TypesetFrame(BaseModel):
    block_id: int
    x: float
    y: float
    width: float
    height: float
    content: str
    css_properties: Dict[str, str] = {}


class TypesetPage(BaseModel):
    page_id: int
    width: float
    height: float
    frames: List[TypesetFrame]
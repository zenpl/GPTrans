from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from pathlib import Path
import uuid

from app.backend.database import get_db, engine
from app.backend.models import Base, Book, Page, Block, Glossary, GlossaryTerm, Job, Export
from app.backend.services.translation import translate_paragraph, get_translation_provider
from app.backend.ocr_providers.mock import MockOCRProvider
from app.shared.schemas import (
    BookCreate, Book as BookSchema, 
    Page as PageSchema, Block as BlockSchema, BlockUpdate,
    GlossaryCreate, Glossary as GlossarySchema,
    GlossaryTermCreate, GlossaryTerm as GlossaryTermSchema,
    TranslationRequest, TypesetRequest, ExportRequest,
    Job as JobSchema, Export as ExportSchema
)
from app.shared.constants import DATA_DIR, BOOKS_DIR, EXPORTS_DIR

# Create database tables
Base.metadata.create_all(bind=engine)

# Ensure data directories exist
DATA_DIR.mkdir(exist_ok=True)
BOOKS_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="GPTrans API",
    description="OCR to Chinese Translation and Typesetting Service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory=str(DATA_DIR)), name="static")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "GPTrans API is running"}


@app.post("/api/upload", response_model=BookSchema)
async def upload_book(
    file: UploadFile = File(...),
    title: str = "Untitled Book",
    source_lang: str = "de",
    db: Session = Depends(get_db)
):
    """Upload a book (image or PDF) and create a new book record."""
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.pdf'}:
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    # Create book record
    book = Book(
        title=title,
        source_lang=source_lang,
        target_lang="zh-CN"
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    
    # Save uploaded file
    book_dir = BOOKS_DIR / str(book.id)
    book_dir.mkdir(exist_ok=True)
    
    file_path = book_dir / f"source{file_ext}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create initial page record for images
    if file_ext != '.pdf':
        page = Page(
            book_id=book.id,
            index=0,
            image_url=f"/static/books/{book.id}/source{file_ext}",
            width=1240,  # Default dimensions
            height=1754,
            dpi=150
        )
        db.add(page)
        db.commit()
    
    return BookSchema.from_orm(book)


@app.post("/api/books/{book_id}/ocr/normalize")
async def normalize_ocr(
    book_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Normalize OCR data for a book."""
    
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Create OCR job
    job = Job(book_id=book_id, type="ocr", status="in_progress")
    db.add(job)
    db.commit()
    
    # Process OCR in background
    background_tasks.add_task(process_ocr_task, book_id, job.id, db)
    
    return {"message": "OCR processing started", "job_id": job.id}


async def process_ocr_task(book_id: int, job_id: int, db: Session):
    """Background task to process OCR."""
    
    try:
        ocr_provider = MockOCRProvider()
        
        # Get book pages or create from source file
        pages = db.query(Page).filter(Page.book_id == book_id).all()
        
        if not pages:
            # Process PDF or create single page
            book_dir = BOOKS_DIR / str(book_id)
            source_files = list(book_dir.glob("source.*"))
            
            if source_files:
                source_file = source_files[0]
                if source_file.suffix.lower() == '.pdf':
                    ocr_results = await ocr_provider.process_pdf(source_file)
                else:
                    ocr_results = [await ocr_provider.process_image(source_file)]
                
                # Create pages and blocks
                for ocr_result in ocr_results:
                    page = Page(
                        book_id=book_id,
                        index=ocr_result.page.index,
                        image_url=f"/static/books/{book_id}/page_{ocr_result.page.index}.png",
                        width=ocr_result.page.width,
                        height=ocr_result.page.height,
                        dpi=ocr_result.page.dpi
                    )
                    db.add(page)
                    db.commit()
                    db.refresh(page)
                    
                    # Create blocks
                    for ocr_block in ocr_result.blocks:
                        block = Block(
                            page_id=page.id,
                            type=ocr_block.type.value,
                            bbox_x=ocr_block.bbox.x,
                            bbox_y=ocr_block.bbox.y,
                            bbox_w=ocr_block.bbox.w,
                            bbox_h=ocr_block.bbox.h,
                            order=ocr_block.order,
                            text_source=" ".join(line.text for line in ocr_block.lines),
                            status="pending"
                        )
                        db.add(block)
                    
                    db.commit()
        
        # Update job status
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "completed"
            db.commit()
    
    except Exception as e:
        # Update job with error
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "failed"
            job.logs = str(e)
            db.commit()


@app.post("/api/books/{book_id}/translate")
async def translate_book(
    book_id: int,
    request: TranslationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Translate all blocks in a book."""
    
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Create translation job
    job = Job(book_id=book_id, type="translate", status="in_progress")
    db.add(job)
    db.commit()
    
    # Process translation in background
    background_tasks.add_task(translate_book_task, book_id, job.id, request, db)
    
    return {"message": "Translation started", "job_id": job.id}


async def translate_book_task(
    book_id: int, 
    job_id: int, 
    request: TranslationRequest, 
    db: Session
):
    """Background task to translate book."""
    
    try:
        # Get glossary if specified
        glossary_terms = []
        if request.glossary_id:
            terms = db.query(GlossaryTerm).filter(
                GlossaryTerm.glossary_id == request.glossary_id
            ).all()
            glossary_terms = [GlossaryTermSchema.from_orm(term) for term in terms]
        
        # Get all blocks to translate
        blocks = db.query(Block).join(Page).filter(
            Page.book_id == book_id,
            Block.text_translated.is_(None)
        ).order_by(Page.index, Block.order).all()
        
        book = db.query(Book).filter(Book.id == book_id).first()
        
        # Translate each block
        for block in blocks:
            try:
                translated = await translate_paragraph(
                    text=block.text_source,
                    source_lang=book.source_lang,
                    target_lang=book.target_lang,
                    glossary=glossary_terms,
                    length_policy=request.length_hint
                )
                
                block.text_translated = translated
                block.status = "translated"
                db.commit()
                
            except Exception as e:
                print(f"Error translating block {block.id}: {e}")
                block.status = "failed"
                db.commit()
        
        # Update job status
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "completed"
            db.commit()
    
    except Exception as e:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "failed"
            job.logs = str(e)
            db.commit()


@app.get("/api/books/{book_id}", response_model=BookSchema)
async def get_book(book_id: int, db: Session = Depends(get_db)):
    """Get book details."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return BookSchema.from_orm(book)


@app.get("/api/books/{book_id}/blocks", response_model=List[BlockSchema])
async def get_book_blocks(book_id: int, db: Session = Depends(get_db)):
    """Get all blocks for a book."""
    blocks = db.query(Block).join(Page).filter(
        Page.book_id == book_id
    ).order_by(Page.index, Block.order).all()
    
    return [BlockSchema.from_orm(block) for block in blocks]


@app.patch("/api/blocks/{block_id}", response_model=BlockSchema)
async def update_block(
    block_id: int,
    update: BlockUpdate,
    db: Session = Depends(get_db)
):
    """Update a block's translation."""
    block = db.query(Block).filter(Block.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    
    if update.text_translated is not None:
        block.text_translated = update.text_translated
    if update.status is not None:
        block.status = update.status
    
    db.commit()
    db.refresh(block)
    return BlockSchema.from_orm(block)


@app.post("/api/glossaries", response_model=GlossarySchema)
async def create_glossary(
    glossary: GlossaryCreate,
    db: Session = Depends(get_db)
):
    """Create a new glossary."""
    db_glossary = Glossary(**glossary.dict())
    db.add(db_glossary)
    db.commit()
    db.refresh(db_glossary)
    return GlossarySchema.from_orm(db_glossary)


@app.post("/api/glossaries/{glossary_id}/terms", response_model=GlossaryTermSchema)
async def create_glossary_term(
    glossary_id: int,
    term: GlossaryTermCreate,
    db: Session = Depends(get_db)
):
    """Add a term to a glossary."""
    glossary = db.query(Glossary).filter(Glossary.id == glossary_id).first()
    if not glossary:
        raise HTTPException(status_code=404, detail="Glossary not found")
    
    db_term = GlossaryTerm(glossary_id=glossary_id, **term.dict())
    db.add(db_term)
    db.commit()
    db.refresh(db_term)
    return GlossaryTermSchema.from_orm(db_term)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
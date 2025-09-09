import os
import asyncio
import logging
from typing import List, Dict, Any
from redis import Redis
from rq import Worker, Queue, Connection
from pathlib import Path
import sys

# Add app to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.backend.models import Book, Page, Block, Job
from app.backend.database import SessionLocal
from app.backend.services.translation import translate_paragraph, get_translation_provider
from app.backend.services.typesetting import TypesettingEngine
from app.backend.services.export import ExportService
from app.backend.ocr_providers.mock import MockOCRProvider
from app.shared.schemas import GlossaryTerm, TranslationRequest, ExportRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection
redis_conn = Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', '6379')),
    db=int(os.getenv('REDIS_DB', '0'))
)

# Queues
ocr_queue = Queue('ocr', connection=redis_conn)
translation_queue = Queue('translation', connection=redis_conn)
typeset_queue = Queue('typeset', connection=redis_conn)
export_queue = Queue('export', connection=redis_conn)


async def process_ocr_job(book_id: int, job_id: int) -> Dict[str, Any]:
    """Process OCR job for a book."""
    db = SessionLocal()
    
    try:
        # Update job status
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise Exception(f"Job {job_id} not found")
        
        job.status = "in_progress"
        db.commit()
        
        # Get book
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise Exception(f"Book {book_id} not found")
        
        # Initialize OCR provider
        ocr_provider = MockOCRProvider()
        
        # Process book source file
        book_dir = Path(f"data/books/{book_id}")
        source_files = list(book_dir.glob("source.*"))
        
        if not source_files:
            raise Exception("No source file found")
        
        source_file = source_files[0]
        
        if source_file.suffix.lower() == '.pdf':
            ocr_results = await ocr_provider.process_pdf(source_file)
        else:
            ocr_results = [await ocr_provider.process_image(source_file)]
        
        # Create pages and blocks
        for ocr_result in ocr_results:
            # Check if page already exists
            existing_page = db.query(Page).filter(
                Page.book_id == book_id,
                Page.index == ocr_result.page.index
            ).first()
            
            if not existing_page:
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
            else:
                page = existing_page
            
            # Remove existing blocks for this page
            db.query(Block).filter(Block.page_id == page.id).delete()
            
            # Create new blocks
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
        job.status = "completed"
        db.commit()
        
        logger.info(f"OCR job {job_id} completed for book {book_id}")
        return {"status": "completed", "pages_processed": len(ocr_results)}
        
    except Exception as e:
        # Update job with error
        if job:
            job.status = "failed"
            job.logs = str(e)
            db.commit()
        
        logger.error(f"OCR job {job_id} failed: {e}")
        raise
    
    finally:
        db.close()


async def process_translation_job(book_id: int, job_id: int, request: Dict[str, Any]) -> Dict[str, Any]:
    """Process translation job for a book."""
    db = SessionLocal()
    
    try:
        # Update job status
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise Exception(f"Job {job_id} not found")
        
        job.status = "in_progress"
        db.commit()
        
        # Get book and blocks
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise Exception(f"Book {book_id} not found")
        
        blocks = db.query(Block).join(Page).filter(
            Page.book_id == book_id,
            Block.text_translated.is_(None)
        ).order_by(Page.index, Block.order).all()
        
        if not blocks:
            raise Exception("No blocks to translate")
        
        # Get glossary terms if specified
        glossary_terms = []
        if request.get('glossary_id'):
            # This would fetch glossary terms from DB
            pass
        
        # Translate each block
        translated_count = 0
        failed_count = 0
        
        for block in blocks:
            try:
                translated = await translate_paragraph(
                    text=block.text_source,
                    source_lang=book.source_lang,
                    target_lang=book.target_lang,
                    glossary=glossary_terms,
                    length_policy=request.get('length_hint', 'normal')
                )
                
                block.text_translated = translated
                block.status = "translated"
                translated_count += 1
                
            except Exception as e:
                logger.error(f"Error translating block {block.id}: {e}")
                block.status = "failed"
                failed_count += 1
            
            db.commit()
        
        # Update job status
        job.status = "completed" if failed_count == 0 else "completed"  # Still mark as completed even with some failures
        job.logs = f"Translated {translated_count} blocks, {failed_count} failed"
        db.commit()
        
        logger.info(f"Translation job {job_id} completed: {translated_count} translated, {failed_count} failed")
        return {
            "status": "completed", 
            "translated_count": translated_count, 
            "failed_count": failed_count
        }
        
    except Exception as e:
        if job:
            job.status = "failed"
            job.logs = str(e)
            db.commit()
        
        logger.error(f"Translation job {job_id} failed: {e}")
        raise
    
    finally:
        db.close()


async def process_typeset_job(book_id: int, job_id: int) -> Dict[str, Any]:
    """Process typesetting job for a book."""
    db = SessionLocal()
    
    try:
        # Update job status
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise Exception(f"Job {job_id} not found")
        
        job.status = "in_progress"
        db.commit()
        
        # Get book, pages, and blocks
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise Exception(f"Book {book_id} not found")
        
        pages = db.query(Page).filter(Page.book_id == book_id).order_by(Page.index).all()
        blocks = db.query(Block).join(Page).filter(Page.book_id == book_id).all()
        
        if not pages or not blocks:
            raise Exception("No pages or blocks found")
        
        # Initialize typesetting engine
        typesetting_engine = TypesettingEngine()
        
        # Typeset all pages
        typeset_pages = await typesetting_engine.typeset_pages(pages, blocks)
        
        # Update block statuses
        for block in blocks:
            if block.text_translated:
                block.status = "typeset"
        
        db.commit()
        
        # Update job status
        job.status = "completed"
        job.logs = f"Typeset {len(typeset_pages)} pages with {len(blocks)} blocks"
        db.commit()
        
        logger.info(f"Typeset job {job_id} completed for book {book_id}")
        return {"status": "completed", "pages_typeset": len(typeset_pages)}
        
    except Exception as e:
        if job:
            job.status = "failed"
            job.logs = str(e)
            db.commit()
        
        logger.error(f"Typeset job {job_id} failed: {e}")
        raise
    
    finally:
        db.close()


async def process_export_job(book_id: int, job_id: int, request: Dict[str, Any]) -> Dict[str, Any]:
    """Process export job for a book."""
    db = SessionLocal()
    
    try:
        # Update job status
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise Exception(f"Job {job_id} not found")
        
        job.status = "in_progress"
        db.commit()
        
        # Get book, pages, and blocks
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise Exception(f"Book {book_id} not found")
        
        pages = db.query(Page).filter(Page.book_id == book_id).order_by(Page.index).all()
        blocks = db.query(Block).join(Page).filter(Page.book_id == book_id).all()
        
        if not pages or not blocks:
            raise Exception("No pages or blocks found")
        
        # Initialize export service
        export_service = ExportService()
        
        # Export book
        export_url = await export_service.export_book(
            book=book,
            pages=pages,
            blocks=blocks,
            formats=request.get('formats', ['pdf'])
        )
        
        if not export_url:
            raise Exception("Export failed - no output URL")
        
        # Update job status
        job.status = "completed"
        job.logs = f"Exported to {', '.join(request.get('formats', ['pdf']))}: {export_url}"
        db.commit()
        
        logger.info(f"Export job {job_id} completed for book {book_id}: {export_url}")
        return {"status": "completed", "export_url": export_url}
        
    except Exception as e:
        if job:
            job.status = "failed"
            job.logs = str(e)
            db.commit()
        
        logger.error(f"Export job {job_id} failed: {e}")
        raise
    
    finally:
        db.close()


# Synchronous wrapper functions for RQ (since RQ doesn't support async directly)
def sync_process_ocr_job(book_id: int, job_id: int):
    return asyncio.run(process_ocr_job(book_id, job_id))

def sync_process_translation_job(book_id: int, job_id: int, request: Dict[str, Any]):
    return asyncio.run(process_translation_job(book_id, job_id, request))

def sync_process_typeset_job(book_id: int, job_id: int):
    return asyncio.run(process_typeset_job(book_id, job_id))

def sync_process_export_job(book_id: int, job_id: int, request: Dict[str, Any]):
    return asyncio.run(process_export_job(book_id, job_id, request))


if __name__ == '__main__':
    logger.info("Starting GPTrans workers...")
    
    # Listen to queues
    with Connection(redis_conn):
        worker = Worker([ocr_queue, translation_queue, typeset_queue, export_queue])
        worker.work()
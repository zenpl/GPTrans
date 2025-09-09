from abc import ABC, abstractmethod
from typing import List, Union
from pathlib import Path
import io
# from PIL import Image  # Optional dependency

from app.shared.schemas import OCRResult


class OCRProvider(ABC):
    """Abstract base class for OCR providers."""
    
    @abstractmethod
    async def process_image(self, image: Union[str, Path, io.BytesIO]) -> OCRResult:
        """
        Process a single image and return OCR results.
        
        Args:
            image: Path to image file or BytesIO buffer
            
        Returns:
            OCRResult with normalized blocks and reading order
        """
        pass
    
    @abstractmethod
    async def process_pdf(self, pdf_path: Union[str, Path]) -> List[OCRResult]:
        """
        Process a PDF file and return OCR results for each page.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of OCRResult objects, one per page
        """
        pass
    
    def normalize_reading_order(self, blocks: List, page_width: int, page_height: int) -> List[str]:
        """
        Determine reading order for blocks when not provided by OCR.
        Simple implementation: column detection + top-to-bottom, left-to-right.
        """
        if not blocks:
            return []
        
        # Sort blocks by position
        sorted_blocks = sorted(blocks, key=lambda b: (b.bbox.y, b.bbox.x))
        
        # Detect columns by grouping blocks with similar x coordinates
        columns = []
        current_column = []
        
        for block in sorted_blocks:
            if not current_column:
                current_column.append(block)
            else:
                # Check if this block is in the same column (similar x position)
                avg_x = sum(b.bbox.x for b in current_column) / len(current_column)
                if abs(block.bbox.x - avg_x) < page_width * 0.1:  # 10% tolerance
                    current_column.append(block)
                else:
                    # Start new column
                    columns.append(current_column)
                    current_column = [block]
        
        if current_column:
            columns.append(current_column)
        
        # Sort columns by average x position
        columns.sort(key=lambda col: sum(b.bbox.x for b in col) / len(col))
        
        # Extract reading order
        reading_order = []
        for column in columns:
            # Sort blocks in column by y position
            column.sort(key=lambda b: b.bbox.y)
            reading_order.extend(b.id for b in column)
        
        return reading_order
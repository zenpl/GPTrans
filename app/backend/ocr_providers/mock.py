import json
import asyncio
from pathlib import Path
from typing import List, Union
import io

from .base import OCRProvider
from app.shared.schemas import OCRResult, OCRPage, OCRBlock, OCRLine, BBox, BlockType


class MockOCRProvider(OCRProvider):
    """Mock OCR provider that loads pre-generated sample data."""
    
    def __init__(self, samples_dir: Path = None):
        self.samples_dir = samples_dir or Path("app/samples/ocr_outputs")
        
    async def process_image(self, image: Union[str, Path, io.BytesIO]) -> OCRResult:
        """Load mock OCR result from sample data."""
        await asyncio.sleep(0.5)  # Simulate processing time
        
        # For demo purposes, always return the same sample
        sample_file = self.samples_dir / "sample_page_1.json"
        if sample_file.exists():
            return await self._load_sample(sample_file)
        else:
            return self._generate_default_sample()
    
    async def process_pdf(self, pdf_path: Union[str, Path]) -> List[OCRResult]:
        """Load mock OCR results for multiple pages."""
        await asyncio.sleep(1.0)  # Simulate processing time
        
        results = []
        for i in range(3):  # Simulate 3 pages
            sample_file = self.samples_dir / f"sample_page_{i+1}.json"
            if sample_file.exists():
                result = await self._load_sample(sample_file)
            else:
                result = self._generate_default_sample(page_index=i)
            results.append(result)
        
        return results
    
    async def _load_sample(self, sample_file: Path) -> OCRResult:
        """Load OCR result from JSON file."""
        try:
            with open(sample_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return OCRResult(**data)
        except Exception as e:
            print(f"Error loading sample {sample_file}: {e}")
            return self._generate_default_sample()
    
    def _generate_default_sample(self, page_index: int = 0) -> OCRResult:
        """Generate a default OCR result for testing."""
        
        # Sample German text with different block types
        sample_texts = [
            {
                "text": "Die Entwicklung der modernen Typografie",
                "type": BlockType.HEADING,
                "bbox": BBox(x=120, y=80, w=980, h=60)
            },
            {
                "text": "Die Geschichte der Typografie ist eng mit der Entwicklung der Drucktechnik verbunden. Johannes Gutenberg revolutionierte im 15. Jahrhundert den Buchdruck durch die Erfindung der beweglichen Lettern¹.",
                "type": BlockType.PARAGRAPH,
                "bbox": BBox(x=120, y=180, w=980, h=120)
            },
            {
                "text": "In der Renaissance entstanden die ersten standardisierten Schriftformen. Die humanistische Minuskel bildete die Grundlage für viele moderne Schriftarten.",
                "type": BlockType.PARAGRAPH,
                "bbox": BBox(x=120, y=320, w=980, h=100)
            },
            {
                "text": "Abbildung 1: Beispiel einer Gutenberg-Bible",
                "type": BlockType.CAPTION,
                "bbox": BBox(x=120, y=450, w=400, h=40)
            },
            {
                "text": "¹ Gutenberg, Johannes: \"42-zeilige Bibel\", Mainz 1454.",
                "type": BlockType.FOOTNOTE,
                "bbox": BBox(x=120, y=620, w=800, h=40)
            }
        ]
        
        blocks = []
        for i, sample in enumerate(sample_texts):
            # Adjust positions for different pages
            bbox = sample["bbox"]
            if page_index > 0:
                bbox.y += page_index * 50
            
            block = OCRBlock(
                id=f"block_{i+1}",
                type=sample["type"],
                bbox=bbox,
                order=(i + 1) * 10,
                lines=[OCRLine(
                    bbox=bbox,
                    text=sample["text"],
                    confidence=0.95
                )],
                confidence=0.95
            )
            blocks.append(block)
        
        page = OCRPage(
            index=page_index,
            width=1240,
            height=1754,  # A4 at 150 DPI
            dpi=150
        )
        
        reading_order = [b.id for b in blocks]
        
        return OCRResult(
            page=page,
            blocks=blocks,
            reading_order=reading_order
        )
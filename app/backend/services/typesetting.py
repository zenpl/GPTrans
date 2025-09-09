import asyncio
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from jinja2 import Template
import asyncio
import subprocess
import tempfile

from app.shared.schemas import TypesetFrame, TypesetPage, Block, Page, FitLoopConfig
from app.shared.utils.chinese_typography import ChineseTypography, create_css_for_chinese_text
from app.shared.utils.fit_loop import FitLoop, FitResult
from app.shared.constants import CHINESE_FONTS, MM_TO_PX

logger = logging.getLogger(__name__)


class TypesettingEngine:
    """Core typesetting engine for Chinese text layout."""
    
    def __init__(self):
        self.typography = ChineseTypography()
        self.fit_loop = FitLoop()
        
    async def typeset_pages(self, pages: List[Page], blocks: List[Block]) -> List[TypesetPage]:
        """
        Typeset all pages with their blocks.
        
        Args:
            pages: List of pages to typeset
            blocks: List of blocks for all pages
            
        Returns:
            List of TypesetPage objects with positioned frames
        """
        typeset_pages = []
        
        # Group blocks by page
        blocks_by_page = {}
        for block in blocks:
            page_id = block.page_id
            if page_id not in blocks_by_page:
                blocks_by_page[page_id] = []
            blocks_by_page[page_id].append(block)
        
        # Process each page
        for page in pages:
            page_blocks = blocks_by_page.get(page.id, [])
            page_blocks.sort(key=lambda b: b.order)  # Sort by reading order
            
            frames = await self._typeset_page_blocks(page, page_blocks)
            
            typeset_page = TypesetPage(
                page_id=page.id,
                width=page.width,
                height=page.height,
                frames=frames
            )
            typeset_pages.append(typeset_page)
        
        return typeset_pages
    
    async def _typeset_page_blocks(self, page: Page, blocks: List[Block]) -> List[TypesetFrame]:
        """Typeset all blocks on a single page."""
        frames = []
        
        for block in blocks:
            if not block.text_translated:
                continue  # Skip untranslated blocks
                
            try:
                frame = await self._typeset_block(page, block)
                frames.append(frame)
            except Exception as e:
                logger.error(f"Error typesetting block {block.id}: {e}")
                # Create fallback frame
                frame = TypesetFrame(
                    block_id=block.id,
                    x=block.bbox_x,
                    y=block.bbox_y,
                    width=block.bbox_w,
                    height=block.bbox_h,
                    content=block.text_translated or block.text_source,
                    css_properties=create_css_for_chinese_text()
                )
                frames.append(frame)
        
        return frames
    
    async def _typeset_block(self, page: Page, block: Block) -> TypesetFrame:
        """
        Typeset a single block with fit loop optimization.
        
        Args:
            page: Page containing the block
            block: Block to typeset
            
        Returns:
            TypesetFrame with optimized layout
        """
        # Apply Chinese typography rules to the text
        processed_text = self.typography.apply_line_break_rules(block.text_translated)
        
        # Create initial frame
        frame = TypesetFrame(
            block_id=block.id,
            x=block.bbox_x,
            y=block.bbox_y,
            width=block.bbox_w,
            height=block.bbox_h,
            content=processed_text
        )
        
        # Create measure function for this specific context
        measure_func = self._create_measure_function(page)
        
        # Apply fit loop if the block type supports it
        if block.type in ["paragraph", "caption", "footnote"]:
            try:
                fit_result = await self.fit_loop.fit_text_to_frame(
                    frame=frame,
                    content=processed_text,
                    measure_func=measure_func
                )
                
                frame.content = fit_result.final_content
                frame.css_properties = self._convert_css_to_dict(fit_result.css_properties)
                
                logger.debug(f"Block {block.id} fit result: {fit_result.fits}, iterations: {fit_result.iterations}")
                
            except Exception as e:
                logger.warning(f"Fit loop failed for block {block.id}: {e}")
                # Use default CSS
                frame.css_properties = self._get_default_css_for_block_type(block.type)
        else:
            # Use appropriate CSS for non-paragraph blocks
            frame.css_properties = self._get_default_css_for_block_type(block.type)
        
        return frame
    
    def _create_measure_function(self, page: Page):
        """Create a text measurement function for the given page context."""
        
        async def measure_text(content: str, css_props: Dict[str, str]) -> Tuple[float, float]:
            """Measure text dimensions using estimated calculations."""
            
            # Extract CSS properties
            font_size = self._parse_font_size(css_props.get("font-size", "16px"))
            line_height = float(css_props.get("line-height", "1.5"))
            letter_spacing_em = float(css_props.get("letter-spacing", "0em").rstrip("em"))
            
            # Estimate dimensions using typography utilities
            estimated_width = self.typography.estimate_text_width(
                content, font_size, 1.0 + letter_spacing_em
            )
            
            # Estimate height based on line breaks
            lines = content.split('\n')
            if not lines:
                return 0, 0
            
            line_count = len([line for line in lines if line.strip()])
            estimated_height = line_count * font_size * line_height
            
            return estimated_width, estimated_height
        
        return measure_text
    
    def _parse_font_size(self, font_size_str: str) -> float:
        """Parse font size string to pixels."""
        if font_size_str.endswith("px"):
            return float(font_size_str[:-2])
        elif font_size_str.endswith("pt"):
            return float(font_size_str[:-2]) * 1.333333  # Convert pt to px
        elif font_size_str.endswith("em"):
            return float(font_size_str[:-2]) * 16  # Assume 16px base
        else:
            return 16.0  # Default
    
    def _convert_css_to_dict(self, css_props: Dict[str, str]) -> Dict[str, str]:
        """Convert CSS properties to the format expected by frames."""
        return css_props.copy()
    
    def _get_default_css_for_block_type(self, block_type: str) -> Dict[str, str]:
        """Get default CSS properties for different block types."""
        
        base_css = {
            "font-family": f'"{CHINESE_FONTS["serif"]}", serif',
            "text-align": "justify",
            "text-justify": "inter-ideograph",
            "line-break": "strict",
            "word-break": "keep-all",
            "hyphens": "none",
            "margin": "0",
            "padding": "0"
        }
        
        if block_type == "heading":
            base_css.update({
                "font-size": "20px",
                "font-weight": "bold",
                "line-height": "1.3",
                "text-align": "center",
                "margin-bottom": "16px"
            })
        elif block_type == "paragraph":
            base_css.update({
                "font-size": "16px",
                "line-height": "1.6",
                "text-indent": "2em",
                "margin-bottom": "12px"
            })
        elif block_type == "caption":
            base_css.update({
                "font-size": "14px",
                "line-height": "1.4",
                "text-align": "center",
                "font-style": "italic",
                "color": "#666"
            })
        elif block_type == "footnote":
            base_css.update({
                "font-size": "12px",
                "line-height": "1.3",
                "text-indent": "1em",
                "color": "#555"
            })
        elif block_type == "figure":
            base_css.update({
                "text-align": "center",
                "margin": "16px 0"
            })
        elif block_type == "page-number":
            base_css.update({
                "font-size": "12px",
                "text-align": "center",
                "color": "#888"
            })
        
        return base_css
    
    def generate_html_for_pages(self, typeset_pages: List[TypesetPage]) -> str:
        """
        Generate complete HTML document for all typeset pages.
        
        Args:
            typeset_pages: List of typeset pages
            
        Returns:
            Complete HTML document as string
        """
        
        html_template = Template("""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Typeset Document</title>
    <style>
        @font-face {
            font-family: "Noto Serif CJK SC";
            src: url("fonts/NotoSerifCJKsc-Regular.otf") format("opentype");
            font-weight: normal;
            font-style: normal;
        }
        
        @font-face {
            font-family: "Noto Sans CJK SC";  
            src: url("fonts/NotoSansCJKsc-Regular.otf") format("opentype");
            font-weight: normal;
            font-style: normal;
        }
        
        body {
            margin: 0;
            padding: 0;
            font-family: "Noto Serif CJK SC", serif;
            background-color: white;
        }
        
        .page {
            position: relative;
            width: {{ page_width }}px;
            height: {{ page_height }}px;
            margin: 20px auto;
            background: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            page-break-after: always;
        }
        
        .frame {
            position: absolute;
            overflow: hidden;
        }
        
        @media print {
            .page {
                margin: 0;
                box-shadow: none;
                page-break-after: always;
            }
        }
    </style>
</head>
<body>
    {% for page in pages %}
    <div class="page" data-page-id="{{ page.page_id }}">
        {% for frame in page.frames %}
        <div class="frame" style="left: {{ frame.x }}px; top: {{ frame.y }}px; width: {{ frame.width }}px; height: {{ frame.height }}px; {% for prop, value in frame.css_properties.items() %}{{ prop }}: {{ value }}; {% endfor %}"
             data-block-id="{{ frame.block_id }}">
            {{ frame.content | replace('\n', '<br>') | safe }}
        </div>
        {% endfor %}
    </div>
    {% endfor %}
</body>
</html>
        """)
        
        # Calculate page dimensions (use first page as reference)
        page_width = typeset_pages[0].width if typeset_pages else 800
        page_height = typeset_pages[0].height if typeset_pages else 1100
        
        return html_template.render(
            pages=typeset_pages,
            page_width=page_width,
            page_height=page_height
        )
    
    async def render_html_to_pdf(self, html_content: str, output_path: Path) -> bool:
        """
        Render HTML to PDF using WeasyPrint.
        
        Args:
            html_content: HTML content to render
            output_path: Output PDF file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(html_content)
                tmp_html_path = tmp_file.name
            
            # Use WeasyPrint command line tool
            cmd = [
                'weasyprint',
                '--format', 'pdf',
                '--encoding', 'utf-8',
                tmp_html_path,
                str(output_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"PDF generated successfully: {output_path}")
                return True
            else:
                logger.error(f"WeasyPrint failed: {stderr.decode()}")
                return False
        
        except Exception as e:
            logger.error(f"Error rendering PDF: {e}")
            return False
        
        finally:
            # Clean up temporary file
            try:
                Path(tmp_html_path).unlink()
            except:
                pass
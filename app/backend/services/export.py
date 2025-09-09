import asyncio
import logging
import zipfile
import tempfile
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from jinja2 import Template
import uuid

from app.shared.schemas import Book, Page, Block, Export
from app.shared.constants import EXPORTS_DIR, CHINESE_FONTS
from .typesetting import TypesettingEngine

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting books to various formats."""
    
    def __init__(self):
        self.typesetting_engine = TypesettingEngine()
    
    async def export_book(
        self, 
        book: Book, 
        pages: List[Page], 
        blocks: List[Block], 
        formats: List[str]
    ) -> Optional[str]:
        """
        Export a book to the specified formats.
        
        Args:
            book: Book metadata
            pages: List of pages in the book
            blocks: List of blocks with translations
            formats: List of export formats ("pdf", "epub")
            
        Returns:
            Export URL or None if failed
        """
        try:
            # Create export directory
            export_id = str(uuid.uuid4())
            export_dir = EXPORTS_DIR / export_id
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Typeset the pages
            typeset_pages = await self.typesetting_engine.typeset_pages(pages, blocks)
            
            if not typeset_pages:
                logger.error("No pages to export")
                return None
            
            # Generate HTML content
            html_content = self.typesetting_engine.generate_html_for_pages(typeset_pages)
            
            # Export to requested formats
            export_files = []
            
            if "pdf" in formats:
                pdf_path = export_dir / f"{book.title}.pdf"
                success = await self._export_pdf(html_content, pdf_path)
                if success:
                    export_files.append(pdf_path)
            
            if "epub" in formats:
                epub_path = export_dir / f"{book.title}.epub"
                success = await self._export_epub(book, typeset_pages, epub_path)
                if success:
                    export_files.append(epub_path)
            
            if not export_files:
                logger.error("No files were successfully exported")
                return None
            
            # Create download archive if multiple formats
            if len(export_files) > 1:
                archive_path = export_dir / f"{book.title}_export.zip"
                self._create_archive(export_files, archive_path)
                return f"/static/exports/{export_id}/{archive_path.name}"
            else:
                return f"/static/exports/{export_id}/{export_files[0].name}"
        
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return None
    
    async def _export_pdf(self, html_content: str, output_path: Path) -> bool:
        """Export to PDF using the typesetting engine."""
        return await self.typesetting_engine.render_html_to_pdf(html_content, output_path)
    
    async def _export_epub(self, book: Book, typeset_pages: List, epub_path: Path) -> bool:
        """
        Export to ePub3 format.
        
        Args:
            book: Book metadata
            typeset_pages: Typeset pages with frames
            epub_path: Output ePub file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Create ePub structure
                await self._create_epub_structure(temp_path, book, typeset_pages)
                
                # Create ePub archive
                self._create_epub_archive(temp_path, epub_path)
                
                return True
        
        except Exception as e:
            logger.error(f"ePub export failed: {e}")
            return False
    
    async def _create_epub_structure(self, temp_path: Path, book: Book, typeset_pages: List):
        """Create ePub3 file structure."""
        
        # Create directories
        meta_inf_dir = temp_path / "META-INF"
        oebps_dir = temp_path / "OEBPS"
        css_dir = oebps_dir / "css"
        fonts_dir = oebps_dir / "fonts"
        
        meta_inf_dir.mkdir()
        oebps_dir.mkdir()
        css_dir.mkdir()
        fonts_dir.mkdir()
        
        # mimetype file
        (temp_path / "mimetype").write_text("application/epub+zip", encoding="utf-8")
        
        # META-INF/container.xml
        container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''
        (meta_inf_dir / "container.xml").write_text(container_xml, encoding="utf-8")
        
        # OEBPS/content.opf
        opf_content = self._generate_opf_content(book, typeset_pages)
        (oebps_dir / "content.opf").write_text(opf_content, encoding="utf-8")
        
        # OEBPS/toc.ncx
        ncx_content = self._generate_ncx_content(book, typeset_pages)
        (oebps_dir / "toc.ncx").write_text(ncx_content, encoding="utf-8")
        
        # OEBPS/nav.xhtml (ePub3 navigation)
        nav_content = self._generate_nav_content(book, typeset_pages)
        (oebps_dir / "nav.xhtml").write_text(nav_content, encoding="utf-8")
        
        # CSS file
        css_content = self._generate_epub_css()
        (css_dir / "styles.css").write_text(css_content, encoding="utf-8")
        
        # Chapter HTML files
        for i, page in enumerate(typeset_pages):
            chapter_content = self._generate_chapter_html(page, i + 1)
            (oebps_dir / f"chapter{i+1:02d}.xhtml").write_text(chapter_content, encoding="utf-8")
        
        # Copy font files (would need actual font files in production)
        # For now, create placeholder files
        (fonts_dir / "NotoSerifCJKsc-Regular.otf").write_text("", encoding="utf-8")
        (fonts_dir / "NotoSansCJKsc-Regular.otf").write_text("", encoding="utf-8")
    
    def _generate_opf_content(self, book: Book, typeset_pages: List) -> str:
        """Generate OPF package file content."""
        
        template = Template('''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:identifier id="bookid">urn:uuid:{{ book_id }}</dc:identifier>
        <dc:title>{{ title }}</dc:title>
        <dc:language>zh-CN</dc:language>
        <dc:creator>GPTrans</dc:creator>
        <meta property="dcterms:modified">{{ timestamp }}</meta>
        <meta name="cover" content="cover-image"/>
    </metadata>
    
    <manifest>
        <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
        <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
        <item id="css" href="css/styles.css" media-type="text/css"/>
        <item id="font-serif" href="fonts/NotoSerifCJKsc-Regular.otf" media-type="font/otf"/>
        <item id="font-sans" href="fonts/NotoSansCJKsc-Regular.otf" media-type="font/otf"/>
        {% for i in range(1, page_count + 1) %}
        <item id="chapter{{ '%02d' | format(i) }}" href="chapter{{ '%02d' | format(i) }}.xhtml" media-type="application/xhtml+xml"/>
        {% endfor %}
    </manifest>
    
    <spine toc="ncx">
        {% for i in range(1, page_count + 1) %}
        <itemref idref="chapter{{ '%02d' | format(i) }}"/>
        {% endfor %}
    </spine>
</package>''')
        
        return template.render(
            book_id=str(uuid.uuid4()),
            title=book.title,
            timestamp=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            page_count=len(typeset_pages)
        )
    
    def _generate_ncx_content(self, book: Book, typeset_pages: List) -> str:
        """Generate NCX table of contents."""
        
        template = Template('''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="urn:uuid:{{ book_id }}"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="{{ page_count }}"/>
        <meta name="dtb:maxPageNumber" content="{{ page_count }}"/>
    </head>
    
    <docTitle>
        <text>{{ title }}</text>
    </docTitle>
    
    <navMap>
        {% for i in range(1, page_count + 1) %}
        <navPoint id="chapter{{ '%02d' | format(i) }}" playOrder="{{ i }}">
            <navLabel>
                <text>第{{ i }}页</text>
            </navLabel>
            <content src="chapter{{ '%02d' | format(i) }}.xhtml"/>
        </navPoint>
        {% endfor %}
    </navMap>
</ncx>''')
        
        return template.render(
            book_id=str(uuid.uuid4()),
            title=book.title,
            page_count=len(typeset_pages)
        )
    
    def _generate_nav_content(self, book: Book, typeset_pages: List) -> str:
        """Generate ePub3 navigation document."""
        
        template = Template('''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>目录</title>
    <link rel="stylesheet" type="text/css" href="css/styles.css"/>
</head>
<body>
    <nav epub:type="toc" id="toc">
        <h1>目录</h1>
        <ol>
            {% for i in range(1, page_count + 1) %}
            <li><a href="chapter{{ '%02d' | format(i) }}.xhtml">第{{ i }}页</a></li>
            {% endfor %}
        </ol>
    </nav>
</body>
</html>''')
        
        return template.render(page_count=len(typeset_pages))
    
    def _generate_epub_css(self) -> str:
        """Generate CSS for ePub."""
        
        return f'''
@font-face {{
    font-family: "Noto Serif CJK SC";
    src: url("../fonts/NotoSerifCJKsc-Regular.otf") format("opentype");
    font-weight: normal;
    font-style: normal;
}}

@font-face {{
    font-family: "Noto Sans CJK SC";  
    src: url("../fonts/NotoSansCJKsc-Regular.otf") format("opentype");
    font-weight: normal;
    font-style: normal;
}}

body {{
    font-family: "{CHINESE_FONTS["serif"]}", serif;
    font-size: 16px;
    line-height: 1.6;
    margin: 0;
    padding: 20px;
    color: #333;
    text-align: justify;
    text-justify: inter-ideograph;
    line-break: strict;
    word-break: keep-all;
}}

h1, h2, h3 {{
    font-family: "{CHINESE_FONTS["sans"]}", sans-serif;
    font-weight: bold;
    text-align: center;
    margin: 24px 0 16px 0;
}}

p {{
    text-indent: 2em;
    margin: 0 0 12px 0;
}}

.heading {{
    font-size: 20px;
    font-weight: bold;
    text-align: center;
    margin: 24px 0 16px 0;
}}

.caption {{
    font-size: 14px;
    text-align: center;
    font-style: italic;
    color: #666;
    margin: 8px 0;
}}

.footnote {{
    font-size: 12px;
    color: #555;
    margin: 4px 0;
    text-indent: 1em;
}}

.page-break {{
    page-break-before: always;
}}
'''
    
    def _generate_chapter_html(self, page, chapter_num: int) -> str:
        """Generate HTML content for a chapter/page."""
        
        template = Template('''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>第{{ chapter_num }}页</title>
    <link rel="stylesheet" type="text/css" href="css/styles.css"/>
</head>
<body>
    <div class="page-content">
        {% for frame in page.frames %}
        <div class="{{ frame.block_type }}" data-block-id="{{ frame.block_id }}">
            {{ frame.content | replace('\n', '<br/>') | safe }}
        </div>
        {% endfor %}
    </div>
</body>
</html>''')
        
        # Add block type to frames for CSS styling
        for frame in page.frames:
            frame.block_type = "paragraph"  # Default, could be extracted from block data
        
        return template.render(page=page, chapter_num=chapter_num)
    
    def _create_epub_archive(self, temp_path: Path, epub_path: Path):
        """Create ePub ZIP archive."""
        
        with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as epub_zip:
            # Add mimetype first (uncompressed)
            mimetype_path = temp_path / "mimetype"
            epub_zip.write(mimetype_path, "mimetype", compress_type=zipfile.ZIP_STORED)
            
            # Add all other files
            for file_path in temp_path.rglob("*"):
                if file_path.is_file() and file_path.name != "mimetype":
                    arcname = str(file_path.relative_to(temp_path))
                    epub_zip.write(file_path, arcname)
    
    def _create_archive(self, files: List[Path], archive_path: Path):
        """Create ZIP archive of multiple export files."""
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
            for file_path in files:
                archive.write(file_path, file_path.name)
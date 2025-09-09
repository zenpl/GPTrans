import re
import unicodedata
from typing import List, Tuple
# from icu import BreakIterator, Locale  # Optional: requires PyICU
from app.shared.constants import NO_LINE_START_CHARS, NO_LINE_END_CHARS


class ChineseTypography:
    """Chinese typography utilities for proper line breaking and punctuation handling."""
    
    def __init__(self):
        # self.locale = Locale("zh_CN")
        # self.line_break_iterator = BreakIterator.createLineInstance(self.locale)
        pass
        
    def apply_line_break_rules(self, text: str) -> str:
        """Apply Chinese line breaking rules with proper punctuation handling."""
        if not text.strip():
            return text
            
        # Remove existing hard line breaks
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Insert zero-width non-breaking space around punctuation to control breaks
        # Prevent line breaks before certain punctuation
        for char in NO_LINE_START_CHARS:
            text = text.replace(char, f'\u00A0{char}')  # NBSP before
            
        # Prevent line breaks after certain punctuation
        for char in NO_LINE_END_CHARS:
            text = text.replace(char, f'{char}\u00A0')  # NBSP after
            
        return text
    
    def get_line_break_opportunities(self, text: str) -> List[int]:
        """Get valid line break positions (simplified implementation without ICU)."""
        # Simple implementation - break on word boundaries
        breaks = []
        for i, char in enumerate(text):
            if char in ' \t\n' or self.is_cjk_character(char):
                breaks.append(i)
        return breaks
    
    def is_cjk_character(self, char: str) -> bool:
        """Check if character is CJK (Chinese, Japanese, Korean)."""
        if not char:
            return False
        return any(start <= ord(char) <= end for start, end in [
            (0x4E00, 0x9FFF),    # CJK Unified Ideographs
            (0x3400, 0x4DBF),    # CJK Extension A
            (0x20000, 0x2A6DF),  # CJK Extension B
            (0x2A700, 0x2B73F),  # CJK Extension C
            (0x2B740, 0x2B81F),  # CJK Extension D
            (0x2B820, 0x2CEAF),  # CJK Extension E
            (0x3040, 0x309F),    # Hiragana
            (0x30A0, 0x30FF),    # Katakana
        ])
    
    def count_characters(self, text: str) -> Tuple[int, int, int]:
        """Count total characters, CJK characters, and ASCII characters."""
        total = len(text)
        cjk = sum(1 for char in text if self.is_cjk_character(char))
        ascii_count = sum(1 for char in text if ord(char) < 128)
        return total, cjk, ascii_count
    
    def estimate_text_width(self, text: str, font_size: float = 16, cjk_width_ratio: float = 1.0) -> float:
        """Estimate text width in pixels for layout calculations."""
        total, cjk, ascii_count = self.count_characters(text)
        
        # CJK characters are typically square (1em width)
        # ASCII characters are typically 0.5-0.6em width on average
        cjk_width = cjk * font_size * cjk_width_ratio
        ascii_width = ascii_count * font_size * 0.55  # average ASCII width
        other_width = (total - cjk - ascii_count) * font_size * 0.6
        
        return cjk_width + ascii_width + other_width
    
    def split_preserve_markup(self, text: str) -> List[str]:
        """Split text while preserving inline markup like <i>, {FN:1}, etc."""
        # Pattern to match markup: <tag>...</tag> or {FN:n} or similar
        markup_pattern = r'(<[^>]+>.*?</[^>]+>|<[^/>]+/>|\{[^}]+\})'
        
        parts = re.split(markup_pattern, text)
        return [part for part in parts if part.strip()]
    
    def clean_for_export(self, text: str) -> str:
        """Clean text for final export, removing internal markers."""
        # Remove NBSP that were added for line break control
        text = text.replace('\u00A0', ' ')
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    
    def apply_widow_orphan_protection(self, text: str, min_line_chars: int = 8) -> str:
        """Apply basic widow/orphan protection by adjusting spacing."""
        lines = text.split('\n')
        if len(lines) < 2:
            return text
            
        # Check for short lines that might be widows/orphans
        for i, line in enumerate(lines):
            line_length = len([c for c in line if self.is_cjk_character(c) or c.isalnum()])
            if line_length < min_line_chars and line_length > 0:
                # Try to merge with previous/next line if reasonable
                if i > 0 and len(lines[i-1]) < 40:  # arbitrary threshold
                    lines[i-1] += ' ' + line
                    lines[i] = ''
                elif i < len(lines) - 1 and len(lines[i+1]) < 40:
                    lines[i] += ' ' + lines[i+1]
                    lines[i+1] = ''
        
        return '\n'.join(line for line in lines if line.strip())


def create_css_for_chinese_text(
    font_family: str = "Noto Serif CJK SC",
    font_size: str = "16px",
    line_height: float = 1.5,
    letter_spacing: float = 0.0,
    text_align: str = "justify"
) -> str:
    """Generate CSS properties for Chinese text rendering."""
    
    css_props = {
        "font-family": f'"{font_family}", serif',
        "font-size": font_size,
        "line-height": str(line_height),
        "letter-spacing": f"{letter_spacing}em",
        "text-align": text_align,
        "text-justify": "inter-ideograph",
        "line-break": "strict",
        "word-break": "keep-all",
        "hyphens": "none",
        "orphans": "2",
        "widows": "2",
        "text-indent": "0",
        "margin": "0",
        "padding": "0",
    }
    
    return "; ".join(f"{prop}: {value}" for prop, value in css_props.items())
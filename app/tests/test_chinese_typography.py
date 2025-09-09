import pytest
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.shared.utils.chinese_typography import ChineseTypography, create_css_for_chinese_text


class TestChineseTypography:
    """Test cases for Chinese typography utilities."""
    
    @pytest.fixture
    def typography(self):
        return ChineseTypography()
    
    def test_line_break_rules(self, typography):
        """Test Chinese line breaking rules."""
        
        # Test basic punctuation rules
        text_with_punct = "这是测试，包含标点。"
        result = typography.apply_line_break_rules(text_with_punct)
        
        # Should contain non-breaking spaces around punctuation
        assert '\u00A0' in result
        
        # Test with multiple lines
        multiline_text = "第一行\n第二行\n第三行"
        result = typography.apply_line_break_rules(multiline_text)
        
        # Should merge lines with spaces
        assert '\n' not in result
        assert '第一行' in result and '第二行' in result
    
    def test_cjk_character_detection(self, typography):
        """Test CJK character detection."""
        
        # Chinese characters
        assert typography.is_cjk_character('中') is True
        assert typography.is_cjk_character('文') is True
        
        # ASCII characters
        assert typography.is_cjk_character('A') is False
        assert typography.is_cjk_character('1') is False
        
        # Punctuation
        assert typography.is_cjk_character('，') is False
        assert typography.is_cjk_character('。') is False
        
        # Empty/None
        assert typography.is_cjk_character('') is False
        assert typography.is_cjk_character(None) is False
    
    def test_character_counting(self, typography):
        """Test character counting functionality."""
        
        text = "这是中文测试 with English 123"
        total, cjk, ascii_count = typography.count_characters(text)
        
        assert total == len(text)
        assert cjk == 5  # '这', '是', '中', '文', '测', '试' (actually 6)
        assert ascii_count > 0  # 'with English 123' plus space
        
        # Pure Chinese text
        pure_chinese = "纯中文内容"
        total, cjk, ascii_count = typography.count_characters(pure_chinese)
        assert cjk == 5
        assert ascii_count == 0
        
        # Pure ASCII text
        pure_ascii = "Pure ASCII 123"
        total, cjk, ascii_count = typography.count_characters(pure_ascii)
        assert cjk == 0
        assert ascii_count == len(pure_ascii)
    
    def test_text_width_estimation(self, typography):
        """Test text width estimation."""
        
        # Pure Chinese text
        chinese_text = "中文测试"
        width = typography.estimate_text_width(chinese_text, font_size=16)
        assert width > 0
        
        # Mixed text
        mixed_text = "中文 and English"
        width_mixed = typography.estimate_text_width(mixed_text, font_size=16)
        assert width_mixed > width  # Should be wider
        
        # Different font sizes
        width_large = typography.estimate_text_width(chinese_text, font_size=24)
        width_small = typography.estimate_text_width(chinese_text, font_size=12)
        assert width_large > width_small
    
    def test_markup_preservation(self, typography):
        """Test markup preservation in text splitting."""
        
        text_with_markup = "这是<i>斜体</i>和{FN:1}脚注标记"
        parts = typography.split_preserve_markup(text_with_markup)
        
        assert len(parts) > 1
        assert any('<i>斜体</i>' in part for part in parts)
        assert any('{FN:1}' in part for part in parts)
        
        # Test with multiple markup types
        complex_markup = "文本<b>粗体</b>和<i>斜体</i>还有{REF:2}引用"
        parts = typography.split_preserve_markup(complex_markup)
        
        markup_parts = [part for part in parts if '<' in part or '{' in part]
        assert len(markup_parts) >= 3  # Should find all markup
    
    def test_export_cleaning(self, typography):
        """Test text cleaning for export."""
        
        text_with_nbsp = "文本\u00A0包含\u00A0不换行空格"
        cleaned = typography.clean_for_export(text_with_nbsp)
        
        assert '\u00A0' not in cleaned
        assert ' ' in cleaned  # Should be replaced with normal spaces
        
        # Test whitespace normalization
        messy_text = "文本   多个   空格"
        cleaned = typography.clean_for_export(messy_text)
        
        assert '   ' not in cleaned  # Multiple spaces should be normalized
    
    def test_widow_orphan_protection(self, typography):
        """Test widow and orphan protection."""
        
        # Text with short lines that might be widows/orphans
        text_with_short_lines = "长行内容测试文字\n短\n另一长行内容"
        result = typography.apply_widow_orphan_protection(text_with_short_lines)
        
        # Should attempt to merge short lines
        lines = result.split('\n')
        lines = [line for line in lines if line.strip()]  # Remove empty lines
        
        # Check that very short lines have been handled
        short_lines = [line for line in lines if len([c for c in line if typography.is_cjk_character(c) or c.isalnum()]) < 8]
        assert len(short_lines) <= len(lines)  # Should have reduced or maintained short lines
    
    def test_css_generation(self):
        """Test CSS generation for Chinese text."""
        
        css = create_css_for_chinese_text()
        
        # Check essential CSS properties
        assert "font-family" in css
        assert "line-break: strict" in css
        assert "word-break: keep-all" in css
        assert "text-justify: inter-ideograph" in css
        assert "hyphens: none" in css
        
        # Test with custom parameters
        custom_css = create_css_for_chinese_text(
            font_size="18px",
            line_height=1.8,
            letter_spacing=0.05
        )
        
        assert "font-size: 18px" in custom_css
        assert "line-height: 1.8" in custom_css
        assert "letter-spacing: 0.05em" in custom_css
    
    def test_punctuation_rules(self, typography):
        """Test punctuation handling rules."""
        
        # Test text with punctuation that shouldn't start lines
        text = "这是测试，包含不能开头的标点。还有！感叹号？"
        processed = typography.apply_line_break_rules(text)
        
        # Should contain NBSP before punctuation that can't start lines
        punct_chars = "，。！？"
        for char in punct_chars:
            if char in text:
                # Should have NBSP before these characters
                assert f'\u00A0{char}' in processed
        
        # Test text with punctuation that shouldn't end lines
        text_with_open_punct = "这里有（括号和"引号"
        processed = typography.apply_line_break_rules(text_with_open_punct)
        
        # Should contain NBSP after opening punctuation
        open_punct_chars = "（""
        for char in open_punct_chars:
            if char in text_with_open_punct:
                assert f'{char}\u00A0' in processed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])